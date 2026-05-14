"""
Coupled Burgers-swept-KdV solver — T_A NegOnly, Experiment E3
Method: Fourier pseudospectral + scipy RK45 adaptive time-stepping
  - All derivatives computed in Fourier space
  - 2/3 dealiasing on all nonlinear products
  - Adaptive RK45 handles stiffness automatically via step-size control
  - rtol=1e-4, atol=1e-6 for accuracy

PDE:
  u_t + 3*u*u_x = -d/dx(3*v^2 + v_xx)
  v_t + 6*v*v_x + v_xxx = -d/dx(u*v)

x in [-15, 15], Nx = 256, T = 8.0
Save 9 snapshots at t = 0, 1, 2, 3, 4, 5, 6, 7, 8.
"""

import numpy as np
import os
from scipy.integrate import solve_ivp

# ── Grid ──────────────────────────────────────────────────────────────────────
L = 30.0
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2.0 * np.pi / L)

# ── Initial conditions ─────────────────────────────────────────────────────────
v0 = 2.0 / np.cosh(x + 5)**2
u0 = 0.5 * v0**2 + 0.2 * v0

# ── 2/3 dealiasing mask ────────────────────────────────────────────────────────
k_max_abs = np.max(np.abs(k))
dealias_mask = (np.abs(k) <= (2.0/3.0) * k_max_abs).astype(float)

def dealias(fhat):
    return fhat * dealias_mask

def rhs_coupled(t, y):
    """
    RHS for the coupled system in Fourier space.
    y = [Re(u_hat), Im(u_hat), Re(v_hat), Im(v_hat)] flattened real array.
    """
    u_hat = y[:Nx] + 1j * y[Nx:2*Nx]
    v_hat = y[2*Nx:3*Nx] + 1j * y[3*Nx:]

    u = np.real(np.fft.ifft(u_hat))
    v = np.real(np.fft.ifft(v_hat))

    # Derivatives in Fourier space
    u_x_hat = 1j * k * u_hat
    v_x_hat = 1j * k * v_hat
    v_xx_hat = -k**2 * v_hat   # (ik)^2 = -k^2
    v_xxx_hat = -1j * k**3 * v_hat  # (ik)^3 = -ik^3

    u_x = np.real(np.fft.ifft(u_x_hat))
    v_x = np.real(np.fft.ifft(v_x_hat))

    # Nonlinear terms (dealiased)
    # u equation: u_t = -3*u*u_x - d/dx(3*v^2 + v_xx)
    #           = -3*u*u_x - 3*d(v^2)/dx - v_xxx
    nl_u_phys = -3.0 * u * u_x
    nl_u_hat = dealias(np.fft.fft(nl_u_phys))
    v2_hat = dealias(np.fft.fft(v**2))
    dv2dx_hat = 1j * k * v2_hat
    u_rhs_hat = nl_u_hat - 3.0 * dv2dx_hat - v_xxx_hat

    # v equation: v_t = -6*v*v_x - v_xxx - d/dx(u*v)
    nl_v_phys = -6.0 * v * v_x
    nl_v_hat = dealias(np.fft.fft(nl_v_phys))
    uv_hat = dealias(np.fft.fft(u * v))
    duv_dx_hat = 1j * k * uv_hat
    v_rhs_hat = nl_v_hat - v_xxx_hat - duv_dx_hat

    # Pack into real array
    dy = np.concatenate([
        np.real(u_rhs_hat), np.imag(u_rhs_hat),
        np.real(v_rhs_hat), np.imag(v_rhs_hat)
    ])
    return dy

# ── Solve ──────────────────────────────────────────────────────────────────────
T_final = 8.0
t_eval = np.linspace(0, T_final, 9)   # 9 snapshots

# Pack initial condition
u0_hat = np.fft.fft(u0)
v0_hat = np.fft.fft(v0)
y0 = np.concatenate([
    np.real(u0_hat), np.imag(u0_hat),
    np.real(v0_hat), np.imag(v0_hat)
])

print(f"Starting RK45 integration to T={T_final}...")
print(f"y0 shape: {y0.shape}, max|y0|: {np.max(np.abs(y0)):.4f}")

sol = solve_ivp(
    rhs_coupled,
    [0.0, T_final],
    y0,
    method='RK45',
    t_eval=t_eval,
    rtol=1e-4,
    atol=1e-6,
    max_step=1e-3,
    dense_output=False
)

print(f"Solver status: {sol.status}, message: {sol.message}")
print(f"Number of steps: {sol.t.shape[0]}, nfev: {sol.nfev}")

# ── Extract snapshots ──────────────────────────────────────────────────────────
snapshots = []
for i in range(len(sol.t)):
    y = sol.y[:, i]
    u_hat = y[:Nx] + 1j * y[Nx:2*Nx]
    v_hat = y[2*Nx:3*Nx] + 1j * y[3*Nx:]
    u_snap = np.real(np.fft.ifft(u_hat))
    v_snap = np.real(np.fft.ifft(v_hat))
    snapshots.append(np.stack([u_snap, v_snap], axis=0))
    if i % 2 == 0:
        print(f"  t={sol.t[i]:.2f}: v_peak={np.max(v_snap):.4f}, max|u|={np.max(np.abs(u_snap)):.4f}")

result = np.array(snapshots)   # shape (n_snapshots, 2, 256)
print(f"\nOutput shape: {result.shape}")

# ── Diagnostics ────────────────────────────────────────────────────────────────
v_final = result[-1, 1, :]
u_final = result[-1, 0, :]
v_init  = result[0, 1, :]

peak_amp = np.max(v_final)
init_amp = np.max(v_init)
print(f"v initial peak: {init_amp:.4f}, v final peak: {peak_amp:.4f}, ratio: {peak_amp/init_amp:.4f}")

mass_init = np.sum(v_init) * dx
mass_final = np.sum(v_final) * dx
mass_drift_pct = abs(mass_final - mass_init) / abs(mass_init) * 100
print(f"mass_init: {mass_init:.4f}, mass_final: {mass_final:.4f}, drift: {mass_drift_pct:.2f}%")

from scipy.signal import find_peaks
peaks, _ = find_peaks(v_final, height=0.1)
print(f"Peaks in v_final (h>0.1): {len(peaks)}")

print(f"max|u_final|: {np.max(np.abs(u_final)):.4f}, max|v_final|: {np.max(np.abs(v_final)):.4f}")
print(f"any NaN: {np.any(np.isnan(result))}, any Inf: {np.any(np.isinf(result))}")

# ── Save ───────────────────────────────────────────────────────────────────────
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_A.npy")
np.save(out_path, result)
print(f"Saved to {out_path}")
