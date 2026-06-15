"""
T_B / PosNeg / E2: Coupled Burgers-swept-KdV — Gaussian -> soliton train.

PDE:
    u_t + 3 u u_x   = -d_x(3 v^2 + v_xx) + nu * u_xx       (added nu*u_xx)
    v_t + 6 v v_x + v_xxx = -d_x(u v)

Method (E2, single-component upgrade from E1):
    - Spatial: Fourier pseudospectral on x in [-15, 15], Nx = 256, periodic
    - Dealiasing: 2/3-rule applied to every nonlinear product
                  (v^2, u*v, v*v_x, u*u_x); we also dealias each state
                  before forming products to be safe.
    - Time: classical explicit RK4 over the *full* RHS (v_xxx explicit too).
    - dt = 1e-4.
    - NEW: explicit linear viscosity nu=5e-2 on the u-equation only
      (BKdV-S6 negative depth=3 recommended_alternative — validated default
       for BKdV with bore-like u-gradient ICs at this exact (Nx, dt, RK4)).

IC:
    v(x,0) = 4 * exp(-(x+5)^2 / 2.25)        # Gaussian, sigma=1.5
    u(x,0) = 0

Output:
    pred_results/T_B.npy  shape (n_snapshots, 2, Nx), channels (u, v)
"""

import os
import time

import numpy as np


# ---------------------------------------------------------------------------
# Grid setup
# ---------------------------------------------------------------------------
Nx = 256
L = 30.0
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]

# Wavenumbers for FFT-derivative on a periodic domain of length L.
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)   # ordinary frequency convention
ik = 1j * k
ik3 = 1j * (k ** 3)
mk2 = -(k ** 2)  # second derivative multiplier

# 2/3-rule dealias mask: zero modes with |k_idx| > Nx/3.
k_index = np.fft.fftfreq(Nx, d=1.0) * Nx     # integer wavenumber indices
dealias_mask = np.abs(k_index) <= Nx / 3.0


def dealias_state(f_hat):
    """Apply 2/3-rule cutoff in Fourier space."""
    out = f_hat.copy()
    out[~dealias_mask] = 0.0
    return out


def fft_d1(f_hat):
    """Spectral first derivative; returns physical-space array."""
    return np.real(np.fft.ifft(ik * f_hat))


def fft_d2(f_hat):
    """Spectral second derivative; returns physical-space array."""
    return np.real(np.fft.ifft(mk2 * f_hat))


def fft_d3(f_hat):
    """Spectral third derivative; returns physical-space array."""
    return np.real(np.fft.ifft(-ik3 * f_hat))
    # Note: ik3 = i k^3, so d^3/dx^3 corresponds to (i k)^3 = -i k^3.
    # We pre-stored ik3 = i k^3, hence the minus sign here gives (i k)^3.


def rhs(u, v):
    """
    Compute time derivatives (u_t, v_t) using spectral derivatives and
    2/3-rule dealiased products. Inputs are physical-space arrays.
    """
    # Dealias the states themselves so that products are well-behaved.
    u_hat = dealias_state(np.fft.fft(u))
    v_hat = dealias_state(np.fft.fft(v))

    u = np.real(np.fft.ifft(u_hat))
    v = np.real(np.fft.ifft(v_hat))

    # First/second/third spatial derivatives via spectral differentiation.
    u_x = fft_d1(u_hat)
    v_x = fft_d1(v_hat)
    v_xx = fft_d2(v_hat)
    v_xxx = fft_d3(v_hat)

    # Nonlinear products (each dealiased in Fourier space).
    uu = u * u
    uu_hat = dealias_state(np.fft.fft(uu))
    uu_x = fft_d1(uu_hat)                    # = 2 u u_x  -> divergence form

    vv = v * v
    vv_hat = dealias_state(np.fft.fft(vv))
    vv_x = fft_d1(vv_hat)                    # = 2 v v_x

    uv = u * v
    uv_hat = dealias_state(np.fft.fft(uv))
    d_uv = fft_d1(uv_hat)                    # = d/dx (u v)

    # v_xx derivative inside RHS of u-eq: d/dx(v_xx) = v_xxx, which we have.
    # Equation (E2): u_t + 3 u u_x = -d/dx(3 v^2 + v_xx) + nu * u_xx
    #        => u_t = -3 u u_x - 3 d/dx(v^2) - d/dx(v_xx) + nu * u_xx
    #             = -(3/2) d/dx(u^2) - 3 d/dx(v^2) - v_xxx + nu * u_xx
    # We use the divergence form for u u_x to keep mass exactly conserved.
    # The viscous term nu*u_xx is computed spectrally from u_hat.
    u_xx = fft_d2(u_hat)
    u_t = -1.5 * uu_x - 3.0 * vv_x - v_xxx + NU_U * u_xx

    # Equation: v_t + 6 v v_x + v_xxx = -d/dx(u v)
    #        => v_t = -6 v v_x - v_xxx - d/dx(u v)
    #             = -3 d/dx(v^2) - v_xxx - d/dx(u v)
    v_t = -3.0 * vv_x - v_xxx - d_uv

    return u_t, v_t


def rk4_step(u, v, dt):
    """Single classical RK4 step for the coupled system."""
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new


# ---------------------------------------------------------------------------
# Initial conditions
# ---------------------------------------------------------------------------
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros_like(x)

# ---------------------------------------------------------------------------
# Time integration
# ---------------------------------------------------------------------------
T_final = 6.0
dt = 1.0e-4
NU_U = 5.0e-2   # linear viscosity for u-equation (E2 upgrade)
n_steps = int(round(T_final / dt))

# Quick CFL-style stability check for explicit treatment of nu*u_xx:
# stability requires nu*k_max^2*dt < ~2.78 for RK4; check it.
_kmax2 = float(np.max(k ** 2))
_visc_cfl = NU_U * _kmax2 * dt
print(f"viscosity stability check: nu*k_max^2*dt = {_visc_cfl:.4f} (must be < ~2.78 for RK4)")

# Snapshots: store IC + 12 intermediate snapshots = 13 total (>=5 required).
n_snaps = 13
snap_times = np.linspace(0.0, T_final, n_snaps)
snap_steps = np.round(snap_times / dt).astype(int)
snap_idx_set = set(snap_steps.tolist())

snapshots = np.zeros((n_snaps, 2, Nx), dtype=np.float64)
mass_v_history = []
mass_u_history = []
max_v_history = []

# Initial snapshot.
u = u0.copy()
v = v0.copy()
snapshots[0, 0] = u
snapshots[0, 1] = v
mass_v_history.append(float(np.sum(v) * dx))
mass_u_history.append(float(np.sum(u) * dx))
max_v_history.append(float(np.max(v)))

next_snap_pos = 1

t0 = time.time()
for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        print(f"BLOWUP at step={step}, t={step*dt:.4f}")
        # Fill remaining snapshots with NaN so eval can see the failure clearly.
        for j in range(next_snap_pos, n_snaps):
            snapshots[j, 0] = np.nan
            snapshots[j, 1] = np.nan
        break
    if step in snap_idx_set:
        snapshots[next_snap_pos, 0] = u
        snapshots[next_snap_pos, 1] = v
        next_snap_pos += 1
        mass_v_history.append(float(np.sum(v) * dx))
        mass_u_history.append(float(np.sum(u) * dx))
        max_v_history.append(float(np.max(v)))

elapsed = time.time() - t0

# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
print(f"elapsed: {elapsed:.2f}s, n_steps: {n_steps}")
print(f"mass_v series: {[f'{m:.6f}' for m in mass_v_history]}")
print(f"mass_u series: {[f'{m:.6f}' for m in mass_u_history]}")
print(f"max_v series: {[f'{m:.4f}' for m in max_v_history]}")

mass_v0 = mass_v_history[0]
mass_v_final = mass_v_history[-1]
mass_v_drift_pct = 100.0 * abs(mass_v_final - mass_v0) / abs(mass_v0)
print(f"mass_v drift: {mass_v_drift_pct:.4f}%")

# Final v peak count (simple local-max counter with min separation 4 cells, ampl >=0.8).
v_final = snapshots[-1, 1]
peaks = []
for i in range(Nx):
    val = v_final[i]
    left = v_final[(i - 1) % Nx]
    right = v_final[(i + 1) % Nx]
    if val > left and val > right and val >= 0.8:
        peaks.append((i, val))
print(f"peaks_above_0.8 (simple max): {len(peaks)}; positions/heights: {peaks[:10]}")

# ---------------------------------------------------------------------------
# Save output
# ---------------------------------------------------------------------------
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", snapshots.astype(np.float32))
print(f"saved pred_results/T_B.npy with shape {snapshots.shape}")
