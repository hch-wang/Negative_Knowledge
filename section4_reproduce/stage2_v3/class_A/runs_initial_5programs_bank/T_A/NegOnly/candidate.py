"""
E3: E2 with dt reduced by 2x (single-component change: dt only).

Method: identical to E2 (Fourier pseudospectral + 2/3-rule dealiasing on
all nonlinear products + classical RK4 on the full explicit RHS) EXCEPT
dt = 5.0e-5 (2x smaller than E2's 1.0e-4). All other parameters fixed.

Purpose: test whether E2's observed v-peak decay (2.0 -> 0.635 at T=8) is
(a) genuinely physical radiation off the m=0 manifold (the bank's
expectation per BKdV-S5 depth=3) or (b) a numerical-accuracy artifact of
RK4 phase error at dt=1e-4. If E3 produces nearly identical end-state
(within ~1%) to E2, then the decay is physical and E2 is converged.

Bank justification:
- Cites_bank: [] (negative-only condition; no positive entries available).
- Rejects_bank: kb-kdv-explicit-RK4-stiffness-blowup (warns very small dt
  RK4 still fragments soliton -- but that was Gardner explicit RK4 with NO
  dealiasing on cubic term and dt=1e-5; we are at dt=5e-5 WITH dealiasing
  on quadratic terms, so the warning is partially mitigated).
- Rejects: kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup -- changing to IMEX is
  TWO-component change, so excluded.

PDE:
    u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -d/dx (u v)

IC: v(x,0) = 2 sech^2(x+5); u(x,0) = 0.5 v0^2 + 0.2 v0.
Domain: x in [-15, 15] (periodic), Nx = 256.
Final time: T = 8.0.
"""

import os
import numpy as np

# ---------------- Configuration ----------------
L = 30.0
Nx = 256
T_final = 8.0
dt = 5.0e-5  # E3: 2x smaller than E2's 1.0e-4
n_snapshots = 9

# ---------------- Grid + spectral operators ----------------
x = np.linspace(-L / 2, L / 2, Nx, endpoint=False)
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=L / Nx)
ik = 1j * k
k_idx = np.fft.fftfreq(Nx, d=1.0 / Nx)
dealias_mask = (np.abs(k_idx) <= Nx // 3).astype(np.float64)

# ---------------- Spectrally-dealiased helpers ----------------
def da(f):
    return np.real(np.fft.ifft(np.fft.fft(f) * dealias_mask))

def dx_da(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f) * dealias_mask))

def dxx_da(f):
    return np.real(np.fft.ifft((ik ** 2) * np.fft.fft(f) * dealias_mask))

def dxxx_da(f):
    return np.real(np.fft.ifft((ik ** 3) * np.fft.fft(f) * dealias_mask))

# ---------------- RHS ----------------
def rhs(u, v):
    ud = da(u)
    vd = da(v)
    ux = dx_da(ud)
    vx = dx_da(vd)
    vxx = dxx_da(vd)
    vxxx = dxxx_da(vd)

    vv = da(vd * vd)
    uv = da(ud * vd)
    uux = da(ud * ux)
    vvx = da(vd * vx)

    forcing_u_inner = 3.0 * vv + vxx
    u_t = -3.0 * uux - dx_da(forcing_u_inner)
    v_t = -6.0 * vvx - vxxx - dx_da(uv)
    return u_t, v_t

# ---------------- RK4 step ----------------
def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return u_new, v_new

# ---------------- Initial condition ----------------
v0 = 2.0 * (1.0 / np.cosh(x + 5.0)) ** 2
u0 = 0.5 * v0 ** 2 + 0.2 * v0

# ---------------- Time stepping ----------------
n_steps = int(round(T_final / dt))
snap_steps = np.linspace(0, n_steps, n_snapshots).astype(int)

snapshots = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)
snapshots[0, 0] = u0
snapshots[0, 1] = v0

u, v = u0.copy(), v0.copy()
snap_idx = 1
blew_up = False
blow_step = -1

for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    if not np.all(np.isfinite(v)) or not np.all(np.isfinite(u)):
        blew_up = True
        blow_step = step
        for j in range(snap_idx, n_snapshots):
            snapshots[j, 0] = u
            snapshots[j, 1] = v
        break
    if snap_idx < n_snapshots and step == snap_steps[snap_idx]:
        snapshots[snap_idx, 0] = u
        snapshots[snap_idx, 1] = v
        snap_idx += 1

# ---------------- Diagnostics ----------------
print(f"E3 (dt=5.0e-5, n_steps={n_steps})")
print(f"blew_up={blew_up}  blow_step={blow_step}/{n_steps}")
print(f"v_peak(T)={np.nanmax(snapshots[-1,1]):.4f}   v_peak(0)={v0.max():.4f}")
print(f"u_peak(T)={np.nanmax(snapshots[-1,0]):.4f}   u_peak(0)={u0.max():.4f}")
print(f"v_min(T)={np.nanmin(snapshots[-1,1]):.4f}")
print(f"u_min(T)={np.nanmin(snapshots[-1,0]):.4f}")
m0 = v0.sum() * (L / Nx)
mT = np.nansum(snapshots[-1, 1]) * (L / Nx)
print(f"mass_v(0)={m0:.6f}   mass_v(T)={mT:.6f}   rel_mass_drift={abs(mT - m0) / max(abs(m0), 1e-12):.4%}")
print(f"max|u|={np.nanmax(np.abs(snapshots[-1,0])):.4f}  max|v|={np.nanmax(np.abs(snapshots[-1,1])):.4f}")
print(f"finite(u_T)={np.all(np.isfinite(snapshots[-1,0]))}  finite(v_T)={np.all(np.isfinite(snapshots[-1,1]))}")

vT = snapshots[-1, 1]
if np.all(np.isfinite(vT)):
    half = 0.5 * np.max(vT)
    left = np.roll(vT, 1); right = np.roll(vT, -1)
    n_peaks_half = int(np.sum((vT > left) & (vT > right) & (vT > half)))
    print(f"n_local_maxima(v_T, >0.5*max)={n_peaks_half}")

print("snap | v_peak | u_peak | v_min  | u_min  | mass_v")
for i in range(snapshots.shape[0]):
    uu = snapshots[i, 0]; vv = snapshots[i, 1]
    print(f"{i:3d}  | {vv.max():6.4f} | {uu.max():6.4f} | {vv.min():7.4f} | {uu.min():7.4f} | {vv.sum()*L/Nx:.4f}")

# ---------------- Save ----------------
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", snapshots)
print(f"saved pred_results/T_A.npy  shape={snapshots.shape}")
