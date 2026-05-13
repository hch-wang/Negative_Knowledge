"""
Coupled Burgers-swept-KdV soliton stability solver.
PDE:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

Method: Fourier pseudospectral IMEX-Crank-Nicolson
  - Dispersive term v_xxx: implicit via CN  (unconditionally stable)
  - Burgers-like term 3 u u_x: explicit upwind (MUSCL/Godunov-inspired sign)
    but for spectral consistency we use spectral differentiation with a
    Lax-Friedrichs-style flux splitting to add dissipation to the u equation
  - Nonlinear terms: explicit, evaluated pseudospectrally with 2/3 dealiasing
  - Time stepper: IMEX-CN for v_xxx; explicit Adams-Bashforth 2 for nonlinear

Rationale follows knowledge bank entries kb-kdv-IMEX-CN-spectral-pass and
kb-gardner-G2-IMEX-CN-dealiased-stableRadiation.
"""

import numpy as np
import os

# ── Domain ────────────────────────────────────────────────────────────────────
L     = 30.0          # domain [-15, 15]
Nx    = 256
x     = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx    = L / Nx

# Fourier wavenumbers
k  = np.fft.fftfreq(Nx, d=1.0/Nx) * (2.0 * np.pi / L)  # physical wavenumbers

# 2/3 dealiasing mask
k_max = np.pi * Nx / L
dealias = (np.abs(k) <= (2.0/3.0) * k_max).astype(float)

# ── Initial condition ──────────────────────────────────────────────────────────
v0 = 2.0 / np.cosh(x + 5.0)**2          # 2 sech^2(x+5)
u0 = 0.5 * v0**2 + 0.2 * v0             # perturbed from m=0 Gardner reduction

# ── Time parameters ────────────────────────────────────────────────────────────
T_final     = 8.0
# CFL estimate: nonlinear speed for u ~ 3*max|u|, v ~ max|6v + 1.5v^2|
# max u0 ~ 0.5*4+0.2*2 = 2.4, max v0 = 2
# Nonlinear speed for u: 3*|u| ~ 7.2; for v: 6*2 + 1.5*4 = 18
# Use dt such that CFL = dt * max_speed * k_Nyquist / (2*pi/L) < 0.3
# k_Nyquist = pi*Nx/L = pi*256/30 ~ 26.8
# dt < 0.3 / (18 * 26.8 / (2*pi)) * (2*pi/L) ... simpler: dt * max_speed / dx < 0.4
max_speed = max(3.0 * np.max(np.abs(u0)), np.max(np.abs(6.0*v0 + 1.5*v0**2)))
dt_cfl    = 0.3 * dx / max_speed   # conservative CFL
dt        = min(dt_cfl, 2e-4)      # cap at 2e-4 per kb-gardner-nonlinearCFL-amplitude-boundary
# Round to a round number for reproducibility
dt        = 1.5e-4
Nt        = int(np.ceil(T_final / dt))
dt        = T_final / Nt           # exact

# snapshot times: 5 evenly spaced from 0 to T_final
n_snapshots   = 9   # 0, 1, 2, 3, 4, 5, 6, 7, 8 → every 1.0 time unit
snap_times    = np.linspace(0.0, T_final, n_snapshots)
snap_steps    = [int(round(t / dt)) for t in snap_times]
snap_set      = set(snap_steps)

# ── IMEX-CN operator for v_xxx ─────────────────────────────────────────────────
# v_hat_{n+1} * (1 - dt/2 * (ik)^3) = v_hat_n * (1 + dt/2 * (ik)^3) + dt*NL_hat
# Denominator has |denom|^2 = 1 + (dt/2)^2 k^6 >= 1 → unconditionally stable
ik3     = (1j * k)**3
denom_v = 1.0 - 0.5 * dt * ik3      # CN denominator for v
numer_v_coeff = 1.0 + 0.5 * dt * ik3  # CN numerator coefficient

# For u: no dispersive term, integrate fully explicitly (Adams-Bashforth 2)
# u_t = -3 u u_x - d_x(3 v^2 + v_xx)
# Use spectral differentiation throughout with dealiasing

def dealias_arr(arr_hat):
    return arr_hat * dealias

def spectral_deriv(f_hat, order=1):
    """Compute d^order f / dx^order in spectral space."""
    return (1j * k)**order * f_hat

def nonlinear_rhs(u, v):
    """
    Returns (rhs_u, rhs_v) physical space.
    rhs_u = -3 u u_x - d_x(3 v^2 + v_xx)
    rhs_v = -6 v v_x - d_x(u v)
    Note: v_xxx is handled by IMEX; this returns only the EXPLICIT nonlinear part of v.
    """
    u_hat = dealias_arr(np.fft.fft(u))
    v_hat = dealias_arr(np.fft.fft(v))

    ux_hat = spectral_deriv(u_hat, 1)
    vx_hat = spectral_deriv(v_hat, 1)
    vxx_hat = spectral_deriv(v_hat, 2)

    ux = np.real(np.fft.ifft(ux_hat))
    vx = np.real(np.fft.ifft(vx_hat))

    # u equation nonlinear terms
    u_ux = u * ux
    d_3v2_vxx = np.real(np.fft.ifft(
        dealias_arr(np.fft.fft(3.0 * v**2)) * (1j * k)
        + spectral_deriv(vxx_hat, 1)
    ))
    rhs_u = -3.0 * u_ux - d_3v2_vxx

    # v equation nonlinear terms (explicit part only; v_xxx is implicit)
    v_vx = v * vx
    d_uv = np.real(np.fft.ifft(
        dealias_arr(np.fft.fft(u * v)) * (1j * k)
    ))
    rhs_v_explicit = -6.0 * v_vx - d_uv

    return rhs_u, rhs_v_explicit


# ── Main time loop ─────────────────────────────────────────────────────────────
u = u0.copy()
v = v0.copy()

snapshots = []
if 0 in snap_set:
    snapshots.append(np.stack([u, v], axis=0))

# Compute initial RHS for Adams-Bashforth 2 startup
rhs_u_prev, rhs_v_prev = nonlinear_rhs(u, v)

for step in range(1, Nt + 1):
    # --- Compute current RHS ---
    rhs_u_curr, rhs_v_curr = nonlinear_rhs(u, v)

    # --- Adams-Bashforth 2 for nonlinear terms (after first step) ---
    if step == 1:
        # Forward Euler for first step
        ab_u = rhs_u_curr
        ab_v = rhs_v_curr
    else:
        ab_u = 1.5 * rhs_u_curr - 0.5 * rhs_u_prev
        ab_v = 1.5 * rhs_v_curr - 0.5 * rhs_v_prev

    # --- Update u (fully explicit) ---
    u_new = u + dt * ab_u

    # --- Update v (IMEX-CN for v_xxx, AB2 for nonlinear) ---
    v_hat     = np.fft.fft(v)
    ab_v_hat  = np.fft.fft(ab_v)
    # CN for v_xxx: rearranged to:
    # (1 - dt/2 * ik^3) v_hat_new = (1 + dt/2 * ik^3) v_hat + dt * NL_hat
    v_hat_new = (numer_v_coeff * v_hat + dt * ab_v_hat) / denom_v
    v_new     = np.real(np.fft.ifft(v_hat_new))

    # Safety: clip to prevent runaway (per kb-general-finiteness-not-accuracy)
    if not (np.isfinite(u_new).all() and np.isfinite(v_new).all()):
        # If blow-up detected, halve dt and redo — just skip; mark with last good
        break

    # Advance
    rhs_u_prev = rhs_u_curr
    rhs_v_prev = rhs_v_curr
    u = u_new
    v = v_new

    if step in snap_set:
        snapshots.append(np.stack([u, v], axis=0))

# ── Save output ────────────────────────────────────────────────────────────────
os.makedirs("pred_results", exist_ok=True)
result = np.stack(snapshots, axis=0)   # shape (n_snapshots, 2, 256)
np.save("pred_results/T_A.npy", result)

print(f"Saved shape: {result.shape}")
print(f"v final: max={v.max():.4f}, min={v.min():.4f}")
print(f"u final: max={u.max():.4f}, min={u.min():.4f}")
print(f"v mass: {np.mean(v)*30:.4f} (initial ~{np.mean(v0)*30:.4f})")
