"""
Coupled Burgers-swept-KdV soliton stability solver.
Method: Fourier pseudospectral IMEX-Crank-Nicolson with 2/3 dealiasing.
  - Dispersive term v_xxx handled implicitly (CN).
  - All nonlinear and coupling terms handled explicitly.
  - Burgers u equation handled spectrally with explicit nonlinear.
"""

import numpy as np
import os

# Domain
L = 30.0  # x in [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2.0 * np.pi / L)

# Dealiasing mask (2/3 rule)
k_max = np.max(np.abs(k))
dealias = np.abs(k) <= (2.0/3.0) * k_max

# Time parameters
T_final = 8.0
dt = 0.0005
n_steps = int(T_final / dt)

# Snapshots: 5 evenly spaced from t=0 to T_final
n_snapshots = 9  # more than required minimum of 5
snapshot_times = np.linspace(0.0, T_final, n_snapshots)
snapshot_indices = [int(round(t / dt)) for t in snapshot_times]
snapshot_indices[-1] = n_steps  # ensure last snapshot is exactly at T

# Initial condition
v0 = 2.0 * (1.0 / np.cosh(x + 5.0))**2
u0 = 0.5 * v0**2 + 0.2 * v0

def deriv_x_spectral(f_hat, k_arr, dealias_mask):
    """Spectral derivative in x."""
    return np.real(np.fft.ifft(1j * k_arr * dealias_mask * f_hat))

def antideriv_from_hat(f_hat, k_arr):
    """Return ifft of f_hat (already in spectral space)."""
    return np.real(np.fft.ifft(f_hat))

def rhs_u(u, v, k_arr, dealias_mask):
    """
    RHS for u equation (explicit part):
    u_t = -3 u u_x - d/dx(3v^2 + v_xx)
    """
    u_hat = np.fft.fft(u) * dealias_mask
    v_hat = np.fft.fft(v) * dealias_mask

    u_x = deriv_x_spectral(u_hat, k_arr, dealias_mask)
    v_xx_hat = (1j * k_arr)**2 * v_hat * dealias_mask
    v_xx = np.real(np.fft.ifft(v_xx_hat))

    nonlin_u = -3.0 * u * u_x
    coupling_u_x_hat = np.fft.fft(3.0 * v**2 + v_xx) * dealias_mask
    coupling_u = -np.real(np.fft.ifft(1j * k_arr * coupling_u_x_hat))

    return nonlin_u + coupling_u

def rhs_v_explicit(u, v, k_arr, dealias_mask):
    """
    Explicit RHS for v equation:
    v_t = -6 v v_x - d/dx(u v)   [v_xxx handled implicitly by CN]
    """
    u_hat = np.fft.fft(u) * dealias_mask
    v_hat = np.fft.fft(v) * dealias_mask

    v_x = deriv_x_spectral(v_hat, k_arr, dealias_mask)

    nonlin_v = -6.0 * v * v_x
    uv_hat = np.fft.fft(u * v) * dealias_mask
    coupling_v = -np.real(np.fft.ifft(1j * k_arr * uv_hat))

    return nonlin_v + coupling_v

# CN operators for v: (I - dt/2 * (-ik^3)) applied in spectral space
# v_t + v_xxx = explicit  =>  implicit: v_xxx term
# CN: (1 + dt/2 * ik^3) V_hat^{n+1} = (1 - dt/2 * ik^3) V_hat^n + dt * explicit_hat
ik3 = (1j * k)**3  # = i^3 k^3 = -ik^3 ... actually: d^3/dx^3 -> (ik)^3 = i^3 k^3 = -ik^3
cn_denom_v = 1.0 + (dt / 2.0) * ik3   # denominator for implicit update
cn_numer_factor_v = 1.0 - (dt / 2.0) * ik3  # factor for current step

# u equation: no dispersive term, handled fully explicitly with Euler
# (spectral for spatial accuracy)

u = u0.copy()
v = v0.copy()

snapshots = []
step = 0

# Store initial snapshot
snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

for snap_idx in range(1, n_snapshots):
    target_step = snapshot_indices[snap_idx]
    while step < target_step:
        u_hat = np.fft.fft(u) * dealias_mask
        v_hat = np.fft.fft(v) * dealias_mask

        # Explicit RHS for u (forward Euler for u — no implicit term)
        du = rhs_u(u, v, k, dealias_mask)
        u_new = u + dt * du

        # IMEX-CN for v: treat v_xxx implicitly
        ev = rhs_v_explicit(u, v, k, dealias_mask)
        ev_hat = np.fft.fft(ev) * dealias_mask

        # CN update in spectral space:
        # cn_denom_v * V_hat_new = cn_numer_factor_v * v_hat + dt * ev_hat
        v_hat_new = (cn_numer_factor_v * v_hat + dt * ev_hat) / cn_denom_v
        v_hat_new *= dealias_mask
        v_new = np.real(np.fft.ifft(v_hat_new))

        u = u_new
        v = v_new
        step += 1

    snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

# Shape: (n_snapshots, 2, 256)
result = np.stack(snapshots, axis=0)
print(f"Result shape: {result.shape}")
print(f"Final v max: {np.max(result[-1, 1, :]):.4f}")
print(f"Final u max: {np.max(np.abs(result[-1, 0, :])):.4f}")
print(f"Final v mass: {np.sum(result[-1, 1, :]) * dx:.4f}")
print(f"Initial v mass: {np.sum(result[0, 1, :]) * dx:.4f}")

# Save
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", result)
print("Saved pred_results/T_A.npy")
