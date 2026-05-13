import numpy as np

# Parameters
Nx = 200
x = np.linspace(-1, 1, Nx, endpoint=False)
dx = x[1] - x[0]
T = 0.1

# Initial condition
u = -np.sin(np.pi * x)

# CFL-based time stepping with upwind scheme (stable for Burgers)
CFL = 0.8
t = 0.0

while t < T:
    max_speed = np.max(np.abs(u))
    if max_speed == 0:
        dt = 1e-4
    else:
        dt = CFL * dx / max_speed
    if t + dt > T:
        dt = T - t

    # Godunov flux for Burgers equation (upwind-like)
    # Flux: f(u) = u^2/2
    # Godunov flux: based on sign of wave speed
    u_plus = np.roll(u, -1)   # u_{i+1}
    u_minus = u                # u_{i}

    # Godunov flux at right interface (between i and i+1)
    def godunov_flux(ul, ur):
        # For Burgers: f(u) = u^2/2, convex flux
        # Godunov: minimize f on [ul,ur] if ul<=ur, maximize if ul>ur
        f_ul = ul**2 / 2.0
        f_ur = ur**2 / 2.0
        flux = np.where(
            ul <= ur,
            np.where(ul >= 0, f_ul, np.where(ur <= 0, f_ur, 0.0)),
            np.where(ul + ur >= 0, f_ul, f_ur)
        )
        return flux

    F_right = godunov_flux(u_minus, u_plus)       # F_{i+1/2}
    F_left = np.roll(F_right, 1)                   # F_{i-1/2}

    u = u - (dt / dx) * (F_right - F_left)
    t += dt

# Save result
import os
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/burgers_A2.npy", u)
