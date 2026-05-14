"""
T_A PosOnly — FINAL candidate (Experiment E2)
Coupled Burgers-swept-KdV soliton-stability run.

PDE:
  u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx (u v)

Final method (E2 = E1 baseline + 2/3-rule dealiasing, single-component upgrade):
  - Fourier pseudospectral spatial derivatives via FFT
  - 2/3-rule dealiasing filter on fields and on nonlinear products
  - Fully explicit RK4 time stepping applied uniformly to both u and v
  - dt = 1.0e-4 chosen so |dt * k_max^3| < 2.83 (RK4 linear stability for ik^3)
  - No operator splitting, no IMEX, no hyperviscosity, no shock-capturing
  - Conservative-form quadratic nonlinearities (u u_x = 1/2 (u^2)_x etc.)
    with the product dealiased before differentiation

E3 (IMEX-CN) was attempted but inadvertently also raised dt; the explicit
treatment of v_xxx as a forcing in the u-equation requires dt*k_max^3<2.83,
so the IMEX advantage on the v-equation alone does not extend to allow
larger dt. E2 remains the most-promising stable run.

IC:
  v(x,0) = 2 sech^2(x+5)
  u(x,0) = 0.5 v(x,0)^2 + 0.2 v(x,0)

Domain: periodic [-15, 15], Nx=256, T_final=8.0.
Output: pred_results/T_A.npy, shape (17, 2, 256), float64.
"""

import numpy as np
from pathlib import Path


# -------------- grid --------------
Nx = 256
x_min, x_max = -15.0, 15.0
L = x_max - x_min
dx = L / Nx
x = x_min + dx * np.arange(Nx)

k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = 1j * (k ** 3)
mk2 = -(k ** 2)

k_max = np.max(np.abs(k))
dealias_mask = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(np.float64)


def fft(f):
    return np.fft.fft(f)


def ifft(F):
    return np.real(np.fft.ifft(F))


def dx_spec(f):
    return ifft(ik * fft(f))


def dxxx_spec(f):
    return ifft(ik3 * fft(f))


def dealias_field(f):
    F = fft(f)
    F = F * dealias_mask
    return ifft(F)


# -------------- RHS with dealiasing --------------
def rhs(u, v):
    """Right-hand side of (u_t, v_t)."""
    vxxx = dxxx_spec(v)

    uu = dealias_field(u * u)
    vv = dealias_field(v * v)
    uv = dealias_field(u * v)

    half_uu_x = 0.5 * dx_spec(uu)
    vv_x_full = dx_spec(vv)
    uv_x = dx_spec(uv)

    # u_t = -3 u u_x - d/dx (3 v^2 + v_xx) = -3 (1/2)(u^2)_x - 3 (v^2)_x - v_xxx
    u_t = -3.0 * half_uu_x - 3.0 * vv_x_full - vxxx

    # v_t = -6 v v_x - v_xxx - (uv)_x = -3 (v^2)_x - v_xxx - (uv)_x
    v_t = -3.0 * vv_x_full - vxxx - uv_x

    return u_t, v_t


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    # dealias state once per step to suppress slow build-up at retained-mode boundary
    u_new = dealias_field(u_new)
    v_new = dealias_field(v_new)
    return u_new, v_new


# -------------- initial condition --------------
v0 = 2.0 * (1.0 / np.cosh(x + 5.0)) ** 2
u0 = 0.5 * v0 ** 2 + 0.2 * v0

# dealias IC for spectral consistency
v0 = dealias_field(v0)
u0 = dealias_field(u0)

# -------------- time loop --------------
T_final = 8.0
dt = 1.0e-4
Nt = int(round(T_final / dt))
assert abs(Nt * dt - T_final) < 1e-9

n_snapshots = 17
snap_idx = np.linspace(0, Nt, n_snapshots).astype(int)
snap_set = set(snap_idx.tolist())

snapshots = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)


def save_snapshot(u, v, idx):
    snapshots[idx, 0] = u
    snapshots[idx, 1] = v


u = u0.copy()
v = v0.copy()
save_snapshot(u, v, 0)

mass_v0 = np.sum(v0) * dx
peak_v0 = float(np.max(v0))
print(f"[FINAL=E2] Nx={Nx}, dx={dx:.4f}, k_max={k_max:.2f}, dt={dt:.2e}, Nt={Nt}")
print(f"[FINAL=E2] 2/3-dealias retains {int(dealias_mask.sum())}/{Nx} modes")
print(f"[FINAL=E2] Initial v: mass={mass_v0:.6f}, peak={peak_v0:.6f}")
print(f"[FINAL=E2] Initial u: peak={float(np.max(u0)):.6f}")

for n in range(1, Nt + 1):
    u, v = rk4_step(u, v, dt)

    if n in snap_set:
        idx = int(np.where(snap_idx == n)[0][0])
        save_snapshot(u, v, idx)
        peak_v = float(np.max(np.abs(v)))
        peak_u = float(np.max(np.abs(u)))
        mass_v = np.sum(v) * dx
        t_now = n * dt
        print(f"[FINAL=E2] t={t_now:.3f} step={n}/{Nt}: max(v)={float(np.max(v)):+.4f} min(v)={float(np.min(v)):+.4f} |u|={peak_u:.4f} mass(v)={mass_v:.4f}")

out_dir = Path(__file__).resolve().parent / "pred_results"
out_dir.mkdir(exist_ok=True)
np.save(out_dir / "T_A.npy", snapshots)

print(f"[FINAL=E2] Final v: mass={np.sum(snapshots[-1,1])*dx:.6f}, peak={float(np.max(snapshots[-1,1])):.6f}, min={float(np.min(snapshots[-1,1])):.6f}")
print(f"[FINAL=E2] Final u: max_abs={float(np.max(np.abs(snapshots[-1,0]))):.6f}")
print(f"[FINAL=E2] Saved shape={snapshots.shape}, dtype={snapshots.dtype}")
