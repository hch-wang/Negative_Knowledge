"""E2: E1 + 2/3-rule dealiasing.
Method: Fourier pseudospectral derivatives, explicit RK4 in time,
WITH 2/3-rule dealiasing applied to nonlinear products (uv, v^2)
before computing their x-derivative.

PDE:
  u_t + 3 u u_x = -d/dx(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx(u v)

Periodic [-15, 15], Nx=256, T=6.0.
IC: v0 = 4 exp(-(x+5)^2/2.25), u0 = 0.
"""
import os
import numpy as np

# Domain
L = 30.0
Nx = 256
x = np.linspace(-L/2, L/2, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=L/Nx)
ik = 1j * k
ik3 = 1j * (k ** 3)

# 2/3-rule dealiasing mask: zero modes with |k_index| > N/3
k_index = np.fft.fftfreq(Nx, d=1.0/Nx)  # returns -N/2..N/2-1 integer indices
dealias_mask = (np.abs(k_index) <= Nx / 3.0).astype(np.float64)
# Apply to FFT coefficients

# Initial conditions
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros_like(x)

def fft_dealiased(arr):
    """FFT then apply dealias mask."""
    f = np.fft.fft(arr)
    return f * dealias_mask

def deriv(arr):
    """First derivative via FFT (no mask)."""
    return np.real(np.fft.ifft(ik * np.fft.fft(arr)))

def deriv_dealiased_product(a, b):
    """Returns d/dx(a*b) with 2/3-rule dealiasing.
    The product is computed in physical space then masked in spectral space
    before differentiation.
    """
    prod = a * b
    f_prod = np.fft.fft(prod) * dealias_mask
    return np.real(np.fft.ifft(ik * f_prod))

def deriv3(arr):
    """Third derivative via FFT (linear, no need to dealias)."""
    return np.real(np.fft.ifft(ik3 * np.fft.fft(arr)))

def rhs(u, v):
    """
    Returns (du/dt, dv/dt) with dealiased nonlinear products.
    PDE:
        u_t + 3 u u_x = -d/dx(3 v^2 + v_xx)
        v_t + 6 v v_x + v_xxx = -d/dx(u v)
    so:
        u_t = -3 u u_x - 6 v v_x - v_xxx
            = -(3/2) d/dx(u^2) - 3 d/dx(v^2) - v_xxx
        v_t = -6 v v_x - v_xxx - d/dx(u v)
            = -3 d/dx(v^2) - v_xxx - d/dx(u v)
    """
    # Linear term v_xxx (no dealiasing needed for linear terms)
    vxxx = deriv3(v)
    # Nonlinear terms: dealiased product-derivative
    u2_x = deriv_dealiased_product(u, u)  # d/dx(u^2)
    v2_x = deriv_dealiased_product(v, v)  # d/dx(v^2)
    uv_x = deriv_dealiased_product(u, v)  # d/dx(u*v)

    du = -1.5 * u2_x - 3.0 * v2_x - vxxx
    dv = -3.0 * v2_x - vxxx - uv_x
    return du, dv

def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    un = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    vn = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return un, vn

# Time stepping
T = 6.0
dt = 2e-5
nsteps = int(round(T / dt))
n_snapshots = 7
snap_steps = np.linspace(0, nsteps, n_snapshots).astype(int)
snap_set = set(snap_steps.tolist())

snapshots = []
u = u0.copy()
v = v0.copy()
snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

import sys
for step in range(1, nsteps + 1):
    u, v = rk4_step(u, v, dt)
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        print(f"[E2] NaN/Inf at step {step} (t={step*dt:.4f}); stopping.")
        while len(snapshots) < n_snapshots:
            snapshots.append(np.stack([np.nan_to_num(u, nan=0.0).copy(), np.nan_to_num(v, nan=0.0).copy()], axis=0))
        break
    if step in snap_set:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        print(f"[E2] snap step={step}, t={step*dt:.4f}, max|v|={np.max(np.abs(v)):.4f}, max|u|={np.max(np.abs(u)):.4f}", flush=True)

while len(snapshots) > n_snapshots:
    snapshots.pop()
while len(snapshots) < n_snapshots:
    snapshots.append(snapshots[-1])

out = np.stack(snapshots, axis=0)
print(f"[E2] output shape: {out.shape}")

v_final = out[-1, 1]
u_final = out[-1, 0]
print(f"[E2] all_finite: {np.all(np.isfinite(out))}")
print(f"[E2] v_final: max={np.max(v_final):.4f}, min={np.min(v_final):.4f}")
mass_v0 = np.sum(v0) * dx
mass_vT = np.sum(v_final) * dx
print(f"[E2] mass(v) initial={mass_v0:.6f}, final={mass_vT:.6f}, drift={(mass_vT-mass_v0)/mass_v0*100:.3f}%")

from scipy.signal import find_peaks
peaks05, _ = find_peaks(v_final, height=0.5)
print(f"[E2] v_final peaks above 0.5: {len(peaks05)} at x={x[peaks05]}, heights={v_final[peaks05]}")
peaks08, _ = find_peaks(v_final, height=0.8)
print(f"[E2] v_final peaks above 0.8: {len(peaks08)} at x={x[peaks08]}, heights={v_final[peaks08]}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", out)
print("[E2] saved pred_results/T_B.npy")
