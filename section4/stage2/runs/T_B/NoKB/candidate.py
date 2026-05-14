"""
E2: Coupled Burgers-swept-KdV system
  u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx (u v)

Single-component upgrade vs E1: Fourier pseudospectral WITH 2/3-rule dealiasing.
Time integrator unchanged (explicit RK4, dt=1e-4).
IC: v(x,0) = 4*exp(-(x+5)^2/2.25), u(x,0)=0
Domain: x in [-15,15], Nx=256, T=6.0
"""

import os
import numpy as np

# ----- Grid -----
L = 30.0
Nx = 256
x = np.linspace(-L / 2, L / 2, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = 1j * k**3

# 2/3-rule dealiasing mask
kmax_idx = Nx // 2
# kept modes: |kx_index| < 2/3 * kmax  i.e. |freq index| < N/3
freq_int = np.fft.fftfreq(Nx, d=1.0) * Nx  # integer-mode indices in [-N/2, N/2)
mask23 = (np.abs(freq_int) < Nx / 3.0).astype(np.float64)

def dealias(fhat):
    return fhat * mask23

# ----- IC -----
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros_like(x)


def dx_spec_dealias(f):
    fh = np.fft.fft(f)
    fh = dealias(fh)
    return np.real(np.fft.ifft(ik * fh))


def d3x_spec_dealias(f):
    fh = np.fft.fft(f)
    fh = dealias(fh)
    return np.real(np.fft.ifft(ik3 * fh))


def filter_field(f):
    """Project field onto 2/3 modes (useful for state truncation)."""
    return np.real(np.fft.ifft(dealias(np.fft.fft(f))))


def rhs(u, v):
    """
    u_t = -3 u u_x - 6 v v_x - v_xxx
    v_t = -6 v v_x - v_xxx - (u v)_x
    """
    u_x = dx_spec_dealias(u)
    v_x = dx_spec_dealias(v)
    v_xxx = d3x_spec_dealias(v)
    # nonlinear products formed in physical space, then dealias when taking derivative
    uv_x = dx_spec_dealias(u * v)
    uu = u * u_x  # quadratic via product
    vv = v * v_x

    du = -3.0 * uu - 6.0 * vv - v_xxx
    dv = -6.0 * vv - v_xxx - uv_x
    # final dealiasing of RHS to clean any aliased modes from u*u_x, v*v_x
    du = filter_field(du)
    dv = filter_field(dv)
    return du, dv


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new


# ----- Initial dealiasing of IC (Gaussian is wide-band) -----
u = filter_field(u0)
v = filter_field(v0)

# ----- Time stepping -----
T = 6.0
dt = 1.0e-4
Nt = int(round(T / dt))
n_snapshots = 13
snap_idx = np.linspace(0, Nt, n_snapshots).astype(int)
snap_set = set(snap_idx.tolist())

snapshots = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)
snapshots[0, 0, :] = u
snapshots[0, 1, :] = v
snap_counter = 1

mass_v0 = float(np.sum(v) * dx)

blew_up = False
last_step_done = 0
import time
t0 = time.time()
for step in range(1, Nt + 1):
    u, v = rk4_step(u, v, dt)
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        blew_up = True
        last_step_done = step
        print(f"BLOW UP at step {step}, t={step*dt:.4f}")
        for j in range(snap_counter, n_snapshots):
            snapshots[j, 0, :] = np.nan
            snapshots[j, 1, :] = np.nan
        break
    if step in snap_set:
        snapshots[snap_counter, 0, :] = u
        snapshots[snap_counter, 1, :] = v
        mvT = float(np.sum(v) * dx)
        print(f"snap {snap_counter}: t={step*dt:.3f}  max v={np.max(v):.4f}  min v={np.min(v):.4f}  max|u|={np.max(np.abs(u)):.4f}  mass drift={(mvT-mass_v0)/abs(mass_v0)*100:+.4f}%")
        snap_counter += 1
    last_step_done = step

print(f"elapsed={time.time()-t0:.1f}s")

if not blew_up:
    mass_vT = float(np.sum(v) * dx)
    print(f"Done. steps={last_step_done}, t_final={last_step_done*dt:.4f}")
    print(f"max|u|={np.max(np.abs(u)):.6f}, max v={np.max(v):.6f}, min v={np.min(v):.6f}")
    print(f"mass(v) initial={mass_v0:.6f}, final={mass_vT:.6f}, drift={(mass_vT-mass_v0)/abs(mass_v0)*100:.4f}%")
else:
    print(f"Last good t before NaN: ~{(last_step_done-1)*dt:.4f}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", snapshots.astype(np.float32))
print("Saved pred_results/T_B.npy with shape", snapshots.shape)
