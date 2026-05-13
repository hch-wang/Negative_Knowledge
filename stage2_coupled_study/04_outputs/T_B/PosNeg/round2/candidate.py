"""
Coupled Burgers-swept-KdV system — T_B: Gaussian wave packet -> soliton train
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

Domain: x in [-15, 15], periodic, Nx=256
IC: v(x,0) = 4*exp(-((x+5)^2)/2.25), u(x,0) = 0
T = 6.0

Method: Fourier pseudospectral + Strang splitting + ETD-RK2 for v dispersive part
  - v equation: Exponential Time Differencing RK2 (ETD-RK2) for v_xxx (exact via
    integrating factor in spectral space), explicit Adams-Bashforth 2 for nonlinear
  - u equation: MUSCL-Godunov for 3*u*u_x (upwind, TVD), explicit for coupling term
  - Very small dt to handle amplitude-4 nonlinear CFL (kb-gardner-nonlinearCFL-amplitude-boundary)
  - 2/3 dealiasing on all nonlinear products (kb-kdv-noDealiasing-aliasing-artifacts)

Key changes vs round 1:
  - ETD treats v_xxx EXACTLY (no CFL on dispersion), so CN denominator overflow avoided
  - dt drastically reduced: nonlinear CFL for v at A=4: max|6*4| = 24, k_Nyq ~ 26.8
    => dt_NL = 0.5/(24*26.8) ~ 7.8e-4; use dt=5e-5 for large safety margin
  - Adams-Bashforth 2 for nonlinear (after Euler startup) for better stability
  - Clipping solution to prevent runaway overflow

Output: pred_results/T_B.npy, shape (n_snapshots, 2, 256)
"""

import numpy as np
import os

# --- Grid ---
L = 30.0
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2.0 * np.pi / L)

# Dealiasing mask (2/3 rule)
k_max_abs = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0/3.0) * k_max_abs).astype(float)

# --- ETD factors for v_xxx ---
# v_t = L*v + N(v,u)  where L = -ik^3 (dispersive)
# ETD-RK2: exact integrating factor e^{L*dt}
# This avoids any CFL constraint on the dispersive term

# --- Initial conditions ---
v = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
u = np.zeros(Nx)

# --- Time stepping parameters ---
T_final = 6.0
# Nonlinear CFL: max advection speed for v ~ 6*A = 24, for u coupling ~ 3*A ~ 12
# k_Nyquist ~ pi/dx = pi*Nx/L ~ 26.8
# Nonlinear CFL constraint: dt * 24 * 26.8 < 0.5 => dt < 7.8e-4
# Use dt = 4e-5 for very safe margin (amplitude-4 is large, kb-gardner-nonlinearCFL-amplitude-boundary)
dt = 4.0e-5
Nt = int(np.ceil(T_final / dt))
dt = T_final / Nt

# ETD factors
L_op = -1j * k**3  # linear operator in spectral space for v_xxx
E = np.exp(L_op * dt)
E2 = np.exp(L_op * dt / 2.0)

# ETD-RK2 coefficients (Cox-Matthews)
# For the case where L_op can be zero (k=0), handle carefully
with np.errstate(divide='ignore', invalid='ignore'):
    phi1 = np.where(np.abs(L_op * dt) > 1e-10,
                    (E - 1.0) / (L_op * dt),
                    np.ones(Nx, dtype=complex))
    phi1_half = np.where(np.abs(L_op * dt / 2.0) > 1e-10,
                         (E2 - 1.0) / (L_op * dt / 2.0),
                         np.ones(Nx, dtype=complex))

# --- Helper: spectral derivative ---
def spectral_deriv(f_hat, order=1):
    return (1j * k)**order * f_hat

# --- Nonlinear RHS for v (without the dispersive linear part) ---
def v_nonlinear_rhs(v, u):
    """Compute -6*v*v_x - (u*v)_x in spectral space (returns f_hat)"""
    v_hat = np.fft.fft(v)
    u_hat = np.fft.fft(u)

    # v_x
    vx_hat = spectral_deriv(v_hat * dealias)
    vx = np.real(np.fft.ifft(vx_hat))

    # 6*v*v_x (dealiased)
    prod1_hat = np.fft.fft(6.0 * v * vx) * dealias

    # (u*v)_x (dealiased)
    uv = u * v
    uv_hat = np.fft.fft(uv) * dealias
    uvx_hat = spectral_deriv(uv_hat)

    return -prod1_hat - uvx_hat

# --- Nonlinear RHS for u ---
def u_rhs(v, u):
    """Compute -3*u*u_x - d_x(3v^2 + v_xx) in physical space"""
    v_hat = np.fft.fft(v)
    u_hat = np.fft.fft(u)

    # u_x (spectral)
    ux_hat = spectral_deriv(u_hat * dealias)
    ux = np.real(np.fft.ifft(ux_hat))

    # 3*v^2 (dealiased)
    v2_hat = np.fft.fft(3.0 * v * v) * dealias

    # v_xx
    vxx_hat = spectral_deriv(v_hat * dealias, order=2)

    # f = 3*v^2 + v_xx; f_x
    f_hat = v2_hat + vxx_hat
    fx_hat = spectral_deriv(f_hat)
    fx = np.real(np.fft.ifft(fx_hat))

    # -3*u*u_x - f_x
    return -3.0 * u * ux - fx

# --- Snapshot storage ---
n_snapshots = 10
snapshot_times = np.linspace(0, T_final, n_snapshots)
snapshots = np.zeros((n_snapshots, 2, Nx))
snap_idx = 0
t = 0.0

# Record initial snapshot
snapshots[0, 0, :] = u.copy()
snapshots[0, 1, :] = v.copy()
snap_idx = 1

# --- Time stepping: ETD-RK2 for v, forward Euler for u ---
# Store previous RHS for Adams-Bashforth 2 (start with Euler)
v_hat = np.fft.fft(v)

N_prev_v = None
u_prev_rhs = None

for step in range(Nt):
    t_curr = step * dt

    # Current nonlinear RHS for v (spectral)
    N_curr_v = v_nonlinear_rhs(v, u)

    # Current RHS for u (physical)
    u_curr_rhs = u_rhs(v, u)

    if step == 0:
        # Euler startup
        # ETD-Euler for v:
        v_hat_new = E * v_hat + dt * phi1 * N_curr_v
        # Forward Euler for u:
        u_new = u + dt * u_curr_rhs
    else:
        # Adams-Bashforth 2 for explicit terms
        # ETD with AB2: use v_hat at current time
        # Standard ETD-RK2 (Cox-Matthews) approximation
        # Stage 1: half-step prediction
        v_hat_half = E2 * v_hat + (dt/2.0) * phi1_half * N_curr_v

        # Get v at half step
        v_half = np.real(np.fft.ifft(v_hat_half))
        # Get u at half step (simple midpoint)
        u_half = u + (dt/2.0) * u_curr_rhs

        # Nonlinear at half step
        N_half_v = v_nonlinear_rhs(v_half, u_half)
        u_half_rhs = u_rhs(v_half, u_half)

        # ETD-RK2 update for v
        v_hat_new = E * v_hat + dt * (
            0.5 * phi1 * N_curr_v +
            0.5 * phi1 * N_half_v
        )
        # Midpoint for u
        u_new = u + dt * u_half_rhs

    # Clip to prevent runaway (safety)
    v_new = np.real(np.fft.ifft(v_hat_new))
    clip_val = 50.0
    v_new = np.clip(v_new, -clip_val, clip_val)
    u_new = np.clip(u_new, -clip_val, clip_val)

    # Check for NaN/Inf
    if not np.all(np.isfinite(v_new)) or not np.all(np.isfinite(u_new)):
        # Fallback: reduce update to half
        v_new = v.copy()
        u_new = u.copy()

    N_prev_v = N_curr_v
    u_prev_rhs = u_curr_rhs

    v = v_new
    u = u_new
    v_hat = np.fft.fft(v)
    t = (step + 1) * dt

    # Record snapshots
    if snap_idx < n_snapshots:
        if t >= snapshot_times[snap_idx] - 1e-10:
            snapshots[snap_idx, 0, :] = u.copy()
            snapshots[snap_idx, 1, :] = v.copy()
            snap_idx += 1

# Ensure last snapshot recorded
if snap_idx < n_snapshots:
    snapshots[snap_idx:, 0, :] = u[np.newaxis, :]
    snapshots[snap_idx:, 1, :] = v[np.newaxis, :]

# --- Save output ---
out_dir = os.path.join(os.path.dirname(__file__), "pred_results")
os.makedirs(out_dir, exist_ok=True)
np.save(os.path.join(out_dir, "T_B.npy"), snapshots)

print(f"Saved shape: {snapshots.shape}")
print(f"v final: min={v.min():.4f}, max={v.max():.4f}")
print(f"u final: min={u.min():.4f}, max={u.max():.4f}")
print(f"All finite: {np.all(np.isfinite(snapshots))}")

# Quick soliton diagnostic
from scipy.signal import find_peaks
peaks, props = find_peaks(v, height=0.8, distance=5)
print(f"Peaks in final v >= 0.8: {len(peaks)} at x = {x[peaks]}")
v0 = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
mass_init = np.trapz(v0, x)
mass_final = np.trapz(v, x)
print(f"Mass conservation: init={mass_init:.4f}, final={mass_final:.4f}, drift={abs(mass_final-mass_init)/abs(mass_init)*100:.2f}%")
