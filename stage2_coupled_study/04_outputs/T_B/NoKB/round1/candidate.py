"""
T_B: Gaussian wave packet -> soliton train decomposition
Coupled Burgers-swept-KdV system on periodic domain x in [-15, 15]

u_t + 3 u u_x = -d/dx(3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -d/dx(u v)
"""

import numpy as np
import os

# Grid
Nx = 256
L = 30.0  # total domain length [-15, 15]
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for spectral differentiation
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi

# Initial conditions
v = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u = np.zeros(Nx)

# Final time and snapshots
T = 6.0
n_snapshots = 7
t_snapshots = np.linspace(0, T, n_snapshots)

# Storage
snapshots = []

def deriv_spectral(f, k):
    """Compute d/dx f using spectral method."""
    return np.real(np.fft.ifft(1j * k * np.fft.fft(f)))

def deriv3_spectral(f, k):
    """Compute d^3/dx^3 f using spectral method."""
    return np.real(np.fft.ifft(-1j * k**3 * np.fft.fft(f)))

def rhs(u, v, k):
    """Compute RHS of the coupled system."""
    # u equation: u_t = -3 u u_x - d/dx(3 v^2 + v_xx)
    u_x = deriv_spectral(u, k)
    v_xx = deriv_spectral(deriv_spectral(v, k), k)
    rhs_inner = 3.0 * v**2 + v_xx
    drhs_inner_dx = deriv_spectral(rhs_inner, k)
    du_dt = -3.0 * u * u_x - drhs_inner_dx

    # v equation: v_t = -6 v v_x - v_xxx - d/dx(u v)
    v_x = deriv_spectral(v, k)
    v_xxx = deriv3_spectral(v, k)
    uv = u * v
    duv_dx = deriv_spectral(uv, k)
    dv_dt = -6.0 * v * v_x - v_xxx - duv_dx

    return du_dt, dv_dt

def rk4_step(u, v, k, dt):
    """Classic 4th-order Runge-Kutta step."""
    k1u, k1v = rhs(u, v, k)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v, k)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v, k)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v, k)
    u_new = u + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v_new = v + (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v)
    return u_new, v_new

# Time stepping with adaptive-ish fixed small dt
# CFL-like constraint: for KdV-like systems, dt ~ dx^3 / (some constant)
# Also Burgers constraint: dt ~ dx / max|u|
# Start with dt = 1e-4
dt = 5e-4

t = 0.0
snap_idx = 0

# Store initial snapshot
if t_snapshots[snap_idx] <= t + 1e-12:
    snapshots.append(np.stack([u.copy(), v.copy()]))
    snap_idx += 1

max_steps = int(T / dt) + 2

for step in range(max_steps):
    if t >= T - 1e-10:
        break

    # Adapt dt to not overshoot snapshot or final time
    next_snap_t = t_snapshots[snap_idx] if snap_idx < n_snapshots else T
    dt_use = min(dt, next_snap_t - t, T - t)
    if dt_use <= 0:
        dt_use = dt

    u, v = rk4_step(u, v, k, dt_use)
    t += dt_use

    # Dealiasing: zero out high wavenumbers (2/3 rule)
    U_hat = np.fft.fft(u)
    V_hat = np.fft.fft(v)
    cutoff = int(Nx / 3)
    U_hat[cutoff:Nx - cutoff] = 0.0
    V_hat[cutoff:Nx - cutoff] = 0.0
    u = np.real(np.fft.ifft(U_hat))
    v = np.real(np.fft.ifft(V_hat))

    # Check for snapshot
    while snap_idx < n_snapshots and t >= t_snapshots[snap_idx] - 1e-10:
        snapshots.append(np.stack([u.copy(), v.copy()]))
        snap_idx += 1

# Ensure we have all snapshots (fill if needed)
while len(snapshots) < n_snapshots:
    snapshots.append(np.stack([u.copy(), v.copy()]))

# Shape: (n_snapshots, 2, 256)
result = np.array(snapshots[:n_snapshots])
assert result.shape == (n_snapshots, 2, Nx), f"Shape mismatch: {result.shape}"

# Save
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", result)
print(f"Saved shape: {result.shape}")
print(f"Final v max: {result[-1, 1, :].max():.4f}, min: {result[-1, 1, :].min():.4f}")
print(f"Final u max: {result[-1, 0, :].max():.4f}, min: {result[-1, 0, :].min():.4f}")

# Quick soliton check
from scipy.signal import find_peaks
v_final = result[-1, 1, :]
peaks, props = find_peaks(v_final, height=0.8, distance=5)
print(f"Detected peaks >= 0.8: {len(peaks)} at indices {peaks}")
