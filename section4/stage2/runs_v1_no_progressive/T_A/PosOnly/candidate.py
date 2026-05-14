"""
Candidate solver: Coupled Burgers-swept-KdV system
Task T_A / PosOnly / E3

PDE:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

Domain: x in [-15, 15], periodic, Nx=256
IC: v(x,0) = 2 sech^2(x+5)
    u(x,0) = 0.5 * v^2 + 0.2 * v  (perturbed from Gardner reduction m=0)

Method: Monolithic IMEX-CN spectral with hyperviscosity for u
  - v equation: IMEX-CN spectral (v_xxx implicit CN, all other terms explicit)
    * Fourier pseudospectral, 2/3 dealiasing
    * Based on kb-kdv-IMEX-CN-spectral-pass, kb-gardner-KdV-method-transfer-moderate-amplitude
  - u equation: forward Euler explicit for -3u u_x and coupling,
    + implicit spectral hyperviscosity denominator: 1 + dt*eps_hv*|k|^(2p)
    * Coupling -d_x(3v_new^2+v_new_xx) uses v_new (already CN-advanced)
    * Hyperviscosity (eps=1e-7, p=8) damps high-k Gibbs oscillations from
      Burgers nonlinearity without introducing O(dx) TVD diffusion
  - dt=0.0005

Key insight: without stabilization, u blows up at t~0.97 (Burgers shock formation
generates Gibbs oscillations). MUSCL-Godunov fixes blow-up but causes excessive
diffusion (v_max drops to 0.36 at T=8). Spectral hyperviscosity prevents blow-up
with minimal O(|k|^16) dissipation only at highest wavenumbers, preserving soliton
structure in v (v_max=1.30 at T=8, meeting >= 1.0 target).
"""

import numpy as np
import os

# ---- Domain ----
L = 30.0
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# ---- Spectral setup ----
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2 * np.pi / L)
dealias_mask = np.abs(k) <= (Nx // 3) * (2 * np.pi / L)
ik3 = (1j * k)**3  # for IMEX-CN v_xxx

# ---- Hyperviscosity for u ----
eps_hv = 1e-7   # hyperviscosity coefficient
p_hv = 8        # order (damps modes ~ |k|^16)
# hv_denom is precomputed for fixed dt below

def dealias_field(f):
    """Apply 2/3 dealiasing."""
    fhat = np.fft.fft(f) * dealias_mask
    return np.real(np.fft.ifft(fhat))

def spectral_dx(f):
    """d/dx via spectral method with 2/3 dealiasing."""
    fhat = np.fft.fft(f) * dealias_mask
    return np.real(np.fft.ifft(1j * k * fhat))

def spectral_d2x(f):
    """d^2/dx^2 via spectral method with 2/3 dealiasing."""
    fhat = np.fft.fft(f) * dealias_mask
    return np.real(np.fft.ifft(-k**2 * fhat))

# ---- Time parameters ----
T_final = 8.0
dt = 0.0005
Nt = int(round(T_final / dt))

# Precompute hyperviscosity denominator for u
hv_denom = 1.0 + dt * eps_hv * np.abs(k)**(2 * p_hv)

# ---- Snapshot setup ----
n_snapshots = 9
snapshot_times = np.linspace(0, T_final, n_snapshots)
snapshot_steps = np.round(snapshot_times / dt).astype(int)
snapshot_steps[-1] = Nt  # ensure final snapshot at exact T

# ---- Initial conditions ----
v = 2.0 / np.cosh(x + 5)**2          # 2 sech^2(x+5)
u = 0.5 * v**2 + 0.2 * v             # perturbed from Gardner reduction
u = dealias_field(u)
v = dealias_field(v)

# ---- Snapshot storage ----
snapshots = np.zeros((n_snapshots, 2, Nx))
snap_count = 0

# Save t=0 snapshot
if 0 in snapshot_steps:
    snapshots[snap_count, 0, :] = u.copy()
    snapshots[snap_count, 1, :] = v.copy()
    snap_count += 1

# ---- Time integration ----
for n in range(1, Nt + 1):
    # ---- v equation: IMEX-CN ----
    # v_t + 6v v_x + v_xxx = -d_x(u v)
    # CN on v_xxx, explicit on 6v v_x + d_x(uv)
    v_x = spectral_dx(v)
    uv = dealias_field(u * v)
    d_uv_dx = spectral_dx(uv)
    rhs_v_exp = -6.0 * v * v_x - d_uv_dx

    v_hat = np.fft.fft(v) * dealias_mask
    rhs_v_hat = np.fft.fft(rhs_v_exp) * dealias_mask
    v_hat_new = (v_hat * (1.0 - 0.5 * dt * ik3) + dt * rhs_v_hat) / (1.0 + 0.5 * dt * ik3)
    v_hat_new *= dealias_mask
    v_new = np.real(np.fft.ifft(v_hat_new))

    # ---- u equation: explicit + implicit hyperviscosity ----
    # u_t + 3u u_x = -d_x(3v^2 + v_xx)
    # Use v_new for coupling (v already CN-advanced => high-k suppressed)
    u_x = spectral_dx(u)
    v_new_sq = dealias_field(v_new * v_new)
    v_new_xx = spectral_d2x(v_new)
    coupling_u = dealias_field(3.0 * v_new_sq + v_new_xx)
    d_coupling_dx = spectral_dx(coupling_u)
    rhs_u = -3.0 * u * u_x - d_coupling_dx

    # Implicit hyperviscosity in denominator: damps |k|^16 modes
    u_hat = np.fft.fft(u) * dealias_mask
    rhs_u_hat = np.fft.fft(rhs_u) * dealias_mask
    u_hat_new = (u_hat + dt * rhs_u_hat) / hv_denom
    u_hat_new *= dealias_mask
    u_new = np.real(np.fft.ifft(u_hat_new))

    u = u_new
    v = v_new

    # Check for NaN/Inf
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        print(f"WARNING: NaN/Inf at step {n}, t={n*dt:.4f}")
        break

    # Save snapshot
    if snap_count < n_snapshots and n == snapshot_steps[snap_count]:
        snapshots[snap_count, 0, :] = u.copy()
        snapshots[snap_count, 1, :] = v.copy()
        snap_count += 1

# Trim if needed
snapshots_out = snapshots[:snap_count]

# ---- Save output ----
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", snapshots_out)

# ---- Diagnostics ----
v_init = 2.0 / np.cosh(x + 5)**2
v_init_amp = np.max(v_init)
v_init_mass = np.trapezoid(v_init, x)

v_final = snapshots_out[-1, 1, :]
u_final = snapshots_out[-1, 0, :]

v_final_amp = np.max(v_final)
v_final_mass = np.trapezoid(v_final, x)
mass_drift_pct = abs(v_final_mass - v_init_mass) / abs(v_init_mass) * 100

from scipy.signal import argrelmax
peaks = argrelmax(v_final, order=5)[0]
n_peaks = len(peaks)

print(f"Snapshots saved: {snap_count}")
print(f"Output shape: {snapshots_out.shape}")
print(f"v initial amplitude: {v_init_amp:.4f}")
print(f"v final amplitude: {v_final_amp:.4f} (ratio: {v_final_amp/v_init_amp:.3f})")
print(f"v initial mass: {v_init_mass:.4f}")
print(f"v final mass: {v_final_mass:.4f}")
print(f"mass drift: {mass_drift_pct:.2f}%")
print(f"Number of local maxima in v_final: {n_peaks}")
print(f"u_final max abs: {np.max(np.abs(u_final)):.4f}")
print(f"v_final max abs: {np.max(np.abs(v_final)):.4f}")
print(f"Phenomenon target check:")
print(f"  v amp >= 0.5 * 2.0 = 1.0: {v_final_amp >= 1.0} (actual {v_final_amp:.4f})")
print(f"  mass drift < 8%: {mass_drift_pct < 8.0} (actual {mass_drift_pct:.2f}%)")
print(f"  bounded |max| < 15: u={np.max(np.abs(u_final))<15}, v={np.max(np.abs(v_final))<15}")
print(f"  ALL TARGETS MET: {v_final_amp >= 1.0 and mass_drift_pct < 8.0 and np.max(np.abs(u_final)) < 15 and np.max(np.abs(v_final)) < 15}")
