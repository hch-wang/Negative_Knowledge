"""
T_B / PosNeg / E1
Coupled Burgers-swept-KdV system:
    u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -d/dx (u v)

IC: v(x,0)=4 exp(-(x+5)^2/2.25), u(x,0)=0; periodic on [-15,15], Nx=256.
T_final=6.0.

E1 baseline (per progressive-complexity rules + BKdV-S1 positive bank):
- Fourier pseudospectral derivatives
- 2/3-rule dealiasing on every nonlinear product
- Classical explicit RK4 (v_xxx kept explicit)
- dt = 1e-4 (cut from BKdV-S1's 2e-4 because amp=4 raises nonlinear-CFL)
"""
import os
import numpy as np

OUT = "pred_results/T_B.npy"
os.makedirs("pred_results", exist_ok=True)

# Domain ----------------------------------------------------------------------
Nx = 256
L = 30.0  # x in [-15, 15]
x = np.linspace(-L / 2, L / 2, Nx, endpoint=False)
dx = L / Nx
# Wavenumbers
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)  # rad/length
ik = 1j * k
ik3 = 1j * (k ** 3)

# 2/3-rule dealiasing mask (zero |k_idx| > Nx/3)
k_idx = np.fft.fftfreq(Nx) * Nx       # integer-ish index, range [-Nx/2, Nx/2-1]
dealias_mask = (np.abs(k_idx) <= (Nx / 3.0))
dealias_mask = dealias_mask.astype(np.float64)


def fft(u):
    return np.fft.fft(u)


def ifft(uh):
    return np.fft.ifft(uh).real


def dealias(uh):
    return uh * dealias_mask


def dx_spec(uh):
    return ik * uh


def dx3_spec(uh):
    return ik3 * uh


# RHS ------------------------------------------------------------------------
def rhs(u, v):
    """
    u_t = -3 u u_x - 6 v v_x - v_xxx                (from -d_x(3 v^2 + v_xx))
        wait — careful: -d/dx (3 v^2 + v_xx) = -6 v v_x - v_xxx, so
    u_t = -3 u u_x - 6 v v_x - v_xxx
    v_t = -6 v v_x - v_xxx - d/dx (u v)
        = -6 v v_x - v_xxx - u_x v - u v_x
    All nonlinear products are dealiased after FFT->mult->FFT^-1.
    """
    uh = fft(u)
    vh = fft(v)

    # derivatives
    u_x = ifft(dealias(dx_spec(uh)))
    v_x = ifft(dealias(dx_spec(vh)))
    v_xxx = ifft(dealias(dx3_spec(vh)))

    # nonlinear products with dealias on the product
    uu_x_h = dealias(fft(u * u_x))
    vv_x_h = dealias(fft(v * v_x))
    uv_h = dealias(fft(u * v))
    uv_x_h = dealias(fft(u * v_x))
    u_x_v_h = dealias(fft(u_x * v))

    # We need -d/dx (u v) for v-equation; computed via spectral derivative of uv
    uv_x_from_prod = ifft(dx_spec(uv_h))  # d/dx (u v)

    # Build RHS arrays
    u_t = -3.0 * ifft(uu_x_h) - 6.0 * ifft(vv_x_h) - v_xxx
    v_t = -6.0 * ifft(vv_x_h) - v_xxx - uv_x_from_prod

    return u_t, v_t


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    un = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    vn = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return un, vn


# IC --------------------------------------------------------------------------
amp = 4.0
sigma = 1.5
v0 = amp * np.exp(-((x + 5.0) ** 2) / (sigma ** 2))  # width sigma=1.5 means exp(-r^2/sigma^2)
u0 = np.zeros_like(x)

# Quick sanity print
print(f"[INIT] mass_v0={dx*np.sum(v0):.6f}, sup_v0={np.max(np.abs(v0)):.6f}, sup_u0={np.max(np.abs(u0)):.6f}")

# Time integration -----------------------------------------------------------
T_final = 6.0
dt = 1e-4
n_steps = int(round(T_final / dt))
n_snapshots = 13  # 0, T/12, ..., T
snap_every = n_steps // (n_snapshots - 1)
print(f"[CFG] n_steps={n_steps}, snap_every={snap_every}, dt={dt}")

snaps = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)
snaps[0, 0, :] = u0
snaps[0, 1, :] = v0

u, v = u0.copy(), v0.copy()
snap_idx = 1

import time
t0 = time.time()
for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        print(f"[BLOWUP] step={step}, t={step*dt:.4f}")
        # fill remaining snapshots with NaN to keep shape
        for j in range(snap_idx, n_snapshots):
            snaps[j, 0, :] = np.nan
            snaps[j, 1, :] = np.nan
        break
    if step % snap_every == 0 and snap_idx < n_snapshots:
        snaps[snap_idx, 0, :] = u
        snaps[snap_idx, 1, :] = v
        sup_u = float(np.max(np.abs(u)))
        sup_v = float(np.max(np.abs(v)))
        mass_v = float(dx * np.sum(v))
        print(f"[SNAP {snap_idx:02d}] t={step*dt:.4f} sup_u={sup_u:.4f} sup_v={sup_v:.4f} mass_v={mass_v:.6f}")
        snap_idx += 1

# Ensure final snapshot is filled (in case snap_every didn't divide cleanly)
if snap_idx < n_snapshots:
    snaps[snap_idx:, 0, :] = u
    snaps[snap_idx:, 1, :] = v

elapsed = time.time() - t0
print(f"[DONE] elapsed={elapsed:.2f}s, final sup_v={np.max(np.abs(snaps[-1, 1])):.4f}, mass_v_final={dx*np.sum(snaps[-1, 1]):.6f}")

np.save(OUT, snaps)
print(f"[SAVE] {OUT} shape={snaps.shape}")
