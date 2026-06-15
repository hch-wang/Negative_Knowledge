"""
T_C — Burgers bore × KdV soliton interaction.
E2 (NegOnly): E1 baseline + single-component upgrade — explicit linear viscosity
nu*u_xx on the u-equation only. nu=5e-2 per BKdV-S6 deep-synthesis empirical floor
on this exact bore IC. Hyperviscosity from BKdV-S4 envelope is explicitly NOT used
(13 orders of magnitude too weak per BKdV-S6).
"""
import numpy as np
import os

# -------------------- domain --------------------
Nx = 256
L = 30.0  # x in [-15, 15]
x = np.linspace(-L/2, L/2, Nx, endpoint=False)
dx = L / Nx
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k * k
ik3 = 1j * (k**3)

# 2/3 dealiasing mask (zero modes with index > 2/3 of Nyquist)
k_max_idx = Nx // 2
cut = (2.0 / 3.0) * k_max_idx
mask = (np.abs(np.fft.fftfreq(Nx, d=1.0)) * Nx <= cut).astype(np.float64)

# -------------------- IC --------------------
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0      # smoothed bore: u_L=1.5, u_R=0
v0 = 1.5 / np.cosh(x + 8.0) ** 2                # KdV soliton at x=-8

# -------------------- u-side dissipation --------------------
NU_U = 5.0e-2                                   # BKdV-S6 deep-synthesis empirical floor

# -------------------- time --------------------
T = 8.0
dt = 2.0e-4
n_steps = int(round(T / dt))
dt = T / n_steps

n_snap = 17
snap_steps = np.linspace(0, n_steps, n_snap, dtype=int)
snap_set = set(snap_steps.tolist())

# -------------------- spectral helpers --------------------
def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def dxx_spec(f):
    return np.real(np.fft.ifft(-k2 * np.fft.fft(f)))

def dxxx_spec(f):
    return np.real(np.fft.ifft(ik3 * np.fft.fft(f)))

def dealias(f):
    F = np.fft.fft(f)
    return np.real(np.fft.ifft(F * mask))

# -------------------- RHS --------------------
def rhs(u, v):
    ud = dealias(u)
    vd = dealias(v)
    u_x   = dx_spec(ud)
    u_xx  = dxx_spec(ud)              # NEW: for linear viscosity
    v_x   = dx_spec(vd)
    v_xxx = dxxx_spec(vd)
    uv    = dealias(ud * vd)
    uv_x  = dx_spec(uv)
    v2    = dealias(vd * vd)
    v2_x  = dx_spec(v2)
    vvx   = dealias(vd * v_x)
    uux   = dealias(ud * u_x)

    # u_t = -3 u u_x - 3 (v^2)_x - v_xxx  +  nu * u_xx
    du = -3.0 * uux - 3.0 * v2_x - v_xxx + NU_U * u_xx
    # v_t = -6 v v_x - v_xxx - (uv)_x
    dv = -6.0 * vvx - v_xxx - uv_x
    return du, dv

# -------------------- RK4 step --------------------
def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new

# -------------------- run --------------------
snapshots = []
u = u0.copy()
v = v0.copy()
snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    if not (np.isfinite(u).all() and np.isfinite(v).all()):
        print(f"BLOWUP at step {step} t={step*dt:.4f}: NaN detected")
        while len(snapshots) < n_snap:
            snapshots.append(snapshots[-1].copy())
        break
    if step in snap_set:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

out = np.stack(snapshots, axis=0)
os.makedirs(os.path.join(os.path.dirname(__file__), "pred_results"), exist_ok=True)
np.save(os.path.join(os.path.dirname(__file__), "pred_results", "T_C.npy"), out)
print("OUT shape", out.shape)
uf, vf = out[-1, 0], out[-1, 1]
print(f"u_max_final={np.max(np.abs(uf)):.4f}  v_max_final={np.max(vf):.4f}  v_min_final={np.min(vf):.4f}")
print(f"all_finite={np.isfinite(out).all()}")
from numpy import roll
pk = (vf > roll(vf, 1)) & (vf > roll(vf, -1)) & (vf > 0.3)
print(f"v peaks > 0.3: {int(pk.sum())}")
TV_u_final = np.abs(np.diff(uf)).sum()
print(f"TV(u_final) = {TV_u_final:.3f}")
