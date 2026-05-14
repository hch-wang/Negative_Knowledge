"""
E2: single-component upgrade over E1 - ADD 2/3-rule dealiasing.
Keep: Fourier pseudospectral, classical RK4, dt=1e-4, Nx=256.
Change: zero modes with |k_idx| > Nx/3 (= 85) on every nonlinear product
        (v^2, u*v, u*u_x, v*v_x). This is exactly the BKdV-S1 deep-synthesis stack.

PDE:
  u_t + 3 u u_x = - d/dx (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = - d/dx (u v)

IC: v0 = 4*exp(-(x+5)^2/2.25), u0 = 0
Domain: x in [-15, 15], Nx = 256, T = 6.0
"""

import numpy as np
import os
import time

# --- Grid ---
Nx = 256
L = 30.0
x = -15.0 + L * np.arange(Nx) / Nx     # x in [-15, 15)
dx = L / Nx

# Fourier wavenumbers for periodic domain length L
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)  # rad/length
ik = 1j * k
ik3 = 1j * k**3

# 2/3-rule dealiasing mask: zero |k_idx|>Nx/3
k_idx = np.fft.fftfreq(Nx, d=1.0/Nx)        # integer indices in (-Nx/2, Nx/2]
cutoff = Nx // 3                             # = 85 for Nx=256
mask = (np.abs(k_idx) <= cutoff).astype(np.float64)

def dealias(arr_phys):
    """FFT -> mask -> iFFT to project a physical-space array onto the resolved band."""
    h = np.fft.fft(arr_phys)
    h = h * mask
    return np.real(np.fft.ifft(h))

# --- IC ---
v = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u = np.zeros_like(x)
# Project IC onto resolved band to be consistent with the scheme
v = dealias(v)
u = dealias(u)

# --- Time params ---
T = 6.0
dt = 1.0e-4
n_steps = int(round(T / dt))
dt = T / n_steps

n_snapshots = 13
snap_steps = np.linspace(0, n_steps, n_snapshots).astype(int)

snaps = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)
snaps[0, 0, :] = u
snaps[0, 1, :] = v
snap_ptr = 1


def rhs(u, v):
    """Compute (du/dt, dv/dt) using spectral derivatives + 2/3-rule dealiasing on nonlinear products."""
    vh = np.fft.fft(v)
    uh = np.fft.fft(u)

    # Linear spectral derivatives (no dealiasing needed for linear ops; mask is applied on products)
    v_x = np.real(np.fft.ifft(ik * vh))
    v_xx = np.real(np.fft.ifft(-(k * k) * vh))
    v_xxx = np.real(np.fft.ifft(ik3 * vh))
    u_x = np.real(np.fft.ifft(ik * uh))

    # Nonlinear products, each dealiased
    v2 = dealias(v * v)                 # quadratic in v
    uv = dealias(u * v)                 # bilinear
    u_ux = dealias(u * u_x)             # u u_x
    v_vx = dealias(v * v_x)             # v v_x

    # Derivative of dealiased products
    v2_x = np.real(np.fft.ifft(ik * np.fft.fft(v2)))
    uv_x = np.real(np.fft.ifft(ik * np.fft.fft(uv)))
    v_xx_x = v_xxx                        # = d/dx(v_xx); already spectrally correct

    # u eqn: u_t = -3 u u_x - 3 v2_x - v_xxx
    rhs_u = -3.0 * u_ux - 3.0 * v2_x - v_xx_x

    # v eqn: v_t = -6 v v_x - v_xxx - (u v)_x
    rhs_v = -6.0 * v_vx - v_xxx - uv_x

    return rhs_u, rhs_v


def step_rk4(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new


t0 = time.time()
mass_v0 = float(np.sum(v) * dx)
print(f"[E2] start: mass_v0={mass_v0:.6e}, sup_v0={np.max(np.abs(v)):.6e}, sup_u0={np.max(np.abs(u)):.6e}")
print(f"[E2] dealias cutoff |k_idx|<={cutoff} (Nx/3={Nx//3})")

abort = False
for step in range(1, n_steps + 1):
    u, v = step_rk4(u, v, dt)

    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        print(f"[E2] NaN/Inf at step {step} (t={step*dt:.4f})")
        for j in range(snap_ptr, n_snapshots):
            snaps[j, 0, :] = np.nan
            snaps[j, 1, :] = np.nan
        abort = True
        break

    if snap_ptr < n_snapshots and step == snap_steps[snap_ptr]:
        snaps[snap_ptr, 0, :] = u
        snaps[snap_ptr, 1, :] = v
        if snap_ptr % 2 == 0 or snap_ptr == n_snapshots - 1:
            mass_v = float(np.sum(v) * dx)
            sup_v = float(np.max(np.abs(v)))
            sup_u = float(np.max(np.abs(u)))
            print(f"[E2] t={step*dt:.3f}: sup_u={sup_u:.4e}, sup_v={sup_v:.4e}, mass_v={mass_v:.6e}, drift={(mass_v-mass_v0)/mass_v0:+.3e}")
        snap_ptr += 1

elapsed = time.time() - t0
print(f"[E2] done: elapsed={elapsed:.2f}s, n_steps={n_steps}, dt={dt:.3e}, abort={abort}")

# Final diagnostics
mass_v_final = float(np.sum(snaps[-1, 1, :]) * dx)
print(f"[E2] mass drift final: {(mass_v_final - mass_v0) / mass_v0 * 100:+.4f}%")
print(f"[E2] final sup_v = {np.max(np.abs(snaps[-1,1,:])):.4e}")
print(f"[E2] final sup_u = {np.max(np.abs(snaps[-1,0,:])):.4e}")

# Crude peak count on final v (positive peaks above threshold 0.8 separated by >= 1.0 in x)
v_final = snaps[-1, 1, :]
if np.all(np.isfinite(v_final)):
    # local maxima
    is_pk = (v_final[1:-1] > v_final[:-2]) & (v_final[1:-1] > v_final[2:]) & (v_final[1:-1] > 0.8)
    pk_idx = np.where(is_pk)[0] + 1
    pk_x = x[pk_idx]
    pk_v = v_final[pk_idx]
    print(f"[E2] final peak count (>0.8): {len(pk_idx)}; locations={pk_x.tolist()}; amps={[float(p) for p in pk_v]}")

# --- Save ---
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_B.npy")
np.save(out_path, snaps)
print(f"[E2] saved -> {out_path}, shape={snaps.shape}")
