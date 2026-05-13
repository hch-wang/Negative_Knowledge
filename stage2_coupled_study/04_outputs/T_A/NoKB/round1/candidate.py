"""
Coupled Burgers-swept-KdV soliton stability simulation.
PDE:
  u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx (u v)

Spatial: pseudo-spectral (FFT) on periodic domain x in [-15, 15], Nx=256
Time:    RK4 with adaptive sub-stepping, dt=1e-3
"""

import numpy as np
import os

# Domain
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]

# Wavenumbers for spectral derivatives
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)

# Dealiasing mask (2/3 rule)
k_max = np.max(np.abs(k))
dealias = np.abs(k) <= (2.0 / 3.0) * k_max


def spectral_deriv(f, order=1):
    """Compute d^order f / dx^order using FFT."""
    fh = np.fft.fft(f)
    fh *= dealias
    return np.real(np.fft.ifft((1j * k) ** order * fh))


def rhs(u, v):
    """Compute time derivatives for u and v."""
    # Spectral derivatives
    u_x = spectral_deriv(u, 1)
    v_x = spectral_deriv(v, 1)
    v_xx = spectral_deriv(v, 2)
    v_xxx = spectral_deriv(v, 3)

    # u_t = -3 u u_x - d/dx(3 v^2 + v_xx)
    #      = -3 u u_x - 6 v v_x - v_xxx
    u_t = -3.0 * u * u_x - 6.0 * v * v_x - v_xxx

    # v_t = -6 v v_x - v_xxx - d/dx(u v)
    #      = -6 v v_x - v_xxx - u_x v - u v_x
    v_t = -6.0 * v * v_x - v_xxx - u_x * v - u * v_x

    return u_t, v_t


def rk4_step(u, v, dt):
    """One RK4 step."""
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)

    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new


# Initial conditions
v0 = 2.0 / np.cosh(x + 5.0) ** 2          # sech^2 soliton
u0 = 0.5 * v0 ** 2 + 0.2 * v0             # perturbed from m=0 reduction

u = u0.copy()
v = v0.copy()

# Time integration parameters
T_final = 8.0
dt = 5e-4
n_snapshots = 9  # t=0 plus 8 more (save at t=0,1,...,8)
t_save = np.linspace(0.0, T_final, n_snapshots)

snapshots = []
t = 0.0
save_idx = 0

# Save initial condition
if save_idx < len(t_save) and abs(t - t_save[save_idx]) < 1e-10:
    snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
    save_idx += 1

# Integrate
while t < T_final - 1e-12:
    # Adjust dt near save points
    if save_idx < len(t_save):
        dt_use = min(dt, t_save[save_idx] - t)
    else:
        dt_use = min(dt, T_final - t)

    if dt_use < 1e-14:
        # At a save point
        if save_idx < len(t_save):
            snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
            save_idx += 1
        dt_use = dt

    u, v = rk4_step(u, v, dt_use)
    t += dt_use

    # Check for save points
    if save_idx < len(t_save) and abs(t - t_save[save_idx]) < 1e-10:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        save_idx += 1

# Save any remaining snapshots at final time
while save_idx < len(t_save):
    snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
    save_idx += 1

result = np.array(snapshots)  # shape: (n_snapshots, 2, 256)
print(f"Result shape: {result.shape}")
print(f"Max |u| = {np.max(np.abs(result[-1, 0])):.4f}, Max |v| = {np.max(np.abs(result[-1, 1])):.4f}")
print(f"v peak amplitude at final time: {np.max(result[-1, 1]):.4f}")
print(f"v mass at t=0: {np.sum(result[0, 1]) * dx:.4f}, at t=T: {np.sum(result[-1, 1]) * dx:.4f}")

# Save output
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", result)
print("Saved to pred_results/T_A.npy")
