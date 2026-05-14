"""
T_C: Burgers bore interacting with a KdV soliton — E3 (final).

Coupled Burgers-swept-KdV with linear u-viscosity to damp bore Gibbs:
    u_t + 3 u u_x = -d_x (3 v^2 + v_xx) + nu * u_xx
    v_t + 6 v v_x + v_xxx = -d_x (u v)

nu = 5e-2 (validated BKdV-S6 prescription for bore-like u IC per dispatcher).
The v-equation is unchanged (still dissipationless, dispersive).

Periodic [-15, 15], Nx=256. Fourier pseudospectral + 2/3 dealias + RK4. dt=5e-4.
"""
import numpy as np
import os, time

# Domain
L = 30.0
Nx = 256
x = np.linspace(-L/2, L/2, Nx, endpoint=False)
dx = L / Nx
k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik2 = (1j * k) ** 2
ik3 = (1j * k) ** 3

# 2/3 dealiasing
k_cut = Nx // 3
idx = np.arange(Nx)
mode_idx = np.where(idx <= Nx // 2, idx, idx - Nx)
dealias_mask = (np.abs(mode_idx) <= k_cut).astype(np.float64)

# Linear u-viscosity (validated nu=5e-2 for bore-like u IC; BKdV-S6 dispatcher hint)
NU_U = 5e-2

# Initial condition: bore in u, soliton in v
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 / np.cosh(x + 8.0) ** 2

# Time stepping
T_final = 8.0
dt = 5e-4
n_steps = int(round(T_final / dt))
n_snapshots = 9
snap_every = n_steps // (n_snapshots - 1)

def dealias_field(f):
    return np.real(np.fft.ifft(np.fft.fft(f) * dealias_mask))

def dx_of(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f) * dealias_mask))

def dxx_of(f):
    return np.real(np.fft.ifft(ik2 * np.fft.fft(f) * dealias_mask))

def dxxx_of(f):
    return np.real(np.fft.ifft(ik3 * np.fft.fft(f) * dealias_mask))

def prod_da(a, b):
    return dealias_field(a * b)

def rhs(u, v):
    """
    u_t = -3 u u_x  - d_x(3 v^2) - v_xxx + nu*u_xx
    v_t = -6 v v_x - v_xxx - d_x(u v)
    """
    uu = prod_da(u, u)
    vv = prod_da(v, v)
    uv = prod_da(u, v)
    v_xxx = dxxx_of(v)

    # u equation
    du_burgers  = -1.5 * dx_of(uu)            # -3 u u_x = -(3/2) d_x(u^2)
    du_coupling = -3.0 * dx_of(vv) - v_xxx     # -d_x(3 v^2 + v_xx) where v_xx_x = v_xxx
    du_visc     = NU_U * dxx_of(u)             # nu u_xx
    du = du_burgers + du_coupling + du_visc

    # v equation
    dv_kdv      = -3.0 * dx_of(vv) - v_xxx     # -6 v v_x - v_xxx
    dv_coupling = -dx_of(uv)                    # -d_x(u v)
    dv = dv_kdv + dv_coupling

    return du, dv

snapshots = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)
snapshots[0, 0] = u0
snapshots[0, 1] = v0

u = u0.copy()
v = v0.copy()
snap_idx = 1

mass_v0 = v.sum() * dx
mass_u0 = u.sum() * dx
print(f"IC: mass_v0={mass_v0:.4f}, mass_u0={mass_u0:.4f}, u in [{u.min():.3f},{u.max():.3f}], v in [{v.min():.3f},{v.max():.3f}]")
print(f"Dealiasing: {int(dealias_mask.sum())} modes; NU_U={NU_U}; dt={dt}; n_steps={n_steps}; snap_every={snap_every}")

t0 = time.time()
for step in range(1, n_steps + 1):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    v = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)

    if not np.isfinite(u).all() or not np.isfinite(v).all():
        print(f"BLOWUP at step {step} t={step*dt:.4f}")
        break

    if step % snap_every == 0 and snap_idx < n_snapshots:
        snapshots[snap_idx, 0] = u
        snapshots[snap_idx, 1] = v
        mv = v.sum() * dx
        mu = u.sum() * dx
        print(f"  t={step*dt:6.3f}  u_max={np.max(np.abs(u)):.4f}  u_min={u.min():.4f}  v_peak={v.max():.4f}  v_min={v.min():.4f}  mass_v={mv:.4f}  mass_u={mu:.4f}")
        snap_idx += 1

elapsed = time.time() - t0
print(f"Elapsed: {elapsed:.1f}s")
print(f"Final: u_max={np.max(np.abs(u)):.4f}, v_peak={np.max(v):.4f}, v_min={np.min(v):.4f}")
print(f"Mass conservation: |dmass_v|={abs(v.sum()*dx-mass_v0):.3e}, |dmass_u|={abs(u.sum()*dx-mass_u0):.3e}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", snapshots)
print(f"Saved pred_results/T_C.npy shape={snapshots.shape}")
