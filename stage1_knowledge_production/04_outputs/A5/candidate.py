import numpy as np

# Parameters
L = 30.0          # domain length: x in [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx
dt = 0.005
T = 2.0
Nsteps = int(round(T / dt))

# Wavenumbers
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi

# Initial condition
v = 2.0 / np.cosh(x + 5) ** 2

# Precompute linear operator in Fourier space: L(k) = -i k^3
# We use Integrating Factor / IMEX: treat v_xxx implicitly (stiff dispersive term),
# treat 6 v v_x explicitly (nonlinear advection).
#
# Equation: v_t = -v_xxx - 6 v v_x
# In Fourier: dV/dt = -(ik)^3 V - 6 * F{v v_x}
#           = i k^3 V - 6 * F{v * ifft(ik * V)}
#
# IMEX Euler (one step):
#   V^{n+1} = (V^n + dt * N^n) / (1 - dt * i k^3)
# where N^n = -6 * F{v^n * ifft(ik * V^n)}   (nonlinear part, explicit)
#
# NO dealiasing, NO mode truncation, NO low-pass filtering as required.

linear_factor = 1j * k**3           # linear operator coefficient
denom = 1.0 - dt * linear_factor    # denominator for implicit solve

V = np.fft.fft(v)

for _ in range(Nsteps):
    # Nonlinear term: -6 v v_x, fully aliased (no 2/3 rule)
    vx = np.real(np.fft.ifft(1j * k * V))
    v_real = np.real(np.fft.ifft(V))
    N = np.fft.fft(-6.0 * v_real * vx)

    # IMEX Euler step
    V = (V + dt * N) / denom

v_final = np.real(np.fft.ifft(V))

import os
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/kdv_A5.npy", v_final.astype(np.float64))
