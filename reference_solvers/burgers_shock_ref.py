"""
Reference solver for BKdV-T1: Inviscid Burgers shock formation.

PDE: u_t + u u_x = 0 on x in [-1, 1] periodic
IC : u_0(x) = -sin(pi x)
T  : final time 0.5

Method: Conservative Lax-Friedrichs on a fine grid (Nx=4000) -- robust if
diffusive, converges to the entropy solution. Then downsample to Nx=200.
"""
import numpy as np
import os

os.makedirs("ref_results", exist_ok=True)

def burgers_flux(u):
    return 0.5 * u**2

def lf_step(u, dx, dt):
    """Lax-Friedrichs conservative step for u_t + (u^2/2)_x = 0 on periodic grid."""
    f = burgers_flux(u)
    alpha = np.max(np.abs(u))
    fp = np.roll(f, -1); fm = np.roll(f, 1)
    up = np.roll(u, -1); um = np.roll(u, 1)
    # numerical flux at i+1/2: F_{i+1/2} = 0.5*(f_i + f_{i+1}) - 0.5*alpha*(u_{i+1} - u_i)
    F_iphalf = 0.5*(f + fp) - 0.5*alpha*(up - u)
    F_imhalf = 0.5*(fm + f) - 0.5*alpha*(u - um)
    return u - (dt/dx) * (F_iphalf - F_imhalf)

# fine reference grid
N_fine = 4000
L = 2.0
dx = L / N_fine
x_fine = -1 + dx*0.5 + dx * np.arange(N_fine)
u = -np.sin(np.pi * x_fine)
t = 0.0; T = 0.5
CFL = 0.4
step = 0
while t < T:
    dt = CFL * dx / (np.max(np.abs(u)) + 1e-12)
    if t + dt > T: dt = T - t
    u = lf_step(u, dx, dt)
    t += dt
    step += 1
    if step % 500 == 0:
        print(f"  step {step}, t={t:.3f}, max|u|={np.max(np.abs(u)):.4f}")

print(f"REF done: {step} steps, max|u|={np.max(np.abs(u)):.4f}")

# downsample 4000 → 200 (factor 20) by cell-averaging
u200 = u.reshape(200, 20).mean(axis=1)
x200 = x_fine.reshape(200, 20).mean(axis=1)

np.save("ref_results/burgers_T05_REF.npy", u200)
np.save("ref_results/burgers_T05_REF_x.npy", x200)

# sanity stats
print(f"saved shape={u200.shape} max={u200.max():.4f} min={u200.min():.4f} L1_mean={np.abs(u200).mean():.4f}")
# expected: shock at x=0, |u| jumps from ~+0.8 to ~-0.8
# location of zero-crossing
near_zero = np.argmin(np.abs(u200))
print(f"zero crossing near x={x200[near_zero]:.4f}, u={u200[near_zero]:.4f}")
