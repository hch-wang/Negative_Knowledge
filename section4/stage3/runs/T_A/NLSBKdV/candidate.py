"""
T_A: Bright NLS soliton stability in the Burgers frame (compound-soliton attractor test).

E1: Madelung-Psi Strang split-step Fourier on Psi = sqrt(N) exp(i phi).
- Standard NLS sign convention adopted (see reasoning.md: user's literal +Q sign would
  yield a parabolic-unstable Psi PDE per S6 evidence; standard sign is the stable
  propagator and we record the caveat).
- phi split: phi(x,0) = c*x + phi_tilde, with c=0.5; Psi_tilde = sqrt(N) exp(i phi_tilde),
  Psi = exp(i c x) * Psi_tilde. The kinetic op acts as exp(-i (k+c)^2 dt / 2) on Psi_tilde.
- 2/3 dealiasing on |Psi|^2 before the cubic nonlinear pointwise exponential.
- u, N, phi reconstructed from Psi at snapshot times. u := Im(conj(Psi) Psi_x) makes
  m = u - N*phi_x = 0 a structural identity (NLS bank entry
  kb-nls-madelung-psi-structural-coupling).

Bank citations: NLS-bank (kb-nls-strang-splitstep-bright-soliton,
                          kb-nls-madelung-psi-handles-zero-density,
                          kb-nls-madelung-psi-structural-coupling,
                          kb-nls-split-linear-phase,
                          kb-nls-23-dealiasing-cubic,
                          kb-nls-direct-n-phi-structural-failure,
                          kb-nls-recommended-default-bnls,
                          kb-nls-sign-convention,
                          kb-nls-cfl-split-step).
BKdV entries rejected: see reasoning.md.
"""

import os
import numpy as np

# ------ Setup ------------------------------------------------------------
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(WORK_DIR, "pred_results")
os.makedirs(OUT_DIR, exist_ok=True)

# Domain & grid
L_half = 15.0
L = 2.0 * L_half                   # period length used by FFT
Nx = 256
x = np.linspace(-L_half, L_half, Nx, endpoint=False)
dx = x[1] - x[0]
# FFT wavenumbers (periodic on length L)
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)

# Physical params
kappa = 1.0
A = 1.5
c = 0.5                            # constant phase gradient (phi_x = 0.5)

# Time stepping
T_final = 8.0
dt = 1e-3
n_steps = int(round(T_final / dt))
assert abs(n_steps * dt - T_final) < 1e-9, "dt must divide T_final exactly"

# Snapshots: 9 evenly spaced from t=0 to T_final inclusive
n_snapshots = 9
snap_step = n_steps // (n_snapshots - 1)
assert snap_step * (n_snapshots - 1) == n_steps, "Snapshot spacing must be integer"

# CFL check (kb-nls-cfl-split-step): pi^2 Nx^2 dt / (2 L^2) <= 1
# pi^2 * 256^2 * 1e-3 / (2 * 30^2) = pi^2 * 65536e-3 / 1800 ~ 0.359 -> OK
cfl_lin = np.pi**2 * Nx**2 * dt / (2.0 * L**2)
print(f"Linear-step CFL budget pi^2 Nx^2 dt / (2 L^2) = {cfl_lin:.4f} (require <= 1)")

# 2/3 dealiasing mask
k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(np.float64)
print(f"Dealiasing keeps {int(dealias.sum())}/{Nx} modes")

# ------ Initial condition ------------------------------------------------
# N(x,0) = A^2 sech^2(A (x+5))
N0 = (A**2) * (1.0 / np.cosh(A * (x + 5.0)))**2
phi0 = c * x                       # constant gradient 0.5 everywhere
u0 = N0 * c                        # = N0 phi_x; on Mcs

# Tilde representation: phi_tilde = 0 initially, Psi_tilde = sqrt(N0)
# Psi = exp(i c x) Psi_tilde
sqrtN0 = np.sqrt(N0)
Psi_tilde = sqrtN0.astype(np.complex128) + 0j   # Psi_tilde(t=0) = sqrt(N0)

# Sanity check
print(f"min(N0)={N0.min():.3e}, max(N0)={N0.max():.3f} (expected ~{A**2:.3f})")
print(f"mass M0 = int N dx = {np.sum(N0)*dx:.6f}")

# ------ Strang split-step propagator on Psi_tilde -----------------------
# Standard NLS: i d Psi / dt = -(1/2) Psi_xx - kappa |Psi|^2 Psi (focusing, kappa=+1)
# Move to tilde frame Psi = exp(i c x) Psi_tilde:
#   i d Psi_t / dt = -(1/2)(d_x + i c)^2 Psi_t - kappa |Psi_t|^2 Psi_t
#   Fourier kinetic operator on Psi_t_hat:  exp(-i (k + c)^2 dt / 2)
# Nonlinear: pointwise exact rotation exp(+ i kappa |Psi_t|^2 dt)
# (Note: sign of nonlinear phase chosen so a focusing soliton |Psi|^2 = A^2 sech^2 is stationary
#  up to a global phase exp(i A^2 t / 2) when v=0.)

kin_half = np.exp(-1j * 0.5 * (k + c)**2 * (dt / 2.0))     # half kinetic step
kin_full = np.exp(-1j * 0.5 * (k + c)**2 * dt)             # full kinetic step (for inner loop)


def nonlinear_step(Psi_t, dt_):
    """Pointwise unitary nonlinear step: exp(+ i kappa |Psi|^2 dt)."""
    rho = np.abs(Psi_t)**2
    # Dealias rho before using it as a phase amplitude (kb-nls-23-dealiasing-cubic).
    rho_hat = np.fft.fft(rho)
    rho_hat *= dealias
    rho = np.fft.ifft(rho_hat).real
    rho = np.maximum(rho, 0.0)
    return Psi_t * np.exp(1j * kappa * rho * dt_)


def linear_step(Psi_t, factor):
    """Linear kinetic step via FFT (with dealiasing applied to the spectrum)."""
    Psi_hat = np.fft.fft(Psi_t)
    Psi_hat *= factor
    Psi_hat *= dealias
    return np.fft.ifft(Psi_hat)


# Output array  shape (n_snapshots, 3, Nx) -> channels (u, N, phi)
out = np.zeros((n_snapshots, 3, Nx), dtype=np.float64)

# Diagnostics
diag_t = []
diag_mass = []
diag_mres = []          # ||m||_2 / ||N phi_x||_2
diag_Nmax = []
diag_umax = []
diag_phimax = []


def reconstruct(Psi_t):
    """Reconstruct (u, N, phi) from Psi = exp(i c x) Psi_tilde.

    Returns u, N, phi as real arrays of length Nx.
    u := Im(conj(Psi) Psi_x); makes m = 0 structurally on Mcs.
    """
    Psi = np.exp(1j * c * x) * Psi_t
    N = np.abs(Psi)**2
    # phi := angle(Psi). Unwrap to remove 2*pi jumps for a smoother field; the linear c*x
    # is already in arg(Psi).
    phi = np.unwrap(np.angle(Psi))
    # u via spectral derivative of Psi (numerically: differentiate Psi spectrally)
    Psi_hat = np.fft.fft(Psi)
    Psi_x = np.fft.ifft(1j * k * Psi_hat)
    u = (np.conjugate(Psi) * Psi_x).imag
    return u, N, phi


def diagnose(t, Psi_t):
    u, N, phi = reconstruct(Psi_t)
    mass = np.sum(N) * dx
    # phi_x via spectral derivative of phi (use Psi-based j/N for stability where N>0)
    # Use j / N where N is non-vanishing (Madelung definition).
    Psi = np.exp(1j * c * x) * Psi_t
    Psi_hat = np.fft.fft(Psi)
    Psi_x = np.fft.ifft(1j * k * Psi_hat)
    j = (np.conjugate(Psi) * Psi_x).imag        # = u
    # m = u - N phi_x = u - j = 0 by identity. Compute numerically.
    # Use phi_x from Madelung: phi_x = Im(Psi_x / Psi) where N safely nonzero
    safe = N > 1e-12
    phix = np.zeros_like(N)
    phix[safe] = (Psi_x[safe] / Psi[safe]).imag
    Nphix = N * phix
    m = u - Nphix
    norm_Nphix = np.linalg.norm(Nphix) + 1e-30
    mres = np.linalg.norm(m) / norm_Nphix
    return mass, mres, N.max(), np.max(np.abs(u)), np.max(np.abs(phi))


# Initial snapshot
u_s, N_s, phi_s = reconstruct(Psi_tilde)
out[0, 0] = u_s
out[0, 1] = N_s
out[0, 2] = phi_s
mass0 = np.sum(N_s) * dx
mass, mres, Nmax, umax, phimax = diagnose(0.0, Psi_tilde)
diag_t.append(0.0)
diag_mass.append(mass)
diag_mres.append(mres)
diag_Nmax.append(Nmax)
diag_umax.append(umax)
diag_phimax.append(phimax)
print(f"t=0.000  mass={mass:.6e}  mres={mres:.3e}  Nmax={Nmax:.4f}  |u|max={umax:.4f}  |phi|max={phimax:.4f}")

# ------ Time loop --------------------------------------------------------
snap_idx = 1
for step in range(1, n_steps + 1):
    # Strang: half-kinetic, full-nonlinear, half-kinetic
    Psi_tilde = linear_step(Psi_tilde, kin_half)
    Psi_tilde = nonlinear_step(Psi_tilde, dt)
    Psi_tilde = linear_step(Psi_tilde, kin_half)

    # NaN / overflow guard
    if not np.all(np.isfinite(Psi_tilde)):
        print(f"BLOWUP at step={step}  t={step*dt:.4e}")
        break

    if step % snap_step == 0:
        t_now = step * dt
        u_s, N_s, phi_s = reconstruct(Psi_tilde)
        out[snap_idx, 0] = u_s
        out[snap_idx, 1] = N_s
        out[snap_idx, 2] = phi_s
        mass, mres, Nmax, umax, phimax = diagnose(t_now, Psi_tilde)
        diag_t.append(t_now)
        diag_mass.append(mass)
        diag_mres.append(mres)
        diag_Nmax.append(Nmax)
        diag_umax.append(umax)
        diag_phimax.append(phimax)
        print(f"t={t_now:.3f}  mass={mass:.6e}  mres={mres:.3e}  Nmax={Nmax:.4f}  |u|max={umax:.4f}  |phi|max={phimax:.4f}")
        snap_idx += 1

# ------ Save -------------------------------------------------------------
np.save(os.path.join(OUT_DIR, "T_A.npy"), out.astype(np.float64))
print(f"Saved {os.path.join(OUT_DIR, 'T_A.npy')}  shape={out.shape}")

# ------ Final assessment -----------------------------------------------
mass_drift = abs(diag_mass[-1] - diag_mass[0]) / abs(diag_mass[0])
print("\n=== Final diagnostics ===")
print(f"mass drift over T={T_final}: {mass_drift:.3e} (target < 5e-2)")
print(f"final Nmax={diag_Nmax[-1]:.4f} (target >= 0.5 * 2.25 = 1.125)")
print(f"final |u|max={diag_umax[-1]:.4f} (target < 25)")
print(f"final |phi|max={diag_phimax[-1]:.4f} (target < 25)")
print(f"final ||m||_2/||N phi_x||_2 = {diag_mres[-1]:.3e} (target < 0.2)")

# Single peak check on final N
N_final = out[-1, 1]
# Count local maxima (excluding boundaries)
local_max = ((N_final[1:-1] > N_final[:-2]) & (N_final[1:-1] > N_final[2:]))
n_peaks = int(local_max.sum())
print(f"final N has {n_peaks} interior local maxima (target ~1 dominant peak)")
print(f"final N peak position: x={x[np.argmax(N_final)]:.3f}")
