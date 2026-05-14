"""
T_D Compound-soliton attractor — E3 (corrected): exact-V-rotation + RK2 transport.

Method outline: Strang split on (Psi_tilde, m) under user's +Q sign.
   Step structure per dt (Lie-Trotter splitting inside the C sub-step):
       V(dt/4) -> T(dt/2) -> V(dt/4) -> L(dt) -> V(dt/4) -> T(dt/2) -> V(dt/4)
       where:
         V = phase rotation by V[N]:  Psi_tilde *= exp(-i V[N] dt_v)
         T = u-transport + m-equation: explicit RK2 (Heun) on Psi_tilde and m
         L = linear Schrödinger kinetic propagator (STANDARD sign):
             Psi_tilde_k *= exp(-i (k+c)^2 dt/2)

Why V-rotation is exact: V[N] depends only on N = |Psi_tilde|^2, and V-rotation
   preserves N exactly. So V[N] is FROZEN during V-rotation and the rotation is
   exp(-i V[N] dt_v) pointwise — unitary, mass-preserving, machine-precision.

Why RK4 of V-step failed at E3v1: RK4 of i Psi_t = -i V Psi is unitary only
   to leading order; combined with spectral noise in V[N] and a non-smooth
   (sqrt N)_xx/sqrt N, the leading-order error amplified. Using EXACT phase
   rotation eliminates this.

Bank citations (E3 corrected):
   kb-nls-sign-convention      — user's +Q absorbed in V[N]; standard kinetic
   kb-nls-madelung-psi-handles-zero-density — sqrt(N+eps_mad) regularization
   kb-nls-strang-splitstep-bright-soliton — Strang split on Psi
   kb-nls-23-dealiasing-cubic   — 2/3 dealiasing on V[N] and kinetic FFT step
   kb-nls-split-linear-phase    — c=0.5 absorbed in (k+c)^2 propagator
   kb-nls-mcs-not-attractor-standard-sign — contrastive: this E3 tests
                                  user's sign (NOT the standard-sign sector
                                  measured by S6)
"""

import numpy as np
import os
import time

# --------------------------- Domain & grid ---------------------------
Lhalf = 15.0
Nx = 256
L = 2 * Lhalf
x = np.linspace(-Lhalf, Lhalf, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k

dealias_mask = np.abs(k) <= (2.0/3.0) * np.max(np.abs(k))

# Hou-Li exponential smoothing filter (gentler than 2/3 brutal cut).
# alpha = 36, p = 36 standard Hou-Li parameters: filter = exp(-alpha (k/k_max)^p)
# Stays ~1.0 for low/mid modes; smoothly cuts the highest few modes.
_hou_li_alpha = 16.0
_hou_li_p = 12
k_max = np.max(np.abs(k))
hou_li_filter = np.exp(-_hou_li_alpha * (np.abs(k)/k_max)**_hou_li_p)

def hou_li_real(f):
    fk = np.fft.fft(f)
    fk *= hou_li_filter
    return np.real(np.fft.ifft(fk))

def hou_li_cplx(f):
    fk = np.fft.fft(f)
    fk *= hou_li_filter
    return np.fft.ifft(fk)

def dx_sp_real(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def dxx_sp_real(f):
    return np.real(np.fft.ifft(-(k**2) * np.fft.fft(f)))

def dx_sp_cplx(f):
    return np.fft.ifft(ik * np.fft.fft(f))

def dealias_real(f):
    fk = np.fft.fft(f)
    fk *= dealias_mask
    return np.real(np.fft.ifft(fk))

def dealias_cplx(f):
    fk = np.fft.fft(f)
    fk *= dealias_mask
    return np.fft.ifft(fk)

# --------------------------- Parameters ---------------------------
kappa = 1.0
A = 1.5
c_phase = 0.5
eps_perturb = 0.05      # smaller perturbation for the first stable run
eps_mad = 1e-3          # soft regularization for sqrt(N + eps_mad)

T_final = 12.0
dt = 2.5e-4             # halved for stability
n_steps = int(round(T_final / dt))
n_snapshots = 25
snap_every = max(1, n_steps // (n_snapshots - 1))

# Linear kinetic propagator (STANDARD sign, with c-shift)
lin_full_k = np.exp(-1j * (k + c_phase)**2 * dt / 2.0)

# --------------------------- IC ---------------------------
N0 = A**2 * (1.0 / np.cosh(A * (x + 5.0)))**2
u0 = N0 * c_phase + eps_perturb * np.cos(2.0 * np.pi * x / L)

Psi_tilde = np.sqrt(N0).astype(np.complex128)
m = u0 - N0 * c_phase

mass0 = np.sum(N0) * dx
m0_norm = np.sqrt(np.sum(m**2) * dx)
phase_budget = np.max((k + c_phase)**2) * dt / 2.0
print(f"E3v2: kappa={kappa}, A={A}, c={c_phase}, eps={eps_perturb}, dt={dt}, T={T_final}")
print(f"      Nx={Nx}, L={L}, dx={dx:.4f}, n_steps={n_steps}, snap_every={snap_every}")
print(f"      IC: N_max={N0.max():.4f}, N_min={N0.min():.3e}, ||m0||={m0_norm:.4f}, mass0={mass0:.4f}")
print(f"      max linear-step phase per dt = {phase_budget:.3f}  (must be < 2 pi)")
print(f"      eps_mad = {eps_mad}")

# --------------------------- Helpers ---------------------------
def compute_phi_x_and_N(Psi_t):
    N = np.abs(Psi_t)**2
    j_curr = np.imag(np.conj(Psi_t) * dx_sp_cplx(Psi_t))
    phi_tilde_x = j_curr / (N + eps_mad)
    phi_x_full = c_phase + phi_tilde_x
    return phi_x_full, N

def V_potential(N_in):
    """V[N] = (sqrt(N+eps_mad))_xx / sqrt(N+eps_mad) - 2 kappa N.
       Stronger 2/3 dealias on Q only (Q has cubic-like singularity at tails)."""
    sqrtNeps = np.sqrt(np.maximum(N_in, 0.0) + eps_mad)
    sqrtNeps = dealias_real(sqrtNeps)
    sqrtNeps_xx = dxx_sp_real(sqrtNeps)
    Q = sqrtNeps_xx / sqrtNeps
    Q = dealias_real(Q)
    V = Q - 2.0 * kappa * N_in
    return V

# Verify V[N0]
V0 = V_potential(N0)
print(f"      V[N0] range: [{V0.min():.4f}, {V0.max():.4f}]   (theoretical [-9.0, +2.25])")

# --------------------------- V-rotation sub-step (exact phase rotation) ---------------------------
def V_step(Psi_t, h):
    """Psi_t *= exp(-i V[|Psi|^2] h).  Exact for fixed V[N]; |Psi|^2=N unchanged."""
    N = np.abs(Psi_t)**2
    V = V_potential(N)
    return Psi_t * np.exp(-1j * V * h)

# --------------------------- T-transport sub-step (explicit RK2 on (Psi_tilde, m)) ---------------------------
# i Psi_tilde_t (T part) = -i u Psi_tilde_x - (i/2) u_x Psi_tilde + u c Psi_tilde
#                          (the u c piece is real-valued phase shift)
# Convert: Psi_tilde_t (T) = -u Psi_tilde_x - (1/2) u_x Psi_tilde - i u c Psi_tilde
# m_t (T) = -2 u_x m - u m_x

def rhs_T(Psi_t, m_in):
    """T-step RHS with 2/3 dealiasing on every product. This destroys some
    soliton mass but is necessary to suppress the m-equation high-frequency
    instability under the user's sign (which lacks the natural quantum
    pressure regularization)."""
    phi_x, N = compute_phi_x_and_N(Psi_t)
    u_real = m_in + N * phi_x
    u_real = dealias_real(u_real)
    u_x = dx_sp_real(u_real)
    Psi_x = dx_sp_cplx(Psi_t)
    uPsix = dealias_cplx(u_real * Psi_x)
    uxPsi = dealias_cplx(u_x * Psi_t)
    ucPsi = dealias_cplx(u_real * Psi_t)
    dPsi = -uPsix - 0.5 * uxPsi - 1j * c_phase * ucPsi
    m_x = dx_sp_real(m_in)
    uxm = dealias_real(u_x * m_in)
    umx = dealias_real(u_real * m_x)
    dm = -2.0 * uxm - umx
    return dPsi, dm

def T_step(Psi_t, m_in, h):
    """Heun (improved Euler / RK2) on T-sub-step."""
    k1P, k1m = rhs_T(Psi_t, m_in)
    P_pred = Psi_t + h * k1P
    m_pred = m_in + h * k1m
    k2P, k2m = rhs_T(P_pred, m_pred)
    P_new = Psi_t + (h/2.0) * (k1P + k2P)
    m_new = m_in + (h/2.0) * (k1m + k2m)
    return P_new, m_new

# --------------------------- L step ---------------------------
def L_step(Psi_t):
    Pk = np.fft.fft(Psi_t)
    Pk *= lin_full_k
    Pk *= dealias_mask
    return np.fft.ifft(Pk)

# --------------------------- Full step (Strang outermost) ---------------------------
# Outer Strang:
#   C(dt/2) = V(dt/4) T(dt/2) V(dt/4)
#   L(dt)
#   C(dt/2) = V(dt/4) T(dt/2) V(dt/4)
def full_step(Psi_t, m_in, dt_step):
    # C(dt/2)
    P, m_cur = V_step(Psi_t, dt_step/4.0), m_in
    P, m_cur = T_step(P, m_cur, dt_step/2.0)
    P = V_step(P, dt_step/4.0)
    # L(dt)
    P = L_step(P)
    # C(dt/2)
    P = V_step(P, dt_step/4.0)
    P, m_cur = T_step(P, m_cur, dt_step/2.0)
    P = V_step(P, dt_step/4.0)
    return P, m_cur

# --------------------------- Snapshots & integration ---------------------------
snaps_u = []
snaps_N = []
snaps_phi = []
ts = []
m_norms = []
N_mins = []
masses = []

def compute_energy(Psi_t, m_in):
    Psi_x = dx_sp_cplx(Psi_t)
    H = (0.5 * np.abs(Psi_x)**2 - kappa * np.abs(Psi_t)**4).real.sum() * dx
    return H

def save_snap(t):
    phi_x_full, N_cur = compute_phi_x_and_N(Psi_tilde)
    u_cur = m + N_cur * phi_x_full
    phi_tilde_cur = np.angle(Psi_tilde)
    phi_full = c_phase * x + phi_tilde_cur
    snaps_u.append(u_cur.copy())
    snaps_N.append(N_cur.copy())
    snaps_phi.append(phi_full.copy())
    ts.append(t)
    m_norms.append(np.sqrt(np.sum(m**2)*dx))
    N_mins.append(N_cur.min())
    masses.append(np.sum(N_cur)*dx)

save_snap(0.0)

t_start = time.time()
t = 0.0
blowup = False

print(f"      Starting integration: dt={dt}, n_steps={n_steps}")

for step in range(1, n_steps + 1):
    Psi_tilde, m = full_step(Psi_tilde, m, dt)
    t = step * dt

    # blowup checks
    if not np.all(np.isfinite(Psi_tilde)) or not np.all(np.isfinite(m)):
        print(f"  BLOWUP at step {step}, t={t:.4f}")
        blowup = True
        break
    pmax = np.max(np.abs(Psi_tilde))
    mmax = np.max(np.abs(m))
    if pmax > 1e3 or mmax > 1e3:
        print(f"  RUNAWAY at step {step}, t={t:.4f}: |Psi|max={pmax:.3e}, |m|max={mmax:.3e}")
        blowup = True
        break

    if step % snap_every == 0 and len(ts) < n_snapshots:
        save_snap(t)
        phi_x_now, N_now = compute_phi_x_and_N(Psi_tilde)
        m_norm = m_norms[-1]
        mass_t = masses[-1]
        E_now = compute_energy(Psi_tilde, m)
        print(f"  t={t:.3f}: ||m||={m_norm:.4f}, max|u|={np.max(np.abs(m + N_now*phi_x_now)):.3f}, "
              f"N_max={N_now.max():.3f}, N_min={N_now.min():.3e}, mass_drift={(mass_t-mass0)/mass0:.3e}, "
              f"E_psi={E_now:.3f}")

if not blowup and len(ts) < n_snapshots:
    save_snap(t)

t_wall = time.time() - t_start
print(f"E3v2 done: t_final={t:.3f}, wall={t_wall:.2f}s, blowup={blowup}, n_snaps={len(ts)}")

# --------------------------- Save output ---------------------------
out = np.stack([np.array(snaps_u), np.array(snaps_N), np.array(snaps_phi)], axis=1)
print(f"Output shape: {out.shape}")
print(f"ts (length {len(ts)}): first={ts[0]:.3f}, last={ts[-1]:.3f}")
print(f"||m||  history first/last: {m_norms[0]:.4f} / {m_norms[-1]:.4f}")
print(f"mass   history first/last: {masses[0]:.6f} / {masses[-1]:.6f}")
print(f"N_min  history first/last: {N_mins[0]:.3e} / {N_mins[-1]:.3e}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_D.npy", out)

np.savez("pred_results/T_D_diag.npz",
         ts=np.array(ts),
         m_norms=np.array(m_norms),
         masses=np.array(masses),
         N_mins=np.array(N_mins),
         blowup=blowup,
         t_final=t,
         eps_perturb=eps_perturb)

print("Saved pred_results/T_D.npy and T_D_diag.npz")
