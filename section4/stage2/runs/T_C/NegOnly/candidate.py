"""
E3 candidate for sub-task T_C (Burgers bore + KdV soliton).

Single-component upgrade over E2: add 2/3 dealiasing on the nonlinear products.

Method: Fourier pseudospectral + 2/3 dealiasing on nonlinear products + IMEX-CN
        (CN treats v_xxx implicitly; nonlinear terms explicit).

PDE:
    u_t = -3 u u_x - 6 v v_x - v_xxx
    v_t = -6 v v_x - v_xxx - (u v)_x

Spectral linear: -v_xxx <-> symbol ik^3.
    u_hat_t = N_u_hat + ik^3 v_hat
    v_hat_t = N_v_hat + ik^3 v_hat
N_u = -3 u u_x - 6 v v_x ; N_v = -6 v v_x - (u v)_x

Dealiasing: 2/3 rule applied to each nonlinear product (u*u_x, v*v_x, u*v)
            BEFORE differentiation in spectral space. Concretely, all
            high-k modes (|k| > 2/3 k_max) of the products are zeroed.

IMEX-CN update:
    v_hat^{n+1} = ( v_hat^n * (1 + a) + dt * Nv_hat ) / (1 - a),  a = ik^3 dt/2
    u_hat^{n+1} = u_hat^n + dt * Nu_hat + a * (v_hat^n + v_hat^{n+1})

IC:
    u(x,0) = 1.5 * (1 - tanh(x/0.5)) / 2     (smoothed bore at x=0)
    v(x,0) = 1.5 * sech^2(x + 8)              (KdV soliton at x=-8)

Domain: x in [-15, 15], Nx = 256, periodic.
T = 8.0, dt = 1e-3, n_steps = 8000, n_snapshots = 9.
"""

import numpy as np
import os

# ---------------- grid ----------------
Nx = 256
L = 30.0
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik  = 1j * k
ik3 = 1j * k**3   # symbol of -d_x^3

# 2/3 dealiasing mask: keep |k_index| <= N/3
N3 = Nx // 3
mask = np.zeros(Nx, dtype=bool)
# fftfreq layout: 0, 1, ..., N/2-1, -N/2, ..., -1. Keep |idx|<=N3 in either direction.
mask[:N3 + 1] = True
mask[-N3:] = True
# float mask for multiplication
dealias = mask.astype(np.float64)

# ---------------- initial conditions ----------------
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 / np.cosh(x + 8.0)**2

# ---------------- time discretization ----------------
T = 8.0
dt = 1.0e-3
n_steps = int(round(T / dt))
n_snapshots = 9
snap_every = n_steps // (n_snapshots - 1)

# storage
out = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)
out[0, 0] = u0
out[0, 1] = v0

# ---------------- helpers ----------------
def fft(f):
    return np.fft.fft(f)

def ifft_real(F):
    return np.real(np.fft.ifft(F))

def dealiased_product(a, b):
    """Compute pointwise a*b, then 2/3-truncate in spectral space, return both spec and phys."""
    P_hat = fft(a * b) * dealias
    return P_hat, ifft_real(P_hat)

def nonlinear_hats(u_hat, v_hat):
    """Return Nu_hat, Nv_hat with 2/3 dealiasing on nonlinear products."""
    # filter inputs to 2/3 band first (so the products use only resolved modes)
    u_hat_f = u_hat * dealias
    v_hat_f = v_hat * dealias
    u_f = ifft_real(u_hat_f)
    v_f = ifft_real(v_hat_f)
    ux_f = ifft_real(ik * u_hat_f)
    vx_f = ifft_real(ik * v_hat_f)

    # products, dealiased
    uux_hat = fft(u_f * ux_f) * dealias        # u*u_x
    vvx_hat = fft(v_f * vx_f) * dealias        # v*v_x
    uv_hat  = fft(u_f * v_f) * dealias         # u*v
    uv_x_hat = ik * uv_hat                     # d/dx(u*v)

    Nu_hat = -3.0 * uux_hat - 6.0 * vvx_hat
    Nv_hat = -6.0 * vvx_hat - uv_x_hat
    return Nu_hat, Nv_hat

# IMEX-CN factors
alpha = ik3 * dt / 2.0
denom = 1.0 - alpha
num_v_old_coeff = 1.0 + alpha

# ---------------- time stepping ----------------
u = u0.copy()
v = v0.copy()
u_hat = fft(u)
v_hat = fft(v)

snap_idx = 1
diverged = False
diverge_step = -1

for step in range(1, n_steps + 1):
    Nu_hat, Nv_hat = nonlinear_hats(u_hat, v_hat)
    v_hat_new = (v_hat * num_v_old_coeff + dt * Nv_hat) / denom
    u_hat_new = u_hat + dt * Nu_hat + (ik3 * dt / 2.0) * (v_hat + v_hat_new)

    u_hat = u_hat_new
    v_hat = v_hat_new
    u = ifft_real(u_hat)
    v = ifft_real(v_hat)

    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        diverged = True
        diverge_step = step
        print(f"NON-FINITE at step {step}, t = {step*dt:.5f}")
        for j in range(snap_idx, n_snapshots):
            out[j, 0] = u
            out[j, 1] = v
        break

    if step % snap_every == 0 and snap_idx < n_snapshots:
        out[snap_idx, 0] = u
        out[snap_idx, 1] = v
        snap_idx += 1

if not diverged:
    out[-1, 0] = u
    out[-1, 1] = v

# ---------------- diagnostics ----------------
u_fin = out[-1, 0]
v_fin = out[-1, 1]
print(f"diverged={diverged} (step={diverge_step})")
print(f"final u: min={np.nanmin(u_fin):.4g}, max={np.nanmax(u_fin):.4g}, n_nan={np.sum(~np.isfinite(u_fin))}")
print(f"final v: min={np.nanmin(v_fin):.4g}, max={np.nanmax(v_fin):.4g}, n_nan={np.sum(~np.isfinite(v_fin))}")
print(f"mass u: {np.nansum(u_fin)*dx:.4f}; mass v: {np.nansum(v_fin)*dx:.4f}")

if np.all(np.isfinite(v_fin)):
    pk_mask = (v_fin > np.roll(v_fin, 1)) & (v_fin > np.roll(v_fin, -1)) & (v_fin > 0.05)
    n_peaks = int(np.sum(pk_mask))
    v_peak = float(np.max(v_fin))
    ix = int(np.argmax(v_fin))
    print(f"v: {n_peaks} peaks(>0.05); peak amp={v_peak:.4g} at x={x[ix]:.3f}; u_max={float(np.max(np.abs(u_fin))):.4g}")

# snapshot diagnostics: print v-peak amp at each saved time
times = np.linspace(0.0, T, n_snapshots)
print("snapshot diagnostics (t, max|u|, max v):")
for j in range(n_snapshots):
    uj = out[j, 0]; vj = out[j, 1]
    if np.all(np.isfinite(uj)) and np.all(np.isfinite(vj)):
        print(f"  t={times[j]:5.2f}  max|u|={np.max(np.abs(uj)):.4f}  max v={np.max(vj):.4f}")
    else:
        print(f"  t={times[j]:5.2f}  NaN")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", out)
print(f"saved pred_results/T_C.npy shape={out.shape}")
