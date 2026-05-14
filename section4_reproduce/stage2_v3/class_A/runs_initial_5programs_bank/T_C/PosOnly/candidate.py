"""
E3: Single-component upgrade vs E2: add Hou-Li-type smooth exponential filter
    applied to both fields after each RK4 step. Filter shape:
        sigma(eta) = exp(-alpha * eta^p),
        eta = |k_idx| / cutoff_dealias = |k_idx| / (Nx/3)
        alpha = 36 (so sigma=exp(-36) ~ 2.3e-16 at eta=1, machine eps)
        p = 16  (moderate roll-off so upper resolved band is damped, not too sharp)
    Keeps E2 stack (Fourier pseudospectral + 2/3-rule dealiasing + RK4, dt=2e-4).

PDE:
    u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -d/dx (u v)

IC: bore u_L=1.5,u_R=0 width 0.5; KdV soliton v amp 1.5 at x=-8.

Cites bank: kb-burgers-MUSCL-Godunov-shock-pass identified the shock-capturing
need; BKdV-S1 confirmed dealiasing+RK4 base. The filter is the smallest
shock-capturing step that does not require operator splitting.
"""
import os
import numpy as np

# ----------------- Domain -----------------
L = 30.0
Nx = 256
x = np.linspace(-L/2, L/2, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = 1j * k**3
mk2 = -(k**2)

# fftfreq integer indices: 0,1,..,N/2-1,-N/2,...,-1
k_idx_signed = np.fft.fftfreq(Nx, d=1.0/Nx)
k_idx_abs = np.abs(k_idx_signed)

# 2/3-rule dealiasing
cutoff = Nx // 3   # 85
dealias_mask = (k_idx_abs <= cutoff).astype(np.float64)

# Hou-Li-type exponential filter
alpha_f = 36.0
p_f = 16
# eta = |k_idx| / cutoff so eta=1 at the dealias cutoff, sigma(1)=exp(-36)~0
# (modes above cutoff are zeroed by dealiasing anyway; filter mainly damps eta in [0.5, 1])
eta = k_idx_abs / float(cutoff)
filter_mask = np.exp(-alpha_f * (eta ** p_f))
# Apply 2/3 dealiasing first (zero above cutoff), then the smooth filter
combined_filter = filter_mask * dealias_mask

def fft(f):
    return np.fft.fft(f)

def ifft_real(F):
    return np.fft.ifft(F).real

def dealias(f):
    """Apply 2/3-rule cutoff in spectral space, return physical-space array."""
    F = fft(f)
    F *= dealias_mask
    return ifft_real(F)

def filter_step(f):
    """Apply the combined Hou-Li filter (which includes the 2/3 dealias cutoff)."""
    F = fft(f)
    F *= combined_filter
    return ifft_real(F)

def dx_spec(f):
    return ifft_real(ik * fft(f))

def dxx_spec(f):
    return ifft_real(mk2 * fft(f))

def dxxx_spec(f):
    return ifft_real(ik3 * fft(f))

# ----------------- IC -----------------
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 * (1.0 / np.cosh(x + 8.0))**2

# ----------------- RHS (with 2/3 dealiasing on every nonlinear product) -----------------
def rhs(u, v):
    ud = dealias(u)
    vd = dealias(v)
    u_x = dx_spec(ud)
    v_x = dx_spec(vd)
    v_xx = dxx_spec(vd)
    v_xxx = dxxx_spec(vd)
    uu_x = dealias(ud * u_x)
    vv_x = dealias(vd * v_x)
    v2   = dealias(vd * vd)
    uv   = dealias(ud * vd)
    rhs_u = -3.0 * uu_x - dx_spec(3.0 * v2 + v_xx)
    rhs_v = -6.0 * vv_x - v_xxx - dx_spec(uv)
    return rhs_u, rhs_v

def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u,     v + dt*k3v)
    u_new = u + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v_new = v + (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v)
    # Apply Hou-Li filter after each full step
    u_new = filter_step(u_new)
    v_new = filter_step(v_new)
    return u_new, v_new

# ----------------- Time loop -----------------
T = 8.0
dt = 2.0e-4
n_steps = int(round(T / dt))
dt = T / n_steps

n_snapshots = 17
snap_times = np.linspace(0.0, T, n_snapshots)
snap_steps = np.round(snap_times / dt).astype(int)

snapshots = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)
snapshots[0, 0] = u0
snapshots[0, 1] = v0

u = u0.copy()
v = v0.copy()

snap_idx = 1
diverged = False
for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    if not (np.isfinite(u).all() and np.isfinite(v).all()):
        print(f"DIVERGED at step {step}, t={step*dt:.4f}")
        diverged = True
        for j in range(snap_idx, n_snapshots):
            snapshots[j, 0] = np.nan
            snapshots[j, 1] = np.nan
        break
    if snap_idx < n_snapshots and step == snap_steps[snap_idx]:
        snapshots[snap_idx, 0] = u
        snapshots[snap_idx, 1] = v
        snap_idx += 1

# diagnostics
if not diverged:
    print(f"E3 OK. T={T}")
    print(f"Final sup|u| = {np.nanmax(np.abs(u)):.4e}, sup|v| = {np.nanmax(np.abs(v)):.4e}")
    print(f"Final max v (signed) = {np.nanmax(v):.4e}")
    print(f"mass_v: init={(v0.sum()*dx):.6e}, final={(v.sum()*dx):.6e}")
    print(f"mass_u: init={(u0.sum()*dx):.6e}, final={(u.sum()*dx):.6e}")
    idx_v = int(np.argmax(v))
    print(f"Final v peak: amp={v[idx_v]:.4e} at x={x[idx_v]:.4f}")
    idx_u = int(np.argmax(np.abs(u)))
    print(f"Final |u| peak: amp={u[idx_u]:.4e} at x={x[idx_u]:.4f}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", snapshots.astype(np.float64))
print(f"Saved pred_results/T_C.npy shape={snapshots.shape}")
