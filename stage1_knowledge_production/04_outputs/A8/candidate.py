import numpy as np
import os

# Parameters
g = 1.0
Nx = 200
x = np.linspace(-1.0, 1.0, Nx, endpoint=False)
dx = x[1] - x[0]
T = 0.4
CFL = 0.4

# Initial conditions: dam-break
h = np.where(x < 0, 2.0, 1.0)
u = np.zeros(Nx)

# Conserved variables: q1 = h, q2 = h*u
q1 = h.copy()
q2 = h * u

def flux(q1, q2):
    h = q1
    hu = q2
    u = np.where(h > 1e-12, hu / h, 0.0)
    f1 = hu
    f2 = h * u * u + 0.5 * g * h * h
    return f1, f2

def max_wave_speed(q1, q2):
    h = q1
    hu = q2
    u = np.where(h > 1e-12, hu / h, 0.0)
    c = np.sqrt(g * np.maximum(h, 0.0))
    return np.max(np.abs(u) + c)

t = 0.0
while t < T:
    # Compute time step from CFL
    smax = max_wave_speed(q1, q2)
    dt = CFL * dx / (smax + 1e-12)
    if t + dt > T:
        dt = T - t

    # Compute fluxes at cell centers
    f1, f2 = flux(q1, q2)

    # Global Lax-Friedrichs flux at interfaces
    # Periodic indexing: interface i+1/2 uses cells i and i+1
    # q_left = q[i], q_right = q[(i+1) % Nx]
    q1_l = q1
    q1_r = np.roll(q1, -1)
    q2_l = q2
    q2_r = np.roll(q2, -1)

    f1_l, f2_l = flux(q1_l, q2_l)
    f1_r, f2_r = flux(q1_r, q2_r)

    # Global Lax-Friedrichs: alpha = max wave speed globally
    alpha = smax

    # Numerical flux at i+1/2
    lf1 = 0.5 * (f1_l + f1_r) - 0.5 * alpha * (q1_r - q1_l)
    lf2 = 0.5 * (f2_l + f2_r) - 0.5 * alpha * (q2_r - q2_l)

    # Flux at i-1/2 = shift of flux at i+1/2 (roll right)
    lf1_left = np.roll(lf1, 1)
    lf2_left = np.roll(lf2, 1)

    # Explicit Euler update
    q1 = q1 - (dt / dx) * (lf1 - lf1_left)
    q2 = q2 - (dt / dx) * (lf2 - lf2_left)

    t += dt

# Save output
result = np.array([q1, q2])  # shape (2, 200)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/sw_A8.npy", result)
