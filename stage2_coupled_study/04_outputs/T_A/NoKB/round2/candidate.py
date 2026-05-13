"""
Coupled Burgers-swept-KdV soliton stability simulation — Round 2.
PDE:
  u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx (u v)

Round-1 blew up due to stiff high-k modes and no step-size control.
Fix: operator splitting — treat dispersive/stiff linear parts (v_xxx, u_xxx-like)
with an implicit/exact spectral exponential integrator (integrating factor),
and the nonlinear parts with explicit RK4, using a smaller dt=2e-4 for safety.

Alternatively (simpler and robust): use spectral RHS + RK4 with much smaller dt
and aggressive de-aliasing + a mild spectral filter to kill aliasing energy.
"""

import numpy as np
import os

# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)

# Wavenumbers
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)

# 2/3 de-aliasing mask
k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)

# Exponential integrating factor for the stiff dispersive part of v:
# v linear part: v_t = -v_xxx  =>  d/dt v_hat = -(-ik)^3 v_hat = i k^3 v_hat
# We factor out exp(i k^3 t) so the nonlinear part is integrated in the
# interaction picture, removing the stiffness.
# Linear phase factor per unit time for v:
omega_v = -1j * k**3  # d/dt v_hat_tilde = omega_v * v_hat  (linear KdV part)

# For u the PDE has no standalone dispersive term that dominates; treat fully explicit.

# ---------------------------------------------------------------------------
# Helper: apply de-aliasing in Fourier space
# ---------------------------------------------------------------------------
def fft_da(f):
    """FFT with 2/3 de-aliasing."""
    fh = np.fft.fft(f)
    fh *= dealias
    return fh

def ifft_da(fh):
    return np.real(np.fft.ifft(fh * dealias))

def deriv(fh, order=1):
    """Spectral derivative of already-transformed (and de-aliased) field."""
    return (1j * k) ** order * fh

# ---------------------------------------------------------------------------
# Integrating-factor RK4 (IFRK4)
# We split: let w_hat = exp(-omega_v * t) * v_hat  (interaction picture)
# Then dw_hat/dt = exp(-omega_v*t) * N_v_hat
# For u, no integrating factor (its linear piece is just a nonlinear flux).
# ---------------------------------------------------------------------------

def nonlinear_rhs_hat(u_hat, v_hat):
    """
    Return (du_hat/dt, N_v_hat) where N_v is the nonlinear part of v_t
    (everything except the -v_xxx linear term which is handled by the integrating factor).
    """
    u = ifft_da(u_hat)
    v = ifft_da(v_hat)

    # --- u equation: u_t = -3 u u_x - d/dx(3v^2 + v_xx)
    # = -3 u u_x - 6 v v_x - v_xxx
    u_x = ifft_da(deriv(u_hat, 1))
    v_x = ifft_da(deriv(v_hat, 1))
    v_xxx = ifft_da(deriv(v_hat, 3))

    u_t_phys = -3.0 * u * u_x - 6.0 * v * v_x - v_xxx
    u_t_hat = fft_da(u_t_phys)

    # --- v equation nonlinear part: N_v = -6 v v_x - d/dx(u v)
    # (the -v_xxx is the linear/stiff part handled by integrating factor)
    uv = u * v
    uv_x = ifft_da(deriv(fft_da(uv), 1))
    Nv_phys = -6.0 * v * v_x - uv_x
    Nv_hat = fft_da(Nv_phys)

    return u_t_hat, Nv_hat


def ifrk4_step(u_hat, w_hat, t, dt):
    """
    One IFRK4 step.
    w_hat = exp(-omega_v * t) * v_hat  (interaction-picture variable for v)
    Returns updated (u_hat, w_hat) at t+dt.
    """
    # Precompute exponential factors for sub-steps
    E  = np.exp(omega_v * dt)       # full step factor
    E2 = np.exp(omega_v * dt / 2)   # half step factor

    # Recover v_hat from w_hat at current time
    v_hat = np.exp(omega_v * t) * w_hat

    # k1
    k1u, k1w_raw = nonlinear_rhs_hat(u_hat, v_hat)
    k1w = np.exp(-omega_v * t) * k1w_raw  # bring into interaction picture

    # k2 (at t + dt/2)
    u2 = u_hat + 0.5 * dt * k1u
    w2 = E2 * (w_hat + 0.5 * dt * k1w)
    v_hat2 = np.exp(omega_v * (t + 0.5*dt)) * w2
    k2u, k2w_raw = nonlinear_rhs_hat(u2, v_hat2)
    k2w = np.exp(-omega_v * (t + 0.5*dt)) * k2w_raw

    # k3 (at t + dt/2, same sub-time)
    u3 = u_hat + 0.5 * dt * k2u
    w3 = E2 * w_hat + 0.5 * dt * k2w
    v_hat3 = np.exp(omega_v * (t + 0.5*dt)) * w3
    k3u, k3w_raw = nonlinear_rhs_hat(u3, v_hat3)
    k3w = np.exp(-omega_v * (t + 0.5*dt)) * k3w_raw

    # k4 (at t + dt)
    u4 = u_hat + dt * k3u
    w4 = E * w_hat + dt * k3w
    v_hat4 = np.exp(omega_v * (t + dt)) * w4
    k4u, k4w_raw = nonlinear_rhs_hat(u4, v_hat4)
    k4w = np.exp(-omega_v * (t + dt)) * k4w_raw

    # Combine
    u_hat_new = u_hat + (dt / 6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    # For w: account for the exponential drift across each sub-step
    w_hat_new = E * w_hat + (dt / 6.0) * (
        E * k1w + 2 * E2 * k2w + 2 * E2 * k3w + k4w
    )

    # Apply de-aliasing to both
    u_hat_new *= dealias
    w_hat_new *= dealias

    return u_hat_new, w_hat_new


# ---------------------------------------------------------------------------
# Initial conditions
# ---------------------------------------------------------------------------
v0 = 2.0 / np.cosh(x + 5.0)**2
u0 = 0.5 * v0**2 + 0.2 * v0

u_hat = fft_da(u0)
v_hat = fft_da(v0)

T_final = 8.0
dt = 1.5e-4          # small dt for safety; v_xxx can be stiff for k~85
n_steps = int(np.ceil(T_final / dt))
dt = T_final / n_steps

# Interaction-picture variable for v
t = 0.0
w_hat = np.exp(-omega_v * t) * v_hat

# ---------------------------------------------------------------------------
# Time integration with snapshot saving
# ---------------------------------------------------------------------------
n_snapshots = 10
snapshot_times = np.linspace(0.0, T_final, n_snapshots)
snapshots = []

def recover_fields(u_hat, w_hat, t):
    v_hat_cur = np.exp(omega_v * t) * w_hat
    u_phys = ifft_da(u_hat)
    v_phys = ifft_da(v_hat_cur)
    return u_phys, v_phys

# Save initial snapshot
u_phys, v_phys = recover_fields(u_hat, w_hat, t)
snapshots.append(np.stack([u_phys, v_phys], axis=0))

snap_idx = 1
for step in range(n_steps):
    u_hat, w_hat = ifrk4_step(u_hat, w_hat, t, dt)
    t += dt

    # Check for blow-up
    if not (np.all(np.isfinite(u_hat)) and np.all(np.isfinite(w_hat))):
        print(f"Blow-up detected at t={t:.4f}, stopping.")
        break

    # Save snapshot if due
    if snap_idx < n_snapshots and t >= snapshot_times[snap_idx] - 1e-10:
        u_phys, v_phys = recover_fields(u_hat, w_hat, t)
        snapshots.append(np.stack([u_phys, v_phys], axis=0))
        snap_idx += 1

# Ensure we have the final snapshot
if len(snapshots) < n_snapshots:
    u_phys, v_phys = recover_fields(u_hat, w_hat, t)
    snapshots.append(np.stack([u_phys, v_phys], axis=0))

result = np.array(snapshots)  # shape (n_snapshots, 2, 256)
print(f"Result shape: {result.shape}")
print(f"v peak at t=T: {np.max(result[-1, 1]):.4f}")
print(f"u max at t=T:  {np.max(np.abs(result[-1, 0])):.4f}")
print(f"v mass ratio (final/initial): {np.sum(result[-1,1])/np.sum(result[0,1]):.4f}")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
np.save(os.path.join(out_dir, "T_A.npy"), result)
print("Saved to pred_results/T_A.npy")
