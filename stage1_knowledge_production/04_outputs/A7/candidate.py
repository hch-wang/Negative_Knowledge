import numpy as np

# Parameters
g = 1.0
Nx = 200
x = np.linspace(-1, 1, Nx, endpoint=False)
dx = x[1] - x[0]
T = 0.4

# CFL: forward Euler requires dt <= dx / max_wave_speed
# We use a fixed small dt to try to stay stable (though instability is expected)
dt = 0.4 * dx  # CFL ~ 0.4, but may blow up near discontinuity

# Initial conditions
h = np.where(x < 0, 2.0, 1.0)
hu = np.zeros(Nx)

t = 0.0
while t < T:
    if t + dt > T:
        dt = T - t

    # Compute flux arrays for h equation: F1 = hu
    # Compute flux arrays for hu equation: F2 = hu^2/h + g*h^2/2
    # Use central finite differences: (F[i+1] - F[i-1]) / (2*dx)

    # Avoid division by zero
    h_safe = np.where(h > 1e-12, h, 1e-12)
    u = hu / h_safe

    # Fluxes
    F1 = hu                          # flux for h equation
    F2 = hu * u + g * h**2 / 2.0    # flux for hu equation

    # Central difference: index wrap for periodic BC
    ip1 = np.roll(np.arange(Nx), -1)  # i+1 indices
    im1 = np.roll(np.arange(Nx), 1)   # i-1 indices

    dF1_dx = (F1[ip1] - F1[im1]) / (2.0 * dx)
    dF2_dx = (F2[ip1] - F2[im1]) / (2.0 * dx)

    # Forward Euler update
    h_new  = h  - dt * dF1_dx
    hu_new = hu - dt * dF2_dx

    h  = h_new
    hu = hu_new
    t += dt

    # If blow-up occurs, stop early
    if np.any(np.isnan(h)) or np.any(np.isnan(hu)) or np.max(np.abs(hu)) > 1e10:
        break

# Save results
import os
os.makedirs("pred_results", exist_ok=True)
result = np.stack([h, hu], axis=0)  # shape (2, 200)
np.save("pred_results/sw_A7.npy", result)
