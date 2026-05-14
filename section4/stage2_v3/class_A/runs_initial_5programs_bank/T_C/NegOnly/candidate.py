"""
T_C: Burgers bore x KdV soliton interaction.
E3: E2 stack + weak hyperviscosity nu_h*k^16 on both u and v.

PDE:
  u_t + 3 u u_x = -d/dx(3 v^2 + v_xx) - nu_h * k^16 u_FFT
  v_t + 6 v v_x + v_xxx = -d/dx(u v) - nu_h * k^16 v_FFT

Single-component change vs E2: add weak hyperviscosity (matches BKdV-S4 envelope).

IC:
  u(x,0) = 1.5 * (1 - tanh(x/0.5))/2
  v(x,0) = 1.5 * sech^2(x + 8)

Domain: x in [-15, 15], Nx=256, T=8.0
"""
import numpy as np
import os
import warnings

warnings.simplefilter("error", RuntimeWarning)

# -------- Parameters --------
L = 30.0
Nx = 256
T_final = 8.0
dt = 1e-4
n_snapshots = 9
nu_h = 1e-22  # weak hyperviscosity coefficient
hv_power = 16

# -------- Grid + spectral wavenumbers --------
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = 1j * k**3
k2 = k**2

# 2/3-rule dealiasing mask
k_idx_signed = np.fft.fftfreq(Nx, d=1.0 / Nx).astype(int)
dealias = (np.abs(k_idx_signed) <= Nx // 3).astype(float)

# Hyperviscosity multiplier: -nu_h * k^{hv_power}, applied as a linear damping in spectral space
hv_mult = nu_h * (np.abs(k) ** hv_power)

def dealias_field(f):
    F = np.fft.fft(f)
    F *= dealias
    return np.real(np.fft.ifft(F))

def dx_spec(f):
    return np.real(np.fft.ifft(ik * dealias * np.fft.fft(f)))

def dxxx_spec(f):
    return np.real(np.fft.ifft(ik3 * dealias * np.fft.fft(f)))

def hyperdiffuse(f):
    """Returns -nu_h*k^p * f_FFT inverse-transformed (a damping force in real space)."""
    F = np.fft.fft(f)
    return np.real(np.fft.ifft(-hv_mult * F))

def rhs(u, v):
    """
    Coupled BKdV RHS with 2/3-rule dealiasing + weak hyperviscosity.
    """
    u_d = dealias_field(u)
    v_d = dealias_field(v)

    # Burgers u: u_t = -3 u u_x - d/dx(3 v^2) - v_xxx - nu_h * D^16 u
    u_x = dx_spec(u_d)
    v2 = dealias_field(v_d * v_d)
    d_v2_dx = dx_spec(v2)
    d_vxx_dx = dxxx_spec(v_d)
    uu_x = dealias_field(u_d * u_x)
    du = -3.0 * uu_x - 3.0 * d_v2_dx - d_vxx_dx + hyperdiffuse(u)

    # KdV v: v_t = -6 v v_x - v_xxx - d/dx(u v) - nu_h * D^16 v
    v_x = dx_spec(v_d)
    uv = dealias_field(u_d * v_d)
    d_uv_dx = dx_spec(uv)
    v_xxx = dxxx_spec(v_d)
    vv_x = dealias_field(v_d * v_x)
    dv = -6.0 * vv_x - v_xxx - d_uv_dx + hyperdiffuse(v)

    return du, dv

def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new

# -------- Initial conditions --------
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v = 1.5 / np.cosh(x + 8.0) ** 2

# -------- Time integration --------
n_steps = int(round(T_final / dt))
snapshot_steps = np.linspace(0, n_steps, n_snapshots).astype(int)
snapshots = []
snapshot_times = []

snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
snapshot_times.append(0.0)

next_snap_idx = 1
blowup = False

try:
    for step in range(1, n_steps + 1):
        u, v = rk4_step(u, v, dt)
        if next_snap_idx < n_snapshots and step == snapshot_steps[next_snap_idx]:
            snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
            snapshot_times.append(step * dt)
            next_snap_idx += 1
        if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
            print(f"BLOWUP at step {step}, t={step*dt:.4f}")
            blowup = True
            while len(snapshots) < n_snapshots:
                snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
                snapshot_times.append(step * dt)
            break
except RuntimeWarning as e:
    print(f"RuntimeWarning trapped at step {step}: {e}")
    blowup = True
    while len(snapshots) < n_snapshots:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        snapshot_times.append(step * dt)
except Exception as e:
    print(f"Exception trapped at step {step}: {e}")
    blowup = True
    while len(snapshots) < n_snapshots:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        snapshot_times.append(step * dt)

# -------- Save --------
out = np.stack(snapshots, axis=0)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", out)

# -------- Diagnostics --------
u_end, v_end = out[-1, 0], out[-1, 1]
print(f"blowup_flag: {blowup}")
print(f"Out shape: {out.shape}")
print(f"snapshot times: {[f'{t:.3f}' for t in snapshot_times]}")
print(f"Final u: min={np.nanmin(u_end):.4g}, max={np.nanmax(u_end):.4g}, NaN={np.isnan(u_end).sum()}")
print(f"Final v: min={np.nanmin(v_end):.4g}, max={np.nanmax(v_end):.4g}, NaN={np.isnan(v_end).sum()}")
print(f"Final v peak amp: {np.nanmax(np.abs(v_end)):.4g} (target >= 0.5)")
print(f"Final |u_max|: {np.nanmax(np.abs(u_end)):.4g} (target < 5)")
def count_peaks(arr, prom=0.05):
    a = arr
    pk = 0
    for i in range(1, len(a) - 1):
        if a[i] > a[i - 1] and a[i] > a[i + 1] and a[i] > prom * np.nanmax(np.abs(a)):
            pk += 1
    return pk
print(f"Final v peak count (prom 0.05*max): {count_peaks(v_end)}")
print(f"Mass v: {np.nansum(v_end)*dx:.4g}  vs IC {np.sum(1.5/np.cosh(x+8.0)**2)*dx:.4g}")
print(f"Mass u: {np.nansum(u_end)*dx:.4g}  vs IC {np.sum(1.5*(1-np.tanh(x/0.5))/2)*dx:.4g}")
