"""
Stress test G4: Gardner equation with large-amplitude KdV-style IC
Method: IMEX-CN spectral (Crank-Nicolson for linear dispersive term, explicit for nonlinear)
PDE: v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0
IC: v_0(x) = 3.0 * sech^2(x + 5)
Domain: x in [-15, 15], periodic, Nx=256, T=2.0
"""

import numpy as np
import os

# Grid
L = 30.0  # domain length [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for spectral differentiation
k = 2 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)

# Initial condition: KdV-amplitude sech^2, NOT a Gardner soliton
v = 3.0 / np.cosh(x + 5) ** 2

# Time stepping parameters
T = 2.0
# Choose dt for stability; dispersive CFL roughly dt ~ dx^3 / (6*pi^3)
# Use a conservative dt
dt = 1e-4
Nt = int(np.ceil(T / dt))
dt = T / Nt

# Precompute spectral operators
ik = 1j * k
ik3 = 1j * k ** 3  # for v_xxx

# IMEX-CN: treat v_xxx implicitly (linear), nonlinear terms explicitly
# Crank-Nicolson for v_xxx:
#   (I + dt/2 * d^3/dx^3) v^{n+1} = (I - dt/2 * d^3/dx^3) v^n - dt * N(v^n)
# where N(v) = 6 v v_x + (3/2) v^2 v_x  (nonlinear flux)
# In Fourier space:
#   (1 + dt/2 * ik^3) vhat^{n+1} = (1 - dt/2 * ik^3) vhat^n - dt * Nhat^n

# Precompute implicit operators
lhs_coeff = 1.0 + 0.5 * dt * ik3   # denominator in Fourier space
rhs_lin = 1.0 - 0.5 * dt * ik3    # explicit part of linear term


def nonlinear_hat(v_phys):
    """Compute FFT of nonlinear terms: 6 v v_x + (3/2) v^2 v_x"""
    vhat = np.fft.fft(v_phys)
    vx = np.real(np.fft.ifft(ik * vhat))
    N = 6.0 * v_phys * vx + 1.5 * v_phys ** 2 * vx
    return np.fft.fft(N)


# Time integration
vhat = np.fft.fft(v)

for n in range(Nt):
    v_phys = np.real(np.fft.ifft(vhat))
    Nhat = nonlinear_hat(v_phys)
    vhat = (rhs_lin * vhat - dt * Nhat) / lhs_coeff

# Final solution
v_final = np.real(np.fft.ifft(vhat))

# Save result
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/gardner_G4.npy", v_final.astype(np.float64))
print("Saved pred_results/gardner_G4.npy, shape:", v_final.shape)
