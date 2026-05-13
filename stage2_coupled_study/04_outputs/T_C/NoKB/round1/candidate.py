"""
Coupled Burgers-swept-KdV system: bore-soliton interaction
u_t + 3 u u_x = -d/dx(3v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -d/dx(u v)
Periodic domain x in [-15, 15], Nx=256, T=8.0
"""

import numpy as np
from scipy.fft import fft, ifft, fftfreq
import os

# ---- Grid ----
L = 30.0          # domain length
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for spectral differentiation
k = 2 * np.pi / L * fftfreq(Nx, d=1.0/Nx)
# Anti-aliasing: zero out top 1/3 of wavenumbers
k_max = np.max(np.abs(k))
k_alias = 2.0 / 3.0 * k_max
k_dealias = np.where(np.abs(k) <= k_alias, k, 0.0)

# ---- Initial conditions ----
def sech2(x):
    return 1.0 / np.cosh(x)**2

u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 * sech2(x + 8.0)

# ---- Spectral derivatives ----
def deriv(f, order=1):
    """Compute d^order f / dx^order spectrally with dealiasing."""
    fh = fft(f)
    return np.real(ifft((1j * k_dealias)**order * fh))

def rhs(u, v):
    """Compute time derivatives for u and v."""
    # u_t = -3 u u_x - d/dx(3v^2 + v_xx)
    u_x = deriv(u, 1)
    v_x = deriv(v, 1)
    v_xx = deriv(v, 2)

    # RHS for u
    bracket_u = 3.0 * v**2 + v_xx
    u_t = -3.0 * u * u_x - deriv(bracket_u, 1)

    # v_t = -6 v v_x - v_xxx - d/dx(u v)
    v_xxx = deriv(v, 3)
    bracket_v = u * v
    v_t = -6.0 * v * v_x - v_xxx - deriv(bracket_v, 1)

    return u_t, v_t

# ---- Time integration: RK4 ----
T = 8.0
# CFL-based dt: dispersive term v_xxx needs small dt
# Conservative choice: dt ~ 0.4 * dx^3 / max(|v|), but simpler: fixed small dt
dt = 0.002
n_steps = int(T / dt)
dt = T / n_steps  # exact

# Snapshot times: 5 snapshots including t=0 and t=T
n_snapshots = 8
snap_times = np.linspace(0, T, n_snapshots)
snap_steps = [int(round(t / dt)) for t in snap_times]
snap_set = set(snap_steps)

snapshots = []

u = u0.copy()
v = v0.copy()

for step in range(n_steps + 1):
    if step in snap_set:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

    if step == n_steps:
        break

    # RK4
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v)

    u = u + dt/6.0 * (k1u + 2*k2u + 2*k3u + k4u)
    v = v + dt/6.0 * (k1v + 2*k2v + 2*k3v + k4v)

# Stack snapshots: shape (n_snapshots, 2, Nx)
result = np.array(snapshots)  # (n_snapshots, 2, 256)

# Save output
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
np.save(os.path.join(out_dir, "T_C.npy"), result)

print(f"Saved shape: {result.shape}")
print(f"u range at T: [{u.min():.4f}, {u.max():.4f}]")
print(f"v range at T: [{v.min():.4f}, {v.max():.4f}]")
print(f"v peak at T: {v.max():.4f}")
