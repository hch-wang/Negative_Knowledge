"""
Coupled Burgers-swept-KdV system solver - Iteration 3
u_t + 3*u*u_x = -d/dx(3*v^2 + v_xx)
v_t + 6*v*v_x + v_xxx = -d/dx(u*v)

Method: Strang splitting for v_xxx + RK4 for nonlinear + spectral smoothing filter on u
  - v_xxx: exact Fourier propagator exp(-ik^3*dt/2) (unconditionally stable, no CFL)
  - Nonlinear terms: RK4 at dt=5e-4 (tighter, nonlinear CFL ~ 0.64 < 2.83)
  - u field: Hou-Li spectral filter applied after each full step to prevent
    Gibbs oscillations from the hyperbolic u equation without intrinsic dispersion
  - 2/3 dealiasing on all nonlinear products

The Hou-Li filter sigma_k = exp(-alpha*(|k|/k_max)^m) with alpha=36, m=36:
  - sigma_k ~ 1 for |k| < 0.6*k_max (physical modes unaffected)
  - sigma_k ~ machine_eps at k = k_max (kills aliased energy)
"""

import numpy as np
import os

# Domain
L = 30.0  # x in [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers (Fourier)
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2 * np.pi / L)
k_abs = np.abs(k)
k_nyquist = np.pi * Nx / L  # ~ 26.8

# Time parameters
T = 6.0
dt = 0.0005
Nt = int(round(T / dt))
t_save = np.linspace(0, T, 61)  # 61 snapshots including t=0

# 2/3 dealiasing mask
dealias_mask = (k_abs <= (2.0 / 3.0) * k_nyquist).astype(float)

def dealias(fhat):
    """Apply 2/3 dealiasing in Fourier space."""
    return fhat * dealias_mask

# Exact propagator for v_xxx: d/dt v = -(ik)^3 v = ik^3 v
# => v_hat(t+h) = exp(-ik^3 * h) * v_hat(t)
# Wait: v_t + v_xxx = 0 => v_hat_t = -(ik)^3 * v_hat = -(-ik^3) * v_hat = ik^3 * v_hat
# No wait: v_t + v_xxx = 0 => v_hat_t = -F{v_xxx} = -(ik)^3 * v_hat
# (ik)^3 = i^3 k^3 = -ik^3
# So v_hat_t = -(-ik^3) * v_hat = ik^3 * v_hat
# => v_hat(t+h) = exp(ik^3 * h) * v_hat(t) [for linear KdV: v_t + v_xxx = 0]
# But our PDE: v_t = -6vvx - vxxx - d/dx(uv)
# The linear part (Strang) is just v_t = -vxxx
# => v_hat_t = -(ik)^3 * v_hat = ik^3 * v_hat
# => propagator = exp(ik^3 * h)
prop_half = np.exp(1j * k**3 * (dt / 2))
prop_full = np.exp(1j * k**3 * dt)

# Hou-Li spectral filter for u (suppress high-k oscillations in the hyperbolic u field)
alpha_filter = 36.0
m_filter = 36
filter_u = np.exp(-alpha_filter * (k_abs / k_nyquist)**m_filter)

def nonlinear_rhs(v_hat, u_hat):
    """
    RHS of nonlinear+coupling terms (no v_xxx here, handled by Strang splitting).

    v equation (nonlinear only): dv/dt = -6*v*v_x - d/dx(u*v)
    u equation: du/dt = -3*u*u_x - d/dx(3*v^2 + v_xx)

    Returns (dv_hat_dt, du_hat_dt)
    """
    # Physical space (take real part since physical fields are real)
    v = np.fft.ifft(v_hat).real
    u = np.fft.ifft(u_hat).real

    # Spectral derivatives (with dealiasing on products)
    vx_hat = 1j * k * v_hat
    ux_hat = 1j * k * u_hat
    vx = np.fft.ifft(dealias(vx_hat)).real
    ux = np.fft.ifft(dealias(ux_hat)).real

    # v_xx for u-equation forcing (no dealiasing needed for linear term)
    vxx_hat = -k**2 * v_hat

    # --- v equation nonlinear part: -6*v*v_x - d/dx(u*v) ---
    # 6*v*v_x
    vvx = 6.0 * v * vx
    vvx_hat = dealias(np.fft.fft(vvx))
    # d/dx(u*v)
    uv = u * v
    uv_hat = dealias(np.fft.fft(uv))
    duv_hat = 1j * k * uv_hat
    # dv/dt
    dv_hat = -vvx_hat - duv_hat

    # --- u equation: -3*u*u_x - d/dx(3*v^2 + v_xx) ---
    # 3*u*u_x
    uux = 3.0 * u * ux
    uux_hat = dealias(np.fft.fft(uux))
    # 3*v^2
    v2 = v * v
    v2_hat = dealias(np.fft.fft(3.0 * v2))
    # 3*v^2 + v_xx
    rhs_inner_hat = v2_hat + vxx_hat
    # d/dx(3*v^2 + v_xx)
    d_rhs_inner_hat = 1j * k * rhs_inner_hat
    # du/dt
    du_hat = -uux_hat - d_rhs_inner_hat

    return dv_hat, du_hat

def rk4_nonlinear(v_hat, u_hat, dt_rk):
    """RK4 step for nonlinear+coupling terms."""
    k1v, k1u = nonlinear_rhs(v_hat, u_hat)
    k2v, k2u = nonlinear_rhs(v_hat + dt_rk/2 * k1v, u_hat + dt_rk/2 * k1u)
    k3v, k3u = nonlinear_rhs(v_hat + dt_rk/2 * k2v, u_hat + dt_rk/2 * k2u)
    k4v, k4u = nonlinear_rhs(v_hat + dt_rk * k3v, u_hat + dt_rk * k3u)

    v_hat_new = v_hat + (dt_rk / 6.0) * (k1v + 2*k2v + 2*k3v + k4v)
    u_hat_new = u_hat + (dt_rk / 6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    return v_hat_new, u_hat_new

def full_step(v_hat, u_hat):
    """
    One full Strang splitting step:
    1. Half-step exact KdV dispersion (v_xxx)
    2. Full RK4 nonlinear step
    3. Half-step exact KdV dispersion again
    4. Apply Hou-Li filter to u (prevents Gibbs oscillations in hyperbolic u field)
    """
    # Half-step dispersion
    v_hat = prop_half * v_hat

    # Full RK4 nonlinear
    v_hat, u_hat = rk4_nonlinear(v_hat, u_hat, dt)

    # Half-step dispersion
    v_hat = prop_half * v_hat

    # Apply spectral filter to u to prevent Gibbs oscillations
    u_hat = filter_u * u_hat

    return v_hat, u_hat

# Initial conditions
v0 = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
u0 = np.zeros(Nx)

v_hat = np.fft.fft(v0)
u_hat = np.fft.fft(u0)

# Save snapshots
snapshots = []
save_idx = 0

initial_mass_v = np.sum(v0) * dx
snapshots.append(np.stack([u0.copy(), v0.copy()], axis=0))
save_idx = 1

nl_cfl = dt * 48 * k_nyquist
print(f"Starting integration: Nt={Nt}, dt={dt}, T={T}")
print(f"Initial v: max={v0.max():.4f}, mass={initial_mass_v:.4f}")
print(f"Nonlinear CFL estimate: {nl_cfl:.4f} (need < 2.83)")
print(f"Filter: Hou-Li alpha={alpha_filter}, m={m_filter}")
print(f"Filter at k_nyquist: {filter_u[np.argmax(k_abs)]:.2e}")

# Time integration
for n in range(Nt):
    t_next = (n + 1) * dt

    v_hat, u_hat = full_step(v_hat, u_hat)

    # Check for NaN/Inf
    if not np.all(np.isfinite(v_hat)) or not np.all(np.isfinite(u_hat)):
        v = np.fft.ifft(v_hat).real
        u = np.fft.ifft(u_hat).real
        print(f"NaN/Inf detected at t={t_next:.4f}, step {n+1}")
        print(f"  v: {np.sum(np.isnan(v))} NaNs, max={np.nanmax(np.abs(v)):.4f}")
        print(f"  u: {np.sum(np.isnan(u))} NaNs, max={np.nanmax(np.abs(u)):.4f}")
        break

    # Save snapshot if time matches
    if save_idx < len(t_save) and t_next >= t_save[save_idx] - dt/2:
        v = np.fft.ifft(v_hat).real
        u = np.fft.ifft(u_hat).real
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        save_idx += 1
        if save_idx % 10 == 0 or save_idx == len(t_save):
            mass_v = np.sum(v) * dx
            dv = np.diff(v)
            n_peaks = int(np.sum((dv[:-1] > 0) & (dv[1:] < 0)))
            print(f"t={t_next:.3f}: v_max={v.max():.4f}, u_max={np.abs(u).max():.4f}, "
                  f"mass_v={mass_v:.4f}, n_peaks_v={n_peaks}")

# Final state
v = np.fft.ifft(v_hat).real
u = np.fft.ifft(u_hat).real
print(f"\nIntegration done. Saved {len(snapshots)} snapshots.")
print(f"Final v: max={v.max():.4f}, min={v.min():.4f}, mass={np.sum(v)*dx:.4f}")
print(f"Final u: max={np.abs(u).max():.4f}")

# Detect peaks in final v
dv = np.diff(v)
peak_idx = np.where((dv[:-1] > 0) & (dv[1:] < 0))[0] + 1
peaks_above = [(x[i], v[i]) for i in peak_idx if v[i] >= 0.8]
print(f"\nFinal v peaks: {len(peak_idx)} total, {len(peaks_above)} with amplitude >= 0.8:")
for px, pa in sorted(peaks_above, key=lambda t: -t[1]):
    print(f"  x={px:.3f}, amplitude={pa:.4f}")

mass_final = np.sum(v) * dx
mass_drift_pct = abs(mass_final - initial_mass_v) / abs(initial_mass_v) * 100
print(f"\nMass: initial={initial_mass_v:.4f}, final={mass_final:.4f}, drift={mass_drift_pct:.2f}%")

# Phenomenon check
n_peaks_above = len(peaks_above)
# Check separation: are peaks well-separated?
if len(peaks_above) >= 2:
    xpos = sorted([p[0] for p in peaks_above])
    min_sep = min(xpos[i+1] - xpos[i] for i in range(len(xpos)-1))
    print(f"Min peak separation: {min_sep:.3f} (well-separated if >> dx={dx:.4f})")
else:
    min_sep = 0.0

print(f"\n--- Phenomenon check ---")
print(f"Peaks >= 0.8: {n_peaks_above} (need >= 2)")
print(f"Mass drift: {mass_drift_pct:.2f}% (need < 8%)")
print(f"Phenomenon satisfied: {n_peaks_above >= 2 and mass_drift_pct < 8.0}")

# Save results
result = np.array(snapshots)
print(f"\nOutput shape: {result.shape}")
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", result)
print("Saved pred_results/T_B.npy")
