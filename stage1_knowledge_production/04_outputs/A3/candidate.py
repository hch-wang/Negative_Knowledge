import numpy as np

# Parameters
Nx = 200
x = np.linspace(-1.0, 1.0, Nx, endpoint=False)
dx = x[1] - x[0]
T = 10.0

# Initial condition
u = -np.sin(np.pi * x)

# Lax-Friedrichs scheme (stable for |u| * dt/dx <= 1)
# Choose dt via CFL with CFL=0.5
CFL = 0.5
t = 0.0

while t < T:
    max_speed = np.max(np.abs(u)) + 1e-12
    dt = CFL * dx / max_speed
    if t + dt > T:
        dt = T - t

    # Periodic indexing
    u_right = np.roll(u, -1)
    u_left = np.roll(u, 1)

    # Lax-Friedrichs flux: F(u) = u^2/2
    F_right = 0.5 * (0.5 * (u ** 2) + 0.5 * (u_right ** 2)) - (dx / (2.0 * dt)) * (u_right - u)
    F_left  = 0.5 * (0.5 * (u_left ** 2) + 0.5 * (u ** 2)) - (dx / (2.0 * dt)) * (u - u_left)

    u_new = u - (dt / dx) * (F_right - F_left)
    u = u_new
    t += dt

np.save("pred_results/burgers_A3.npy", u)
