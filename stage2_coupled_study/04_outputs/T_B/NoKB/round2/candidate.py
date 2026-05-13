"""
T_B Round 2: Gaussian wave packet -> soliton train decomposition
Coupled Burgers-swept-KdV system on periodic domain x in [-15, 15]

u_t + 3 u u_x = -d/dx(3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -d/dx(u v)

Round 1 blew up due to insufficient time-step control.
Round 2 fixes: adaptive RK45 via scipy.integrate.solve_ivp + 2/3 dealiasing.
"""

import numpy as np
import os
from scipy.integrate import solve_ivp

# Grid
Nx = 256
L = 30.0  # total domain length [-15, 15]
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for spectral differentiation
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi

# 2/3 dealiasing mask
k_max = np.max(np.abs(k))
dealias = np.abs(k) <= (2.0 / 3.0) * k_max

def deriv_spectral(f_hat):
    """Compute d/dx f from its hat, return in physical space."""
    return np.real(np.fft.ifft(1j * k * f_hat))

def deriv3_spectral(f_hat):
    """Compute d^3/dx^3 f from its hat, return in physical space."""
    return np.real(np.fft.ifft(-1j * k**3 * f_hat))

def rhs_flat(t, y):
    u = y[:Nx]
    v = y[Nx:]

    # Dealias
    u_hat = np.fft.fft(u) * dealias
    v_hat = np.fft.fft(v) * dealias

    u = np.real(np.fft.ifft(u_hat))
    v = np.real(np.fft.ifft(v_hat))

    # Spectral derivatives
    u_x = deriv_spectral(u_hat)
    v_x = deriv_spectral(v_hat)
    v_xx = deriv_spectral(1j * k * v_hat)
    v_xxx = deriv3_spectral(v_hat)

    # u equation: u_t = -3 u u_x - d/dx(3 v^2 + v_xx)
    inner_u = 3.0 * v**2 + v_xx
    inner_u_hat = np.fft.fft(inner_u) * dealias
    d_inner_u_dx = deriv_spectral(inner_u_hat)
    du_dt = -3.0 * u * u_x - d_inner_u_dx

    # v equation: v_t = -6 v v_x - v_xxx - d/dx(u v)
    uv = u * v
    uv_hat = np.fft.fft(uv) * dealias
    duv_dx = deriv_spectral(uv_hat)
    dv_dt = -6.0 * v * v_x - v_xxx - duv_dx

    return np.concatenate([du_dt, dv_dt])

# Initial conditions
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros(Nx)
y0 = np.concatenate([u0, v0])

# Time integration with adaptive RK45
T = 6.0
n_snapshots = 7
t_eval = np.linspace(0, T, n_snapshots)

sol = solve_ivp(
    rhs_flat,
    [0, T],
    y0,
    method='RK45',
    t_eval=t_eval,
    rtol=1e-6,
    atol=1e-8,
    max_step=0.01,
)

# Build output array: shape (n_snapshots, 2, 256)
snapshots = np.zeros((n_snapshots, 2, Nx))
for i in range(n_snapshots):
    snapshots[i, 0, :] = sol.y[:Nx, i]   # u
    snapshots[i, 1, :] = sol.y[Nx:, i]   # v

# Save
os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_B.npy', snapshots)

print(f"Saved shape: {snapshots.shape}")
print(f"Final v max: {snapshots[-1, 1, :].max():.4f}, min: {snapshots[-1, 1, :].min():.4f}")
print(f"Final u max: {snapshots[-1, 0, :].max():.4f}")
