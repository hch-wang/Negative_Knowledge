"""
G2: Gardner equation IMEX Crank-Nicolson Fourier pseudo-spectral solver
v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0
Implicit: linear dispersive term v_xxx (Crank-Nicolson in Fourier space)
Explicit: nonlinear terms 6 v v_x + (3/2) v^2 v_x
2/3 dealiasing on nonlinear terms
"""

import numpy as np
import os

# --- Domain ---
L = 30.0          # domain length, x in [-15, 15]
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

# --- Wavenumbers ---
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)

# --- 2/3 dealiasing mask ---
k_max = np.max(np.abs(k))
dealias = np.abs(k) <= (2.0 / 3.0) * k_max

# --- Initial condition ---
v = 1.5 / np.cosh(x + 5.0) ** 2

# --- Time stepping ---
T = 2.0
dt = 0.0005
Nsteps = int(np.round(T / dt))

# Pre-compute IMEX Crank-Nicolson factors in Fourier space
# Linear operator L_k = -i k^3  (from v_xxx term)
# CN: (1 - dt/2 * L_k) V^{n+1} = (1 + dt/2 * L_k) V^n + dt * NL^n  (but IMEX alternates)
# More precisely for IMEX-CN:
#   (I - dt/2 * Lhat) vhat^{n+1} = (I + dt/2 * Lhat) vhat^n - dt * NLhat^n
# where Lhat = -ik^3 and NL = 6 v v_x + 1.5 v^2 v_x (explicit, evaluated at time n)
# But standard IMEX-CN uses the nonlinear term extrapolated or evaluated at n.
# Here we use first-order explicit for NL (Adams-Bashforth-1 / forward Euler for NL):
#   (I - dt/2 * Lhat) vhat^{n+1} = (I + dt/2 * Lhat) vhat^n - dt * NLhat^n

Lhat = -1j * k ** 3          # linear Fourier multiplier
denom = 1.0 - 0.5 * dt * Lhat
numer_base = 1.0 + 0.5 * dt * Lhat

def compute_nonlinear(v_phys):
    """Compute NL = 6 v v_x + 1.5 v^2 v_x with 2/3 dealiasing."""
    vhat = np.fft.fft(v_phys)
    # Apply dealiasing to v before computing products
    vhat_d = vhat * dealias
    v_d = np.fft.ifft(vhat_d).real

    # v_x via spectral differentiation (on dealiased v)
    vx_d = np.fft.ifft(1j * k * vhat_d).real

    nl = 6.0 * v_d * vx_d + 1.5 * v_d ** 2 * vx_d
    # Transform NL, dealias again
    nl_hat = np.fft.fft(nl) * dealias
    return nl_hat

# Main time loop
vhat = np.fft.fft(v)

for step in range(Nsteps):
    nl_hat = compute_nonlinear(np.fft.ifft(vhat).real)
    vhat = (numer_base * vhat - dt * nl_hat) / denom

v_final = np.fft.ifft(vhat).real

# --- Save ---
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/gardner_G2.npy", v_final.astype(np.float64))
