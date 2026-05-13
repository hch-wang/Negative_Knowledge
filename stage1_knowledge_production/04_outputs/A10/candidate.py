import numpy as np
import os

# Parameters
g = 1.0
Nx = 200
x = np.linspace(-1, 1, Nx, endpoint=False)
dx = x[1] - x[0]
T = 0.4
CFL = 0.4

# Initial condition: dam-break
h = np.where(x < 0, 2.0, 1.0)
u = np.zeros(Nx)

def conserved_to_flux(h, hu):
    u = np.where(h > 1e-12, hu / h, 0.0)
    F1 = hu
    F2 = hu * u + 0.5 * g * h**2
    return F1, F2

def hll_flux(hL, huL, hR, huR):
    uL = np.where(hL > 1e-12, huL / hL, 0.0)
    uR = np.where(hR > 1e-12, huR / hR, 0.0)
    cL = np.sqrt(g * np.maximum(hL, 0.0))
    cR = np.sqrt(g * np.maximum(hR, 0.0))

    # HLL wave speed estimates
    sL = np.minimum(uL - cL, uR - cR)
    sR = np.maximum(uL + cL, uR + cR)

    F1L, F2L = conserved_to_flux(hL, huL)
    F1R, F2R = conserved_to_flux(hR, huR)

    # HLL flux
    F1 = np.where(
        sL >= 0,
        F1L,
        np.where(
            sR <= 0,
            F1R,
            (sR * F1L - sL * F1R + sL * sR * (hR - hL)) / (sR - sL)
        )
    )
    F2 = np.where(
        sL >= 0,
        F2L,
        np.where(
            sR <= 0,
            F2R,
            (sR * F2L - sL * F2R + sL * sR * (huR - huL)) / (sR - sL)
        )
    )
    return F1, F2

# Time integration
hu = h * u
t = 0.0

while t < T:
    c = np.sqrt(g * np.maximum(h, 0.0))
    u_vel = np.where(h > 1e-12, hu / h, 0.0)
    max_speed = np.max(np.abs(u_vel) + c)
    if max_speed < 1e-12:
        dt = CFL * dx
    else:
        dt = CFL * dx / max_speed
    if t + dt > T:
        dt = T - t

    # Periodic indexing
    ip1 = (np.arange(Nx) + 1) % Nx

    hL = h
    huL = hu
    hR = h[ip1]
    huR = hu[ip1]

    # Interface fluxes (Nx interfaces, interface i is between cell i and i+1)
    F1, F2 = hll_flux(hL, huL, hR, huR)

    # Update: flux from right interface minus flux from left interface
    # Left interface of cell i is interface i-1
    im1 = (np.arange(Nx) - 1) % Nx

    h_new = h - dt / dx * (F1 - F1[im1])
    hu_new = hu - dt / dx * (F2 - F2[im1])

    h = h_new
    hu = hu_new
    t += dt

# Save results
result = np.zeros((2, Nx))
result[0] = h
result[1] = np.where(h > 1e-12, hu / h, 0.0)

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/sw_A10.npy", result)
print("Saved pred_results/sw_A10.npy with shape", result.shape)
