"""
KdV single-soliton propagation solver.
PDE: v_t + 6 v v_x + v_xxx = 0
Uses Fourier spectral space + IMEX time integration:
  - v_xxx handled implicitly (stiff dispersive term) via exact exponential factor
  - 6 v v_x handled explicitly via Fourier differentiation
  - Time stepping: 4th-order Runge-Kutta on the nonlinear part with integrating factor
"""
import numpy as np
import os

# Grid setup
Nx = 256
x_left, x_right = -15.0, 15.0
L = x_right - x_left  # 30
dx = L / Nx
x = x_left + np.arange(Nx) * dx

# Initial condition: soliton of amplitude 2 centered at x=-5
v = 2.0 * (1.0 / np.cosh(x + 5.0))**2

# Wavenumbers for spectral differentiation
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2.0 * np.pi / L)

# The linear part operator in Fourier space: L_hat = -i k^3 (from v_xxx term)
# PDE in Fourier: dV_hat/dt = -i k^3 V_hat - 6 * FFT(v * v_x)
# Integrating factor: W_hat = exp(i k^3 t) * V_hat
# dW_hat/dt = exp(i k^3 t) * (-6 * FFT(v * v_x))

# Time stepping parameters
T_final = 2.0
# Use a moderate dt; stability requires dt << dx^3 for explicit dispersion,
# but with integrating factor the dispersive stiffness is handled exactly.
# Nonlinear term stability: need dt * max|v| / dx ~ O(1)
# max|v| ~ 2, dx ~ 0.117, so dt ~ 0.05 is safe for nonlinear CFL
dt = 0.005
Nt = int(np.ceil(T_final / dt))
dt = T_final / Nt

def nonlinear_rhs_hat(v_hat, t):
    """Compute FFT of -6 * v * v_x, then multiply by integrating factor exp(i k^3 t)."""
    # v in physical space
    v_phys = np.real(np.fft.ifft(v_hat))
    # v_x via spectral differentiation
    vx_hat = 1j * k * v_hat
    vx_phys = np.real(np.fft.ifft(vx_hat))
    # nonlinear term: -6 v v_x
    nl_phys = -6.0 * v_phys * vx_phys
    nl_hat = np.fft.fft(nl_phys)
    # Multiply by integrating factor exp(i k^3 t)
    return nl_hat * np.exp(1j * k**3 * t)

# Transform to integrating-factor variable: W_hat = exp(i k^3 t) * V_hat
v_hat = np.fft.fft(v)
t = 0.0
w_hat = v_hat * np.exp(1j * k**3 * t)  # at t=0, factor is 1

# Classical 4th-order Runge-Kutta on W_hat
for n in range(Nt):
    # RK4 stages
    k1 = nonlinear_rhs_hat(w_hat * np.exp(-1j * k**3 * t), t)
    k2 = nonlinear_rhs_hat((w_hat + 0.5*dt*k1) * np.exp(-1j * k**3 * (t + 0.5*dt)), t + 0.5*dt)
    k3 = nonlinear_rhs_hat((w_hat + 0.5*dt*k2) * np.exp(-1j * k**3 * (t + 0.5*dt)), t + 0.5*dt)
    k4 = nonlinear_rhs_hat((w_hat + dt*k3) * np.exp(-1j * k**3 * (t + dt)), t + dt)

    w_hat = w_hat + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)
    t += dt

# Recover v from integrating factor variable
v_hat_final = w_hat * np.exp(-1j * k**3 * t)
v_final = np.real(np.fft.ifft(v_hat_final))

# Save output
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "kdv_T2.npy")
np.save(out_path, v_final)

print(f"Saved {out_path}")
print(f"Max amplitude: {v_final.max():.4f} (expect ~2.0)")
print(f"Argmax x: {x[np.argmax(v_final)]:.4f} (expect ~3.0)")
print(f"Mass integral: {v_final.sum() * dx:.4f} (expect ~4.0)")
