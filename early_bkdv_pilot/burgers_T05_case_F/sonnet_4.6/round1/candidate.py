"""
Inviscid Burgers equation solver using Godunov (exact Riemann) scheme with MUSCL reconstruction (van Leer limiter).
PDE: u_t + (u^2/2)_x = 0 on x in [-1, 1], periodic BC, T=0.5
IC: u_0(x) = -sin(pi * x)
Output: pred_results/burgers_T05.npy, shape (200,)
"""

import numpy as np
import os

# Grid setup
Nx = 200
x_left, x_right = -1.0, 1.0
dx = (x_right - x_left) / Nx
x = x_left + dx / 2 + np.arange(Nx) * dx  # cell centers

# Initial condition
u = -np.sin(np.pi * x)

# Time stepping parameters
T = 0.5
CFL = 0.45

def van_leer_limiter(r):
    """Van Leer flux limiter: (r + |r|) / (1 + |r|)"""
    return (r + np.abs(r)) / (1.0 + np.abs(r))

def godunov_flux(uL, uR):
    """Godunov flux for inviscid Burgers: f(u) = u^2/2"""
    # Entropy-satisfying Godunov flux
    # If uL >= uR: shock — flux is f(uL) if uL+uR >= 0, else f(uR)
    # If uL < uR: rarefaction — flux is f(uL) if uL >= 0, f(uR) if uR <= 0, else 0
    flux = np.where(
        uL >= uR,
        # Shock case: Rankine-Hugoniot speed s = (uL + uR)/2
        np.where((uL + uR) >= 0, 0.5 * uL**2, 0.5 * uR**2),
        # Rarefaction case
        np.where(uL >= 0, 0.5 * uL**2,
                 np.where(uR <= 0, 0.5 * uR**2, 0.0))
    )
    return flux

t = 0.0
while t < T:
    # Adaptive time step based on max wave speed
    max_speed = np.max(np.abs(u))
    if max_speed < 1e-12:
        dt = CFL * dx
    else:
        dt = CFL * dx / max_speed

    if t + dt > T:
        dt = T - t

    # MUSCL reconstruction with van Leer limiter (2nd order in space)
    # Periodic indexing
    u_m1 = np.roll(u, 1)   # u[i-1]
    u_p1 = np.roll(u, -1)  # u[i+1]

    # Compute slopes
    delta_minus = u - u_m1  # backward difference
    delta_plus  = u_p1 - u  # forward difference

    # Van Leer limiter: need ratio r = delta_minus / delta_plus
    # Avoid division by zero
    eps = 1e-10
    r_L = delta_minus / (delta_plus + np.sign(delta_plus + eps) * eps)
    r_R = delta_plus / (delta_minus + np.sign(delta_minus + eps) * eps)

    phi_L = van_leer_limiter(r_L)
    phi_R = van_leer_limiter(r_R)

    # Reconstructed values at cell interfaces
    # Left state at right face of cell i: u_i + 0.5 * phi * delta_plus_i
    # Right state at right face of cell i: u_{i+1} - 0.5 * phi * delta_minus_{i+1}
    u_iR = u + 0.5 * phi_L * delta_plus   # right face, left state (i+1/2 left)
    u_ip1L = u_m1 - 0.5 * phi_R * delta_minus  # This needs rethinking

    # Simpler: reconstruct uL and uR at each interface i+1/2
    # uL[i+1/2] = u[i] + 0.5 * limiter * (u[i] - u[i-1])  -- slope from left
    # uR[i+1/2] = u[i+1] - 0.5 * limiter * (u[i+2] - u[i+1])  -- slope from right

    # Recompute properly
    # slope for cell i using van Leer
    slope = np.zeros(Nx)
    for approach in [True]:  # single pass
        # van Leer limiter: sigma_i = minmod-style based on neighboring differences
        dp = u_p1 - u          # forward
        dm = u - u_m1          # backward
        # Van Leer: phi(r) * dp where r = dm/dp
        # slope = 0.5 * (sign(dp) + sign(dm)) * min(|dp|, |dm|) -- minmod
        # Use van Leer instead:
        denom = np.abs(dp) + np.abs(dm)
        slope = np.where(denom > 1e-12, 2.0 * dp * dm / denom, 0.0)

    # Interface values: u at i+1/2
    uL_face = u + 0.5 * slope            # left state at i+1/2
    uR_face = np.roll(u - 0.5 * slope, -1)  # right state at i+1/2 (from cell i+1)

    # Godunov flux at each interface i+1/2
    F = godunov_flux(uL_face, uR_face)

    # Update: conservative finite volume
    F_left = np.roll(F, 1)  # flux at i-1/2
    u_new = u - (dt / dx) * (F - F_left)

    u = u_new
    t += dt

# Save output
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
np.save(os.path.join(out_dir, "burgers_T05.npy"), u)
print(f"Saved solution: shape={u.shape}, max={u.max():.4f}, min={u.min():.4f}")
