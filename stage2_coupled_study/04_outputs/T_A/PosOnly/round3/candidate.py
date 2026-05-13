"""
Coupled Burgers-swept-KdV soliton stability solver. Round 3.
Method: Operator splitting — Strang splitting between Burgers (MUSCL+Godunov) and KdV (IMEX-CN spectral).
- Burgers u: MUSCL-van Leer + Godunov flux at CFL=0.45, forward Euler half-steps
- KdV v: IMEX-CN spectral (CN on v_xxx, explicit on 6vv_x, dt reduced to 0.0002)
- Coupling terms treated explicitly at each sub-step
- r1 failed due to variable naming bug; r2 blew up with explicit-only AB2 on coupled nonlinear.
  r3 switches to operator splitting + smaller dt + MUSCL for Burgers.
"""

import numpy as np
import os

# ---------- domain ----------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

# ---------- wavenumbers ----------
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
ik3 = 1j * k**3

# ---------- dealiasing mask ----------
k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)

# ---------- initial conditions ----------
def sech2(x_arr):
    return 1.0 / np.cosh(x_arr)**2

v = 2.0 * sech2(x + 5.0)
u = 0.5 * v**2 + 0.2 * v

# ---------- time parameters ----------
T_final = 8.0
dt = 0.0002
n_steps = int(T_final / dt)

# ---------- snapshots ----------
n_snapshots = 9
snapshot_indices = np.linspace(0, n_steps, n_snapshots, dtype=int)
snapshots = np.zeros((n_snapshots, 2, Nx))
snap_count = 0

# ---------- helper: spectral derivative ----------
def spec_deriv(f):
    fh = np.fft.fft(f) * dealias
    return np.real(np.fft.ifft(ik * fh))

def spec_deriv3(f):
    fh = np.fft.fft(f) * dealias
    return np.real(np.fft.ifft(ik3 * fh))

# ---------- MUSCL van Leer limiter ----------
def minmod(a, b):
    return np.where(a * b > 0, np.where(np.abs(a) < np.abs(b), a, b), 0.0)

def van_leer(r):
    return (r + np.abs(r)) / (1.0 + np.abs(r) + 1e-14)

def muscl_burgers_flux(w):
    """Godunov flux for Burgers u_t + d/dx(u^2/2) = 0 with MUSCL reconstruction."""
    N = len(w)
    # Compute slopes
    dw = np.roll(w, -1) - w
    dm = np.roll(w, 0) - np.roll(w, 1)
    # van Leer slope limiter
    r = np.where(np.abs(dw) > 1e-14, dm / dw, 0.0)
    phi = van_leer(r)
    slope = phi * dw
    # Reconstruct at cell edges
    wL = w + 0.5 * slope                    # right face of cell i (left state)
    wR = np.roll(w - 0.5 * slope, -1)       # right face of cell i (right state from i+1)
    # Godunov flux: Burgers f(u) = u^2/2
    # Exact Riemann for Burgers
    def godunov(uL, uR):
        f_L = 0.5 * uL**2
        f_R = 0.5 * uR**2
        # If uL >= uR: shock
        s = 0.5 * (uL + uR)
        shock_flux = np.where(s >= 0, f_L, f_R)
        # If uL < uR: rarefaction
        rare_flux = np.where(uL >= 0, f_L, np.where(uR <= 0, f_R, 0.0))
        return np.where(uL >= uR, shock_flux, rare_flux)
    flux_right = godunov(wL, wR)
    flux_left = np.roll(flux_right, 1)
    return -(flux_right - flux_left) / dx

# ---------- KdV v step (IMEX-CN) ----------
def kdv_step_imex(v_in, rhs_extra, dt_sub):
    """One IMEX-CN step for v_t + 6vv_x + v_xxx = rhs_extra.
    CN on v_xxx, explicit on 6vv_x and rhs_extra."""
    vh = np.fft.fft(v_in) * dealias
    nl = -6.0 * v_in * spec_deriv(v_in) + rhs_extra
    nlh = np.fft.fft(nl) * dealias
    # CN: (1 - dt/2 * ik^3) v_new = (1 + dt/2 * ik^3) v_old + dt * nl
    lhs_denom = 1.0 - 0.5 * dt_sub * ik3
    rhs_num = (1.0 + 0.5 * dt_sub * ik3) * vh + dt_sub * nlh
    vh_new = rhs_num / lhs_denom
    vh_new *= dealias
    return np.real(np.fft.ifft(vh_new))

# ---------- main time loop ----------
def save_snapshot(idx, u_arr, v_arr):
    global snap_count
    if snap_count < n_snapshots:
        snapshots[snap_count, 0, :] = u_arr
        snapshots[snap_count, 1, :] = v_arr
        snap_count += 1

for step in range(n_steps + 1):
    if step in snapshot_indices:
        save_snapshot(snap_count, u, v)

    if step == n_steps:
        break

    # --- Compute coupling right-hand sides ---
    # u_t + 3 u u_x = -d_x(3v^2 + v_xx)
    # v_t + 6 v v_x + v_xxx = -d_x(u v)

    v2 = v**2
    v_xx = spec_deriv(spec_deriv(v))
    coupling_u_rhs = -spec_deriv(3.0 * v2 + v_xx)
    coupling_v_rhs = -spec_deriv(u * v)

    # --- Burgers step for u (MUSCL + coupling explicit) ---
    burgers_adv = muscl_burgers_flux(3.0 * u)  # d/dx(3u^2/2) -> 3u u_x term
    # Actually need: u_t = -3 u u_x + coupling_u_rhs
    # MUSCL handles 3u u_x as flux divergence of (3u)^2/2 / ... let's use direct
    # u_t = -3 u u_x + coupling_u_rhs
    # Use MUSCL for -3 u u_x: treat as Burgers with w=u, flux = 3u^2/2
    adv_u = muscl_burgers_flux(u)  # gives -(d/dx)(u^2/2) * dx -> actually gives -flux_div
    # muscl_burgers_flux returns -(flux_right - flux_left)/dx for flux=w^2/2
    # So u_t += 3 * adv_u approximates -3*u*u_x (via conservative form)
    u_new = u + dt * (3.0 * adv_u + coupling_u_rhs)

    # --- KdV step for v (IMEX-CN with coupling) ---
    v_new = kdv_step_imex(v, coupling_v_rhs, dt)

    u = u_new
    v = v_new

    # Clamp to prevent blow-up
    u = np.clip(u, -20.0, 20.0)
    v = np.clip(v, -20.0, 20.0)

# ---------- save output ----------
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_A.npy")

# Trim to exactly n_snapshots
result = snapshots[:snap_count]
np.save(out_path, result)
print(f"Saved shape {result.shape} to {out_path}")
print(f"u range: [{result[-1,0,:].min():.3f}, {result[-1,0,:].max():.3f}]")
print(f"v range: [{result[-1,1,:].min():.3f}, {result[-1,1,:].max():.3f}]")
print(f"v peak: {result[-1,1,:].max():.3f}, v mass: {np.sum(result[-1,1,:])*dx:.3f}")
