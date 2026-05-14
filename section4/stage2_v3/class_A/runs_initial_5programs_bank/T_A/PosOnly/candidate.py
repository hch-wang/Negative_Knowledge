"""
E3: E2 (Fourier pseudospectral + 2/3 dealiasing + RK4) PLUS spectral hyperviscosity on u-eqn only.
Single new component vs E2: -nu_h * (k^2)^p damping applied ONLY to u (p=4), to control
Burgers steepening in u observed at sup_u ~ 20 by T=8 in E2 (violates |u|<15 phenomenon bound).
v-eqn discretization unchanged so dispersive soliton phase is unaffected.

Coupled Burgers-swept-KdV:
  u_t + 3 u u_x = -d_x (3 v^2 + v_xx)  - nu_h * (-Delta)^p u
  v_t + 6 v v_x + v_xxx = -d_x (u v)
on x in [-15, 15], Nx=256, periodic.
IC: v0 = 2 sech^2(x+5), u0 = 0.5 v0^2 + 0.2 v0
T = 8.0
Output: pred_results/T_A.npy of shape (n_snap, 2, 256), channels (u,v).
"""
import os
import time
import numpy as np

# Grid
Nx = 256
L = 30.0
xL, xR = -15.0, 15.0
dx = (xR - xL) / Nx
x = xL + dx * np.arange(Nx)
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = 1j * (k ** 3)
mk2 = -(k ** 2)

# 2/3-rule dealiasing
k_idx = np.fft.fftfreq(Nx, d=1.0 / Nx)
DEALIAS = (np.abs(k_idx) <= (Nx // 3)).astype(np.float64)

# Hyperviscosity ONLY on u-equation (single new component vs E2)
P_HYP = 4
# Calibrated so that damping rate at k_cut = 2*pi*(Nx/3)/L is ~5 per unit time
# (decay over T=8 at k_cut is ~exp(-40), effectively zero, while k<=5 is essentially untouched).
NU_H_U = 5.0e-10
HYP_FACTOR_U = -NU_H_U * (k ** 2) ** P_HYP   # negative real; applied to uhat

def fft_dealias(f):
    F = np.fft.fft(f)
    F *= DEALIAS
    return F

def ifft_real(F):
    return np.real(np.fft.ifft(F))

def dx_spec(f):
    return ifft_real(ik * fft_dealias(f))

def dxx_spec(f):
    return ifft_real(mk2 * fft_dealias(f))

def dxxx_spec(f):
    return ifft_real(ik3 * fft_dealias(f))

def dealias_product(a, b):
    return ifft_real(DEALIAS * np.fft.fft(a * b))

def rhs(u, v):
    # v_eqn unchanged from E2
    v_x   = dx_spec(v)
    v_xxx = dxxx_spec(v)
    uv     = dealias_product(u, v)
    uv_x   = dx_spec(uv)
    v_vx   = dealias_product(v, v_x)
    v_t    = -6.0 * v_vx - v_xxx - uv_x

    # u_eqn: same as E2 plus hyperviscosity
    u_x   = dx_spec(u)
    v_xx  = dxx_spec(v)
    v2    = dealias_product(v, v)
    inner = 3.0 * v2 + v_xx
    rhs_u_x = dx_spec(inner)
    u_ux  = dealias_product(u, u_x)
    # spectral hyperviscosity on u
    uhat  = np.fft.fft(u) * DEALIAS
    hyp_u = ifft_real(HYP_FACTOR_U * uhat)
    u_t   = -3.0 * u_ux - rhs_u_x + hyp_u
    return u_t, v_t

def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u,     v + dt*k3v)
    return (u + dt/6.0*(k1u + 2*k2u + 2*k3u + k4u),
            v + dt/6.0*(k1v + 2*k2v + 2*k3v + k4v))

# IC
v0 = 2.0 / np.cosh(x + 5.0) ** 2
u0 = 0.5 * v0 ** 2 + 0.2 * v0

T_final = 8.0
dt = 1.0e-4
n_steps = int(round(T_final / dt))
n_snap = 9
snap_every = n_steps // (n_snap - 1)

u = u0.copy()
v = v0.copy()

snaps = np.zeros((n_snap, 2, Nx), dtype=np.float64)
snaps[0, 0] = u
snaps[0, 1] = v
snap_idx = 1

mass_v0 = np.sum(v) * dx
mass_u0 = np.sum(u) * dx
t0 = time.time()
diverged = False
last_step = 0
for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    last_step = step
    if step % 1000 == 0:
        sup_u = np.max(np.abs(u))
        sup_v = np.max(np.abs(v))
        if not np.isfinite(sup_u) or not np.isfinite(sup_v) or sup_u > 1e3 or sup_v > 1e3:
            print(f"DIVERGED at step={step}, t={step*dt:.4f}, sup_u={sup_u:.3e}, sup_v={sup_v:.3e}")
            diverged = True
            break
    if snap_idx < n_snap and step % snap_every == 0:
        snaps[snap_idx, 0] = u
        snaps[snap_idx, 1] = v
        snap_idx += 1

elapsed = time.time() - t0

if diverged:
    snaps = snaps[:snap_idx]
else:
    snaps[-1, 0] = u
    snaps[-1, 1] = v

print(f"elapsed={elapsed:.2f}s steps={last_step} snap_idx={snap_idx} n_snap_saved={snaps.shape[0]}")
print(f"final sup_u={np.max(np.abs(snaps[-1,0])):.4e} sup_v={np.max(np.abs(snaps[-1,1])):.4e}")
mass_v_final = np.sum(snaps[-1, 1]) * dx
mass_u_final = np.sum(snaps[-1, 0]) * dx
print(f"mass_v initial={mass_v0:.6e} final={mass_v_final:.6e} drift_frac={(mass_v_final-mass_v0)/mass_v0:.3e}")
print(f"mass_u initial={mass_u0:.6e} final={mass_u_final:.6e} drift_frac={(mass_u_final-mass_u0)/mass_u0:.3e}")
print(f"max amplitude v(T) = {np.max(snaps[-1,1]):.4f} (initial 2.0); min v(T) = {np.min(snaps[-1,1]):.4f}")

for i in range(snaps.shape[0]):
    t_i = i * (T_final / (n_snap - 1))
    print(f"snap[{i}] t~{t_i:.3f}  max_v={np.max(snaps[i,1]):.4f} sup_u={np.max(np.abs(snaps[i,0])):.4f} mass_v={np.sum(snaps[i,1])*dx:.6e}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", snaps)
print(f"saved shape={snaps.shape} to pred_results/T_A.npy")
