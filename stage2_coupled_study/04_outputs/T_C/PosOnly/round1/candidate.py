"""
T_C: Burgers bore interacting with a KdV soliton
Coupled Burgers-swept-KdV system:
  u_t + 3 u u_x = -dx(3v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -dx(u v)

Domain: x in [-15, 15], Nx=256, T=8.0
Method: Fourier pseudospectral + IMEX-Crank-Nicolson
  - dispersive (v_xxx) term handled implicitly (CN)
  - all nonlinear and coupling terms handled explicitly
  - Burgers component (3 u u_x) treated explicitly via spectral differentiation
"""

import numpy as np
import os

# Grid
L = 30.0  # domain length [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers
k = 2 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)
ik = 1j * k
ik3 = 1j * k**3

# Initial conditions
u = 1.5 * (1 - np.tanh(x / 0.5)) / 2.0
v = 1.5 / np.cosh(x + 8)**2

# Time stepping
T = 8.0
dt = 0.0005
Nt = int(T / dt) + 1
t = 0.0

# Snapshot times: 5 snapshots spread to capture encounter
n_snapshots = 8
snapshot_times = np.linspace(0.0, T, n_snapshots)
snapshots = []

def dealias(f_hat, Nx):
    """Apply 2/3 dealiasing"""
    f_hat_d = f_hat.copy()
    N3 = Nx // 3
    f_hat_d[N3:Nx-N3] = 0.0
    return f_hat_d

def compute_rhs(u, v):
    """Compute explicit RHS for both equations."""
    u_hat = np.fft.fft(u)
    v_hat = np.fft.fft(v)

    # Dealias
    u_hat_d = dealias(u_hat, Nx)
    v_hat_d = dealias(v_hat, Nx)

    u_d = np.fft.ifft(u_hat_d).real
    v_d = np.fft.ifft(v_hat_d).real

    # Spatial derivatives via spectral
    u_x = np.fft.ifft(ik * u_hat).real
    v_x = np.fft.ifft(ik * v_hat).real

    # u equation: u_t = -3 u u_x - dx(3v^2 + v_xx)
    # v_xx = ifft((ik)^2 * v_hat) = ifft(-k^2 * v_hat)
    v_xx = np.fft.ifft(-k**2 * v_hat).real
    # coupling term for u: -dx(3v^2 + v_xx)
    coupling_u_field = 3 * v**2 + v_xx
    coupling_u_hat = dealias(np.fft.fft(coupling_u_field), Nx)
    dcoupling_u = np.fft.ifft(ik * coupling_u_hat).real

    rhs_u = -3.0 * u * u_x - dcoupling_u

    # v equation: v_t = -6 v v_x - v_xxx - dx(u v)
    # v_xxx handled implicitly (CN); only nonlinear + coupling here
    # coupling term for v: -dx(u v)
    uv = u * v
    uv_hat = dealias(np.fft.fft(uv), Nx)
    duv = np.fft.ifft(ik * uv_hat).real

    rhs_v_explicit = -6.0 * v * v_x - duv
    # (v_xxx is handled in CN step)

    return rhs_u, rhs_v_explicit

# IMEX-CN time integration
# For v: (v_hat_new - v_hat_old)/dt + ik3/2*(v_hat_new + v_hat_old) = rhs_v_explicit_hat
# => v_hat_new * (1 + dt/2 * ik3) = v_hat_old * (1 - dt/2 * ik3) + dt * rhs_v_explicit_hat
# For u: pure explicit (no dispersive stiffness)
# u_new = u_old + dt * rhs_u

CN_denom = 1.0 + 0.5 * dt * ik3  # denominator for v CN step

# Record snapshot at t=0
snap_idx = 0
if abs(t - snapshot_times[snap_idx]) < dt * 0.5:
    snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
    snap_idx += 1

for n in range(Nt - 1):
    # Compute explicit RHS
    rhs_u, rhs_v_exp = compute_rhs(u, v)

    # Update u (fully explicit)
    u_new = u + dt * rhs_u

    # Update v via IMEX-CN
    v_hat = np.fft.fft(v)
    rhs_v_hat = np.fft.fft(rhs_v_exp)
    rhs_v_hat = dealias(rhs_v_hat, Nx)

    # CN: v_hat_new = (v_hat*(1 - dt/2*ik3) + dt*rhs_v_hat) / (1 + dt/2*ik3)
    v_hat_new = (v_hat * (1.0 - 0.5 * dt * ik3) + dt * rhs_v_hat) / CN_denom
    v_new = np.fft.ifft(v_hat_new).real

    u = u_new
    v = v_new
    t += dt

    # Record snapshots
    if snap_idx < n_snapshots:
        if t >= snapshot_times[snap_idx] - dt * 0.5:
            snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
            snap_idx += 1

# Ensure we have at least n_snapshots snapshots
while len(snapshots) < n_snapshots:
    snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

result = np.array(snapshots[:n_snapshots])  # shape (n_snapshots, 2, 256)
print(f"Output shape: {result.shape}")
print(f"u range: [{u.min():.4f}, {u.max():.4f}]")
print(f"v range: [{v.min():.4f}, {v.max():.4f}]")
print(f"v peak amplitude: {v.max():.4f}")
print(f"All finite: {np.all(np.isfinite(result))}")

# Save
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", result)
print("Saved pred_results/T_C.npy")
