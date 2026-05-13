"""
KdV single-soliton propagation using IMEX-spectral (Fourier + Crank-Nicolson on dispersion).
Method: in Fourier domain,
  (1 - dt/2 * ik^3) v_hat^{n+1} = (1 + dt/2 * ik^3) v_hat^n + dt * N_hat^n
where N_hat^n = -3 ik * FFT(v^2)  (nonlinear term in conservation form)
"""

import numpy as np
import os

# Grid
Nx = 256
L = 30.0
dx = L / Nx
x = -15.0 + np.arange(Nx) * dx

# Initial condition: single soliton
v = 2.0 * (1.0 / np.cosh(x + 5.0))**2

# Wavenumbers for periodic domain of length L=30
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2.0 * np.pi / L)

# Time parameters
T = 2.0
dt = 0.0005
Nt = int(round(T / dt))
dt = T / Nt  # ensure exact final time

# Precompute IMEX factors
ik3 = 1j * k**3
denom = 1.0 - (dt / 2.0) * ik3   # left-hand side factor
numer_lin = 1.0 + (dt / 2.0) * ik3  # right-hand side linear factor

# Time integration
v_hat = np.fft.fft(v)

for _ in range(Nt):
    # Nonlinear term: -6 v v_x = -3 (v^2)_x  in conservation form
    # N_hat = -3 * ik * FFT(v^2)
    v_phys = np.fft.ifft(v_hat).real
    v2_hat = np.fft.fft(v_phys**2)
    N_hat = -3.0 * 1j * k * v2_hat

    # IMEX Crank-Nicolson step
    v_hat = (numer_lin * v_hat + dt * N_hat) / denom

# Final solution
v_final = np.fft.ifft(v_hat).real

# Save
out_dir = os.path.join(os.path.dirname(__file__), "pred_results")
os.makedirs(out_dir, exist_ok=True)
np.save(os.path.join(out_dir, "kdv_T2.npy"), v_final)
