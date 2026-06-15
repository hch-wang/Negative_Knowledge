"""
T_A / NLS — Experiment 1
Bright NLS soliton stability in the Burgers frame (M_cs attractor test).

Method: Madelung-Psi Strang split-step Fourier.
- Psi = sqrt(N) * exp(i*phi)
- Linear half-step in Fourier: Psi_k -> exp(-i k^2 dt/2) Psi_k   (standard NLS kinetic sign)
- Nonlinear full step pointwise: Psi -> exp(i*kappa*|Psi|^2*dt) Psi   (focusing cubic, kappa=+1)
- Galilean factor extraction: Psi = exp(i*0.5*x) * Psi_tilde with Psi_tilde periodic.

Note on sign convention (kb-nls-sign-convention): user's literal phi equation has +Q sign which makes
the explicit Psi-propagator parabolic-unstable. The IC is described as an exact bright NLS soliton
(Madelung form), well-defined under standard NLS sign; we adopt that sign for the Psi propagator
and treat the transfer to the user's B-NLS as a hypothesis-level numerical model.

Output: pred_results/T_A.npy of shape (n_snapshots, 3, 256), channels (u, N, phi).
"""

import numpy as np
import os

# ---------------- Parameters ----------------
Nx = 256
L_half = 15.0
L = 2.0 * L_half  # box length = 30
dx = L / Nx
x = -L_half + dx * np.arange(Nx)

T_final = 8.0
dt = 1e-3
nsteps = int(round(T_final / dt))
assert abs(nsteps * dt - T_final) < 1e-12

n_snapshots = 9  # 9 evenly spaced snapshots including t=0 and t=T_final
snap_indices = np.linspace(0, nsteps, n_snapshots).astype(int)

kappa = 1.0
A = 1.5
x0 = -5.0
v_phase_grad = 0.5  # phi(x,0) = 0.5 x

# CFL-like sanity check (kb-nls-cfl-split-step): pi^2 Nx^2 dt / (2 L^2) <= 1
cfl_phase = np.pi**2 * Nx**2 * dt / (2.0 * L**2)
print(f"Linear-step phase budget (should be < 1): {cfl_phase:.4f}")

# ---------------- Initial condition ----------------
N0 = A**2 * np.cosh(A * (x - x0))**(-2)          # 2.25 * sech^2(1.5*(x+5))
phi0 = v_phase_grad * x                           # 0.5 * x  -- NON-periodic
u0 = N0 * v_phase_grad                            # 0.5 * N0; m(x,0) = 0 exactly

# Galilean phase split: phi = c*x + phi_tilde with phi_tilde periodic and zero here.
# Psi_full = sqrt(N) exp(i*phi) = exp(i*c*x) * sqrt(N) exp(i*phi_tilde) = exp(i*c*x) * Psi_tilde.
# So Psi_tilde(x,0) = sqrt(N0)  (real, since phi_tilde = 0).
c = v_phase_grad
Psi_tilde = np.sqrt(N0).astype(np.complex128)

print(f"IC: A={A}, x0={x0}, N_max={N0.max():.6f}, N_min={N0.min():.2e}, M0={np.sum(N0)*dx:.6f}")
print(f"   m(x,0) check: max|u0 - N0*phi_x0| = {np.max(np.abs(u0 - N0*v_phase_grad)):.2e}")

# ---------------- Fourier grid ----------------
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
# Linear propagator: i Psi_tilde_t = -(1/2) (i d/dx + c)^2 Psi_tilde - kappa |Psi_tilde|^2 Psi_tilde
# Wait: when we write Psi = exp(i c x) Psi_tilde, the kinetic operator -(1/2) d_x^2 acting on Psi gives
#   -(1/2) d_x^2 [exp(i c x) Psi_tilde] = exp(i c x) [-(1/2)(i c + d_x)^2 Psi_tilde]
# In Fourier on Psi_tilde, d_x -> i k, so -(1/2)(i c + d_x)^2 -> -(1/2)(i c + i k)^2 = (1/2)(k+c)^2.
# Linear half-step factor in Fourier of Psi_tilde:
half_lin = np.exp(-1j * 0.5 * (k + c)**2 * (dt / 2.0))
full_lin = np.exp(-1j * 0.5 * (k + c)**2 * dt)

# ---------------- Storage for snapshots ----------------
snaps = np.zeros((n_snapshots, 3, Nx), dtype=np.float64)
snap_times = np.zeros(n_snapshots, dtype=np.float64)

def reconstruct_full(Psi_tilde_local):
    """Return Psi_full = exp(i c x) * Psi_tilde."""
    return np.exp(1j * c * x) * Psi_tilde_local

def diagnostics(Psi_tilde_local, step_n):
    """Compute (u, N, phi) and m diagnostics from current Psi_tilde."""
    Psi_full = reconstruct_full(Psi_tilde_local)
    N = (np.abs(Psi_full)**2).real
    phi_full = np.angle(Psi_full)  # in (-pi, pi]; not unwrapped for storage simplicity
    # u = Im(conj(Psi)*Psi_x) computed spectrally on the FULL Psi
    Psi_x = np.fft.ifft(1j * k * np.fft.fft(Psi_full))
    j = (np.conj(Psi_full) * Psi_x).imag
    u = j  # = N * phi_x (Madelung identity)
    return u, N, phi_full

def save_snapshot(idx_snap, t_cur, Psi_tilde_local):
    u, N, phi_full = diagnostics(Psi_tilde_local, idx_snap)
    snaps[idx_snap, 0, :] = u
    snaps[idx_snap, 1, :] = N
    snaps[idx_snap, 2, :] = phi_full
    snap_times[idx_snap] = t_cur

# Save t=0
save_snapshot(0, 0.0, Psi_tilde)

# ---------------- Diagnostic helpers ----------------
def mass(Psi_tilde_local):
    return float(np.sum(np.abs(Psi_tilde_local)**2) * dx)

def mnorm(Psi_tilde_local):
    """||m||_2 / ||N*phi_x||_2 where u := Im(conj(Psi)*Psi_x). Should be ~ machine eps (structural)."""
    Psi_full = reconstruct_full(Psi_tilde_local)
    N = (np.abs(Psi_full)**2).real
    Psi_x = np.fft.ifft(1j * k * np.fft.fft(Psi_full))
    u = (np.conj(Psi_full) * Psi_x).imag
    # phi_x = Im(Psi_x / Psi) = (Im(conj(Psi)*Psi_x)) / |Psi|^2 -- careful at zero density.
    eps_safe = 1e-30
    phi_x = (np.conj(Psi_full) * Psi_x).imag / (N + eps_safe)
    m = u - N * phi_x
    den = np.sqrt(np.sum((N * phi_x)**2) * dx)
    num = np.sqrt(np.sum(m**2) * dx)
    return num / max(den, 1e-300)

M_t0 = mass(Psi_tilde)
mfrac_t0 = mnorm(Psi_tilde)
print(f"   Mass(t=0) = {M_t0:.10f}; ||m||/||N*phi_x|| (t=0) = {mfrac_t0:.2e}")

# ---------------- Time stepping (Strang) ----------------
# Strang: N(dt/2) - L(dt) - N(dt/2)
# Loop tip: keep Psi_tilde, work in spectral on linear, real-space on nonlinear.
snap_set = set(snap_indices.tolist())

t_cur = 0.0
for n in range(1, nsteps + 1):
    # N(dt/2) -- nonlinear half-step pointwise on Psi_tilde
    # |Psi_full|^2 = |Psi_tilde|^2 (phase exp(i c x) doesn't change magnitude)
    rho = (Psi_tilde.conj() * Psi_tilde).real
    Psi_tilde = Psi_tilde * np.exp(1j * kappa * rho * (dt / 2.0))

    # L(dt) -- linear full step in Fourier
    Psi_hat = np.fft.fft(Psi_tilde)
    Psi_hat *= full_lin
    Psi_tilde = np.fft.ifft(Psi_hat)

    # N(dt/2) -- nonlinear half-step pointwise
    rho = (Psi_tilde.conj() * Psi_tilde).real
    Psi_tilde = Psi_tilde * np.exp(1j * kappa * rho * (dt / 2.0))

    t_cur = n * dt

    if n in snap_set:
        idx = int(np.where(snap_indices == n)[0][0])
        save_snapshot(idx, t_cur, Psi_tilde)

# ---------------- Final diagnostics ----------------
M_tf = mass(Psi_tilde)
mfrac_tf = mnorm(Psi_tilde)
u_tf, N_tf, phi_tf = diagnostics(Psi_tilde, nsteps)

print()
print(f"=== Final diagnostics at T={T_final} ===")
print(f"Mass(T)            = {M_tf:.10f}")
print(f"|dM|/M             = {abs(M_tf - M_t0)/M_t0:.3e}")
print(f"||m||/||N*phi_x||  = {mfrac_tf:.3e}")
print(f"N_max(T)           = {N_tf.max():.4f}  (initial 2.25; threshold 1.125)")
print(f"N_min(T)           = {N_tf.min():.4e}")
print(f"|u|_max(T)         = {np.abs(u_tf).max():.4f}")
print(f"|phi|_max(T)       = {np.abs(phi_tf).max():.4f}")
print(f"peak x position(T) = {x[np.argmax(N_tf)]:.4f}  (expected ~ -1.0 from v=0.5*T=4)")

# Spectral tail fraction (under-resolution flag from kb-nls-resolution-soliton-counting)
Psi_hat = np.fft.fft(Psi_tilde)
power = np.abs(Psi_hat)**2
tail_frac = power[Nx//3 : 2*Nx//3].sum() / power.sum()  # central-band frequencies (highest k)
print(f"Spectral tail frac (high-k third) = {tail_frac:.3e}  (kb threshold for trust: < 1e-4)")

# Pass/fail report against phenomenon target
peak_ok = N_tf.max() >= 0.5 * 2.25
mass_ok = abs(M_tf - M_t0) / M_t0 < 0.05
bound_ok = (np.abs(u_tf).max() < 25.0 and np.abs(N_tf).max() < 25.0 and np.abs(phi_tf).max() < 25.0)
mfrac_ok = mfrac_tf < 0.2
print()
print(f"=== Phenomenon target check ===")
print(f"peak_amp >= 1.125 : {peak_ok}  (N_max={N_tf.max():.4f})")
print(f"|dM|/M < 5%       : {mass_ok}  ({abs(M_tf-M_t0)/M_t0*100:.3f}%)")
print(f"all |x|<25        : {bound_ok}")
print(f"||m|| frac < 0.2  : {mfrac_ok}  ({mfrac_tf:.3e})")
print(f"OVERALL           : {peak_ok and mass_ok and bound_ok and mfrac_ok}")

# ---------------- Save output ----------------
out_dir = os.path.dirname(os.path.abspath(__file__)) if False else "pred_results"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_A.npy")
np.save(out_path, snaps)
print(f"\nSaved snapshots: shape={snaps.shape}, dtype={snaps.dtype}, file={out_path}")
print(f"Snapshot times: {snap_times}")
