"""
Reference solver for BKdV-T2: KdV single soliton propagation.

PDE: v_t + 6 v v_x + v_xxx = 0 on x in [-15, 15] periodic, Nx=256
IC : v_0(x) = 2 sech^2(x + 5)   (soliton amplitude 2, speed c=4)
T  : 2.0  (soliton should be at x = -5 + 4*2 = +3)

Method: Fourier spectral in space + IMEX (Crank-Nicolson for linear dispersion,
explicit Euler for nonlinear advection). Robust + fast.
"""
import numpy as np
import os

os.makedirs("ref_results", exist_ok=True)

L = 30.0   # x in [-15, 15]
Nx = 256
dx = L / Nx
x = -15 + dx * np.arange(Nx)   # cell-centered grid would be x_j = -15 + (j+0.5)*dx,
                                # but for spectral we use grid-point form
# wavenumbers k = 2*pi*n/L for n = 0, 1, ..., Nx/2, -Nx/2+1, ..., -1
k = 2*np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k

v = 2 * (1.0 / np.cosh(x + 5))**2

T = 2.0
dt = 0.0005  # small enough for stability
nsteps = int(np.round(T / dt))
print(f"running {nsteps} steps of dt={dt}")

# linear operator: -v_xxx in Fourier domain = -(ik)^3 v_hat = -(-i k^3) v_hat = (i k^3) v_hat
# so v_t = L v + N(v) where L (mult by ik^3) is linear, N(v) = -6 v v_x is nonlinear.
# IMEX: (I - dt/2 L) v^{n+1} = (I + dt/2 L) v^n + dt * N(v^n)
# In Fourier: (1 - dt/2 * ik^3) v_hat^{n+1} = (1 + dt/2 * ik^3) v_hat^n + dt * Nhat^n
# (Crank-Nicolson on linear part; explicit on nonlinear)

L_op = 1j * k**3  # so v_t_linear = L_op * v_hat

denom_implicit = 1 - 0.5 * dt * L_op
num_implicit = 1 + 0.5 * dt * L_op

t = 0.0
for step in range(nsteps):
    v_hat = np.fft.fft(v)
    # nonlinear: -6 v v_x = -3 (v^2)_x
    v_sq = v**2
    Nhat = -3.0 * ik * np.fft.fft(v_sq)
    v_hat_new = (num_implicit * v_hat + dt * Nhat) / denom_implicit
    v = np.real(np.fft.ifft(v_hat_new))
    t += dt
    if (step+1) % 1000 == 0:
        peak_x = x[np.argmax(v)]
        peak_a = v.max()
        mass = v.sum() * dx
        print(f"  step {step+1}, t={t:.3f}, peak at x={peak_x:.3f}, amplitude={peak_a:.4f}, mass={mass:.4f}")

print(f"REF done. final peak x={x[np.argmax(v)]:.4f}, amplitude={v.max():.4f}")
np.save("ref_results/kdv_T2_REF.npy", v)
np.save("ref_results/kdv_T2_REF_x.npy", x)
