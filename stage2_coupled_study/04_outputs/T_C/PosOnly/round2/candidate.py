"""
T_C: Burgers bore interacting with a KdV soliton (Round 2)
Coupled Burgers-swept-KdV system:
  u_t + 3 u u_x = -dx(3v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -dx(u v)

Domain: x in [-15, 15], Nx=256, T=8.0
Method: Split operator approach
  - u: MUSCL-van Leer + Godunov flux for the 3u u_x term (TVD, handles bore)
    coupling term -dx(3v^2 + v_xx) added spectrally
  - v: IMEX-Crank-Nicolson spectral: CN on v_xxx (stiff), explicit on nonlinear
    coupling term -dx(u v) handled explicitly
  - dt chosen conservatively (CFL ~ 0.3 for Burgers, small enough for KdV)
"""

import numpy as np
import os

# Grid
L = 30.0  # domain length [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx_grid = L / Nx

# Wavenumbers
k = 2 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
ik3 = (1j * k) ** 3

# Initial conditions
u = 1.5 * (1 - np.tanh(x / 0.5)) / 2.0
v = 1.5 / np.cosh(x + 8) ** 2

# Time stepping
T_final = 8.0
# Conservative dt: CFL for Burgers u_max ~ 1.5, speed ~ 3*1.5=4.5
# CFL condition: 3*u_max * dt/dx <= 0.4 => dt <= 0.4*dx/(3*1.5)
u_max_est = 1.5
dt = 0.3 * dx_grid / (3.0 * u_max_est + 1e-10)
dt = min(dt, 0.0002)  # also cap for KdV dispersive stability
Nt = int(np.ceil(T_final / dt))
dt = T_final / Nt

# Snapshot times: 8 snapshots to capture encounter
n_snapshots = 8
snapshot_indices = set([int(round(i * Nt / (n_snapshots - 1))) for i in range(n_snapshots)])
snapshot_indices.add(Nt)
snapshot_times_list = sorted(snapshot_indices)
snapshots = []


def godunov_flux_burgers(u_L, u_R):
    """Exact Godunov flux for Burgers: flux = u^2/2, char speed = u."""
    f_L = 0.5 * u_L ** 2
    f_R = 0.5 * u_R ** 2
    flux = np.where(
        u_L >= u_R,
        # Shock: use Rankine-Hugoniot speed s = (u_L + u_R)/2
        np.where((u_L + u_R) / 2.0 >= 0, f_L, f_R),
        # Rarefaction
        np.where(u_L >= 0, f_L, np.where(u_R <= 0, f_R, 0.0)),
    )
    return flux


def van_leer_limiter(r):
    """Van Leer limiter phi(r) = (r + |r|) / (1 + |r|)."""
    return (r + np.abs(r)) / (1.0 + np.abs(r))


def muscl_reconstruct(u_arr):
    """MUSCL reconstruction with van Leer limiter, returns u_L, u_R at cell interfaces."""
    # Differences
    du_fwd = np.roll(u_arr, -1) - u_arr  # u_{i+1} - u_i
    du_bwd = u_arr - np.roll(u_arr, 1)   # u_i - u_{i-1}

    # Ratio (avoid division by zero)
    eps = 1e-14
    r = du_bwd / (du_fwd + np.where(np.abs(du_fwd) < eps, eps * np.sign(du_fwd + eps), 0.0))
    phi = van_leer_limiter(r)

    slope = phi * du_fwd

    # Reconstruct at right face of cell i: u^R_i = u_i + slope_i/2
    # At left face of cell i+1: u^L_{i+1} = u_{i+1} - slope_{i+1}/2
    u_right = u_arr + 0.5 * slope   # right state of cell i
    u_left = u_arr - 0.5 * slope    # left state of cell i

    # At interface i+1/2: left state = u_right_i, right state = u_left_{i+1}
    u_L_face = u_right                        # at right face of cell i
    u_R_face = np.roll(u_left, -1)            # at right face = left face of cell i+1

    return u_L_face, u_R_face


def burgers_rhs_muscl(u_arr):
    """Compute -3 * d/dx(u^2/2) using MUSCL-Godunov = -3 * (F_{i+1/2} - F_{i-1/2}) / dx"""
    u_L_face, u_R_face = muscl_reconstruct(u_arr)
    F = godunov_flux_burgers(u_L_face, u_R_face)
    # flux difference: F_{i+1/2} - F_{i-1/2} = F[i] - F[i-1]
    divF = (F - np.roll(F, 1)) / dx_grid
    return -3.0 * divF


def spectral_dx(f_arr):
    """Spectral derivative d/dx."""
    return np.fft.ifft(ik * np.fft.fft(f_arr)).real


def spectral_d2x(f_arr):
    """Spectral second derivative d^2/dx^2."""
    return np.fft.ifft(-(k ** 2) * np.fft.fft(f_arr)).real


# IMEX-CN denominator for v: (1 - dt/2 * ik^3)
# Precomputed at each step since dt is fixed
cn_denom = 1.0 - (dt / 2.0) * ik3
cn_num_factor = 1.0 + (dt / 2.0) * ik3  # numerator acting on v^n


def step(u_arr, v_arr):
    """One time step using split MUSCL (Burgers) + IMEX-CN (KdV)."""

    # --- u equation: u_t = -3 u u_x - dx(3v^2 + v_xx)
    # Burgers part via MUSCL-Godunov
    rhs_u_burgers = burgers_rhs_muscl(u_arr)

    # Coupling: -dx(3v^2 + v_xx)
    coupling_u = 3.0 * v_arr ** 2 + spectral_d2x(v_arr)
    rhs_u_coupling = -spectral_dx(coupling_u)

    rhs_u = rhs_u_burgers + rhs_u_coupling
    u_new = u_arr + dt * rhs_u

    # --- v equation: v_t + v_xxx = -6 v v_x - dx(u v)
    # IMEX-CN: CN on v_xxx (implicit), explicit on nonlinear
    v_hat = np.fft.fft(v_arr)

    # Explicit nonlinear at time n
    rhs_v_nl = -6.0 * v_arr * spectral_dx(v_arr) - spectral_dx(u_arr * v_arr)
    rhs_v_nl_hat = np.fft.fft(rhs_v_nl)

    # CN update: (1 - dt/2 * ik^3) v^{n+1} = (1 + dt/2 * ik^3) v^n + dt * RHS_explicit
    rhs_hat = cn_num_factor * v_hat + dt * rhs_v_nl_hat
    v_new_hat = rhs_hat / cn_denom
    v_new = np.fft.ifft(v_new_hat).real

    return u_new, v_new


# Time integration
t = 0.0
snap_count = 0

for step_idx in range(Nt + 1):
    if step_idx in snapshot_times_list:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        snap_count += 1
        if snap_count >= n_snapshots:
            break

    if step_idx < Nt:
        u, v = step(u, v)

# Ensure we have at least n_snapshots
while len(snapshots) < n_snapshots:
    snapshots.append(snapshots[-1].copy())

snapshots_arr = np.stack(snapshots[:n_snapshots], axis=0)  # (n_snapshots, 2, 256)

# Save output
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_C.npy")
np.save(out_path, snapshots_arr)

print(f"Saved {snapshots_arr.shape} to {out_path}")
print(f"u range: [{u.min():.3f}, {u.max():.3f}]")
print(f"v peak amplitude: {v.max():.3f}")
print(f"v mass: {v.sum() * dx_grid:.3f}")
print(f"Any NaN: {np.any(np.isnan(snapshots_arr))}")
print(f"Any Inf: {np.any(np.isinf(snapshots_arr))}")
