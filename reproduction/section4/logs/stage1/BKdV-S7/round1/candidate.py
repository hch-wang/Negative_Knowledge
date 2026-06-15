"""
BKdV-S7 Round 1 (E1): Gardner-only baseline.

Equation (single PDE, periodic x in [-15, 15], Nx=256):
    v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0     (Gardner, with cubic coefficient 3/2)

This is the m = 0 reduction of BKdV (derived in the program prompt: substitute
u = v^2/2 into BKdV's v-equation; quadratic and cubic terms collect to the
form above).

IC (FIXED across the program):
    v(x, 0) = A * sech^2(x + 5),   A = 1.5
Periodic on x in [-15, 15], Nx = 256, T = 10.0.

Numerical stack (mandated by prompt; identical to E2 BKdV solver):
- Fourier pseudospectral spatial derivatives
- 2/3 dealiasing on every nonlinear product
- Explicit RK4 in time

Goal of E1: verify the chosen IC propagates as a clean single peak in
Gardner-only evolution. Diagnostics:
- mass_v conservation
- L2 energy ||v||_2 conservation
- Hamiltonian H = integral (v_x^2/2 - v^3 - (3/8) v^4)   (Gardner energy invariant)
- v_max(t) drift
- single-peak count
- snapshot times for later comparison with BKdV

Saves snapshots to round1/snapshots.npz and diagnostics to round1/diag.npz.
"""

import os
import sys
import time
import numpy as np

ROUND_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------
# Grid & spectral operators
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

# 2/3 dealiasing mask
k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)


def fft_dealias(a):
    """FFT followed by dealiasing mask."""
    return np.fft.fft(a) * dealias


def dx_spec(f_phys):
    """Spectral first derivative (with dealiasing applied)."""
    return np.real(np.fft.ifft(ik * fft_dealias(f_phys)))


def dxx_spec(f_phys):
    return np.real(np.fft.ifft(-k2 * fft_dealias(f_phys)))


def dxxx_spec(f_phys):
    return np.real(np.fft.ifft(-ik3 * fft_dealias(f_phys)))


# ------------------------------------------------------------
# Gardner RHS:  v_t = - 6 v v_x - (3/2) v^2 v_x - v_xxx
# All nonlinear products are dealiased.
# ------------------------------------------------------------
def gardner_rhs(v):
    vh_d = fft_dealias(v)
    v_d = np.real(np.fft.ifft(vh_d))
    v_x_d = np.real(np.fft.ifft(ik * vh_d))
    v_xxx_d = np.real(np.fft.ifft(-ik3 * vh_d))
    # nonlinear products (dealiased)
    v2 = fft_dealias(v_d * v_d)
    v2_phys = np.real(np.fft.ifft(v2))
    nl_quad = 6.0 * v_d * v_x_d
    nl_cub = 1.5 * v2_phys * v_x_d
    # dealias the products against the derivative as a final pass
    rhs = -(nl_quad + nl_cub + v_xxx_d)
    rh = fft_dealias(rhs)
    return np.real(np.fft.ifft(rh))


def rk4_step(v, dt):
    k1 = gardner_rhs(v)
    k2_ = gardner_rhs(v + 0.5 * dt * k1)
    k3_ = gardner_rhs(v + 0.5 * dt * k2_)
    k4_ = gardner_rhs(v + dt * k3_)
    return v + (dt / 6.0) * (k1 + 2.0 * k2_ + 2.0 * k3_ + k4_)


# ------------------------------------------------------------
# Gardner Hamiltonian (conserved by Gardner equation):
# For   v_t = -(6 v v_x + (3/2) v^2 v_x + v_xxx),
# the Hamiltonian is  H = integral [ (1/2) v_x^2 - v^3 - (3/8) v^4 ] dx
# This is the standard Gardner Hamiltonian; use as an invariant check.
# ------------------------------------------------------------
def gardner_hamiltonian(v):
    v_x = dx_spec(v)
    H = np.sum(0.5 * v_x ** 2 - v ** 3 - (3.0 / 8.0) * v ** 4) * dx
    return float(H)


def diagnostics(v):
    mass_v = float(np.sum(v) * dx)
    L2v = float(np.sqrt(np.sum(v * v) * dx))
    v_max = float(np.max(v))
    v_min = float(np.min(v))
    v_max_x = float(x[int(np.argmax(v))])
    H = gardner_hamiltonian(v)
    # local maxima count (relative to immediate neighbors), above threshold
    thr = 0.05 * (v_max if v_max > 0 else 1.0)
    left = np.roll(v, 1)
    right = np.roll(v, -1)
    peaks = ((v > left) & (v > right) & (v > thr))
    n_peaks = int(np.sum(peaks))
    finite = bool(np.all(np.isfinite(v)))
    sup = float(np.max(np.abs(v)))
    return dict(
        mass_v=mass_v, L2v=L2v, H=H,
        v_max=v_max, v_min=v_min, v_max_x=v_max_x,
        n_peaks=n_peaks, sup=sup, finite=finite,
    )


# ------------------------------------------------------------
# Initial condition: v(x,0) = A * sech^2(x+5),  A = 1.5
# ------------------------------------------------------------
A = 1.5
v = A * (1.0 / np.cosh(x + 5.0)) ** 2

# ------------------------------------------------------------
# Time integration
# RK4 stability for v_xxx requires dt <~ 2.83 / (k_max^3).
# With Nx=256, L=30:  k_max ~ pi * Nx / L = 26.81, k_max^3 ~ 1.93e4.
# 2/3 dealiased k_eff_max ~ 17.87, k_eff_max^3 ~ 5.71e3.
# Stability bound dt < 2.83 / 5.71e3 ~ 4.95e-4. Use dt = 2e-4 for safety.
# ------------------------------------------------------------
T = 10.0
dt = 2.0e-4
nsteps = int(round(T / dt))

print(f"[grid]  Nx={Nx}  L={L}  dx={dx:.4e}", flush=True)
print(f"[time]  T={T}  dt={dt:.4e}  nsteps={nsteps}", flush=True)
print(f"[IC]    A={A}  v0 = A sech^2(x+5)", flush=True)

d0 = diagnostics(v)
print(f"[init]  mass_v={d0['mass_v']:+.6e}  L2v={d0['L2v']:.6e}  "
      f"H={d0['H']:+.6e}  v_max={d0['v_max']:.4f}@x={d0['v_max_x']:+.3f}  "
      f"n_peaks={d0['n_peaks']}", flush=True)

# Snapshot schedule: 21 evenly-spaced snapshots including t=0 and t=T (dt=0.5)
n_snap = 21
snap_steps = np.linspace(0, nsteps, n_snap, dtype=int)
snap_set = set(int(s) for s in snap_steps)

snapshots_v = []
snapshot_times = []
diag_log = []

snapshots_v.append(v.copy())
snapshot_times.append(0.0)
diag_log.append({'t': 0.0, **d0})

t0 = time.time()
report_every = max(1, nsteps // 30)

for n in range(1, nsteps + 1):
    v = rk4_step(v, dt)
    # final dealias safety
    v = np.real(np.fft.ifft(fft_dealias(v)))
    t = n * dt
    if n in snap_set:
        snapshots_v.append(v.copy())
        snapshot_times.append(t)
        d = diagnostics(v)
        diag_log.append({'t': t, **d})
    if n % report_every == 0 or n == nsteps:
        d = diagnostics(v)
        print(f"[t={t:7.4f}] mass_v={d['mass_v']:+.4e}  L2v={d['L2v']:.4e}  "
              f"H={d['H']:+.4e}  v_max={d['v_max']:.4f}@x={d['v_max_x']:+.3f}  "
              f"npk={d['n_peaks']}  sup={d['sup']:.3e}", flush=True)
        if not d['finite'] or d['sup'] > 1e4:
            print(f"[BLOWUP] at t={t:.4f}", flush=True)
            break

elapsed = time.time() - t0
final = diagnostics(v)

# Save snapshots & diagnostics
out_npz = os.path.join(ROUND_DIR, "snapshots.npz")
np.savez(out_npz,
         x=x,
         times=np.array(snapshot_times),
         v=np.array(snapshots_v))
diag_keys = list(diag_log[0].keys())
diag_arrs = {k: np.array([d[k] for d in diag_log]) for k in diag_keys}
np.savez(os.path.join(ROUND_DIR, "diag.npz"), **diag_arrs)

print(f"[saved] {out_npz}  ({len(snapshot_times)} snapshots)", flush=True)
print(f"[final] t={T:.4f}  v_max={final['v_max']:.5f}@x={final['v_max_x']:+.3f}  "
      f"mass_v={final['mass_v']:+.5e}  L2v={final['L2v']:.5e}  "
      f"H={final['H']:+.5e}  n_peaks={final['n_peaks']}  elapsed={elapsed:.1f}s",
      flush=True)

# --- Summary ---
v_maxs = np.array([d['v_max'] for d in diag_log])
mass_vs = np.array([d['mass_v'] for d in diag_log])
L2vs = np.array([d['L2v'] for d in diag_log])
Hs = np.array([d['H'] for d in diag_log])
npks = np.array([d['n_peaks'] for d in diag_log])

print(f"[summary] v_max range = [{v_maxs.min():.4f}, {v_maxs.max():.4f}]  "
      f"drift = {(v_maxs[-1]-v_maxs[0])/v_maxs[0]*100:+.4f}%", flush=True)
print(f"[summary] mass_v drift  = {(mass_vs[-1]-mass_vs[0])/mass_vs[0]*100:+.6f}%",
      flush=True)
print(f"[summary] L2v drift     = {(L2vs[-1]-L2vs[0])/L2vs[0]*100:+.6f}%",
      flush=True)
print(f"[summary] H drift       = {(Hs[-1]-Hs[0])/abs(Hs[0])*100:+.6f}%",
      flush=True)
print(f"[summary] n_peaks min/max = {npks.min()} / {npks.max()}", flush=True)

# Phase speed estimate from peak positions (account for periodic wrap)
v_max_xs = np.array([d['v_max_x'] for d in diag_log])
ts_arr = np.array([d['t'] for d in diag_log])
xs_unwrap = np.unwrap(v_max_xs * 2 * np.pi / L) * L / (2 * np.pi)
if len(ts_arr) > 1:
    speed = np.polyfit(ts_arr, xs_unwrap, 1)[0]
    # Gardner pure-cubic mKdV soliton: c = (3/2) eta^2/... ; for our equation
    # the linear-in-v term gives leading speed ~ 2 A (KdV part), cubic adds.
    # We just report empirical speed.
    print(f"[summary] phase speed (peak fit) = {speed:.4f}", flush=True)

print("[done] E1 Gardner-only baseline complete.", flush=True)
