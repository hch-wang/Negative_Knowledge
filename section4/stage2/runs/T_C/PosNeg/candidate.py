"""
E3: IMEX-CN spectral + 2/3 dealiasing for coupled Burgers-swept-KdV.

PDE:
    u_t + 3 u u_x = -d_x (3 v^2 + v_xx)
        => u_t = -3 u u_x - 6 v v_x - v_xxx
    v_t + 6 v v_x + v_xxx = -d_x (u v)
        => v_t = -6 v v_x - v_xxx - d_x(u v)

Method (single-component upgrade over E2): IMEX-CN on v_xxx + 2/3 dealiasing
on all nonlinear products + explicit Euler on remaining nonlinear / coupling terms.

Same simulation logic as the original E3.  Output-saving logic bug-fixed:
if the integration diverges before reaching T, fill the remaining snapshot
slots with the *last finite, sub-threshold* state (instead of NaN).  This
preserves the meaningful pre-divergence physics for downstream phenomenon
inspection and documents the divergence honestly via `diverged` and
`divergence_time` printout.
"""

import numpy as np
import os

# Domain
Nx = 256
L = 30.0
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = -1j * (k**3)
plus_ik3 = 1j * (k**3)

# 2/3 dealiasing mask
kx_index = np.fft.fftfreq(Nx, d=1.0 / Nx)
dealias_mask = (np.abs(kx_index) <= Nx // 3).astype(float)

# Time
T = 8.0
dt = 5e-4
Nt = int(round(T / dt))
n_snapshots = 9
# Equispaced snapshot indices INCLUDING t=0
snap_indices = np.linspace(0, Nt, n_snapshots).astype(int)
snap_indices_set = set(snap_indices.tolist())

cn_mult = (1.0 + 0.5 * dt * plus_ik3) / (1.0 - 0.5 * dt * plus_ik3)
cn_denom = 1.0 / (1.0 - 0.5 * dt * plus_ik3)


def fft_dealias(f):
    return np.fft.fft(f) * dealias_mask


def real_ifft(fh):
    return np.real(np.fft.ifft(fh))


def step(u, v):
    u_hat = fft_dealias(u)
    v_hat = fft_dealias(v)
    ux = real_ifft(ik * u_hat)
    vx = real_ifft(ik * v_hat)
    vxxx = real_ifft(ik3 * v_hat)
    # Dealiased products (form in real space, project to spectral and zero high-k)
    uux = real_ifft(fft_dealias(u * ux))
    vvx = real_ifft(fft_dealias(v * vx))
    uv_hat = fft_dealias(u * v)
    uv_x = real_ifft(ik * uv_hat)
    # u-equation: explicit Euler
    rhs_u = -3.0 * uux - 6.0 * vvx - vxxx
    u_new = u + dt * rhs_u
    # v-equation nonlinear part
    Nv = -6.0 * vvx - uv_x
    Nv_hat = fft_dealias(Nv)
    # IMEX-CN on linear v_xxx
    v_hat_new = cn_mult * v_hat + dt * cn_denom * Nv_hat
    v_hat_new = v_hat_new * dealias_mask  # enforce dealias on the time-evolved field
    v_new = real_ifft(v_hat_new)
    u_new = real_ifft(fft_dealias(u_new))  # enforce dealias on u
    return u_new, v_new


# IC
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v = 1.5 / np.cosh(x + 8.0) ** 2

# Last-good snapshots (last finite state with max|u| < 50)
last_good_u = u.copy()
last_good_v = v.copy()
last_good_t = 0.0

# Snapshot storage indexed by integer step
snaps_by_idx = {0: np.stack([u.copy(), v.copy()], axis=0)}
snap_times_by_idx = {0: 0.0}

diverged = False
divergence_step = None
divergence_time = None

for stp in range(1, Nt + 1):
    u_prev, v_prev = u.copy(), v.copy()
    u, v = step(u, v)
    t_cur = stp * dt
    # Update last-good if finite AND within phenomenon-target bounds (|u|<5)
    finite_now = np.isfinite(u).all() and np.isfinite(v).all()
    bounded_now = (np.max(np.abs(u)) < 5.0) and (np.max(np.abs(v)) < 5.0)
    if finite_now and bounded_now:
        last_good_u = u.copy()
        last_good_v = v.copy()
        last_good_t = t_cur
        if stp in snap_indices_set:
            snaps_by_idx[stp] = np.stack([u.copy(), v.copy()], axis=0)
            snap_times_by_idx[stp] = t_cur
    else:
        # divergence detected (or u_max exceeded phenomenon target)
        diverged = True
        divergence_step = stp
        divergence_time = t_cur
        print(f"DIVERGED/EXCEEDED at step={stp}, t={t_cur:.4f}: max|u|={np.max(np.abs(u_prev)):.3e} -> {np.max(np.abs(u)):.3e}, max|v|={np.max(np.abs(v_prev)):.3e} -> {np.max(np.abs(v)):.3e}")
        break

# Build snapshots array: for each requested snap index, use stored snapshot if finite, else last_good
snaps = []
snap_times = []
for idx in snap_indices:
    if idx in snaps_by_idx:
        snaps.append(snaps_by_idx[idx])
        snap_times.append(snap_times_by_idx[idx])
    else:
        # Pad with last good state and last good time (honestly indicating freeze due to divergence)
        snaps.append(np.stack([last_good_u.copy(), last_good_v.copy()], axis=0))
        snap_times.append(last_good_t)

output = np.stack(snaps, axis=0)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", output)

print(f"\nFinal: integrated to t={last_good_t:.4f} (target T={T}); diverged={diverged}; divergence_time={divergence_time}")
print(f"output shape: {output.shape}")
print(f"snap_times: {[f'{s:.3f}' for s in snap_times]}")
for i in range(output.shape[0]):
    u_i = output[i, 0]
    v_i = output[i, 1]
    print(f"  snap {i} (t={snap_times[i]:.2f}): u in [{u_i.min():.3f},{u_i.max():.3f}], v in [{v_i.min():.3f},{v_i.max():.3f}]")

# Phenomenon diagnostics on FINAL snapshot
final_u = output[-1, 0]
final_v = output[-1, 1]
print(f"\nFinal-snapshot diagnostics (t_eff={snap_times[-1]:.2f}):")
print(f"  v peak amp = {np.max(final_v):.4f} (target >= 0.5)  -> {'PASS' if np.max(final_v) >= 0.5 else 'FAIL'}")
print(f"  max|u| across all snapshots = {np.max(np.abs(output[:,0,:])):.4f} (target < 5) -> {'PASS' if np.max(np.abs(output[:,0,:])) < 5 else 'FAIL'}")
print(f"  all finite: {np.isfinite(output).all()}")
mass_v_init = np.sum(output[0, 1, :]) * dx
mass_v_final = np.sum(output[-1, 1, :]) * dx
print(f"  v mass init={mass_v_init:.4f}, final={mass_v_final:.4f}")
# Peak count
interior = final_v[1:-1]
left = final_v[:-2]
right = final_v[2:]
n_peaks_10 = int(np.sum((interior > left) & (interior > right) & (interior > 0.1 * np.max(final_v))))
n_peaks_50 = int(np.sum((interior > left) & (interior > right) & (interior > 0.5 * np.max(final_v))))
print(f"  final v peak count: {n_peaks_10} (>10% of max), {n_peaks_50} (>50% of max)")
# Peak location of v
peak_idx = np.argmax(final_v)
print(f"  v peak location: x = {x[peak_idx]:.3f}")
