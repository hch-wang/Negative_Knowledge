"""
Coupled Burgers-swept-KdV solver for bore-soliton interaction (Task T_C).

PDE:
  u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx (u v)

Domain: x in [-15, 15], periodic, Nx=256
T = 8.0, save 9 snapshots.

Numerical scheme:
  - u equation: MUSCL-van Leer + Godunov flux for the 3 u u_x term (hyperbolic, shock-bearing),
    explicit Euler for the RHS source -d/dx(3v^2 + v_xx) via spectral differentiation.
  - v equation: IMEX-Crank-Nicolson spectral:
    * v_xxx treated implicitly (CN denominator), unconditionally stable.
    * 6 v v_x + v_xxx coupling + d/dx(uv) treated explicitly.
    * 2/3 dealiasing on all nonlinear terms.
"""

import numpy as np
import os

# ── Grid ──────────────────────────────────────────────────────────────────────
L = 30.0          # domain length [-15, 15]
Nx = 256
dx = L / Nx
x = -15.0 + dx * np.arange(Nx)

# ── Spectral helpers ──────────────────────────────────────────────────────────
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)   # wavenumbers

def spec_deriv(f, order=1):
    """Spectral derivative of f, order=1 or 3."""
    fhat = np.fft.fft(f)
    return np.real(np.fft.ifft((1j * k)**order * fhat))

# 2/3 dealiasing mask
dealias_mask = np.zeros(Nx, dtype=bool)
dealias_mask[np.abs(k) <= (2.0/3.0) * np.max(np.abs(k))] = True

def nonlinear_dealiased(f, g_x):
    """Dealiased version of f * g_x (both already in physical space)."""
    fhat = np.fft.fft(f)
    gxhat = np.fft.fft(g_x)
    fhat[~dealias_mask] = 0.0
    gxhat[~dealias_mask] = 0.0
    return np.real(np.fft.ifft(fhat)) * np.real(np.fft.ifft(gxhat))

def dealiased_deriv_of_product(f, g):
    """Compute d/dx(f*g) spectrally with 2/3 dealiasing."""
    fhat = np.fft.fft(f)
    ghat = np.fft.fft(g)
    fhat[~dealias_mask] = 0.0
    ghat[~dealias_mask] = 0.0
    fd = np.real(np.fft.ifft(fhat))
    gd = np.real(np.fft.ifft(ghat))
    prod = fd * gd
    return np.real(np.fft.ifft(1j * k * np.fft.fft(prod)))

# ── MUSCL-van Leer + Godunov for Burgers-like term ───────────────────────────
def minmod(a, b):
    return np.where(a * b > 0, np.where(np.abs(a) < np.abs(b), a, b), 0.0)

def van_leer(r):
    return (r + np.abs(r)) / (1.0 + np.abs(r) + 1e-30)

def muscl_godunov_burgers_flux(u, coeff=3.0):
    """
    Compute finite-volume flux for coeff * u * u_x  (= d/dx(coeff/2 * u^2)).
    Uses MUSCL reconstruction with van Leer limiter + Godunov (exact Riemann).
    Returns du/dt contribution (already divided by dx).
    """
    # MUSCL slope reconstruction
    du = np.roll(u, -1) - u        # u_{i+1} - u_i
    du_back = u - np.roll(u, 1)    # u_i - u_{i-1}

    # van Leer limiter
    r = du_back / (du + np.sign(du + 1e-30) * 1e-14)
    phi = van_leer(r)
    slope = phi * du

    # Interface reconstructions: u_L at i+1/2, u_R at i+1/2
    u_L = u + 0.5 * slope
    u_R = np.roll(u + 0.5 * slope - slope, -1)
    # Actually: u_R_{i+1/2} = left value from cell i+1: u[i+1] - 0.5*slope[i+1]
    slope_right = np.roll(slope, -1)
    u_R = np.roll(u, -1) - 0.5 * slope_right

    # Godunov flux for f(u) = coeff/2 * u^2
    def godunov_flux(uL, uR):
        f_L = coeff / 2.0 * uL**2
        f_R = coeff / 2.0 * uR**2
        # Entropy fix: flux is max of f(u) between uL and uR at the sonic point
        # Exact Godunov: sonic point at u=0
        flux = np.where(
            uL >= uR,
            # Shock: Rankine-Hugoniot wave speed s = coeff*(uL+uR)/2
            np.where(uL + uR >= 0, f_L, f_R),
            # Rarefaction
            np.where(uL >= 0, f_L, np.where(uR <= 0, f_R, 0.0))
        )
        return flux

    F = godunov_flux(u_L, u_R)        # F_{i+1/2}
    F_back = np.roll(F, 1)            # F_{i-1/2}
    return -(F - F_back) / dx

# ── Initial conditions ────────────────────────────────────────────────────────
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v = 1.5 / np.cosh(x + 8.0)**2

# ── Time integration parameters ──────────────────────────────────────────────
T_final = 8.0
# Choose dt based on CFL and nonlinear stability.
# Burgers CFL: dt * max(3*|u|) / dx < 0.45  => dt < 0.45*dx/(3*1.5) ~ 0.003
# KdV nonlinear CFL (from memory kb-gardner-nonlinearCFL-amplitude-boundary):
#   dt * max(6*A + 1.5*A^2) * k_Nyq < O(1)  => at A=1.5: 12.4, k_Nyq~27 => dt < ~0.003
# Use dt = 0.001 for safety.
dt = 0.001
n_steps = int(np.ceil(T_final / dt))
dt = T_final / n_steps

# Snapshot times: 9 snapshots spread over [0, T_final]
n_snapshots = 9
snap_indices = np.linspace(0, n_steps, n_snapshots, dtype=int)
snap_indices[-1] = n_steps

# Storage
snapshots = np.zeros((n_snapshots, 2, Nx))
snap_idx = 0

# IMEX-CN denominator for v_xxx: (1 + dt/2 * (ik)^3) ... wait, CN:
# v_hat^{n+1} / (1 - dt/2 * (ik)^3) - v_hat^n = dt * [explicit terms]
# Dispersive term: -v_xxx  =>  Fourier: -(ik)^3 v_hat = -ik^3 v_hat (note k real => (ik)^3 = i*k^3)
# CN: (v^{n+1} - v^n)/dt = -(1/2)(v_xxx^{n+1} + v_xxx^n) + NL
# => v_hat^{n+1} (1 + dt/2 * ik^3) = v_hat^n (1 - dt/2 * ik^3) + dt * NL_hat
# Wait: v_t + v_xxx = NL  =>  v_xxx appears on the left side as stiffness
# The sign: v_t = -v_xxx + NL
# CN: (v^{n+1} - v^n)/dt = -(1/2)(v_xxx^{n+1} + v_xxx^n) + NL_exp
# FT: (v_hat^{n+1} - v_hat^n)/dt = -(1/2)((ik)^3 v_hat^{n+1} + (ik)^3 v_hat^n) + NL_hat
# v_hat^{n+1} [1 + dt/2 * (ik)^3] = v_hat^n [1 - dt/2 * (ik)^3] + dt * NL_hat
# (ik)^3 = i^3 k^3 = -ik^3   (for real k)
cn_denom = 1.0 + dt / 2.0 * (-1j * k**3)   # = 1 - i*dt/2*k^3
cn_numer_factor = 1.0 - dt / 2.0 * (-1j * k**3)  # = 1 + i*dt/2*k^3

def explicit_rhs_v(u_, v_):
    """
    Explicit (nonlinear) RHS for v equation, with 2/3 dealiasing.
    v_t + 6vv_x + v_xxx = -d/dx(uv)
    => after moving v_xxx implicit:
    NL = -6vv_x - d/dx(uv)
    """
    # Dealiased v_x
    vhat = np.fft.fft(v_)
    vhat_d = vhat.copy(); vhat_d[~dealias_mask] = 0.0
    v_x = np.real(np.fft.ifft(1j * k * vhat_d))
    vd = np.real(np.fft.ifft(vhat_d))

    # 6 v v_x (dealiased)
    term1 = -6.0 * dealiased_product_times_vx(v_, v_x)

    # d/dx(u*v) (dealiased)
    term2 = -dealiased_deriv_of_product(u_, v_)

    return term1 + term2

def dealiased_product_times_vx(v_, v_x_):
    """v * v_x with dealiasing applied to v before multiplying."""
    vhat = np.fft.fft(v_); vhat[~dealias_mask] = 0.0
    v_d = np.real(np.fft.ifft(vhat))
    vxhat = np.fft.fft(v_x_); vxhat[~dealias_mask] = 0.0
    vx_d = np.real(np.fft.ifft(vxhat))
    return v_d * vx_d

def step(u_, v_):
    """One time step."""
    # ── u equation ─────────────────────────────────────────────────────────
    # u_t + 3 u u_x = -d/dx(3v^2 + v_xx)
    # Hyperbolic part via MUSCL-Godunov, source term via spectral.

    adv_u = muscl_godunov_burgers_flux(u_, coeff=3.0)

    # Source: -d/dx(3v^2 + v_xx)
    v2 = v_**2
    v_xx = spec_deriv(v_, order=2)
    src_u = -spec_deriv(3.0 * v2 + v_xx, order=1)

    u_new = u_ + dt * (adv_u + src_u)

    # ── v equation (IMEX-CN) ─────────────────────────────────────────────────
    # v_t = -v_xxx - 6vv_x - d/dx(uv)
    # CN on v_xxx, explicit on nonlinear terms.
    NL_v = explicit_rhs_v(u_, v_)

    vhat = np.fft.fft(v_)
    rhs_hat = cn_numer_factor * vhat + dt * np.fft.fft(NL_v)
    v_hat_new = rhs_hat / cn_denom
    v_new = np.real(np.fft.ifft(v_hat_new))

    return u_new, v_new

# ── Main time loop ─────────────────────────────────────────────────────────────
for step_i in range(n_steps + 1):
    if snap_idx < n_snapshots and step_i == snap_indices[snap_idx]:
        snapshots[snap_idx, 0, :] = u
        snapshots[snap_idx, 1, :] = v
        snap_idx += 1

    if step_i < n_steps:
        u, v = step(u, v)

# ── Save ──────────────────────────────────────────────────────────────────────
out_dir = os.path.join(
    "${REPO_ROOT}/paper/experiments/"
    "pde_pilot_2026-05-11/stage2/runs/T_C/PosNeg/round1",
    "pred_results"
)
os.makedirs(out_dir, exist_ok=True)
np.save(os.path.join(out_dir, "T_C.npy"), snapshots)
print(f"Saved snapshots shape {snapshots.shape} to {out_dir}/T_C.npy")
print(f"Final u: min={u.min():.4f}, max={u.max():.4f}")
print(f"Final v: min={v.min():.4f}, max={v.max():.4f}, peak={v.max():.4f}")
