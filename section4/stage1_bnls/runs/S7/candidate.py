"""
S7 candidate solver: B-NLS Burgers bore (u) colliding with NLS bright soliton (N).

Three method combinations are implemented and run as Experiments E1, E2, E3:

  E1  (negative control): all-spectral RK4 on (u, N, phi) with no dealiasing.
                          Expected to Gibbs-oscillate at the bore and to blow up
                          in the HJ equation via the quantum pressure term
                          (sqrt N)_xx / (2 sqrt N) as the soliton tail thins.

  E2  (intended success): MUSCL-Godunov SSP-RK3 on u for the Burgers self-flux;
                          Strang-split Madelung-Psi on Psi = sqrt(N) e^{i phi}
                          for the NLS sector with Burgers boost u via an
                          advection sub-step.  This is the FINAL CANDIDATE
                          method.

  E3  (intermediate):     MUSCL-Godunov on u + spectral SSP-RK3 on (N, phi) in
                          Madelung-free form.  Shows that the bare quantum
                          pressure (sqrt N)_xx/(2 sqrt N) blows up immediately
                          whenever N goes through small values -- shock
                          capturing on u alone is NOT enough.

For each method we run T = 0 .. 8.0 on x in [-15, 15], Nx = 256.

Mass conservation (|Psi|^2 integral) is reported snapshot-by-snapshot for E2
to characterize the dt -> mass-drift boundary.

PDE (kappa = +1):
  m_t + (u m)_x + m u_x = 0,         m := u - N phi_x        (EPDiff-Burgers)
  N_t + d_x((u + phi_x) N) = 0                                (continuity)
  phi_t + u phi_x + (1/2) phi_x^2 + (sqrt N)_xx/(2 sqrt N) - 2 kappa N = 0
"""

import os
import numpy as np

# ----------------------------- Grid -----------------------------
L = 30.0
Nx = 256
dx = L / Nx
x = -15.0 + dx * np.arange(Nx)

# Wavenumbers (periodic FFT, fftfreq convention)
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
mk2 = -(k ** 2)
# 2/3 dealias mask (anti-Gibbs for cubic nonlinearity in E2)
kmax = float(np.max(np.abs(k)))
DEALIAS = (np.abs(k) <= (2.0 / 3.0) * kmax).astype(float)

KAPPA = 1.0
T_FINAL = 8.0

# ----------------------------- ICs ------------------------------
def make_ic():
    u0 = 1.0 * (1.0 - np.tanh(x / 0.5)) / 2.0
    N0 = 1.0 / np.cosh(x + 8.0) ** 2
    phi0 = 0.6 * x
    return u0, N0, phi0

# ----------------------------- Spectral helpers ----------------
def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def d2x_spec(f):
    return np.real(np.fft.ifft(mk2 * np.fft.fft(f)))

# ------------------------- MUSCL + Godunov for u-Burgers --------
# Conservative finite-volume update of u_t = -(1/2) d_x(u^2).

def muscl_godunov_burgers_rhs(u):
    """Return du/dt contribution from u_t + u u_x = 0."""
    du_b = u - np.roll(u, 1)
    du_f = np.roll(u, -1) - u
    eps = 1e-30
    sigma = (np.sign(du_b) + np.sign(du_f)) * np.abs(du_b * du_f) \
            / (np.abs(du_b) + np.abs(du_f) + eps)
    uL = u + 0.5 * sigma
    uR_next = np.roll(u, -1) - 0.5 * np.roll(sigma, -1)
    le = uL <= uR_next
    contains_zero = (uL <= 0) & (uR_next >= 0)
    F1 = 0.5 * np.minimum(uL * uL, uR_next * uR_next)
    F1 = np.where(contains_zero, 0.0, F1)
    F2 = 0.5 * np.maximum(uL * uL, uR_next * uR_next)
    F = np.where(le, F1, F2)
    return -(F - np.roll(F, 1)) / dx

def ssp_rk3_u_step(u, dt):
    k1 = muscl_godunov_burgers_rhs(u)
    u1 = u + dt * k1
    k2 = muscl_godunov_burgers_rhs(u1)
    u2 = 0.75 * u + 0.25 * (u1 + dt * k2)
    k3 = muscl_godunov_burgers_rhs(u2)
    return (1.0 / 3.0) * u + (2.0 / 3.0) * (u2 + dt * k3)

# -------------------------------------------------------------------------
#                     E1:  all-spectral RK4 on (u, N, phi)
# -------------------------------------------------------------------------

def rhs_E1(u, N, phi):
    phix = dx_spec(phi)
    u_x = dx_spec(u)
    du = -u * u_x
    flux = (u + phix) * N
    dN = -dx_spec(flux)
    sN = np.sqrt(np.maximum(N, 1e-30))
    qp = d2x_spec(sN) / (2.0 * sN)
    dphi = -u * phix - 0.5 * phix * phix - qp + 2.0 * KAPPA * N
    return du, dN, dphi

def rk4_step_E1(u, N, phi, dt):
    k1u, k1N, k1p = rhs_E1(u, N, phi)
    k2u, k2N, k2p = rhs_E1(u + 0.5*dt*k1u, N + 0.5*dt*k1N, phi + 0.5*dt*k1p)
    k3u, k3N, k3p = rhs_E1(u + 0.5*dt*k2u, N + 0.5*dt*k2N, phi + 0.5*dt*k2p)
    k4u, k4N, k4p = rhs_E1(u + dt*k3u,     N + dt*k3N,     phi + dt*k3p)
    return (u + (dt/6.0)*(k1u + 2*k2u + 2*k3u + k4u),
            N + (dt/6.0)*(k1N + 2*k2N + 2*k3N + k4N),
            phi + (dt/6.0)*(k1p + 2*k2p + 2*k3p + k4p))

def run_E1():
    u, N, phi = make_ic()
    dt = 5e-4
    n_steps = int(np.ceil(T_FINAL / dt))
    dt = T_FINAL / n_steps
    n_snap = 21
    snap_every = max(1, n_steps // (n_snap - 1))
    snaps_u, snaps_N, snaps_phi = [u.copy()], [N.copy()], [phi.copy()]
    u_max_during = float(np.max(np.abs(u)))
    blew_at = None
    with np.errstate(over='ignore', invalid='ignore'):
        for step in range(1, n_steps + 1):
            u, N, phi = rk4_step_E1(u, N, phi, dt)
            if np.all(np.isfinite(u)):
                u_max_during = max(u_max_during, float(np.max(np.abs(u))))
            if not (np.all(np.isfinite(u)) and np.all(np.isfinite(N)) and np.all(np.isfinite(phi))):
                blew_at = step * dt
                print(f"  E1 BLEW UP at t={blew_at:.4f}")
                break
            if step % snap_every == 0 or step == n_steps:
                snaps_u.append(u.copy()); snaps_N.append(N.copy()); snaps_phi.append(phi.copy())
    # pad with the last good snapshot if blew up
    while len(snaps_u) < n_snap + 1:
        snaps_u.append(snaps_u[-1].copy()); snaps_N.append(snaps_N[-1].copy()); snaps_phi.append(snaps_phi[-1].copy())
    return dict(u=np.array(snaps_u), N=np.array(snaps_N), phi=np.array(snaps_phi),
                u_max=u_max_during, blew_at=blew_at, dt=dt)

# -------------------------------------------------------------------------
#                E3:  MUSCL on u + spectral SSP-RK3 on (N, phi)
# -------------------------------------------------------------------------

def rhs_E3_Nphi(u, N, phi):
    """RHS for N and phi only, given fixed u (for stage-split SSP-RK3)."""
    phix = dx_spec(phi)
    flux = (u + phix) * N
    dN = -dx_spec(flux)
    sN = np.sqrt(np.maximum(N, 1e-30))
    qp = d2x_spec(sN) / (2.0 * sN)
    dphi = -u * phix - 0.5 * phix * phix - qp + 2.0 * KAPPA * N
    return dN, dphi

def ssp_rk3_Nphi_step(u_frozen, N, phi, dt):
    k1N, k1p = rhs_E3_Nphi(u_frozen, N, phi)
    N1 = N + dt * k1N; p1 = phi + dt * k1p
    k2N, k2p = rhs_E3_Nphi(u_frozen, N1, p1)
    N2 = 0.75*N + 0.25*(N1 + dt*k2N)
    p2 = 0.75*phi + 0.25*(p1 + dt*k2p)
    k3N, k3p = rhs_E3_Nphi(u_frozen, N2, p2)
    Nn = (1.0/3.0)*N + (2.0/3.0)*(N2 + dt*k3N)
    pn = (1.0/3.0)*phi + (2.0/3.0)*(p2 + dt*k3p)
    return Nn, pn

def run_E3():
    u, N, phi = make_ic()
    dt = 2e-3
    n_steps = int(np.ceil(T_FINAL / dt))
    dt = T_FINAL / n_steps
    n_snap = 21
    snap_every = max(1, n_steps // (n_snap - 1))
    snaps_u, snaps_N, snaps_phi = [u.copy()], [N.copy()], [phi.copy()]
    u_max_during = float(np.max(np.abs(u)))
    blew_at = None
    with np.errstate(over='ignore', invalid='ignore'):
        for step in range(1, n_steps + 1):
            u_new = ssp_rk3_u_step(u, dt)
            N, phi = ssp_rk3_Nphi_step(u, N, phi, dt)
            u = u_new
            if np.all(np.isfinite(u)):
                u_max_during = max(u_max_during, float(np.max(np.abs(u))))
            if not (np.all(np.isfinite(u)) and np.all(np.isfinite(N)) and np.all(np.isfinite(phi))):
                blew_at = step * dt
                print(f"  E3 BLEW UP at t={blew_at:.4f}")
                break
            if step % snap_every == 0 or step == n_steps:
                snaps_u.append(u.copy()); snaps_N.append(N.copy()); snaps_phi.append(phi.copy())
    while len(snaps_u) < n_snap + 1:
        snaps_u.append(snaps_u[-1].copy()); snaps_N.append(snaps_N[-1].copy()); snaps_phi.append(snaps_phi[-1].copy())
    return dict(u=np.array(snaps_u), N=np.array(snaps_N), phi=np.array(snaps_phi),
                u_max=u_max_during, blew_at=blew_at, dt=dt)

# -------------------------------------------------------------------------
#         E2:  MUSCL on u + Madelung-Psi Strang split on (N, phi)
# -------------------------------------------------------------------------
# Madelung NLS for the (N, phi) sector with Burgers boost u:
#   i Psi_t = -(1/2) Psi_xx  -  i u Psi_x  -  i (u_x/2) Psi  -  kappa |Psi|^2 Psi
#
# Strang split per dt:
#   1) Cubic half-step (dealiased projection of |psi|^2):
#         psi <- psi * exp(+i kappa |psi|^2 dt/2)
#   2) Linear dispersion full step (spectral):
#         psi_hat <- psi_hat * exp(-i (k^2/2) dt)
#   3) Advection full step (real-space RK2 with spectral Psi_x and u frozen):
#         d psi / dt = - u psi_x - (u_x/2) psi
#   4) Cubic half-step:
#         psi <- psi * exp(+i kappa |psi|^2 dt/2)
#
# To reduce aliasing during the focusing collision we apply the dealias mask
# in the linear step (which is the standard place for it) and also project
# |psi|^2 to its dealiased version before the cubic exponential.

def psi_from_Nphi(N, phi):
    return np.sqrt(np.maximum(N, 0.0)) * np.exp(1j * phi)

def Nphi_from_psi(psi):
    N = np.abs(psi) ** 2
    phi = np.angle(psi)
    return N, phi

def dealias(f):
    return np.fft.ifft(DEALIAS * np.fft.fft(f))

def psi_step_strang(psi, u, dt):
    # Cubic half-step
    N = np.abs(psi) ** 2
    N = np.real(dealias(N))
    psi = psi * np.exp(1j * KAPPA * N * (dt / 2.0))
    # Linear dispersion (full step, dealiased)
    psih = np.fft.fft(psi) * DEALIAS
    psih = psih * np.exp(-1j * 0.5 * (k ** 2) * dt)
    psi = np.fft.ifft(psih)
    # Advection (RK2)
    def adv_rhs(p):
        px = np.fft.ifft(ik * np.fft.fft(p))
        ux = dx_spec(u)
        return -u * px - 0.5 * ux * p
    k1 = adv_rhs(psi)
    k2 = adv_rhs(psi + dt * k1)
    psi = psi + 0.5 * dt * (k1 + k2)
    # Cubic half-step
    N = np.abs(psi) ** 2
    N = np.real(dealias(N))
    psi = psi * np.exp(1j * KAPPA * N * (dt / 2.0))
    return psi

def run_E2(dt=5e-4):
    u0, N0, phi0 = make_ic()
    u = u0.copy()
    psi = psi_from_Nphi(N0, phi0).astype(np.complex128)
    n_steps = int(np.ceil(T_FINAL / dt))
    dt = T_FINAL / n_steps
    n_snap = 21
    snap_every = max(1, n_steps // (n_snap - 1))
    snaps_u = [u.copy()]
    N0c, phi0c = Nphi_from_psi(psi)
    snaps_N = [N0c.copy()]; snaps_phi = [phi0c.copy()]
    masses = [float(np.sum(np.abs(psi) ** 2) * dx)]
    times = [0.0]
    u_max_during = float(np.max(np.abs(u)))
    blew_at = None
    # detect collision time: first snapshot at which N peak crosses x = bore_x
    # bore is initially at x ~ 0; soliton enters bore region when N peak > -1
    collision_t = None
    for step in range(1, n_steps + 1):
        # MUSCL u
        u = ssp_rk3_u_step(u, dt)
        # Strang on Psi (frozen u)
        psi = psi_step_strang(psi, u, dt)
        u_max_during = max(u_max_during, float(np.max(np.abs(u))))
        if not (np.all(np.isfinite(u)) and np.all(np.isfinite(psi))):
            blew_at = step * dt
            print(f"  E2 BLEW UP at t={blew_at:.4f}")
            break
        if step % snap_every == 0 or step == n_steps:
            N_, phi_ = Nphi_from_psi(psi)
            snaps_u.append(u.copy()); snaps_N.append(N_.copy()); snaps_phi.append(phi_.copy())
            masses.append(float(np.sum(N_) * dx))
            times.append(step * dt)
            ix = int(np.argmax(N_))
            if collision_t is None and x[ix] > -1.0:
                collision_t = step * dt
    return dict(u=np.array(snaps_u), N=np.array(snaps_N), phi=np.array(snaps_phi),
                u_max=u_max_during, blew_at=blew_at, dt=dt,
                masses=np.array(masses), times=np.array(times),
                collision_t=collision_t)

# -------------------------------------------------------------------------
#                              Driver / diagnostics
# -------------------------------------------------------------------------

def count_peaks(y, prominence=0.05):
    n = len(y)
    peaks = 0
    for i in range(n):
        l = y[(i - 1) % n]; c = y[i]; r = y[(i + 1) % n]
        if c > l and c > r and c > prominence:
            peaks += 1
    return peaks

def diagnose(label, res):
    u_fin = res['u'][-1]; N_fin = res['N'][-1]
    out = {}
    out['u_max_during_run'] = float(res['u_max'])
    out['blew_at'] = (None if res['blew_at'] is None else float(res['blew_at']))
    out['u_min_final'] = float(np.min(u_fin)) if np.all(np.isfinite(u_fin)) else float('nan')
    out['u_max_final'] = float(np.max(u_fin)) if np.all(np.isfinite(u_fin)) else float('nan')
    out['N_max_final'] = float(np.max(N_fin)) if np.all(np.isfinite(N_fin)) else float('nan')
    out['N_min_final'] = float(np.min(N_fin)) if np.all(np.isfinite(N_fin)) else float('nan')
    out['soliton_survives'] = bool(np.isfinite(out['N_max_final']) and out['N_max_final'] > 0.2)
    if np.all(np.isfinite(N_fin)):
        out['n_peaks_final'] = int(count_peaks(N_fin, prominence=0.05))
    else:
        out['n_peaks_final'] = -1
    if np.all(np.isfinite(u_fin)):
        mask = u_fin >= 0.5
        if mask.any():
            out['bore_position_final'] = float(x[np.max(np.where(mask)[0])])
        else:
            out['bore_position_final'] = float('nan')
    else:
        out['bore_position_final'] = float('nan')
    if np.all(np.isfinite(u_fin)):
        tv_u = float(np.sum(np.abs(np.diff(u_fin))))
        out['TV_u_final'] = tv_u
        out['u_overshoot_above_1'] = float(max(0.0, np.max(u_fin) - 1.0))
        out['u_undershoot_below_0'] = float(max(0.0, 0.0 - np.min(u_fin)))
    if 'masses' in res:
        out['psi_mass_initial'] = float(res['masses'][0])
        out['psi_mass_t4'] = float(res['masses'][min(10, len(res['masses'])-1)])
        out['psi_mass_final'] = float(res['masses'][-1])
        out['psi_mass_drift_pre_collision'] = float(abs(res['masses'][min(8, len(res['masses'])-1)] - res['masses'][0])/res['masses'][0])
    if 'collision_t' in res and res['collision_t'] is not None:
        out['collision_t'] = float(res['collision_t'])
    print(f"  [{label}] {out}")
    return out

if __name__ == "__main__":
    os.makedirs("pred_results", exist_ok=True)
    print("S7: B-NLS Burgers bore (u) colliding with NLS soliton (N).  T=", T_FINAL)
    print("Nx=", Nx, "dx=", dx)

    print("\n--- E1: all-spectral RK4 ---")
    r1 = run_E1()
    d1 = diagnose("E1", r1)

    print("\n--- E2: MUSCL u + Madelung-Psi Strang split (FINAL CANDIDATE) ---")
    r2 = run_E2(dt=5e-4)
    d2 = diagnose("E2", r2)

    print("\n--- E3: MUSCL u + spectral SSP-RK3 (N, phi) ---")
    r3 = run_E3()
    d3 = diagnose("E3", r3)

    np.savez("pred_results/S7.npz",
             x=x,
             E1_u=r1['u'], E1_N=r1['N'], E1_phi=r1['phi'],
             E2_u=r2['u'], E2_N=r2['N'], E2_phi=r2['phi'],
             E3_u=r3['u'], E3_N=r3['N'], E3_phi=r3['phi'],
             E2_masses=r2['masses'], E2_times=r2['times'])
    print("\nSaved pred_results/S7.npz with x, E{1,2,3}_{u,N,phi}, E2_masses, E2_times.")

    import json
    with open("pred_results/diagnostics.json", "w") as f:
        json.dump({"E1": d1, "E2": d2, "E3": d3}, f, indent=2)
    print("Wrote pred_results/diagnostics.json.")
