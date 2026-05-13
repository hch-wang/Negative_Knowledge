"""Reference for Shallow Water dam-break.

System (with g=1):
  h_t + (hu)_x = 0
  (hu)_t + (hu^2 + g h^2 / 2)_x = 0

Domain x in [-1, 1] periodic-like (we treat extrapolation BCs); Nx=200.
IC dam-break: h_L=2, h_R=1, u=0 everywhere.
T = 0.4 (rarefaction left, shock right).

Method: HLL Riemann flux, Euler time step at CFL=0.4.
"""
import numpy as np, os

os.makedirs("ref_results", exist_ok=True)
G = 1.0
Nx = 200; L = 2.0; dx = L/Nx
x = -1 + dx*0.5 + dx*np.arange(Nx)

# IC
h = np.where(x < 0, 2.0, 1.0).astype(float)
hu = np.zeros_like(h)

def flux(h, hu):
    u = hu / np.maximum(h, 1e-12)
    f1 = hu
    f2 = hu*u + 0.5*G*h*h
    return f1, f2

def hll_flux(hL, huL, hR, huR):
    """HLL Riemann flux at one interface."""
    uL = huL / max(hL, 1e-12); uR = huR / max(hR, 1e-12)
    cL = np.sqrt(G*max(hL,0)); cR = np.sqrt(G*max(hR,0))
    SL = min(uL - cL, uR - cR)
    SR = max(uL + cL, uR + cR)
    f1L = huL; f2L = huL*uL + 0.5*G*hL*hL
    f1R = huR; f2R = huR*uR + 0.5*G*hR*hR
    if SL >= 0: return f1L, f2L
    if SR <= 0: return f1R, f2R
    f1 = (SR*f1L - SL*f1R + SL*SR*(hR - hL)) / (SR - SL)
    f2 = (SR*f2L - SL*f2R + SL*SR*(huR - huL)) / (SR - SL)
    return f1, f2

t = 0; T = 0.4; step = 0
while t < T:
    u = hu/np.maximum(h, 1e-12)
    c = np.sqrt(G*np.maximum(h, 0))
    a_max = np.max(np.abs(u) + c)
    dt = 0.4*dx/a_max
    if t + dt > T: dt = T - t
    F1 = np.zeros(Nx+1); F2 = np.zeros(Nx+1)
    for i in range(Nx+1):
        # interface i+1/2 between cells i-1 and i (with periodic wrap)
        iL = (i-1) % Nx; iR = i % Nx
        f1, f2 = hll_flux(h[iL], hu[iL], h[iR], hu[iR])
        F1[i] = f1; F2[i] = f2
    h  -= (dt/dx)*(F1[1:] - F1[:-1])
    hu -= (dt/dx)*(F2[1:] - F2[:-1])
    t += dt; step += 1
    if step % 100 == 0:
        print(f"  step {step}, t={t:.3f}, h: min={h.min():.3f} max={h.max():.3f}")

print(f"REF done step={step} h: min={h.min():.4f} max={h.max():.4f} mass={(h*dx).sum():.4f}")
np.save("ref_results/sw_T04_REF.npy", np.stack([h, hu], axis=0))
np.save("ref_results/sw_T04_REF_x.npy", x)
