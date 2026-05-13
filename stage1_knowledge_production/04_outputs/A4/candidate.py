import numpy as np
import os

# Domain
L = 30.0  # x in [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Initial condition: KdV soliton
v = 2.0 / np.cosh(x + 5)**2

# Time parameters
T = 2.0
# CFL-like estimate for stability: dt ~ dx^3 / (some factor)
# For KdV with explicit RK4, the stiff 3rd-derivative term
# requires dt << dx^3. dx ~ 30/256 ~ 0.117, dx^3 ~ 0.0016
# Use a very small dt to attempt stability
dt = 1e-5
Nt = int(np.ceil(T / dt))
dt = T / Nt

def v_xxx_fd(v, dx):
    """Central finite difference for third derivative (periodic)."""
    # Use standard central FD: v_xxx ~ (-v_{i+2} + 2v_{i+1} - 2v_{i-1} + v_{i-2}) / (2 dx^3)
    vp1 = np.roll(v, -1)
    vp2 = np.roll(v, -2)
    vm1 = np.roll(v, 1)
    vm2 = np.roll(v, 2)
    return (-vp2 + 2*vp1 - 2*vm1 + vm2) / (2.0 * dx**3)

def v_x_fd(v, dx):
    """Central finite difference for first derivative (periodic)."""
    vp1 = np.roll(v, -1)
    vm1 = np.roll(v, 1)
    return (vp1 - vm1) / (2.0 * dx)

def rhs(v, dx):
    """RHS of KdV: -6 v v_x - v_xxx"""
    return -6.0 * v * v_x_fd(v, dx) - v_xxx_fd(v, dx)

# Explicit RK4 time integration
for n in range(Nt):
    k1 = rhs(v, dx)
    k2 = rhs(v + 0.5 * dt * k1, dx)
    k3 = rhs(v + 0.5 * dt * k2, dx)
    k4 = rhs(v + dt * k3, dx)
    v = v + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)

    # Early exit if blow-up detected
    if not np.isfinite(v).all():
        break

# Save result
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/kdv_A4.npy", v)
