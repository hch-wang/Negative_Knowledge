import numpy as np

# Grid
L = 30.0
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = x[1] - x[0]

# Initial condition
v = 1.5 / np.cosh(x + 5)**2

# Time parameters
T = 2.0
# CFL-like estimate for third derivative: dt ~ dx^3 / 2 for stability (very restrictive)
dt = 1e-5
Nt = int(np.ceil(T / dt))
dt = T / Nt

def rhs(v):
    # First derivative: central difference
    vx = (np.roll(v, -1) - np.roll(v, 1)) / (2 * dx)
    # Third derivative: standard 2nd-order central FD
    # v_xxx ~ (v[i+2] - 2v[i+1] + 2v[i-1] - v[i-2]) / (2 dx^3)
    vxxx = (np.roll(v, -2) - 2*np.roll(v, -1) + 2*np.roll(v, 1) - np.roll(v, 2)) / (2 * dx**3)
    # Gardner equation: v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0
    return -(6*v*vx + 1.5*v**2*vx + vxxx)

# Explicit RK4 time integration
for _ in range(Nt):
    k1 = rhs(v)
    k2 = rhs(v + 0.5*dt*k1)
    k3 = rhs(v + 0.5*dt*k2)
    k4 = rhs(v + dt*k3)
    v = v + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
    if not np.isfinite(v).all():
        break

np.save("pred_results/gardner_G1.npy", v)
