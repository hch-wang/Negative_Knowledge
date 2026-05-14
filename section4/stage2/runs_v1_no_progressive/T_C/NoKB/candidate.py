"""
Candidate solver for T_C: Burgers bore interacting with KdV soliton (Iteration 3)
Coupled Burgers-swept-KdV system:
  u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx (u v)

Method: Explicit pseudo-spectral RK4 with 2/3-rule de-aliasing
  - dt = 0.00008, below k_max^3 stability limit of ~0.000104
  - All derivatives via FFT; 2/3 mask applied after each full RK4 step
Domain: x in [-15, 15], Nx=256, periodic BC
"""

import numpy as np
import os

# Domain parameters
L = 30.0
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)

# Wavenumbers
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)

# De-aliasing mask: zero out top 1/3 of wavenumbers (2/3 rule)
k_max_alias = np.max(np.abs(k)) * 2.0 / 3.0
dealias_mask = (np.abs(k) <= k_max_alias).astype(float)

# Time parameters
T = 8.0
dt = 0.00008
n_steps = int(round(T / dt))

# Snapshot times: 9 snapshots at t = 0, 1, 2, ..., 8
n_snapshots = 9
snapshot_times = np.linspace(0, T, n_snapshots)
snapshot_steps = [int(round(t / dt)) for t in snapshot_times]
snapshot_steps[-1] = n_steps
snap_set = set(snapshot_steps)

# Initial conditions
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0   # smoothed bore
v = 1.5 / np.cosh(x + 8.0)**2               # KdV soliton sech^2

def spec_d(f):
    """Spectral first derivative with de-aliasing."""
    fh = np.fft.fft(f) * dealias_mask
    return np.real(np.fft.ifft(1j * k * fh))

def spec_d2(f):
    """Spectral second derivative with de-aliasing."""
    fh = np.fft.fft(f) * dealias_mask
    return np.real(np.fft.ifft((1j * k)**2 * fh))

def spec_d3(f):
    """Spectral third derivative with de-aliasing."""
    fh = np.fft.fft(f) * dealias_mask
    return np.real(np.fft.ifft((1j * k)**3 * fh))

def dealias(f):
    """Apply 2/3 de-aliasing to physical field."""
    return np.real(np.fft.ifft(np.fft.fft(f) * dealias_mask))

def rhs(u, v):
    """
    RHS for coupled Burgers-swept-KdV:
      du/dt = -3 u u_x - d/dx(3 v^2 + v_xx)
      dv/dt = -6 v v_x - v_xxx - d/dx(u v)
    """
    u_x = spec_d(u)
    v_x = spec_d(v)
    v_xx = spec_d2(v)
    v_xxx = spec_d3(v)

    # u equation coupling: -d/dx(3v^2 + v_xx)
    coupling_u_x = spec_d(3.0 * v**2 + v_xx)
    du_dt = -3.0 * u * u_x - coupling_u_x

    # v equation coupling: -d/dx(u*v)
    uv_x = spec_d(u * v)
    dv_dt = -6.0 * v * v_x - v_xxx - uv_x

    return du_dt, dv_dt

def rk4_step(u, v, dt):
    """One RK4 step."""
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v)
    u_new = u + dt/6.0 * (k1u + 2*k2u + 2*k3u + k4u)
    v_new = v + dt/6.0 * (k1v + 2*k2v + 2*k3v + k4v)
    # Apply de-aliasing after each full step
    u_new = dealias(u_new)
    v_new = dealias(v_new)
    return u_new, v_new

# Storage for snapshots
snapshots = []

print(f"Starting RK4+dealias simulation: Nx={Nx}, dt={dt}, T={T}, n_steps={n_steps}")
print(f"k_max_alias={k_max_alias:.4f}, stability limit dt<{2/np.max(np.abs(k))**3:.6f}")
print(f"Snapshot steps: {sorted(snap_set)}")

# Record initial condition
if 0 in snap_set:
    snapshots.append(np.array([u.copy(), v.copy()]))
    print(f"Step     0 (t=0.000): max|u|={np.max(np.abs(u)):.4f}, max|v|={np.max(np.abs(v)):.4f}")

for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)

    if step in snap_set:
        t_curr = step * dt
        snapshots.append(np.array([u.copy(), v.copy()]))
        print(f"Step {step:6d} (t={t_curr:.3f}): max|u|={np.max(np.abs(u)):.4f}, max|v|={np.max(np.abs(v)):.4f}")

    # Safety check every 5000 steps
    if step % 5000 == 0:
        if np.any(np.isnan(u)) or np.any(np.isnan(v)):
            print(f"NaN at step {step} (t={step*dt:.4f})! Aborting.")
            break
        if np.max(np.abs(u)) > 20 or np.max(np.abs(v)) > 20:
            print(f"Blow-up at step {step}: |u|={np.max(np.abs(u)):.2f}, |v|={np.max(np.abs(v)):.2f}")
            break

result = np.array(snapshots)
print(f"\nFinal array shape: {result.shape}")
print(f"Final u: max={np.max(result[-1,0]):.4f}, min={np.min(result[-1,0]):.4f}")
print(f"Final v: max={np.max(result[-1,1]):.4f}, min={np.min(result[-1,1]):.4f}")
print(f"NaN in result: {np.any(np.isnan(result))}")
print(f"Snapshots saved: {result.shape[0]}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", result)
print(f"Saved to pred_results/T_C.npy, shape={result.shape}")
