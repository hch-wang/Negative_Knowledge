"""
Stage-2 v3 Class A, Task T_C, NoKB condition.
FINAL CANDIDATE = E2 (Fourier pseudospectral + 2/3-rule dealiasing + explicit RK4).

Self-rollback from E3: E3 added Hou-Li-style exponential smoothing (alpha=36, p=36)
on top of E2, hoping to suppress the late-time u overshoot. Instead E3 destabilized
(|u|max 28.8 at T=8 vs 11.5 for E2; v became chaotic). E2 is more stable and
satisfies the soliton-survival half of the phenomenon target.

E2 method:
- Spatial: Fourier pseudospectral derivatives (k, ik^3) on periodic [-15, 15], Nx=256.
  Nyquist mode zeroed for odd-order derivatives.
- Dealiasing: 2/3-rule mask applied to every nonlinear product (uu_x, vv_x, u_x v, u v_x).
- Time: explicit RK4 with dt = 1.0e-4 (T=8 → 80000 steps).
- IC filtered with the 2/3-rule before t=0 so the start state lives on resolved modes.

PDE:
    u_t + 3 u u_x = -d_x (3 v^2 + v_xx) = -6 v v_x - v_xxx
    v_t + 6 v v_x + v_xxx           = -d_x (u v)         = -u_x v - u v_x

Output: pred_results/T_C.npy shape (9, 2, 256), t = 0, 1, ..., 8.

Phenomenon notes:
- The Burgers term 3 u u_x on the smoothed bore drives shock formation; pure spectral
  with only 2/3-dealiasing develops Gibbs-style overshoots (|u| grows above the
  target 5.0). Without shock-capturing or higher-order hyperviscosity the bound
  |u_max| < 5 is unattainable for this IC. v soliton survives the encounter with
  amplitude well above 0.5 — that half of the target is met.
"""

import numpy as np

# -----------------------------------------------------------------------------
# Grid
# -----------------------------------------------------------------------------
L = 30.0
Nx = 256
x = np.linspace(-L/2, L/2, Nx, endpoint=False)
dx = x[1] - x[0]

# wavenumbers
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k.copy()
ik3 = 1j * k.copy()**3

# zero Nyquist mode for odd derivatives
nyq = Nx // 2
ik[nyq] = 0.0
ik3[nyq] = 0.0

# 2/3-rule dealiasing
k_max = np.max(np.abs(k))
kcut = (2.0 / 3.0) * k_max
dealias_mask = (np.abs(k) <= kcut).astype(np.float64)

def filt(f):
    return np.real(np.fft.ifft(dealias_mask * np.fft.fft(f)))

# -----------------------------------------------------------------------------
# Initial condition
# -----------------------------------------------------------------------------
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 / np.cosh(x + 8.0)**2
u0 = filt(u0)
v0 = filt(v0)

# -----------------------------------------------------------------------------
# Spectral derivative helpers
# -----------------------------------------------------------------------------
def dx_(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def dxxx_(f):
    return np.real(np.fft.ifft(ik3 * np.fft.fft(f)))

def prod_dealias(a, b):
    return filt(a * b)

# -----------------------------------------------------------------------------
# RHS
# -----------------------------------------------------------------------------
def rhs(u, v):
    u_x = dx_(u)
    v_x = dx_(v)
    v_xxx = dxxx_(v)
    u_t = -3.0 * prod_dealias(u, u_x) - 6.0 * prod_dealias(v, v_x) - v_xxx
    v_t = -6.0 * prod_dealias(v, v_x) - v_xxx - prod_dealias(u_x, v) - prod_dealias(u, v_x)
    return u_t, v_t

def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u,     v + dt*k3v)
    u_new = u + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v_new = v + (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v)
    return u_new, v_new

# -----------------------------------------------------------------------------
# Time loop
# -----------------------------------------------------------------------------
T_final = 8.0
dt = 1.0e-4
nsteps = int(round(T_final / dt))

n_snap = 9
snap_times = np.linspace(0.0, T_final, n_snap)
snap_steps = np.round(snap_times / dt).astype(int)

snapshots = np.zeros((n_snap, 2, Nx), dtype=np.float64)
snapshots[0, 0, :] = u0
snapshots[0, 1, :] = v0

u = u0.copy()
v = v0.copy()

snap_idx = 1
aborted = False
for step in range(1, nsteps + 1):
    u, v = rk4_step(u, v, dt)
    if snap_idx < n_snap and step == snap_steps[snap_idx]:
        snapshots[snap_idx, 0, :] = u
        snapshots[snap_idx, 1, :] = v
        umax = float(np.max(np.abs(u)))
        vmax = float(np.max(np.abs(v)))
        print(f"snap {snap_idx}/{n_snap-1} at t={step*dt:.3f}: |u|max={umax:.4f}, |v|max={vmax:.4f}")
        snap_idx += 1
        if not np.isfinite(umax) or not np.isfinite(vmax):
            print("NON-FINITE: aborting time loop")
            aborted = True
            break

np.save("pred_results/T_C.npy", snapshots)
print("Saved pred_results/T_C.npy, shape =", snapshots.shape)
print("Final |u|max =", float(np.max(np.abs(snapshots[-1, 0]))))
print("Final |v|max =", float(np.max(np.abs(snapshots[-1, 1]))))
print("aborted =", aborted)
