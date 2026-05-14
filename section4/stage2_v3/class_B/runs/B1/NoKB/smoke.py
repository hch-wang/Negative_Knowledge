"""Quick smoke test of solver: T=2 with Gaussian IC."""
import numpy as np
import os
import sys
sys.path.insert(0, "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/NoKB")

# Inline a short version
Nx = 256
L = 30.0
dx = L / Nx
x = -L / 2 + dx * np.arange(Nx)
k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k * k
k3 = ik * k2
kmax = (2.0 / 3.0) * (np.pi / dx)
dealias = (np.abs(k) <= kmax).astype(float)


def to_phys(uhat):
    return np.real(np.fft.ifft(uhat))


def rhs(u, v, nu_u=5e-2):
    uhat = np.fft.fft(u) * dealias
    vhat = np.fft.fft(v) * dealias
    u_d = to_phys(uhat)
    v_d = to_phys(vhat)
    ux = to_phys(ik * uhat)
    uux = u_d * ux
    v2 = v_d * v_d
    v2_x = to_phys(ik * np.fft.fft(v2) * dealias)
    vvx = v_d * to_phys(ik * vhat)
    uv = u_d * v_d
    uv_x = to_phys(ik * np.fft.fft(uv) * dealias)
    vxx = to_phys(-k2 * vhat)
    vxx_x = to_phys(ik * np.fft.fft(vxx) * dealias)
    rhs_u = -3.0 * uux - 3.0 * v2_x - vxx_x + nu_u * to_phys(-k2 * uhat)
    rhs_v = -6.0 * vvx - vxx_x - uv_x
    return rhs_u, rhs_v


def step(u, v, dt, nu):
    k1u, k1v = rhs(u, v, nu)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v, nu)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v, nu)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v, nu)
    return u + (dt / 6) * (k1u + 2 * k2u + 2 * k3u + k4u), v + (dt / 6) * (
        k1v + 2 * k2v + 2 * k3v + k4v
    )


A = 1.5
sig = 1.2
v = A * np.exp(-(x ** 2) / (2 * sig ** 2))
u = 0.5 * v * v
dt = 1e-4
T = 2.0
N = int(T / dt)
for n in range(1, N + 1):
    u, v = step(u, v, dt, 5e-2)
    if n % 2000 == 0:
        m = u - 0.5 * v * v
        vmax = float(np.abs(v).max())
        L2m = float(np.sqrt(dx * np.sum(m * m)))
        print(f"t={n*dt:.3f} vmax={vmax:.4f} L2m={L2m:.4f}")
print("smoke ok")
