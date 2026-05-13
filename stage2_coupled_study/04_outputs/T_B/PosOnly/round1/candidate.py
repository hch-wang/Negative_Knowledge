"""
T_B: Gaussian wave packet -> soliton train decomposition
Coupled Burgers-swept-KdV system (Holm et al. 2025):
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

Method: Fourier pseudospectral + IMEX-Crank-Nicolson
- Dispersive term v_xxx treated implicitly (CN)
- All nonlinear and coupling terms treated explicitly
- u equation: fully explicit (no dispersive stiffness)
"""

import numpy as np
import os

# Domain setup
L = 30.0  # domain [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = x[1] - x[0]

# Wavenumbers (Fourier)
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi

# Initial conditions
v = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u = np.zeros(Nx)

# Time stepping
T_final = 6.0
dt = 0.0005
Nt = int(T_final / dt) + 1
dt = T_final / (Nt - 1)  # adjust to hit T exactly

# Snapshot times: 5 evenly spaced snapshots including t=T
n_snapshots = 7
snapshot_times = np.linspace(0, T_final, n_snapshots)
snapshot_idx = set([int(round(t / dt)) for t in snapshot_times])
snapshot_idx.add(Nt - 1)

# Dealiasing mask (2/3 rule)
k_max = np.max(np.abs(k))
dealias = np.abs(k) <= (2.0 / 3.0) * k_max

# CN denominator for v_xxx: 1 - (dt/2)*(ik)^3 = 1 + (dt/2)*ik^3
# CN numerator:            1 + (dt/2)*(ik)^3 = 1 - (dt/2)*ik^3
ik3 = (1j * k) ** 3  # = i^3 k^3 = -ik^3
cn_num = 1.0 + (dt / 2.0) * ik3    # 1 - (dt/2)*ik^3
cn_den = 1.0 - (dt / 2.0) * ik3    # 1 + (dt/2)*ik^3

def spectral_deriv(f_hat, order=1):
    """Compute d^order f / dx^order via spectral differentiation."""
    return np.fft.ifft((1j * k) ** order * f_hat).real

def compute_rhs_v(u, v):
    """RHS of v equation (explicit part, excluding v_xxx which is implicit):
       -6 v v_x - d_x(u v)
    """
    v_hat = np.fft.fft(v)
    u_hat = np.fft.fft(u)
    # Apply dealiasing to nonlinear products
    vv_x = 6.0 * v * spectral_deriv(v_hat * dealias)
    uv = u * v
    uv_hat = np.fft.fft(uv) * dealias
    d_uv = np.fft.ifft(1j * k * uv_hat).real
    return -vv_x - d_uv

def compute_rhs_u(u, v):
    """RHS of u equation:
       -3 u u_x - d_x(3v^2 + v_xx)
    """
    u_hat = np.fft.fft(u)
    v_hat = np.fft.fft(v)
    # Apply dealiasing
    uu_x = 3.0 * u * spectral_deriv(u_hat * dealias)
    v2 = 3.0 * v ** 2
    v2_hat = np.fft.fft(v2) * dealias
    # v_xx
    vxx_hat = (1j * k) ** 2 * v_hat * dealias
    # d_x(3v^2 + v_xx)
    d_expr = np.fft.ifft(1j * k * (v2_hat + vxx_hat)).real
    return -3.0 * uu_x - d_expr

# Store snapshots
snapshots = []
snapshot_steps_sorted = sorted(snapshot_idx)

step = 0
t = 0.0

# Record initial state if step 0 is a snapshot
if step in snapshot_idx:
    snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

for step in range(1, Nt):
    t_prev = (step - 1) * dt

    # --- IMEX-CN step ---
    # For v: IMEX-CN handles v_xxx implicitly, explicit part is R_v
    # For u: fully explicit (Euler -- no dispersive stiffness in u)

    # Compute explicit RHS at current state
    rhs_v = compute_rhs_v(u, v)
    rhs_u = compute_rhs_u(u, v)

    # Update u with forward Euler (u has no dispersive term)
    # Use second-order approach: Adams-Bashforth style or simple Euler
    u_new = u + dt * rhs_u

    # Update v with IMEX-CN:
    # (v_new - v)/dt + (1/2)(v_xxx_new + v_xxx) = R_v
    # => v_new - (dt/2) v_xxx_new = v + (dt/2) v_xxx + dt * R_v
    v_hat = np.fft.fft(v)
    v_xxx_hat = ik3 * v_hat
    # RHS in spectral space
    rhs_v_hat = np.fft.fft(rhs_v)
    # Note: ik3 = (ik)^3, v_xxx = IFFT(ik3 * v_hat)
    # CN: v_hat_new * cn_den = v_hat * cn_num + dt * rhs_v_hat
    # cn_num = 1 + (dt/2)*ik3 (the "old" implicit side added to RHS)
    # cn_den = 1 - (dt/2)*ik3 (the "new" implicit side in denominator)
    rhs_total_hat = cn_num * v_hat + dt * rhs_v_hat
    # Apply dealiasing to the update
    rhs_total_hat *= dealias
    v_hat_new = rhs_total_hat / cn_den
    v_new = np.fft.ifft(v_hat_new).real

    u = u_new
    v = v_new

    if step in snapshot_idx:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

# Ensure we have exactly n_snapshots (at least 5)
# We targeted 7 snapshots
result = np.array(snapshots)  # shape (n_snapshots, 2, 256)

# Save output
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", result)

print(f"Saved shape: {result.shape}")
print(f"Final v: max={result[-1, 1].max():.4f}, mass={np.mean(result[-1, 1]):.4f}")
print(f"Initial v mass: {np.mean(result[0, 1]):.4f}")

# Count peaks in final v
from scipy.signal import find_peaks
peaks, props = find_peaks(result[-1, 1], height=0.8, distance=5)
print(f"Final v peaks (amp>=0.8): {len(peaks)} at positions x={x[peaks]}")
print(f"Final u: max={np.abs(result[-1, 0]).max():.4f}")
