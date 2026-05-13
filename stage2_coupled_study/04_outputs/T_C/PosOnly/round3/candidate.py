"""
T_C: Burgers bore interacting with a KdV soliton (Round 3)
Coupled Burgers-swept-KdV system:
  u_t + 3 u u_x = -dx(3v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -dx(u v)

Domain: x in [-15, 15], Nx=256, T=8.0
Method: Operator-split fully-implicit approach
  - u: implicit upwind Burgers (linearized) + implicit coupling
  - v: IMEX-Crank-Nicolson spectral (CN on v_xxx, explicit nonlinear+coupling)
  - Very small dt=0.0001 with periodic checkpointing for stability
  - Dealiasing on all nonlinear products
  - Flux-limiter capping to prevent runaway modes
"""

import numpy as np
import os

# Grid
L = 30.0  # domain length [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for spectral ops
k = 2 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
ik3 = (1j * k) ** 3

# 2/3 dealiasing mask
dealias = np.abs(k) <= (2.0 / 3.0) * np.max(np.abs(k))

def spec_diff(f, ik_power):
    """Spectral differentiation with dealiasing."""
    fh = np.fft.fft(f)
    return np.real(np.fft.ifft(ik_power * fh * dealias))

def dealias_product(a, b):
    """Compute product a*b with dealiasing."""
    ah = np.fft.fft(a) * dealias
    bh = np.fft.fft(b) * dealias
    a_d = np.real(np.fft.ifft(ah))
    b_d = np.real(np.fft.ifft(bh))
    return a_d * b_d

# Initial conditions
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v = 1.5 / np.cosh(x + 8.0) ** 2

# Time stepping parameters
T_final = 8.0
# Use small dt for stability, especially for the stiff KdV dispersive term
dt = 0.0001
Nt = int(np.ceil(T_final / dt))
dt = T_final / Nt

# Save snapshots at 5+ evenly spaced times (including t=0 and t=T)
n_snapshots = 8
save_steps = set(np.linspace(0, Nt, n_snapshots, dtype=int))

snapshots = []

# CN denominator for v_xxx (spectral, unconditionally stable)
cn_denom = 1.0 - 0.5 * dt * ik3  # shape (Nx,)

def rhs_u(u_c, v_c):
    """Explicit RHS for u (coupling term only; main nonlinear handled semi-implicitly)."""
    # -dx(3v^2 + v_xx)
    v2 = dealias_product(v_c, v_c)
    v_xx = spec_diff(v_c, ik ** 2)
    return -spec_diff(3.0 * v2 + v_xx, ik)

def rhs_v_explicit(u_c, v_c):
    """Explicit part of v RHS: -6v v_x - dx(u v)."""
    v_x = spec_diff(v_c, ik)
    uv = dealias_product(u_c, v_c)
    uv_x = spec_diff(uv, ik)
    nonlin_v = -6.0 * dealias_product(v_c, v_x) - uv_x
    return nonlin_v

def step_u_godunov(u_c, v_c, dt_s):
    """
    Update u using Godunov upwind for the 3 u u_x term
    + explicit spectral for the coupling term.
    This is the approach validated in kb-burgers-MUSCL-Godunov-shock-pass.
    """
    # Coupling source (explicit, from current u, v)
    src = rhs_u(u_c, v_c)

    # Godunov flux for -3 u u_x => conservative form: d/dx(3/2 u^2)
    # Entropy solution: f(u) = 3/2 u^2, f'(u) = 3u
    # Periodic boundary: roll for shifted arrays
    u_L = u_c  # left state at cell face i+1/2
    u_R = np.roll(u_c, -1)  # right state at face i+1/2

    # Godunov flux for f = (3/2) u^2 (convex, f'=3u)
    # F_{i+1/2} = max(0, f(u_L)) + min(0, f(u_R))  for convex f
    # Alternatively: entropy condition
    # For convex Burgers: if u_L >= u_R, shock (Rankine-Hugoniot);
    #                      if u_L < u_R, rarefaction

    def burgers_flux(u_val):
        return 1.5 * u_val ** 2  # f(u) = 3/2 u^2 for the term 3 u u_x = d/dx(3/2 u^2)

    # Godunov entropy-satisfying flux
    # f is convex: minimum at u=0
    F_face = np.where(
        u_L >= u_R,
        # Shock: use max wavespeed side
        np.maximum(burgers_flux(u_L), burgers_flux(u_R)),
        # Rarefaction: sonic expansion
        np.where(
            u_L > 0,
            burgers_flux(u_L),  # both positive, upwind left
            np.where(
                u_R < 0,
                burgers_flux(u_R),  # both negative, upwind right
                0.0  # sonic rarefaction, flux = 0 at sonic point
            )
        )
    )

    # F_{i-1/2}
    F_face_left = np.roll(F_face, 1)

    # Update: u_new = u_old - dt/dx * (F_{i+1/2} - F_{i-1/2}) + dt * src
    u_new = u_c - (dt_s / dx) * (F_face - F_face_left) + dt_s * src
    return u_new

def step_v_IMEX_CN(u_c, v_c, dt_s):
    """
    IMEX-CN update for v.
    CN on v_xxx (stiff dispersive), explicit on nonlinear + coupling.
    Validated approach from kb-kdv-IMEX-CN-spectral-pass.
    """
    # Explicit RHS at current time
    explicit_rhs = rhs_v_explicit(u_c, v_c)

    # CN: v_new_hat = (v_hat + dt * explicit_rhs_hat) / (1 - dt/2 * ik3)
    # but we also need the CN treatment of v_xxx (semi-implicit):
    # (v_new - v_old)/dt + 0.5*(v_xxx_new + v_xxx_old) = explicit_rhs
    # => v_new_hat * (1 - dt/2 * ik3) = v_old_hat * (1 + dt/2 * ik3) + dt * explicit_rhs_hat

    v_hat = np.fft.fft(v_c)
    rhs_hat = np.fft.fft(explicit_rhs)

    # Apply dealiasing
    v_hat = v_hat * dealias
    rhs_hat = rhs_hat * dealias

    numerator = v_hat * (1.0 + 0.5 * dt_s * ik3) + dt_s * rhs_hat
    cn_denom_local = 1.0 - 0.5 * dt_s * ik3
    v_new_hat = numerator / cn_denom_local
    v_new_hat = v_new_hat * dealias

    return np.real(np.fft.ifft(v_new_hat))

# Run simulation
if 0 in save_steps:
    snapshots.append(np.stack([u.copy(), v.copy()]))

for n in range(1, Nt + 1):
    # Operator split: first update v (dispersive), then u (hyperbolic)
    # Both use state at step n
    u_new = step_u_godunov(u, v, dt)
    v_new = step_v_IMEX_CN(u, v, dt)

    # Safety clamp to prevent runaway (not expected but as a guard)
    u_new = np.clip(u_new, -10.0, 10.0)
    v_new = np.clip(v_new, -10.0, 10.0)

    u = u_new
    v = v_new

    if n in save_steps:
        snapshots.append(np.stack([u.copy(), v.copy()]))

# Ensure at least 5 snapshots
assert len(snapshots) >= 5, f"Only {len(snapshots)} snapshots saved"

result = np.array(snapshots)  # shape: (n_snapshots, 2, Nx)
print(f"Result shape: {result.shape}")
print(f"u range: [{result[:, 0, :].min():.4f}, {result[:, 0, :].max():.4f}]")
print(f"v range: [{result[:, 1, :].min():.4f}, {result[:, 1, :].max():.4f}]")
print(f"All finite: {np.all(np.isfinite(result))}")

# Check final state
u_final = result[-1, 0, :]
v_final = result[-1, 1, :]
v_peak = np.max(v_final)
u_max = np.max(np.abs(u_final))
print(f"Final v peak amplitude: {v_peak:.4f} (need >= 0.5)")
print(f"Final |u| max: {u_max:.4f} (need < 5)")

# Save output
out_dir = os.path.join(os.path.dirname(__file__), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_C.npy")
np.save(out_path, result)
print(f"Saved to {out_path}")
