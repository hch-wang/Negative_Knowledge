"""
T_A / PosOnly  --  FINAL solver = E2: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4.

Coupled Burgers-swept-KdV:
    u_t + 3 u u_x = - d_x (3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = - d_x (u v)

IC: v0 = 2 sech^2(x+5);  u0 = 0.5 v0^2 + 0.2 v0  (perturbed m = +0.2 v0)
Domain: x in [-15, 15], Nx = 256, L = 30, periodic.
Time: T = 8.0,  dt = 2e-4,  classical RK4.

Why E2 and not E3:
- E1 = no dealiasing -> aliasing blew up before t=1.
- E2 = add 2/3 dealiasing (single-component upgrade) -> stable, mass exact, |max|<2.5, v_max(T)=0.92.
- E3 = add IFRK4 on v_xxx for v (another single-component upgrade) -> HURT because v_xxx also appears in u_t (coupling),
  so treating it exactly in one equation and explicitly in the other broke balance: u surged to ~9, v dropped to 0.33.
  Rolled back. E2 is bank-validated (BKdV-S1 r2/r3) and is the final answer.
"""
import os
import time
import numpy as np

# ---- domain & grid ----
L = 30.0
Nx = 256
x = np.linspace(-L / 2, L / 2, Nx, endpoint=False)
dx = L / Nx
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = 1j * k**3

# 2/3 dealias mask (keep |k_idx| <= Nx/3)
k_idx = np.fft.fftfreq(Nx, d=1.0 / Nx)
dealias_mask = (np.abs(k_idx) <= Nx / 3).astype(np.float64)

# ---- initial condition ----
v0 = 2.0 * (1.0 / np.cosh(x + 5.0))**2
u0 = 0.5 * v0**2 + 0.2 * v0

def dealias(f):
    fhat = np.fft.fft(f)
    fhat *= dealias_mask
    return np.real(np.fft.ifft(fhat))

def d_x(f):
    fhat = np.fft.fft(f) * dealias_mask
    return np.real(np.fft.ifft(ik * fhat))

def d_xxx(f):
    fhat = np.fft.fft(f) * dealias_mask
    return np.real(np.fft.ifft(ik3 * fhat))

def rhs(u, v):
    """Return (du/dt, dv/dt) for the coupled BKdV system, with 2/3 dealiasing on every product."""
    v_dl = dealias(v)
    u_dl = dealias(u)
    v2   = dealias(v_dl * v_dl)
    uv   = dealias(u_dl * v_dl)
    uu   = dealias(u_dl * u_dl)
    # u_t = -3 u u_x - 3 d_x(v^2) - v_xxx       (Burgers conservative form: u u_x = (1/2)(u^2)_x)
    v_xxx = d_xxx(v_dl)
    v2_x  = d_x(v2)
    uu_x  = d_x(uu)
    du_dt = -1.5 * uu_x - 3.0 * v2_x - v_xxx
    # v_t = -6 v v_x - v_xxx - d_x(uv)          (6 v v_x = 3 (v^2)_x)
    uv_x  = d_x(uv)
    dv_dt = -3.0 * v2_x - v_xxx - uv_x
    return du_dt, dv_dt

def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u,       v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return u_new, v_new

# ---- time loop ----
T_final = 8.0
dt = 2.0e-4
n_steps = int(round(T_final / dt))
dt = T_final / n_steps                # exact division

n_snapshots = 9
snap_steps = np.linspace(0, n_steps, n_snapshots, dtype=int)
snap_set = set(int(s) for s in snap_steps)

snapshots = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)
snap_idx = 0
snapshots[snap_idx] = np.stack([u0, v0])
snap_idx += 1

u = u0.copy()
v = v0.copy()

t0 = time.time()
mass_v0 = np.sum(v) * dx
print(f"[FINAL=E2] Nx={Nx}, L={L}, dt={dt:.3e}, n_steps={n_steps}, T={T_final}")
print(f"[FINAL=E2] mass_v(0)={mass_v0:.6f}, u_max(0)={np.max(np.abs(u)):.4f}, v_max(0)={np.max(np.abs(v)):.4f}")

for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    if step in snap_set:
        snapshots[snap_idx] = np.stack([u, v])
        snap_idx += 1
        mass_v_t = np.sum(v) * dx
        u_max_t = float(np.max(np.abs(u)))
        v_max_t = float(np.max(np.abs(v)))
        print(f"[FINAL=E2] step {step}/{n_steps}  t={step*dt:.3f}  u_max={u_max_t:.4f}  v_max={v_max_t:.4f}  mass_v={mass_v_t:.6f}  drift={(mass_v_t-mass_v0)/mass_v0*100:+.4f}%")
        if not (np.isfinite(u_max_t) and np.isfinite(v_max_t)):
            print("[FINAL=E2] BLEW UP — non-finite. Stopping.")
            break

elapsed = time.time() - t0
print(f"[FINAL=E2] elapsed {elapsed:.2f}s")

# ---- save ----
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_A.npy")
np.save(out_path, snapshots)
print(f"[FINAL=E2] saved to {out_path}  shape={snapshots.shape}")
