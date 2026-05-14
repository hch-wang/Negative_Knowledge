"""
T_D Compound-soliton attractor — E3 corrected Madelung-Psi + (Psi_tilde, m).

Method: Strang split on (Psi_tilde, m) under user's sign convention.

CORRECTED Madelung-Psi derivation under user's +Q sign:
   The user's HJ:  phi_t + (1/2) phi_x^2 + Q_user - 2 kappa N = 0
       with Q_user = +(sqrt N)_xx / (2 sqrt N)
   Standard NLS continuity:  N_t + (N (u+phi_x))_x = 0
   ----------------------------------------------------------------
   The CORRECT Madelung-Psi mapping uses STANDARD kinetic sign:
      i Psi_t = -(1/2) Psi_xx + V[N] Psi
   where the real "potential":
      V[N] = +(sqrt N)_xx / sqrt N - 2 kappa N
           = +N_xx/(2N) - N_x^2/(2 N^2) - 2 kappa N
   Adding the u-coupling (off-Mcs Burgers velocity advecting N and phi):
      i Psi_t = -(1/2) Psi_xx + V[N] Psi - i u Psi_x - (i/2) u_x Psi
   With linear phase split Psi = exp(i c x) Psi_tilde (c=0.5 from T_A IC):
      i Psi_tilde_t = -(1/2)(k + c)^2-equivalent kinetic + V[N] Psi_tilde
                    + i(c - u) (Psi_tilde)_x - (i/2) u_x Psi_tilde + (terms)
   In Fourier the linear (kinetic) propagator for Psi_tilde_k:
      Psi_tilde_k -> exp(- i (k + c)^2 dt / 2) Psi_tilde_k       (STANDARD sign)

   The +Q sign user's variational form is REALIZED through the V[N] potential
   in the C sub-step (a real-valued pointwise multiplication), NOT by inverting
   the kinetic propagator. The propagator is stable, unitary, standard.

   E2's earlier derivation (anti-Schrödinger +(1/2) Psi_xx) was WRONG: that
   form would require flipped continuity (N_t = +(N phi_x)_x), which is not
   what the user's system has. The corrected mapping uses standard Schrödinger
   kinetic and absorbs the +Q sign into V[N]. (V[N] in turn is REAL and
   bounded for smooth bright-soliton ICs because (sqrt N)_xx/sqrt N tends to
   +A^2 in deep tails and bounded everywhere in between.)

Strang split per dt:
   C(dt/2) — explicit RK4 on (Psi_tilde, m) under user's V[N] + u-coupling RHS
             (with 2/3 dealiasing on |Psi|^2 product)
   L(dt)   — Psi_tilde_k *= exp(- i (k+c)^2 dt / 2)                    [standard]
   C(dt/2) — same as first

Bank citations:
   kb-nls-sign-convention      — user's +Q implemented via V[N], NOT via kinetic flip
   kb-nls-strang-splitstep-bright-soliton — Strang split-step is the gold standard
   kb-nls-madelung-psi-handles-zero-density — N>=0 by unitarity (now valid because
                                              kinetic uses standard sign)
   kb-nls-madelung-psi-structural-coupling — Psi_tilde representation handles
                                              the m=0 limit naturally if we let m=0
   kb-nls-split-linear-phase   — c=0.5 absorbed via (k+c)^2 in propagator
   kb-nls-23-dealiasing-cubic  — 2/3 dealias on |Psi|^2 (added at E3 — single
                                  upgrade from E2)
   kb-nls-cfl-split-step       — phase budget check
   kb-nls-mcs-not-attractor-standard-sign — CONTRASTING bank entry: under
                                  standard sign, S6 found Mcs is NOT an attractor
                                  with ||m|| growing to plateau. This E3 tests
                                  the USER'S sign — distinct question.

Output: pred_results/T_D.npy shape (n_snapshots, 3, Nx). Channels = (u, N, phi).
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

# 2/3 dealiasing mask
dealias_mask = np.abs(k) <= (2.0/3.0) * np.max(np.abs(k))

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

# --------------------------- Parameters ---------------------------
kappa = 1.0
A = 1.5
c_phase = 0.5
eps_perturb = 0.1
eps_mad = 1e-3          # soft regularization sqrt(N + eps_mad) for V[N]
eps_N   = 1e-10         # tiny offset for phi_x reconstruction

T_final = 12.0
dt = 2.5e-4             # halved from previous to be conservative
n_steps = int(round(T_final / dt))
n_snapshots = 25
snap_every = max(1, n_steps // (n_snapshots - 1))

# Linear kinetic propagator (STANDARD sign, with c-shift). Recomputed per dt.
def make_lin_full(dt_use):
    return np.exp(-1j * (k + c_phase)**2 * dt_use / 2.0)
lin_full_k = make_lin_full(dt)

# --------------------------- Initial condition ---------------------------
N0 = A**2 * (1.0 / np.cosh(A * (x + 5.0)))**2
phi_tilde0 = np.zeros_like(x)              # phi = c*x + phi_tilde; T_A has phi=0.5*x => phi_tilde=0
u0 = N0 * c_phase + eps_perturb * np.cos(2.0 * np.pi * x / L)

Psi_tilde = np.sqrt(N0).astype(np.complex128)   # phi_tilde=0 so exp(i*0)=1
# m initial: u0 - N0 * phi_x where phi_x = c_phase + 0 = 0.5
m = u0 - N0 * c_phase                      # = eps * cos(2 pi x /L)

mass0 = np.sum(N0) * dx
m0_norm = np.sqrt(np.sum(m**2) * dx)
phase_budget = np.max((k + c_phase)**2) * dt / 2.0
print(f"E3 sim: kappa={kappa}, A={A}, c={c_phase}, eps={eps_perturb}, dt={dt}, T={T_final}")
print(f"        Nx={Nx}, L={L}, dx={dx:.4f}, n_steps={n_steps}, snap_every={snap_every}")
print(f"        IC: N_max={N0.max():.4f}, N_min={N0.min():.3e}, ||m0||={m0_norm:.4f}, mass0={mass0:.4f}")
print(f"        max linear-step phase per dt = {phase_budget:.3f}  (must be < 2 pi for fidelity)")
print(f"        dealias mask: {np.sum(dealias_mask)} of {Nx} modes kept")

# Test V[N] at IC to validate finite values
N_test = N0.copy()
Nx_t = dx_sp_real(N_test)
Nxx_t = dxx_sp_real(N_test)
V0 = Nxx_t / (2 * (N_test + eps_N)) - Nx_t**2 / (2 * (N_test + eps_N)**2) - 2 * kappa * N_test
print(f"        V[N0] range: [{V0.min():.4f}, {V0.max():.4f}]   (expected ~ A^2(1 - 3 sech^2(A x)))")

# --------------------------- Helper functions ---------------------------
def compute_phi_x_and_N(Psi_t):
    N = np.abs(Psi_t)**2
    j_curr = np.imag(np.conj(Psi_t) * dx_sp_cplx(Psi_t))   # = N * phi_tilde_x exactly
    phi_tilde_x = j_curr / (N + eps_N)
    phi_x_full = c_phase + phi_tilde_x
    return phi_x_full, N

def V_potential(N_in):
    """V[N] = (sqrt(N+eps_mad))_xx / sqrt(N+eps_mad) - 2 kappa N.
       Soft regularization sqrt(N+eps_mad) avoids the spectral-Gibbs blowup
       of N_xx/(2N) - N_x^2/(2 N^2) in the tails. eps_mad ~ noise floor
       (kb-nls-madelung-psi-handles-zero-density / kb-nls-hard-floor-counterproductive)."""
    sqrtNeps = np.sqrt(np.maximum(N_in, 0.0) + eps_mad)
    sqrtNeps_xx = dxx_sp_real(sqrtNeps)
    Q_kinetic_part = sqrtNeps_xx / sqrtNeps    # (sqrt N)_xx / sqrt N = 2 Q_user
    # dealias the Q term (mode product of two FFT-derived fields)
    Q_kinetic_part = dealias_real(Q_kinetic_part)
    V = Q_kinetic_part - 2.0 * kappa * N_in
    return V

# --------------------------- RHS for C sub-step ---------------------------
# i Psi_tilde_t (C part) = + V[N] Psi_tilde - i u (Psi_tilde)_x + ... (other coupling)
# but careful with linear phase split. Let's derive from full Psi:
#   i Psi_t = -(1/2) Psi_xx + V[N] Psi - i u Psi_x - (i/2) u_x Psi
# We've moved the kinetic to the L step. The C step has:
#   i Psi_t (C) = V[N] Psi - i u Psi_x - (i/2) u_x Psi
# Substitute Psi = e^(i c x) Psi_tilde:
#   Psi_x = e^(icx) (i c + d/dx) Psi_tilde
#   i Psi_t = e^(icx) i Psi_tilde_t
# So i Psi_tilde_t (C) = V[N] Psi_tilde - i u (i c Psi_tilde + Psi_tilde_x) - (i/2) u_x Psi_tilde
#                     = V[N] Psi_tilde + u c Psi_tilde - i u Psi_tilde_x - (i/2) u_x Psi_tilde
# => Psi_tilde_t (C) = -i V[N] Psi_tilde - i u c Psi_tilde - u Psi_tilde_x - (1/2) u_x Psi_tilde
# Cleaner: bundle the real "phase" part u c into V_eff = V[N] + u c (real-valued shift)
#   Psi_tilde_t (C) = -i V_eff Psi_tilde - u Psi_tilde_x - (1/2) u_x Psi_tilde

def rhs_C(Psi_t, m_in):
    """C-step RHS: (V[N] + u c) phase rotation + u-transport."""
    phi_x, N = compute_phi_x_and_N(Psi_t)
    u_real = m_in + N * phi_x
    u_x = dx_sp_real(u_real)
    Psi_x = dx_sp_cplx(Psi_t)
    V_eff = V_potential(N) + u_real * c_phase
    dPsi = -1j * V_eff * Psi_t - u_real * Psi_x - 0.5 * u_x * Psi_t
    # m equation: m_t = -2 u_x m - u m_x
    m_x = dx_sp_real(m_in)
    dm = -2.0 * u_x * m_in - u_real * m_x
    return dPsi, dm

def rk4_C_step(Psi_t, m_in, h):
    k1P, k1m = rhs_C(Psi_t, m_in)
    k2P, k2m = rhs_C(Psi_t + 0.5*h*k1P, m_in + 0.5*h*k1m)
    k3P, k3m = rhs_C(Psi_t + 0.5*h*k2P, m_in + 0.5*h*k2m)
    k4P, k4m = rhs_C(Psi_t + h*k3P, m_in + h*k3m)
    Psi_new = Psi_t + (h/6.0) * (k1P + 2*k2P + 2*k3P + k4P)
    m_new = m_in + (h/6.0) * (k1m + 2*k2m + 2*k3m + k4m)
    return Psi_new, m_new

# --------------------------- L step ---------------------------
def L_step(Psi_t):
    Psi_t_k = np.fft.fft(Psi_t)
    Psi_t_k *= lin_full_k
    # apply dealiasing
    Psi_t_k *= dealias_mask
    return np.fft.ifft(Psi_t_k)

# --------------------------- Snapshots ---------------------------
snaps_u = []
snaps_N = []
snaps_phi = []
ts = []
m_norms = []
N_mins = []
masses = []
energies = []

def compute_energy(Psi_t, m_in):
    """Hamiltonian (NLS part only): H_psi = (1/2) |Psi_x|^2 - kappa |Psi|^4 (standard NLS).
       NB: this is a partial diagnostic; full B-NLS energy is more complex but
       we just want a smooth conservation indicator. Use standard NLS energy
       (kinetic+nonlinear); B-NLS energy off-Mcs has extra m-coupling terms.
    """
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
    energies.append(compute_energy(Psi_tilde, m))

save_snap(0.0)

# --------------------------- Integrate ---------------------------
t_start = time.time()
t = 0.0
blowup = False

for step in range(1, n_steps + 1):
    Psi_tilde, m = rk4_C_step(Psi_tilde, m, dt/2.0)
    Psi_tilde = L_step(Psi_tilde)
    Psi_tilde, m = rk4_C_step(Psi_tilde, m, dt/2.0)
    t = step * dt

    if not np.all(np.isfinite(Psi_tilde)) or not np.all(np.isfinite(m)):
        print(f"  BLOWUP at step {step}, t={t:.4f}")
        blowup = True
        break
    if np.max(np.abs(Psi_tilde)) > 1e3 or np.max(np.abs(m)) > 1e3:
        print(f"  RUNAWAY at step {step}, t={t:.4f}: |Psi|max={np.max(np.abs(Psi_tilde)):.3e}, |m|max={np.max(np.abs(m)):.3e}")
        blowup = True
        break

    if step % snap_every == 0 and len(ts) < n_snapshots:
        save_snap(t)
        phi_x_now, N_now = compute_phi_x_and_N(Psi_tilde)
        m_norm = m_norms[-1]
        mass_t = masses[-1]
        print(f"  t={t:.3f}: ||m||={m_norm:.4f}, max|u|={np.max(np.abs(m + N_now*phi_x_now)):.3f}, "
              f"N_max={N_now.max():.3f}, N_min={N_now.min():.3e}, mass_drift={(mass_t-mass0)/mass0:.3e}, E={energies[-1]:.3f}")

if not blowup and len(ts) < n_snapshots:
    save_snap(t)

t_wall = time.time() - t_start
print(f"E3 done: t_final={t:.3f}, wall={t_wall:.2f}s, blowup={blowup}, n_snaps={len(ts)}")

# --------------------------- Save output ---------------------------
out = np.stack([np.array(snaps_u), np.array(snaps_N), np.array(snaps_phi)], axis=1)
print(f"Output shape: {out.shape}")
print(f"ts = {[f'{x:.2f}' for x in ts]}")
print(f"||m||(t)  = {[f'{x:.4f}' for x in m_norms]}")
print(f"mass(t)   = {[f'{x:.6f}' for x in masses]}")
print(f"N_min(t)  = {[f'{x:.3e}' for x in N_mins]}")
print(f"E_psi(t)  = {[f'{x:.4f}' for x in energies]}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_D.npy", out)

np.savez("pred_results/T_D_diag.npz",
         ts=np.array(ts),
         m_norms=np.array(m_norms),
         masses=np.array(masses),
         N_mins=np.array(N_mins),
         energies=np.array(energies),
         blowup=blowup,
         t_final=t,
         eps_perturb=eps_perturb)

print("Saved pred_results/T_D.npy and T_D_diag.npz")
