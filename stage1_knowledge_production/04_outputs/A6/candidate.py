"""
Stress test A6: KdV / very small amplitude IC
Method: IMEX-spectral (pseudo-spectral spatial discretization, integrating factor for dispersive term,
explicit RK4 for nonlinear term)
IC amplitude: 0.1 (forced)
"""

import numpy as np
import os

# Domain
L = 30.0  # x in [-15, 15], period = 30
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for spectral differentiation
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2 * np.pi / L)

# Initial condition: amplitude 0.1 (forced per constraint)
v = 0.1 / np.cosh(x + 5)**2

# Time stepping parameters
T = 2.0
dt = 1e-4  # small dt for stability
Nt = int(T / dt)
dt = T / Nt  # adjust to hit T exactly

# Integrating factor for the linear dispersive term v_xxx
# v_t = -6 v v_x - v_xxx
# In spectral space: dv_hat/dt = -6 * FFT(v * v_x) + (ik)^3 * v_hat  ... wait, sign:
# v_xxx contributes -(ik^3) v_hat (since v_t + v_xxx = 0 for linear part)
# Linear operator: L_k = -(i k)^3 = -i k^3 (note: (ik)^3 = i^3 k^3 = -i k^3)
# Integrating factor: mu = exp(L_k * t) = exp(i k^3 t)

# We use the integrating factor method (exact for linear part):
# Let w_hat = exp(i k^3 t) v_hat
# dw_hat/dt = exp(i k^3 t) * (-6 * FFT(v v_x))

def compute_nonlinear_rhs(v_hat, k):
    """Compute -6 * FFT(v * v_x) in spectral space."""
    v = np.real(np.fft.ifft(v_hat))
    vx_hat = 1j * k * v_hat
    vx = np.real(np.fft.ifft(vx_hat))
    return np.fft.fft(-6.0 * v * vx)

# RK4 integrating factor method
v_hat = np.fft.fft(v)
t = 0.0

for n in range(Nt):
    # Current integrating factor
    IF = np.exp(1j * k**3 * t)
    IF_half = np.exp(1j * k**3 * (t + 0.5*dt))
    IF_full = np.exp(1j * k**3 * (t + dt))

    # w_hat = IF * v_hat
    w_hat = IF * v_hat

    # RK4 stages in w_hat space
    # k1
    k1 = dt * IF * compute_nonlinear_rhs(v_hat, k)

    # k2: advance half step
    w2 = w_hat + 0.5 * k1
    v2_hat = w2 / IF_half
    k2 = dt * IF_half * compute_nonlinear_rhs(v2_hat, k)

    # k3: advance half step with k2
    w3 = w_hat + 0.5 * k2
    v3_hat = w3 / IF_half
    k3 = dt * IF_half * compute_nonlinear_rhs(v3_hat, k)

    # k4: advance full step
    w4 = w_hat + k3
    v4_hat = w4 / IF_full
    k4 = dt * IF_full * compute_nonlinear_rhs(v4_hat, k)

    # Update w_hat
    w_hat_new = w_hat + (k1 + 2*k2 + 2*k3 + k4) / 6.0

    # Convert back to v_hat
    v_hat = w_hat_new / IF_full
    t += dt

v_final = np.real(np.fft.ifft(v_hat))

# Save result
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/kdv_A6.npy", v_final.astype(np.float64))
print(f"Saved kdv_A6.npy, shape={v_final.shape}, max={v_final.max():.6f}, min={v_final.min():.6f}")
