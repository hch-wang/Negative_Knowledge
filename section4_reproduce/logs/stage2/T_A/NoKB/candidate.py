"""
T_A: Coupled Burgers-swept-KdV — Experiment 3
PDE:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

E3: single-component upgrade over E2 — add weak exponential spectral filter.
  - Spatial: Fourier pseudospectral + 2/3-rule dealiasing
  - Time: explicit RK4 (unchanged)
  - dt: unchanged
  - NEW: exponential filter applied at end of each step on u, v
"""
import os
import numpy as np

# ------------------ Setup ------------------
L = 30.0
xL, xR = -15.0, 15.0
Nx = 256
x = np.linspace(xL, xR, Nx, endpoint=False)
dx = x[1] - x[0]

# Wavenumbers
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = 1j * (k ** 3)

# 2/3 dealiasing mask
k_max_grid = np.max(np.abs(k))
k_cut = (2.0 / 3.0) * k_max_grid
dealias = (np.abs(k) < k_cut).astype(float)

# Exponential filter (Hou-Li style soft): smoothly damp top ~45% modes
# eta = |k|/k_max_grid in [0,1]; below 0.55, no damping; above, smooth exp decay.
eta = np.abs(k) / k_max_grid
filter_mask = np.ones_like(eta)
alpha = 36.0
p = 18
above = eta > 0.55
filter_mask[above] = np.exp(-alpha * ((eta[above] - 0.55) / 0.45) ** p)
# Apply dealias on top: hard cut above 2/3 stays zero.
filter_mask = filter_mask * dealias

# Initial condition
v0 = 2.0 / np.cosh(x + 5.0) ** 2
u0 = 0.5 * v0 ** 2 + 0.2 * v0

# CFL
k_max = np.max(np.abs(k))
dt_lin = 2.8 / (k_max ** 3)
dt = 0.4 * dt_lin
T_final = 8.0
n_steps = int(np.ceil(T_final / dt))
dt = T_final / n_steps

print(f"Nx={Nx}, dx={dx:.4f}, k_max={k_max:.3f}, k_cut={k_cut:.3f}, dt={dt:.3e}, n_steps={n_steps}")
print(f"Filter min/max: {filter_mask.min():.3e} / {filter_mask.max():.3e}, " +
      f"#modes <1 (filtered): {np.sum(filter_mask < 0.999)}, #zero: {np.sum(filter_mask == 0)}")

# Snapshots
n_snap = 9
snap_times = np.linspace(0.0, T_final, n_snap)
snap_steps = np.round(snap_times / dt).astype(int)
snapshots = np.zeros((n_snap, 2, Nx))
snapshots[0, 0] = u0
snapshots[0, 1] = v0
snap_idx = 1

# ------------------ Helpers ------------------
def dealias_fft(f):
    F = np.fft.fft(f)
    F = F * dealias
    return F

def dx_spec(f):
    return np.real(np.fft.ifft(ik * dealias_fft(f)))

def dxx_spec(f):
    return np.real(np.fft.ifft((ik * ik) * dealias_fft(f)))

def dxxx_spec(f):
    return np.real(np.fft.ifft(ik3 * dealias_fft(f)))

def project(f):
    return np.real(np.fft.ifft(dealias_fft(f)))

def apply_filter(f):
    return np.real(np.fft.ifft(np.fft.fft(f) * filter_mask))

def rhs(u, v):
    u_x = dx_spec(u)
    v_x = dx_spec(v)
    v_xx = dxx_spec(v)
    v_xxx = dxxx_spec(v)
    v2 = project(v * v)
    inner_u = 3.0 * v2 + v_xx
    d_inner_u = dx_spec(inner_u)
    uv = project(u * v)
    d_uv = dx_spec(uv)
    u2 = project(u * u)
    d_u2 = dx_spec(u2)
    d_v2 = dx_spec(v2)
    du = -1.5 * d_u2 - d_inner_u
    dv = -3.0 * d_v2 - v_xxx - d_uv
    return du, dv

# ------------------ Time stepping (RK4 + filter) ------------------
u = u0.copy()
v = v0.copy()
t = 0.0
blew_up = False
for step in range(1, n_steps + 1):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    # Apply spectral filter (smoothing)
    u = apply_filter(u)
    v = apply_filter(v)
    t += dt

    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        print(f"BLEW UP at step {step}, t={t:.4f}")
        blew_up = True
        break

    while snap_idx < n_snap and step >= snap_steps[snap_idx]:
        snapshots[snap_idx, 0] = u
        snapshots[snap_idx, 1] = v
        snap_idx += 1

    if step % max(1, n_steps // 10) == 0:
        umax = np.max(np.abs(u))
        vmax = np.max(np.abs(v))
        print(f"  step={step}/{n_steps} t={t:.3f} |u|max={umax:.4e} |v|max={vmax:.4e}")

while snap_idx < n_snap:
    snapshots[snap_idx, 0] = u
    snapshots[snap_idx, 1] = v
    snap_idx += 1

# ------------------ Save ------------------
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", snapshots)
print(f"\nSaved snapshots shape {snapshots.shape}")
print(f"v(T) max = {np.max(snapshots[-1,1]):.4f}, min = {np.min(snapshots[-1,1]):.4f}")
print(f"u(T) max = {np.max(snapshots[-1,0]):.4f}, min = {np.min(snapshots[-1,0]):.4f}")
mass_v0 = np.sum(v0) * dx
mass_vT = np.sum(snapshots[-1,1]) * dx
print(f"mass(v): t=0: {mass_v0:.4f}, t=T: {mass_vT:.4f}, drift: {(mass_vT - mass_v0)/mass_v0 * 100:.3f}%")

v_final = snapshots[-1, 1]
def count_peaks(arr, prominence=0.5):
    peaks = []
    for i in range(len(arr)):
        L = arr[i-1] if i>0 else arr[-1]
        R = arr[(i+1)%len(arr)]
        if arr[i] > L and arr[i] > R and arr[i] > prominence:
            peaks.append((i, arr[i]))
    return peaks
peaks_05 = count_peaks(v_final, 0.5)
peaks_10 = count_peaks(v_final, 1.0)
print(f"v(T) peaks >0.5: {len(peaks_05)}; peaks >1.0: {len(peaks_10)}")
print(f"v(T) peak amplitude: {v_final.max():.4f}")
print(f"Blew up: {blew_up}")
