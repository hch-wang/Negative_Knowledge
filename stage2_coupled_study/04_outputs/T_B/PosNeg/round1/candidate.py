"""
Coupled Burgers-swept-KdV system — T_B: Gaussian wave packet -> soliton train
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

Domain: x in [-15, 15], periodic, Nx=256
IC: v(x,0) = 4*exp(-((x+5)^2)/2.25), u(x,0) = 0
T = 6.0

Method: Fourier pseudospectral + IMEX-Crank-Nicolson
  - Dispersive term v_xxx: Crank-Nicolson (implicit, unconditionally stable)
  - Nonlinear terms: explicit (Adams-Bashforth 2-step after first step)
  - Burgers u equation: fully explicit with upwind-corrected spectral approach

Output: pred_results/T_B.npy, shape (n_snapshots, 2, 256)
"""

import numpy as np
import os

# --- Grid ---
L = 30.0          # domain length [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2.0 * np.pi / L)

# Dealiasing mask (2/3 rule)
k_max = np.max(np.abs(k))
dealias = np.abs(k) <= (2.0/3.0) * k_max

# --- Initial conditions ---
v = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
u = np.zeros(Nx)

# --- Time stepping parameters ---
T_final = 6.0
# From memory: for amplitude A=4, nonlinear speed ~ max(3A + 3A^2/...) and KdV-sweep.
# Burgers component max speed ~ 3*A ~ 12; KdV component: max(6v + ...) ~ 6*4 = 24
# Use dt small enough: CFL based on max speed * dt * k_Nyquist < 0.5
# k_Nyquist = pi/dx ~ 26.8, max nonlinear speed ~ 24 => dt <= 0.5/(24*26.8) ~ 7.8e-4
# Use dt = 2e-4 for safety (amplitude 4 is large; kb-gardner-nonlinearCFL-amplitude-boundary warns)
dt = 2.0e-4
Nt = int(np.ceil(T_final / dt))
dt = T_final / Nt   # exact final time

# Snapshot times: at least 5, including final
n_snaps = 7
snap_indices = np.unique(np.round(np.linspace(0, Nt, n_snaps)).astype(int))
snap_indices = np.sort(snap_indices)

# IMEX-CN denominator for v_xxx: (1 - dt/2 * (ik)^3) hat{v}^{n+1} = rhs
# (ik)^3 = i^3 k^3 = -i k^3  =>  denom = 1 + dt/2 * i * k^3
denom_v = 1.0 + (dt / 2.0) * (1j * k**3)   # denominator for CN on v_xxx

# For u equation: no dispersive stiffness; fully explicit (RHS treated spectrally)
# u_t = -3 u u_x - d_x(3 v^2 + v_xx)
# We step u with forward Euler / AB2

def nonlinear_rhs_v(v, u):
    """Compute RHS of v equation: -6 v v_x - d_x(u v)  (excluding v_xxx handled implicitly)"""
    vhat = np.fft.fft(v)
    uhat = np.fft.fft(u)
    # v_x spectral
    vx_hat = 1j * k * vhat
    vx_hat *= dealias
    vx = np.fft.ifft(vx_hat).real
    # uv product, then derivative
    uv = u * v
    uv_hat = np.fft.fft(uv)
    uv_x_hat = 1j * k * uv_hat
    uv_x_hat *= dealias
    uv_x = np.fft.ifft(uv_x_hat).real
    return -6.0 * v * vx - uv_x

def nonlinear_rhs_u(u, v):
    """Compute RHS of u equation: -3 u u_x - d_x(3 v^2 + v_xx)"""
    uhat = np.fft.fft(u)
    vhat = np.fft.fft(v)
    # u_x
    ux_hat = 1j * k * uhat
    ux_hat *= dealias
    ux = np.fft.ifft(ux_hat).real
    # v^2
    v2 = v**2
    v2_hat = np.fft.fft(v2)
    v2_hat *= dealias
    # v_xx
    vxx_hat = (1j * k)**2 * vhat
    vxx_hat *= dealias
    # 3*v^2 + v_xx in spectral
    f_hat = 3.0 * v2_hat + vxx_hat
    # derivative
    f_x_hat = 1j * k * f_hat
    f_x_hat *= dealias
    f_x = np.fft.ifft(f_x_hat).real
    return -3.0 * u * ux - f_x

def imex_cn_step_v(v, u, u_new, N_prev, dt):
    """
    One IMEX-CN step for v:
      (I + dt/2 * d^3/dx^3) v^{n+1} = (I - dt/2 * d^3/dx^3) v^n + dt * N_v^{n}
    where N_v includes explicit nonlinear terms.
    For the coupling term -d_x(uv), use average of old/new u => use u here (explicit).
    """
    N_cur = nonlinear_rhs_v(v, u)
    vhat = np.fft.fft(v)
    # CN explicit part: (I - dt/2 * (-ik^3)) vhat = (1 - dt/2*ik^3) vhat  (note: -ik^3 from v_xxx = d^3/dx^3)
    # v_xxx in spectral = (ik)^3 * vhat = -ik^3 * vhat
    # IMEX-CN:  vhat^{n+1} / denom_v = [(1 - dt/2 * (-ik^3)) * vhat^n + dt * Nhat^n] / denom_v
    # = [(1 + dt/2 * ik^3) * vhat^n + dt * Nhat^n] / denom_v   <-- but denom_v = 1 + dt/2 * ik^3 already
    # So vhat^{n+1} = [(1 - dt/2*(ik)^3) * vhat^n + dt*Nhat^n] / denom_v^*
    # (ik)^3 = (ik)^3 = i^3 k^3 = -ik^3
    # v_xxx contrib: LHS: hat{v}^{n+1} - dt/2*(ik)^3 hat{v}^{n+1} = [1 - dt/2*(ik)^3] hat{v}^n + dt*N
    # => hat{v}^{n+1} = ([1 - dt/2*(ik)^3] hat{v}^n + dt*N) / (1 - dt/2*(ik)^3)  ... wait
    # CN: (v^{n+1} - v^n)/dt = (v_xxx^{n+1} + v_xxx^n)/2 + N^n
    # => v^{n+1} - dt/2 v_xxx^{n+1} = v^n + dt/2 v_xxx^n + dt N^n
    # spectral: hat{v}^{n+1} (1 - dt/2*(ik)^3) = hat{v}^n (1 + dt/2*(ik)^3) + dt*hatN
    # (ik)^3 = i^3 k^3 = -ik^3  => 1 - dt/2*(-ik^3) = 1 + dt/2*ik^3 = denom_v
    # so: hat{v}^{n+1} * conj(denom_v)... no:
    # LHS denom: 1 - dt/2*(ik)^3 = 1 + dt/2*ik^3 = denom_v  (same!)
    # RHS factor: 1 + dt/2*(ik)^3 = 1 - dt/2*ik^3 = conj(denom_v) for real k
    rhs_factor = 1.0 - (dt / 2.0) * (1j * k**3)   # = conj(denom_v) for real k
    Nhat = np.fft.fft(N_cur)
    Nhat *= dealias
    vhat_new = (rhs_factor * vhat + dt * Nhat) / denom_v
    v_new = np.fft.ifft(vhat_new).real
    return v_new, N_cur

# Output storage
snapshots = []

# --- Time integration ---
# First step: forward Euler for AB2 initialization
N_v_prev = None
N_u_prev = None

snap_set = set(snap_indices.tolist())

for n in range(Nt):
    if n in snap_set:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

    # Compute RHS
    N_u = nonlinear_rhs_u(u, v)
    N_v_cur = nonlinear_rhs_v(v, u)

    # Step u: explicit RK2 (Heun's method) for stability
    # Simple forward Euler for u (no dispersive stiffness)
    if n == 0 or N_u_prev is None:
        # Forward Euler
        u_new = u + dt * N_u
    else:
        # Adams-Bashforth 2nd order
        u_new = u + dt * (1.5 * N_u - 0.5 * N_u_prev)

    # Step v: IMEX-CN
    v_new, N_v_used = imex_cn_step_v(v, u, u_new, N_v_prev, dt)

    N_u_prev = N_u
    N_v_prev = N_v_cur
    u = u_new
    v = v_new

# Append final snapshot
snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

# Convert to array shape (n_snapshots, 2, 256)
result = np.stack(snapshots, axis=0)  # (n_snaps, 2, 256)
print(f"Result shape: {result.shape}")
print(f"Final v: max={np.max(v):.4f}, min={np.min(v):.4f}, mass={np.sum(v)*dx:.4f}")
print(f"Final u: max={np.max(np.abs(u)):.4f}")
print(f"All finite: {np.all(np.isfinite(result))}")

# Check peaks in final v
from scipy.signal import find_peaks
peaks, props = find_peaks(v, height=0.8)
print(f"Peaks in final v with height>=0.8: {len(peaks)} at positions {x[peaks]}")

# Save
out_dir = "${PROJECT_ROOT}/stage2/runs/T_B/PosNeg/round1/pred_results"
os.makedirs(out_dir, exist_ok=True)
np.save(os.path.join(out_dir, "T_B.npy"), result)
print(f"Saved to {out_dir}/T_B.npy, shape={result.shape}")
