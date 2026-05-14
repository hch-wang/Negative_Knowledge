"""
BKdV-S1 Round 1: simplest stack — Fourier pseudospectral + classical RK4,
NO dealiasing, NO IMEX splitting. Explicit treatment of the entire RHS
(including the stiff v_xxx term).

PDE:
    u_t + 3 u u_x   = -d/dx (3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -d/dx (u v)

Periodic domain x in [-15, 15], Nx = 256, T = 10.
IC: v0 = 1.5 sech^2(x+5), u0 = v0^2 / 2.
"""

import os
import sys
import time
import numpy as np

# ------------------------------------------------------------
# Grid & operators
# ------------------------------------------------------------
L = 30.0
Nx = 256
dx = L / Nx
x = -15.0 + dx * np.arange(Nx)

# Fourier wavenumbers for periodic domain of length L
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k ** 2
k3 = k ** 3

def dx_spec(f):
    """spectral first derivative"""
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def dxx_spec(f):
    return np.real(np.fft.ifft(-k2 * np.fft.fft(f)))

def dxxx_spec(f):
    return np.real(np.fft.ifft(-1j * k3 * np.fft.fft(f)))

# ------------------------------------------------------------
# RHS of the BKdV system  (everything explicit, no dealiasing)
# ------------------------------------------------------------
def rhs(state):
    u, v = state
    # Burgers-side: u_t = -3 u u_x - d/dx (3 v^2 + v_xx)
    u_x = dx_spec(u)
    v2 = v * v
    v_xx = dxx_spec(v)
    rhs_u = -3.0 * u * u_x - dx_spec(3.0 * v2 + v_xx)

    # KdV-side: v_t = -6 v v_x - v_xxx - d/dx(u v)
    v_x = dx_spec(v)
    v_xxx = dxxx_spec(v)
    rhs_v = -6.0 * v * v_x - v_xxx - dx_spec(u * v)
    return np.stack([rhs_u, rhs_v], axis=0)

def step_rk4(state, dt):
    k1 = rhs(state)
    k2_ = rhs(state + 0.5 * dt * k1)
    k3_ = rhs(state + 0.5 * dt * k2_)
    k4_ = rhs(state + dt * k3_)
    return state + (dt / 6.0) * (k1 + 2 * k2_ + 2 * k3_ + k4_)

# ------------------------------------------------------------
# Diagnostics
# ------------------------------------------------------------
def diagnostics(state):
    u, v = state
    mass_v = np.sum(v) * dx
    mass_u = np.sum(u) * dx
    energy = 0.5 * np.sum(u * u + v * v) * dx
    sup = max(np.max(np.abs(u)), np.max(np.abs(v)))
    finite = np.all(np.isfinite(u)) and np.all(np.isfinite(v))
    return dict(mass_u=mass_u, mass_v=mass_v, energy=energy, sup=sup, finite=finite)

# ------------------------------------------------------------
# Initial condition
# ------------------------------------------------------------
amp = 1.5
v0 = amp * (1.0 / np.cosh(x + 5.0)) ** 2
u0 = 0.5 * v0 ** 2
state = np.stack([u0, v0], axis=0)
init = diagnostics(state)
print(f"[init] dx={dx:.4e} amp={amp} mass_v={init['mass_v']:.6e} energy={init['energy']:.6e} sup={init['sup']:.4e}", flush=True)

# ------------------------------------------------------------
# Time integration
# ------------------------------------------------------------
T = 10.0
dt = 2.0e-4     # explicit RK4 must respect v_xxx CFL: dt < O(dx^3); dx ~ 0.117, dx^3 ~ 1.6e-3
nsteps = int(round(T / dt))
print(f"[time] dt={dt:.4e} nsteps={nsteps}", flush=True)

t0 = time.time()
report_every = max(1, nsteps // 20)
blowup_t = None
for n in range(nsteps):
    state = step_rk4(state, dt)
    if (n + 1) % report_every == 0 or n == nsteps - 1:
        d = diagnostics(state)
        t = (n + 1) * dt
        print(f"[t={t:7.4f}] mass_v={d['mass_v']:+.4e} energy={d['energy']:.4e} sup={d['sup']:.4e} finite={d['finite']}", flush=True)
        if not d['finite'] or d['sup'] > 1e6:
            blowup_t = t
            print(f"[BLOWUP] at t={t:.4f}", flush=True)
            break

elapsed = time.time() - t0
final = diagnostics(state)
print(f"[final] t_final={(n+1)*dt:.4f} sup={final['sup']:.4e} mass_v={final['mass_v']:+.4e} energy={final['energy']:.4e} finite={final['finite']} elapsed={elapsed:.2f}s", flush=True)
print(f"[summary] blowup_t={blowup_t} reached_T10={(blowup_t is None and (n+1)*dt >= T - 1e-9)}", flush=True)
