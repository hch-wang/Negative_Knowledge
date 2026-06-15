"""
BKdV-S7 Round 2 (E2): full BKdV with matching IC.

PDE system (periodic x in [-15, 15], Nx = 256):
    u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -∂_x (u v)

IC (same as E1 for v, plus u_0 = v_0^2 / 2 so m_0 = u_0 - v_0^2/2 = 0 exactly):
    v(x, 0) = A sech^2(x + 5),  A = 1.5
    u(x, 0) = v(x, 0)^2 / 2

Numerical stack — IDENTICAL to E1 by prompt mandate:
- Fourier pseudospectral spatial derivatives
- 2/3 dealiasing on every nonlinear product
- Explicit RK4 in time, dt = 2e-4

Goal: quantify how BKdV's coupling drives the system off the m = 0 manifold
and how the BKdV v(t) diverges from the Gardner-only solution from E1.

Diagnostics every snapshot:
- mass_u, mass_v (conservation)
- m_norm = ||u - v^2/2||_L2  (drift off the Gardner reduction)
- v_max, v_min, v_max_x
- u_max, u_min, u_max_x
- L2 distance to E1 Gardner solution:  ||v_BKdV(t) - v_Gardner(t)||_L2
- single-peak count for v
- finite, sup

Compares against round1/snapshots.npz at matching snapshot times.
Saves snapshots to round2/snapshots.npz and diagnostics to round2/diag.npz.
"""

import os
import sys
import time
import numpy as np

ROUND_DIR = os.path.dirname(os.path.abspath(__file__))
ROUND1_DIR = os.path.join(os.path.dirname(ROUND_DIR), "round1")

# ------------------------------------------------------------
# Grid & spectral operators (identical to E1)
# ------------------------------------------------------------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
k2 = k ** 2
k3 = k ** 3
ik3 = 1j * k ** 3

k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)


def fft_dealias(a):
    return np.fft.fft(a) * dealias


def dx_spec(f_phys):
    return np.real(np.fft.ifft(ik * fft_dealias(f_phys)))


def dxx_spec(f_phys):
    return np.real(np.fft.ifft(-k2 * fft_dealias(f_phys)))


def dxxx_spec(f_phys):
    return np.real(np.fft.ifft(-ik3 * fft_dealias(f_phys)))


# ------------------------------------------------------------
# BKdV RHS:
#   u_t = -3 u u_x - ∂_x(3 v^2 + v_xx)
#   v_t = -6 v v_x - v_xxx - ∂_x(u v)
# All nonlinear products are dealiased before differentiation.
# ------------------------------------------------------------
def bkdv_rhs(u, v):
    uh_d = fft_dealias(u)
    vh_d = fft_dealias(v)
    u_d = np.real(np.fft.ifft(uh_d))
    v_d = np.real(np.fft.ifft(vh_d))
    v_x = np.real(np.fft.ifft(ik * vh_d))
    v_xx = np.real(np.fft.ifft(-k2 * vh_d))
    v_xxx = np.real(np.fft.ifft(-ik3 * vh_d))
    u_x = np.real(np.fft.ifft(ik * uh_d))

    # ---- u equation ----
    # 3 u u_x is a product, dealias it
    uu_x = 3.0 * u_d * u_x
    # ∂_x(3 v^2 + v_xx): compute 3 v^2, dealias, derive; v_xx is linear, derive.
    v2 = fft_dealias(v_d * v_d)
    v2_phys = np.real(np.fft.ifft(v2))
    inner = 3.0 * v2_phys + v_xx
    d_inner = np.real(np.fft.ifft(ik * fft_dealias(inner)))
    rhs_u = -uu_x - d_inner

    # ---- v equation ----
    vv_x = 6.0 * v_d * v_x
    uv = fft_dealias(u_d * v_d)
    uv_phys = np.real(np.fft.ifft(uv))
    d_uv = np.real(np.fft.ifft(ik * fft_dealias(uv_phys)))
    rhs_v = -vv_x - v_xxx - d_uv

    # final dealias on the RHS as a clean-up pass
    rhs_u = np.real(np.fft.ifft(fft_dealias(rhs_u)))
    rhs_v = np.real(np.fft.ifft(fft_dealias(rhs_v)))
    return rhs_u, rhs_v


def rk4_step(u, v, dt):
    k1u, k1v = bkdv_rhs(u, v)
    k2u, k2v = bkdv_rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = bkdv_rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = bkdv_rhs(u + dt * k3u,        v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return u_new, v_new


# ------------------------------------------------------------
# Diagnostics
# ------------------------------------------------------------
def diagnostics(u, v, v_gardner=None):
    mass_u = float(np.sum(u) * dx)
    mass_v = float(np.sum(v) * dx)
    L2u = float(np.sqrt(np.sum(u * u) * dx))
    L2v = float(np.sqrt(np.sum(v * v) * dx))
    m = u - 0.5 * v ** 2
    m_norm = float(np.sqrt(np.sum(m * m) * dx))
    v_max = float(np.max(v))
    v_min = float(np.min(v))
    v_max_x = float(x[int(np.argmax(v))])
    u_max = float(np.max(u))
    u_min = float(np.min(u))
    u_max_x = float(x[int(np.argmax(u))])
    sup = float(max(np.max(np.abs(u)), np.max(np.abs(v))))
    finite = bool(np.all(np.isfinite(u)) and np.all(np.isfinite(v)))
    # Peak count
    thr = 0.05 * (v_max if v_max > 0 else 1.0)
    left = np.roll(v, 1)
    right = np.roll(v, -1)
    peaks = ((v > left) & (v > right) & (v > thr))
    n_peaks = int(np.sum(peaks))
    out = dict(
        mass_u=mass_u, mass_v=mass_v, L2u=L2u, L2v=L2v,
        m_norm=m_norm,
        v_max=v_max, v_min=v_min, v_max_x=v_max_x,
        u_max=u_max, u_min=u_min, u_max_x=u_max_x,
        n_peaks=n_peaks, sup=sup, finite=finite,
    )
    if v_gardner is not None:
        out['L2_v_diff'] = float(np.sqrt(np.sum((v - v_gardner) ** 2) * dx))
    else:
        out['L2_v_diff'] = float('nan')
    return out


# ------------------------------------------------------------
# Load E1 Gardner snapshots for comparison
# ------------------------------------------------------------
snap1 = np.load(os.path.join(ROUND1_DIR, "snapshots.npz"))
t1 = snap1["times"]
v1 = snap1["v"]
x1 = snap1["x"]
assert np.allclose(x1, x), "grid mismatch with round1"
print(f"[ref] loaded E1 Gardner snapshots: {len(t1)} times "
      f"from t={t1[0]:.4f} to t={t1[-1]:.4f}", flush=True)

# ------------------------------------------------------------
# Initial condition: same v0, u0 = v0^2/2  -> m_0 = 0
# ------------------------------------------------------------
A = 1.5
v = A * (1.0 / np.cosh(x + 5.0)) ** 2
u = 0.5 * v ** 2

# ------------------------------------------------------------
# Time integration
# ------------------------------------------------------------
T = 10.0
dt = 2.0e-4
nsteps = int(round(T / dt))

print(f"[grid]  Nx={Nx}  L={L}  dx={dx:.4e}", flush=True)
print(f"[time]  T={T}  dt={dt:.4e}  nsteps={nsteps}", flush=True)
print(f"[IC]    A={A}  v0 = A sech^2(x+5)  u0 = v0^2/2 (m0=0)", flush=True)

# Snapshot schedule: 21 snapshots matching E1
n_snap = 21
snap_steps = np.linspace(0, nsteps, n_snap, dtype=int)
snap_set = set(int(s) for s in snap_steps)
# Map step number -> Gardner snapshot index (in t1 order)
step_to_snap_idx = {int(s): i for i, s in enumerate(snap_steps)}

snapshots_u = []
snapshots_v = []
snapshot_times = []
diag_log = []

# t = 0 init diagnostic
d0 = diagnostics(u, v, v_gardner=v1[0])
snapshots_u.append(u.copy())
snapshots_v.append(v.copy())
snapshot_times.append(0.0)
diag_log.append({'t': 0.0, **d0})
print(f"[init]  mass_v={d0['mass_v']:+.6e} mass_u={d0['mass_u']:+.6e} "
      f"m_norm={d0['m_norm']:.3e} v_max={d0['v_max']:.4f} u_max={d0['u_max']:.4f} "
      f"L2vdiff={d0['L2_v_diff']:.3e}", flush=True)

t0 = time.time()
report_every = max(1, nsteps // 30)
blowup = False

for n in range(1, nsteps + 1):
    u, v = rk4_step(u, v, dt)
    # safety final dealias
    u = np.real(np.fft.ifft(fft_dealias(u)))
    v = np.real(np.fft.ifft(fft_dealias(v)))
    t = n * dt
    if n in snap_set:
        snapshots_u.append(u.copy())
        snapshots_v.append(v.copy())
        snapshot_times.append(t)
        idx = step_to_snap_idx[n]
        d = diagnostics(u, v, v_gardner=v1[idx])
        diag_log.append({'t': t, **d})
    if n % report_every == 0 or n == nsteps:
        # always compute L2_v_diff against the closest E1 snapshot
        idx = int(np.argmin(np.abs(t1 - t)))
        vref = v1[idx]
        d = diagnostics(u, v, v_gardner=vref)
        print(f"[t={t:7.4f}] mass_v={d['mass_v']:+.4e} m_norm={d['m_norm']:.3e} "
              f"v_max={d['v_max']:.4f}@x={d['v_max_x']:+.3f} "
              f"u_max={d['u_max']:.4f}@x={d['u_max_x']:+.3f} "
              f"L2vdf={d['L2_v_diff']:.3e} sup={d['sup']:.3e}", flush=True)
        if not d['finite'] or d['sup'] > 1e3:
            print(f"[BLOWUP] at t={t:.4f}", flush=True)
            blowup = True
            break

elapsed = time.time() - t0
final_idx = int(np.argmin(np.abs(t1 - (snapshot_times[-1]))))
final = diagnostics(u, v, v_gardner=v1[final_idx])

# Save
out_npz = os.path.join(ROUND_DIR, "snapshots.npz")
np.savez(out_npz,
         x=x,
         times=np.array(snapshot_times),
         u=np.array(snapshots_u),
         v=np.array(snapshots_v))
diag_keys = list(diag_log[0].keys())
diag_arrs = {kk: np.array([d[kk] for d in diag_log], dtype=float)
             for kk in diag_keys}
np.savez(os.path.join(ROUND_DIR, "diag.npz"), **diag_arrs)

print(f"[saved] {out_npz}  ({len(snapshot_times)} snapshots)", flush=True)
print(f"[final] t={snapshot_times[-1]:.4f}  v_max={final['v_max']:.5f}@x={final['v_max_x']:+.3f}  "
      f"u_max={final['u_max']:.5f}@x={final['u_max_x']:+.3f}  "
      f"m_norm={final['m_norm']:.4e}  L2_v_diff={final['L2_v_diff']:.4e}  "
      f"mass_v={final['mass_v']:+.5e} mass_u={final['mass_u']:+.5e}  "
      f"elapsed={elapsed:.1f}s blowup={blowup}", flush=True)

# Summary tables
ts_arr = np.array([d['t'] for d in diag_log])
m_arr  = np.array([d['m_norm'] for d in diag_log])
vmax   = np.array([d['v_max'] for d in diag_log])
umax   = np.array([d['u_max'] for d in diag_log])
mass_v = np.array([d['mass_v'] for d in diag_log])
mass_u = np.array([d['mass_u'] for d in diag_log])
L2_diff= np.array([d['L2_v_diff'] for d in diag_log])
npks   = np.array([d['n_peaks'] for d in diag_log])

print("\n[m_norm(t)]", flush=True)
for tt, mm in zip(ts_arr, m_arr):
    print(f"  t={tt:6.3f}  m_norm={mm:.4e}", flush=True)

print("\n[L2 distance to Gardner: ||v_BKdV - v_Gardner||]", flush=True)
for tt, dd in zip(ts_arr, L2_diff):
    print(f"  t={tt:6.3f}  ||v_BKdV - v_Gardner||_L2 = {dd:.4e}", flush=True)

print("\n[summary]", flush=True)
print(f"  m_norm: t0={m_arr[0]:.3e}  t=1.0={m_arr[2]:.3e}  "
      f"t=5={m_arr[10]:.3e}  t=10={m_arr[-1]:.3e}", flush=True)
print(f"  v_max  drift = {(vmax[-1]-vmax[0])/vmax[0]*100:+.3f}%  range=[{vmax.min():.3f}, {vmax.max():.3f}]", flush=True)
print(f"  u_max  range = [{umax.min():.3f}, {umax.max():.3f}]", flush=True)
print(f"  mass_v drift = {(mass_v[-1]-mass_v[0])/mass_v[0]*100:+.6f}%", flush=True)
print(f"  mass_u drift = {(mass_u[-1]-mass_u[0])/(abs(mass_u[0])+1e-30)*100:+.6f}%", flush=True)
print(f"  n_peaks min/max = {npks.min()} / {npks.max()}", flush=True)
print(f"  L2 distance to Gardner at T: {L2_diff[-1]:.4e}  "
      f"(L2 norm of v itself = {np.sqrt(np.sum(v**2)*dx):.4e})", flush=True)

print("[done] E2 BKdV run complete.", flush=True)
