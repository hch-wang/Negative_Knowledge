import numpy as np

# Domain
Nx = 200
x = np.linspace(-1, 1, Nx, endpoint=False)
dx = x[1] - x[0]

# Initial condition
u = -np.sin(np.pi * x)

# Time parameters
T = 0.5
CFL = 0.4  # <= 0.5 as required

# Time-stepping: forward Euler + 2nd-order central finite differences
t = 0.0
while t < T:
    max_u = np.max(np.abs(u))
    if max_u < 1e-12:
        dt = CFL * dx
    else:
        dt = CFL * dx / max_u
    if t + dt > T:
        dt = T - t

    # 2nd-order central finite difference for u_x (periodic BC)
    u_x = (np.roll(u, -1) - np.roll(u, 1)) / (2.0 * dx)

    # Forward Euler update
    u = u - dt * u * u_x

    t += dt

# Save result
import os
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/burgers_A1.npy", u)
