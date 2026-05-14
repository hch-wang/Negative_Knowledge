"""
Coupled Burgers-swept-KdV system solver — Iteration 2
  u_t + 3 u u_x = -d/dx(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx(u v)

Method: Operator splitting
- v equation: IMEX-Crank-Nicolson spectral (CN on v_xxx, explicit nonlinear), 2/3 dealiasing
- u equation: MUSCL-van Leer + Godunov upwind for 3uu_x (hyperbolic Burgers),
              spectral evaluation for source term -d/dx(3v^2 + v_xx)
- Coupled via operator splitting: each global step:
  1. Advance v with IMEX-CN (fixed dt)
  2. Advance u with MUSCL-Godunov using adaptive substeps (CFL=0.45)

Cites: kb-kdv-IMEX-CN-spectral-pass, kb-burgers-MUSCL-Godunov-shock-pass,
       kb-kdv-spectral-solitonAmplitude-conservation

Domain: x in [-15, 15], Nx=256, periodic
IC: v(x,0) = 4*exp(-(x+5)^2/2.25), u(x,0) = 0
T = 6.0, dt = 0.002 (global), n_snapshots = 61
"""

import numpy as np
import os

# --- Parameters ---
L = 30.0
Nx = 256
T = 6.0
dt_global = 0.002   # global time step (IMEX-CN for v)
Nt = int(round(T / dt_global))
n_snapshots = 61
CFL_u = 0.45        # CFL for Burgers/u equation sub-stepping

# --- Grid ---
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# --- Wavenumbers ---
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2 * np.pi / L)

# --- 2/3 dealiasing mask ---
k_max_dealias = (Nx // 3) * (2 * np.pi / L)
dealias_mask = np.abs(k) <= k_max_dealias

# --- Initial conditions ---
v = 4.0 * np.exp(-((x + 5)**2) / 2.25)
u = np.zeros(Nx)

# --- Snapshot storage ---
snapshot_times = np.linspace(0, T, n_snapshots)
snapshot_idx = 0
snapshots = np.zeros((n_snapshots, 2, Nx))
snapshots[snapshot_idx, 0, :] = u
snapshots[snapshot_idx, 1, :] = v
snapshot_idx += 1

# --- Precompute CN factors for v_xxx ---
lin_coeff = (1j * k)**3   # -i k^3
cn_denom = 1.0 + 0.5 * dt_global * lin_coeff
cn_numer_coeff = 1.0 - 0.5 * dt_global * lin_coeff

# ============================================================
# Spectral helpers
# ============================================================
def dealias_f(f_hat):
    return f_hat * dealias_mask

def spectral_dx(f_hat):
    return np.real(np.fft.ifft(1j * k * f_hat))

# ============================================================
# v equation: IMEX-CN nonlinear RHS (excluding v_xxx)
# Returns Fourier-space array
# ============================================================
def v_nonlinear_rhs_hat(v, u):
    v_hat = dealias_f(np.fft.fft(v))
    u_hat = dealias_f(np.fft.fft(u))
    # 6 v v_x
    vx = spectral_dx(v_hat)
    term1 = 6.0 * v * vx
    # d/dx(uv)
    uv_hat = dealias_f(np.fft.fft(u * v))
    term2 = spectral_dx(uv_hat)
    rhs = -(term1 + term2)
    return dealias_f(np.fft.fft(rhs))

# ============================================================
# MUSCL-Godunov for Burgers equation: q_t + d/dx(q^2/2) = 0
# We need: u_t + 3 u u_x = 0  =>  u_t + d/dx(3u^2/2) = 0
# Source term handled separately.
# ============================================================
def van_leer_limiter(r):
    """Van Leer limiter: phi(r) = (r + |r|) / (1 + |r|)"""
    abs_r = np.abs(r)
    return (r + abs_r) / (1.0 + abs_r + 1e-15)

def muscl_godunov_burgers_flux(u, coeff=3.0):
    """
    MUSCL-Godunov flux for: u_t + coeff * u * u_x = 0
    i.e., u_t + d/dx(coeff * u^2 / 2) = 0
    Returns flux at cell interfaces i+1/2 for i=0..Nx-1 (periodic)
    """
    # Compute slope ratios (periodic)
    du = np.roll(u, -1) - u  # u[i+1] - u[i]
    du_prev = u - np.roll(u, 1)   # u[i] - u[i-1]
    # Avoid division by zero
    r = np.where(np.abs(du_prev) > 1e-15, du / du_prev, 0.0)
    phi = van_leer_limiter(r)
    # Reconstructed states at i+1/2
    u_L = u + 0.5 * phi * du_prev          # left state at i+1/2
    # For right state: at interface i+1/2, right state comes from cell i+1
    # slope for cell i+1: r = (u[i+2]-u[i+1])/(u[i+1]-u[i])
    du_next = np.roll(du, -1)              # u[i+2]-u[i+1]
    r_right = np.where(np.abs(du) > 1e-15, du_next / du, 0.0)
    phi_right = van_leer_limiter(r_right)
    u_R = np.roll(u, -1) - 0.5 * phi_right * du  # right state at i+1/2
    # Godunov flux for f(u) = coeff*u^2/2
    # Exact Riemann for convex flux:
    #   if u_L >= u_R: entropy solution shock or rarefaction
    #   if u_L <= u_R: rarefaction
    u_sonic = 0.0  # sonic point
    f_L = coeff * u_L**2 / 2.0
    f_R = coeff * u_R**2 / 2.0
    # Godunov flux
    flux = np.where(u_L >= u_R,
                    np.where(u_L + u_R >= 0, f_L, f_R),  # shock: s = (f_R-f_L)/(u_R-u_L) ~ (u_L+u_R)/2
                    np.where(u_L >= 0, f_L,
                             np.where(u_R <= 0, f_R, 0.0)))  # rarefaction
    return flux

def advance_u_muscl(u, v, dt_total):
    """
    Advance u equation: u_t + d/dx(3u^2/2) = source
    source = -d/dx(3v^2 + v_xx)
    Using adaptive sub-stepping with CFL=0.45.
    v is assumed constant over dt_total (Strang/operator splitting).
    """
    # Compute source term (spectral, constant over dt_total)
    v_hat = dealias_f(np.fft.fft(v))
    v2_hat = dealias_f(np.fft.fft(3.0 * v**2))
    d_v2_dx = spectral_dx(v2_hat)
    v_xxx = spectral_dx(dealias_f((1j*k)**2 * v_hat * (1j*k)))  # = d/dx(v_xx) = v_xxx
    # Actually: v_xx = ifft((ik)^2 v_hat), d/dx(v_xx) = ifft((ik)^3 v_hat)
    v_xxx = np.real(np.fft.ifft(lin_coeff * dealias_f(v_hat)))
    source = -d_v2_dx - v_xxx

    t_elapsed = 0.0
    u_curr = u.copy()
    while t_elapsed < dt_total - 1e-12:
        # Adaptive dt for Burgers CFL
        max_speed = 3.0 * np.max(np.abs(u_curr)) + 1e-10
        dt_cfl = CFL_u * dx / max_speed
        dt_sub = min(dt_cfl, dt_total - t_elapsed)

        # MUSCL-Godunov flux
        flux = muscl_godunov_burgers_flux(u_curr)  # f at i+1/2, f(u) = 3u^2/2
        flux_diff = (flux - np.roll(flux, 1)) / dx  # (f_{i+1/2} - f_{i-1/2}) / dx
        # Forward Euler update with source
        u_curr = u_curr - dt_sub * flux_diff + dt_sub * source
        t_elapsed += dt_sub

    return u_curr

# ============================================================
# Time integration
# ============================================================
t = 0.0

for n_step in range(Nt):
    t_new = t + dt_global

    # Step 1: Advance v with IMEX-CN (uses current u and v)
    v_hat = dealias_f(np.fft.fft(v))
    NL_v = v_nonlinear_rhs_hat(v, u)
    v_hat_new = (cn_numer_coeff * v_hat + dt_global * NL_v) / cn_denom
    v_hat_new = dealias_f(v_hat_new)
    v_new = np.real(np.fft.ifft(v_hat_new))

    # Step 2: Advance u with MUSCL-Godunov (uses v_new for source, u_curr)
    u_new = advance_u_muscl(u, v_new, dt_global)

    # Dealias u
    u_hat_new = dealias_f(np.fft.fft(u_new))
    u_new = np.real(np.fft.ifft(u_hat_new))

    u = u_new
    v = v_new
    t = t_new

    # Save snapshots
    while snapshot_idx < n_snapshots and t >= snapshot_times[snapshot_idx] - 1e-10:
        snapshots[snapshot_idx, 0, :] = u
        snapshots[snapshot_idx, 1, :] = v
        snapshot_idx += 1

# --- Save output ---
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", snapshots)

print(f"Saved pred_results/T_B.npy, shape={snapshots.shape}")
print(f"Final t = {t:.4f}, snapshots saved = {snapshot_idx}")

# --- Diagnostics ---
v_final = snapshots[-1, 1, :]
u_final = snapshots[-1, 0, :]
v_init = snapshots[0, 1, :]

mass_v_init = np.sum(v_init) * dx
mass_v_final = np.sum(v_final) * dx
mass_drift_pct = abs(mass_v_final - mass_v_init) / abs(mass_v_init) * 100 if abs(mass_v_init) > 1e-10 else 0.0

print(f"\n--- Diagnostics ---")
print(f"v_final: max={v_final.max():.4f}, min={v_final.min():.4f}")
print(f"u_final: max={u_final.max():.4f}, min={u_final.min():.4f}")
print(f"mass(v) initial={mass_v_init:.4f}, final={mass_v_final:.4f}, drift={mass_drift_pct:.2f}%")
print(f"NaN in v_final: {np.any(np.isnan(v_final))}")
print(f"NaN in u_final: {np.any(np.isnan(u_final))}")

# Count peaks in v_final
from scipy.signal import find_peaks
peaks, _ = find_peaks(v_final, height=0.8, distance=5)
print(f"Peaks in v_final with amp>=0.8: {len(peaks)}")
for p in peaks:
    print(f"  x={x[p]:.3f}, amp={v_final[p]:.4f}")

# Check intermediate snapshots
print("\n--- Intermediate snapshot summary ---")
for i in [0, 10, 20, 30, 40, 50, 60]:
    if i < len(snapshots):
        vi = snapshots[i, 1, :]
        ui = snapshots[i, 0, :]
        print(f"t={snapshot_times[i]:.1f}: v_max={vi.max():.4f}, u_max={ui.max():.4f}, nan_v={np.any(np.isnan(vi))}")
