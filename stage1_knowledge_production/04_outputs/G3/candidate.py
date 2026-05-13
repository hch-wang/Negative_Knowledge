import numpy as np

# Parameters
L = 30.0          # domain length [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx
dt = 0.001
T = 2.0
Nsteps = int(round(T / dt))

# Wavenumbers for periodic domain [-15, 15]
k = 2 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)

# Initial condition
v = 1.5 / np.cosh(x + 5)**2

# Precompute linear operator in Fourier space: dispersion v_xxx -> (ik)^3 v_hat
# IMEX Crank-Nicolson: treat linear (dispersion) implicitly, nonlinear explicitly
# Linear operator L_hat = -i k^3 (from -v_xxx term in the PDE rearranged)
# PDE: v_t = -6 v v_x - (3/2) v^2 v_x - v_xxx

ik = 1j * k
ik3 = ik**3  # (ik)^3

# CN factors for linear part: (I - dt/2 * L_hat) v_hat^{n+1} = (I + dt/2 * L_hat) v_hat^n + dt * NL_hat
# Linear operator in spectral space: L_hat = -ik^3 (i.e., -v_xxx term)
# So: dv_hat/dt = L_hat * v_hat + NL_hat
# where L_hat = -ik^3, NL_hat = FFT(-6vv_x - (3/2)v^2 v_x)

L_op = -ik3  # spectral linear operator

denom = 1.0 - (dt / 2.0) * L_op  # for implicit side

def nonlinear_rhs(v_phys):
    """Compute nonlinear terms in physical space, return in Fourier space.
    NL = -6 v v_x - (3/2) v^2 v_x
    No dealiasing applied (as required by the stress test).
    """
    v_hat = np.fft.fft(v_phys)
    vx_hat = ik * v_hat
    vx = np.fft.ifft(vx_hat).real
    v2 = v_phys**2
    v2_hat = np.fft.fft(v2)
    v2x_hat = ik * v2_hat
    v2x = np.fft.ifft(v2x_hat).real
    nl_phys = -6.0 * v_phys * vx - 1.5 * v2 * vx
    nl_hat = np.fft.fft(nl_phys)
    return nl_hat

# IMEX CN time integration
v_hat = np.fft.fft(v)

for n in range(Nsteps):
    v_phys = np.fft.ifft(v_hat).real
    NL_n = nonlinear_rhs(v_phys)
    # CN update: (1 - dt/2 * L) v_hat^{n+1} = (1 + dt/2 * L) v_hat^n + dt * NL^n
    rhs = (1.0 + (dt / 2.0) * L_op) * v_hat + dt * NL_n
    v_hat = rhs / denom

v_final = np.fft.ifft(v_hat).real

# Save result
import os
out_dir = "${PROJECT_ROOT}/stage1/sandboxes/G3/pred_results"
np.save(os.path.join(out_dir, "gardner_G3.npy"), v_final)
