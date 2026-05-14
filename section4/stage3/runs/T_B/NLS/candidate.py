"""
T_B / NLS — Experiment 3 (final)

Single upgrade over E2: refine resolution to Nx_fine=512, dt=5e-4
(kb-nls-resolution-soliton-counting recommendation for Gaussian ICs with A*sigma >= 2).
Output spec requires Nx=256; snapshots are downsampled via Fourier truncation.

Method recap:
  - Madelung-Psi Strang split-step Fourier on Psi = sqrt(N) exp(i phi).
  - Standard-NLS sign (i Psi_t = -1/2 Psi_xx - kappa |Psi|^2 Psi) per
    kb-nls-sign-convention working hypothesis.
  - Phase split: phi(x,0) = 0.3*x absorbed analytically into Psi(x,0) = sqrt(N0) exp(i 0.3 x).
  - 2/3-rule dealiasing on |Psi|^2 before cubic exponential AND on linear FFT step.
  - u reconstructed at snapshot times as u := Im(conj(Psi) Psi_x).
  - All carried forward from E2 except (Nx, dt).
"""

import numpy as np
import os

# -----------------------------------------------------------------------------
# Computational grid (fine) and output grid (coarse, output spec requires 256)
# -----------------------------------------------------------------------------
Nx_fine = 512
Nx_save = 256
xL, xR = -15.0, 15.0
L_box = xR - xL

dx_fine = L_box / Nx_fine
x_fine = xL + dx_fine * np.arange(Nx_fine)
kx_fine = 2.0 * np.pi * np.fft.fftfreq(Nx_fine, d=dx_fine)

dx_save = L_box / Nx_save
x_save = xL + dx_save * np.arange(Nx_save)
kx_save = 2.0 * np.pi * np.fft.fftfreq(Nx_save, d=dx_save)

# 2/3-rule dealiasing on the fine grid
k_max_fine = np.pi * Nx_fine / L_box
dealias_mask_fine = (np.abs(kx_fine) <= (2.0 / 3.0) * k_max_fine).astype(np.float64)
print(f"[dealias] killing {int(np.sum(1 - dealias_mask_fine))} of {Nx_fine} modes on fine grid")

# -----------------------------------------------------------------------------
# Time stepping
# -----------------------------------------------------------------------------
T_final = 6.0
dt = 5.0e-4
n_steps = int(round(T_final / dt))
assert abs(n_steps * dt - T_final) < 1e-12

phase_budget = np.pi**2 * Nx_fine**2 * dt / (2.0 * L_box**2)
print(f"[CFL] linear-step phase budget = {phase_budget:.4f}  (must be <=1)")
assert phase_budget < 1.0

snap_times = np.linspace(0.0, T_final, 13)
snap_steps = set(int(round(t / dt)) for t in snap_times)

# -----------------------------------------------------------------------------
# Initial condition
# -----------------------------------------------------------------------------
kappa = 1.0
A0 = 2.0
sigma = 1.5
x0 = -5.0
c_boost = 0.3

N0_fine = A0 * np.exp(-(x_fine - x0)**2 / (2.0 * sigma**2))
Psi = np.sqrt(N0_fine).astype(np.complex128) * np.exp(1j * c_boost * x_fine)

mass0 = np.sum(np.abs(Psi)**2) * dx_fine
print(f"[IC] mass0 = {mass0:.10f}  (analytic A sigma sqrt(2 pi) = {A0*sigma*np.sqrt(2*np.pi):.10f})")
print(f"[IC] max|Psi|^2 = {np.max(np.abs(Psi)**2):.4f}")

lin_full = np.exp(-1j * 0.5 * kx_fine**2 * dt)

def hamiltonian(Psi):
    Psi_x = np.fft.ifft(1j * kx_fine * np.fft.fft(Psi))
    H_kin = 0.5 * np.sum(np.abs(Psi_x)**2) * dx_fine
    H_int = -0.5 * kappa * np.sum(np.abs(Psi)**4) * dx_fine
    return H_kin + H_int

E0 = hamiltonian(Psi)
print(f"[IC] H0 = {E0:.8e}")

def dealias_fine(field):
    fhat = np.fft.fft(field)
    fhat *= dealias_mask_fine
    return np.fft.ifft(fhat)

def downsample_psi_to_save_grid(Psi_fine):
    """Spectral downsample from Nx_fine to Nx_save (Fourier truncation)."""
    Psi_hat_fine = np.fft.fft(Psi_fine)
    # Build Nx_save spectrum: keep the lowest-frequency modes, mapped to standard FFT layout.
    # np.fft.fft uses [k=0, 1, 2, ..., N/2-1, -N/2, ..., -1] ordering.
    # For Nx_fine=512, Nx_save=256:
    Psi_hat_save = np.zeros(Nx_save, dtype=complex)
    half = Nx_save // 2
    # Positive freqs: 0..127 of save grid <=> 0..127 of fine grid
    Psi_hat_save[:half] = Psi_hat_fine[:half]
    # Negative freqs: -128..-1 of save grid <=> -128..-1 of fine grid (last 128 of array)
    Psi_hat_save[half:] = Psi_hat_fine[Nx_fine - half:]
    # Rescale because FFT normalization depends on N
    Psi_hat_save *= (Nx_save / Nx_fine)
    return np.fft.ifft(Psi_hat_save)

snapshots = []
mass_log = []
energy_log = []
N_max_log = []
m_norm_log = []

def save_snapshot(Psi, t):
    # Compute fields on fine grid first, then downsample.
    Psi_save = downsample_psi_to_save_grid(Psi)
    # Build (u, N, phi) on save grid using Psi_save and kx_save
    N_save = np.abs(Psi_save)**2
    Psi_save_x = np.fft.ifft(1j * kx_save * np.fft.fft(Psi_save))
    u_save = np.imag(np.conj(Psi_save) * Psi_save_x).real
    phi_save = np.angle(Psi_save)
    snapshots.append((t, np.stack([u_save, N_save, phi_save])))
    # Diagnostics on fine grid
    rho = np.abs(Psi)**2
    mass = np.sum(rho) * dx_fine
    Eh = hamiltonian(Psi)
    Psi_x = np.fft.ifft(1j * kx_fine * np.fft.fft(Psi))
    u_arr = np.imag(np.conj(Psi) * Psi_x).real
    safe = rho > 1e-14
    phi_x_rec = np.zeros_like(rho)
    phi_x_rec[safe] = u_arr[safe] / rho[safe]
    m_struct = u_arr - rho * phi_x_rec
    mass_log.append((t, mass))
    energy_log.append((t, Eh))
    N_max_log.append((t, np.max(rho)))
    m_norm_log.append((t, np.sqrt(np.sum(m_struct**2) * dx_fine)))
    return mass, Eh

save_snapshot(Psi, 0.0)
print("[run] Strang + dealias on Nx=512, dt=5e-4...")
for step in range(1, n_steps + 1):
    rho = np.abs(Psi)**2
    rho_dealias = np.real(dealias_fine(rho))
    Psi = Psi * np.exp(1j * kappa * rho_dealias * 0.5 * dt)

    Psi_hat = np.fft.fft(Psi) * lin_full * dealias_mask_fine
    Psi = np.fft.ifft(Psi_hat)

    rho = np.abs(Psi)**2
    rho_dealias = np.real(dealias_fine(rho))
    Psi = Psi * np.exp(1j * kappa * rho_dealias * 0.5 * dt)

    if step in snap_steps:
        t_now = step * dt
        mass, Eh = save_snapshot(Psi, t_now)
        print(f"  step={step:6d}  t={t_now:6.3f}  mass={mass:.8f}  H={Eh:.6e}  N_max(fine)={N_max_log[-1][1]:.4f}  ||m||_2={m_norm_log[-1][1]:.3e}")

    if step % 2000 == 0 and not np.all(np.isfinite(Psi)):
        print(f"  *** NaN/Inf at step {step}, t={step*dt}")
        break

# -----------------------------------------------------------------------------
# Save downsampled output
# -----------------------------------------------------------------------------
snapshots.sort(key=lambda s: s[0])
times = np.array([s[0] for s in snapshots])
out = np.stack([s[1] for s in snapshots], axis=0)
print(f"[out] shape = {out.shape}  (expected: ({len(snap_times)}, 3, {Nx_save}))")
print(f"[out] times = {times}")

os.makedirs(os.path.join(os.path.dirname(__file__) or '.', 'pred_results'), exist_ok=True)
np.save(os.path.join(os.path.dirname(__file__) or '.', 'pred_results', 'T_B.npy'), out)
print("[out] saved pred_results/T_B.npy")

# -----------------------------------------------------------------------------
# Final diagnostics
# -----------------------------------------------------------------------------
mass_final_fine = mass_log[-1][1]
print(f"[diag] mass_drift_fine = {(mass_final_fine - mass0)/mass0:.3e}")
H_final = energy_log[-1][1]
print(f"[diag] H_final_fine = {H_final:.8e}  dH/H0 = {(H_final - E0)/abs(E0):.3e}")

# On the saved (coarse) grid, the natural-time check of the phenomenon:
N_final_save = out[-1, 1]
mass_final_save = np.sum(N_final_save) * dx_save
print(f"[diag] mass_final (saved Nx=256) = {mass_final_save:.6f}  (vs mass0 {mass0:.6f})  drift = {(mass_final_save - mass0)/mass0:.3e}")

peaks = []
for i in range(Nx_save):
    iprev = (i - 1) % Nx_save
    inext = (i + 1) % Nx_save
    if N_final_save[i] >= 1.0 and N_final_save[i] > N_final_save[iprev] and N_final_save[i] > N_final_save[inext]:
        peaks.append((x_save[i], N_final_save[i]))
print(f"[diag] peaks (N>=1.0) in final snapshot on saved grid: {len(peaks)}")
for px, pa in peaks:
    print(f"   peak  x={px:7.3f}  N={pa:.4f}")
print(f"[diag] N_max_final (saved) = {np.max(N_final_save):.4f}")
print(f"[diag] N_min_final (saved) = {np.min(N_final_save):.4e}")

# Spectral tail on fine grid
Psi_hat = np.fft.fft(Psi)
hat_mag2 = np.abs(Psi_hat)**2
upper_mask = np.abs(kx_fine) > (2.0/3.0) * k_max_fine
tail_frac = np.sum(hat_mag2[upper_mask]) / max(np.sum(hat_mag2), 1e-30)
print(f"[diag] spectral tail fraction on fine grid (upper 1/3 of |k|) = {tail_frac:.4e}")

print(f"[diag] N_max trajectory (fine):")
for t, nm in N_max_log:
    print(f"   t={t:.2f}  N_max={nm:.4f}")
