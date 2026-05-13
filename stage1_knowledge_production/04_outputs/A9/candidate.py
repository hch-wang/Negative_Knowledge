import numpy as np
import os

# Shallow water equations with dry-bed IC (stress test A9)
# h_t + (hu)_x = 0
# (hu)_t + (hu^2 + g*h^2/2)_x = 0
# g=1, x in [-1,1] periodic, Nx=200, T=0.3

g = 1.0
Nx = 200
x = np.linspace(-1, 1, Nx, endpoint=False)
dx = 2.0 / Nx
T = 0.3

# Initial condition: dry-bed dam-break
h = np.where(x < 0, 1.0, 0.0)
u = np.zeros(Nx)
hu = h * u

def hll_flux(hL, huL, hR, huR, g):
    """HLL flux for shallow water equations."""
    eps = 1e-10
    # velocities
    uL = huL / (hL + eps) if hL > eps else 0.0
    uR = huR / (hR + eps) if hR > eps else 0.0
    # wave speeds (Einfeldt estimates)
    aL = np.sqrt(g * (hL + eps))
    aR = np.sqrt(g * (hR + eps))
    sL = min(uL - aL, uR - aR)
    sR = max(uL + aL, uR + aR)

    # physical fluxes
    fh_L = huL
    fhu_L = huL * uL + 0.5 * g * hL**2
    fh_R = huR
    fhu_R = huR * uR + 0.5 * g * hR**2

    if sL >= 0:
        return fh_L, fhu_L
    elif sR <= 0:
        return fh_R, fhu_R
    else:
        fh = (sR * fh_L - sL * fh_R + sL * sR * (hR - hL)) / (sR - sL)
        fhu = (sR * fhu_L - sL * fhu_R + sL * sR * (huR - huL)) / (sR - sL)
        return fh, fhu

def hll_flux_arrays(h, hu, g):
    """Compute HLL fluxes at all interfaces (periodic BC)."""
    N = len(h)
    eps = 1e-10
    u_arr = hu / (h + eps)
    u_arr[h < eps] = 0.0

    Fh = np.zeros(N)
    Fhu = np.zeros(N)

    for i in range(N):
        ip1 = (i + 1) % N
        hL, huL = h[i], hu[i]
        hR, huR = h[ip1], hu[ip1]
        fh, fhu = hll_flux(hL, huL, hR, huR, g)
        Fh[i] = fh
        Fhu[i] = fhu

    return Fh, Fhu

t = 0.0
while t < T:
    # CFL condition
    eps = 1e-10
    u_arr = hu / (h + eps)
    u_arr[h < eps] = 0.0
    a_arr = np.sqrt(g * np.maximum(h, 0.0))
    max_speed = np.max(np.abs(u_arr) + a_arr)
    if max_speed < eps:
        dt = 1e-4
    else:
        dt = 0.45 * dx / max_speed

    dt = min(dt, T - t)

    Fh, Fhu = hll_flux_arrays(h, hu, g)

    # Conservative update
    h_new = h - (dt / dx) * (Fh - np.roll(Fh, 1))
    hu_new = hu - (dt / dx) * (Fhu - np.roll(Fhu, 1))

    # Positivity fix: clip h to non-negative
    h_new = np.maximum(h_new, 0.0)
    # Where h is dry, set momentum to zero
    hu_new[h_new < eps] = 0.0

    h = h_new
    hu = hu_new
    t += dt

# Save result
out = np.stack([h, hu], axis=0)  # shape (2, 200)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/sw_A9.npy", out)
print("Saved pred_results/sw_A9.npy with shape", out.shape)
