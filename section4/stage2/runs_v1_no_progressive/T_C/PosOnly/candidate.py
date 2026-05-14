"""
T_C: Burgers bore interacting with a KdV soliton
Coupled system:
  u_t + 3 u u_x = -d/dx(3v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx(u v)

Method (E1):
  - Operator splitting: Strang split each full dt
  - Burgers (u) equation: MUSCL-van Leer + Godunov flux + Forward Euler (CFL-limited)
  - KdV/swept-KdV (v) equation: IMEX-CN spectral with 2/3 dealiasing
  - Coupling terms handled explicitly in each half-step

Domain: x in [-15, 15], Nx=256, T=8.0
Save 9 snapshots (including t=0 and t=T)
"""

import numpy as np
import os

# ---- Grid setup ----
L = 30.0  # domain length
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = x[1] - x[0]
T_final = 8.0
n_snapshots = 9  # 0, 1, 2, 3, 4, 5, 6, 7, 8

# ---- Wavenumbers for spectral v-equation ----
k = 2 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)

# 2/3 dealiasing mask
dealias_mask = np.abs(k) <= (2.0/3.0) * np.max(np.abs(k))

# ---- Initial conditions ----
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0   # smoothed bore
v = 1.5 / np.cosh(x + 8)**2                  # KdV soliton at x=-8

# ---- Time parameters ----
dt_target = 0.001
t = 0.0

# ---- Snapshot storage ----
snapshot_times = np.linspace(0, T_final, n_snapshots)
snapshots = []

def save_snapshot(u, v):
    snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

save_snapshot(u, v)
next_snap_idx = 1

# ---- MUSCL-van Leer limiter ----
def van_leer(r):
    """Van Leer flux limiter."""
    phi = (r + np.abs(r)) / (1.0 + np.abs(r) + 1e-14)
    return phi

def burgers_godunov_flux(u):
    """Godunov flux for Burgers: f(u) = u^2/2, multiplied by 3 to match 3*u*u_x."""
    # f(u) = (3/2)*u^2 so flux = (3/2)*u^2
    # Godunov: f*(u_L, u_R) = max(f(max(u_L,0)), f(min(u_R,0))) if u_L <= u_R
    #                       = f(u_L) if u_L >= u_R (both same sign or upwind)
    # Exact Riemann: shock if u_L > u_R, rarefaction if u_L < u_R
    u_L = u
    u_R = np.roll(u, -1)

    # Entropy fix: Godunov for convex flux f(u) = (3/2)*u^2
    # Characteristic speed s = 3*u (since (3u^2/2)' = 3u)
    # If u_L > u_R: shock at s = (3/2)*(u_L + u_R)
    # If u_L <= u_R: rarefaction - use entropy solution

    # f(u) = (3/2)*u^2
    f_L = 1.5 * u_L**2
    f_R = 1.5 * u_R**2

    # Shock condition: u_L > u_R (both considered as neighboring cells)
    shock_mask = u_L >= u_R

    # Shock flux: upwind based on shock speed s = (3/2)*(u_L + u_R)
    s_shock = 1.5 * (u_L + u_R)
    flux_shock = np.where(s_shock >= 0, f_L, f_R)

    # Rarefaction flux: entropy solution
    # f* = f(u_L) if 3*u_L >= 0 (all chars from left go right)
    # f* = f(u_R) if 3*u_R <= 0 (all chars from right go left)
    # f* = 0 if 3*u_L < 0 < 3*u_R (sonic point u=0 between them)
    flux_raref = np.where(u_L >= 0, f_L, np.where(u_R <= 0, f_R, 0.0))

    return np.where(shock_mask, flux_shock, flux_raref)

def muscl_reconstruct(u):
    """MUSCL reconstruction with van Leer limiter.
    Returns u_L (left face value using right-biased reconstruction of cell i)
            u_R (right face value using left-biased reconstruction of cell i+1)
    """
    # Slopes
    du_left  = u - np.roll(u, 1)   # u_i - u_{i-1}
    du_right = np.roll(u, -1) - u  # u_{i+1} - u_i

    # Van Leer limiter
    r = np.where(np.abs(du_left) > 1e-14, du_right / (du_left + 1e-30), 0.0)
    phi = van_leer(r)
    slope = phi * du_left

    # Reconstructed values at i+1/2
    u_L = u + 0.5 * slope           # left state at i+1/2 (from cell i)
    u_R = np.roll(u - 0.5 * slope, -1)  # right state at i+1/2 (from cell i+1)

    return u_L, u_R

def godunov_flux_muscl(u_L, u_R):
    """Godunov flux for 3*u*u_x term (f = (3/2)*u^2) with MUSCL states."""
    f_L = 1.5 * u_L**2
    f_R = 1.5 * u_R**2

    shock_mask = u_L >= u_R

    s_shock = 1.5 * (u_L + u_R)
    flux_shock = np.where(s_shock >= 0, f_L, f_R)

    flux_raref = np.where(u_L >= 0, f_L, np.where(u_R <= 0, f_R, 0.0))

    return np.where(shock_mask, flux_shock, flux_raref)

def spectral_deriv(f, k):
    """Compute df/dx using spectral (FFT) differentiation."""
    fh = np.fft.fft(f)
    return np.real(np.fft.ifft(1j * k * fh))

def spectral_deriv3(f, k):
    """Compute d^3f/dx^3 using spectral differentiation."""
    fh = np.fft.fft(f)
    return np.real(np.fft.ifft((1j * k)**3 * fh))

def spectral_deriv2(f, k):
    """Compute d^2f/dx^2 using spectral differentiation."""
    fh = np.fft.fft(f)
    return np.real(np.fft.ifft(-k**2 * fh))

def compute_rhs_u(u, v, k, dealias_mask):
    """
    RHS for u-equation: -3*u*u_x - d/dx(3v^2 + v_xx)
    = -(d/dx)(3u^2/2) - 3*d/dx(v^2) - d/dx(v_xx)
    We split this:
      - hyperbolic part: -3*u*u_x (handled by MUSCL-Godunov)
      - coupling source: -d/dx(3v^2 + v_xx) (spectral)
    """
    # Coupling source term (spectral)
    v2 = v**2
    v2h = np.fft.fft(v2)
    v2h_da = v2h * dealias_mask
    v2_da = np.real(np.fft.ifft(v2h_da))

    d_dx_3v2 = 3.0 * spectral_deriv(v2_da, k)

    vh = np.fft.fft(v)
    vxx = np.real(np.fft.ifft(-k**2 * vh * dealias_mask))
    d_dx_vxx = spectral_deriv(vxx, k)

    coupling_u = -(d_dx_3v2 + d_dx_vxx)
    return coupling_u

def compute_rhs_v_nonlinear(u, v, k, dealias_mask):
    """
    Explicit (nonlinear) part of v-equation RHS:
    -6*v*v_x - d/dx(u*v)
    (v_xxx handled implicitly by CN)
    """
    # 6v*v_x = 3 * d/dx(v^2)
    vh = np.fft.fft(v)
    v2 = v**2
    v2h = np.fft.fft(v2) * dealias_mask
    d_dx_v2 = np.real(np.fft.ifft(1j * k * v2h))
    nonlin_v = -3.0 * d_dx_v2

    # coupling: -d/dx(u*v)
    uv = u * v
    uvh = np.fft.fft(uv) * dealias_mask
    d_dx_uv = np.real(np.fft.ifft(1j * k * uvh))
    coupling_v = -d_dx_uv

    return nonlin_v + coupling_v

def step_u_muscl(u, v, dt_step, k, dealias_mask, dx):
    """
    Full u-equation step using MUSCL-Godunov for hyperbolic part + spectral coupling.
    Forward Euler time integration with CFL-limited dt.
    """
    # MUSCL reconstruction
    u_L, u_R = muscl_reconstruct(u)
    flux_hydro = godunov_flux_muscl(u_L, u_R)

    # d/dx flux term for -3*u*u_x: -(flux_{i+1/2} - flux_{i-1/2})/dx
    rhs_hyperbolic = -(flux_hydro - np.roll(flux_hydro, 1)) / dx

    # Coupling source (spectral)
    coupling = compute_rhs_u(u, v, k, dealias_mask)

    u_new = u + dt_step * (rhs_hyperbolic + coupling)
    return u_new

def step_v_imex_cn(u, v, dt_step, k, dealias_mask):
    """
    IMEX-CN step for v-equation:
    v_t = -v_xxx - 6*v*v_x - d/dx(uv)
    CN on v_xxx (implicit), explicit on rest.
    (v^{n+1} - v^n)/dt = -(1/2)(v_xxx^{n+1} + v_xxx^n) + Explicit^n
    => (1 + dt/2 * ik^3) v_hat^{n+1} = (1 - dt/2 * ik^3) v_hat^n + dt * Explicit^n_hat
    """
    vh = np.fft.fft(v)

    # Explicit nonlinear terms
    explicit_rhs = compute_rhs_v_nonlinear(u, v, k, dealias_mask)
    explicit_hat = np.fft.fft(explicit_rhs) * dealias_mask

    # CN time step in spectral space
    lhs_denom = 1.0 + 0.5 * dt_step * (1j * k)**3
    rhs_num = (1.0 - 0.5 * dt_step * (1j * k)**3) * vh + dt_step * explicit_hat

    vh_new = rhs_num / lhs_denom
    vh_new *= dealias_mask  # Apply dealiasing to solution

    v_new = np.real(np.fft.ifft(vh_new))
    return v_new

# ---- Main time integration (Strang splitting) ----
t = 0.0
snap_idx = 1

while t < T_final - 1e-10:
    dt_step = min(dt_target, T_final - t)

    # Strang split: U(dt/2) -> V(dt) -> U(dt/2)
    # But we need CFL check for u-step
    # CFL for Burgers: s_max = 3 * max|u|
    s_max = 3.0 * np.max(np.abs(u)) + 1e-10
    dt_cfl = 0.45 * dx / s_max
    dt_step = min(dt_step, dt_cfl)

    # Half step for u
    u_half = step_u_muscl(u, v, 0.5 * dt_step, k, dealias_mask, dx)

    # Full step for v (with u_half as the coupling field)
    v_new = step_v_imex_cn(u_half, v, dt_step, k, dealias_mask)

    # Half step for u (with v_new)
    u_new = step_u_muscl(u_half, v_new, 0.5 * dt_step, k, dealias_mask, dx)

    u = u_new
    v = v_new
    t += dt_step

    # Save snapshots at requested times
    while snap_idx < n_snapshots and t >= snapshot_times[snap_idx] - 1e-10:
        save_snapshot(u, v)
        snap_idx += 1

# Ensure we have all snapshots
while len(snapshots) < n_snapshots:
    save_snapshot(u, v)

# ---- Save output ----
result = np.stack(snapshots[:n_snapshots], axis=0)  # shape (n_snapshots, 2, Nx)
print(f"Output shape: {result.shape}")
print(f"Final t: {t:.4f}")
print(f"u_max: {np.max(u):.4f}, u_min: {np.min(u):.4f}")
print(f"v_max: {np.max(v):.4f}, v_min: {np.min(v):.4f}")
print(f"NaN in u: {np.any(np.isnan(u))}, NaN in v: {np.any(np.isnan(v))}")
print(f"Inf in u: {np.any(np.isinf(u))}, Inf in v: {np.any(np.isinf(v))}")

# Count local maxima in final v
from scipy.signal import find_peaks
peaks_v, _ = find_peaks(v, height=0.3)
print(f"Final v peaks >= 0.3: {len(peaks_v)}, peak amplitudes: {v[peaks_v] if len(peaks_v) > 0 else 'none'}")
print(f"Final v peak max: {np.max(v):.4f}")

# Mass diagnostics
mass_u = np.sum(u) * dx
mass_v = np.sum(v) * dx
print(f"Final mass_u: {mass_u:.4f}, mass_v: {mass_v:.4f}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", result)
print("Saved pred_results/T_C.npy")
