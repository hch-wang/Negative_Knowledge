"""
T_C E2: Spectral RK4 baseline (from E1) with ONE single-component upgrade:
  -3 u u_x  =  -(3/2) d_x(u^2)  --> MUSCL-van-Leer reconstruction + Godunov flux
                                    (replaces spectral handling of u-Burgers nonlinearity)

EVERYTHING else from E1 unchanged:
  - v_xxx, v_x, v^2_x  -> Fourier spectral
  - d_x(3 v^2 + v_xx) coupling -> Fourier spectral
  - d_x(u v) coupling -> Fourier spectral
  - Time integrator: explicit RK4
  - No dealiasing, no IMEX, no filter

Justification (bank): kb-burgers-MUSCL-Godunov-shock-pass establishes MUSCL+Godunov
as the proven single-component spatial upgrade for sharp bores in coupled
Burgers-swept-KdV problems.

PDE:
  u_t + 3 u u_x = -d_x (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x (u v)
"""
import numpy as np
import os

# --- Grid ---
L = 30.0
Nx = 256
dx = L / Nx
x = -15.0 + dx * np.arange(Nx)  # cell-center grid, periodic

# Wavenumbers
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
mk2 = -(k**2)
ik3 = 1j * k**3

# --- ICs ---
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 / np.cosh(x + 8.0) ** 2

# ----- Spectral helpers -----
def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def d2x_spec(f):
    return np.real(np.fft.ifft(mk2 * np.fft.fft(f)))

def d3x_spec(f):
    return np.real(np.fft.ifft(ik3 * np.fft.fft(f)))

# ----- MUSCL + Godunov for Burgers flux f(u) = (3/2) u^2 -----
# Conservative finite-volume update of u_t = -(3/2) d_x(u^2)
# = -(F_{i+1/2} - F_{i-1/2}) / dx
# with cell averages u_i (treat point values at cell centers as cell averages).

def van_leer(r):
    """van Leer limiter phi(r). r is ratio of consecutive slopes."""
    # phi = (r + |r|) / (1 + |r|)
    return (r + np.abs(r)) / (1.0 + np.abs(r) + 1e-300)

def muscl_godunov_burgers_dudt(u):
    """Compute -(3/2) d_x(u^2) on the periodic grid via MUSCL+Godunov.

    Returns array of length Nx of d(u)/dt contributions from the Burgers self-flux.

    Steps:
      1) Compute backward and forward differences du_b, du_f.
      2) Limited slope sigma_i = van_leer(r_i) * du_b   where r_i = du_f/du_b.
         (using a slope-limiter formulation that returns 0 at extrema)
      3) Left/right cell-edge states:
           uL_{i+1/2} = u_i + 0.5 * sigma_i
           uR_{i+1/2} = u_{i+1} - 0.5 * sigma_{i+1}
      4) Godunov flux for f(u) = (3/2) u^2 (convex):
           if uL <= uR:
              F = min over [uL, uR] of (3/2) u^2 with stationary point at 0
              = (3/2) * (0 if uL<=0<=uR else min(uL^2, uR^2))
           else (uL > uR):
              F = max over [uR, uL] of (3/2) u^2
              = (3/2) * max(uL^2, uR^2)
      5) du/dt = -(F_{i+1/2} - F_{i-1/2})/dx
    """
    # backward and forward differences (periodic)
    du_b = u - np.roll(u, 1)       # u_i - u_{i-1}
    du_f = np.roll(u, -1) - u      # u_{i+1} - u_i
    # van Leer slope using phi(r) form  (equivalent to 2 du_b du_f / (du_b + du_f) when same sign)
    eps = 1e-30
    sigma = (np.sign(du_b) + np.sign(du_f)) * np.abs(du_b * du_f) / (np.abs(du_b) + np.abs(du_f) + eps)
    # cell-edge states at i+1/2 (left state from cell i, right state from cell i+1)
    uL = u + 0.5 * sigma
    uR_next = np.roll(u, -1) - 0.5 * np.roll(sigma, -1)
    # Godunov flux for convex f(u) = (3/2) u^2, sonic point at u=0
    F = np.empty_like(u)
    # vectorized branches
    le = uL <= uR_next
    # case 1: uL <= uR
    # min over [uL,uR] of (3/2)u^2 = 0 if 0 in [uL,uR] else min((3/2)uL^2, (3/2)uR^2)
    contains_zero = (uL <= 0) & (uR_next >= 0)
    F1 = 1.5 * np.minimum(uL * uL, uR_next * uR_next)
    F1 = np.where(contains_zero, 0.0, F1)
    # case 2: uL > uR
    F2 = 1.5 * np.maximum(uL * uL, uR_next * uR_next)
    F = np.where(le, F1, F2)
    # du/dt = -(F_{i+1/2} - F_{i-1/2}) / dx
    return -(F - np.roll(F, 1)) / dx

# ----- Combined RHS -----
def rhs(u, v):
    # Burgers self-flux on u: MUSCL+Godunov  (single-component upgrade)
    du_burgers = muscl_godunov_burgers_dudt(u)
    # Coupling into u: -d_x(3 v^2 + v_xx), spectral
    vh = np.fft.fft(v)
    vxx = np.real(np.fft.ifft(mk2 * vh))
    v2x = dx_spec(v * v)
    vxx_x = dx_spec(vxx)
    du = du_burgers - (3.0 * v2x + vxx_x)
    # v sector: spectral, exactly as E1
    vx = dx_spec(v)
    vxxx = np.real(np.fft.ifft(ik3 * vh))
    uv_x = dx_spec(u * v)
    dv = -6.0 * v * vx - vxxx - uv_x
    return du, dv

def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v)
    u_new = u + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v_new = v + (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v)
    return u_new, v_new

# --- Time stepping ---
T = 8.0
# dt limited by spectral v_xxx dispersion: |dt * k_max^3| < 2.78 for RK4
# k_max = pi*Nx/L ~ 26.81, k_max^3 ~ 19250, so dt < 1.44e-4
dt = 1e-4
n_steps = int(np.ceil(T / dt))
dt = T / n_steps

n_snapshots = 21
snap_every = max(1, n_steps // (n_snapshots - 1))

snapshots = []
u, v = u0.copy(), v0.copy()
snapshots.append(np.stack([u.copy(), v.copy()]))

t = 0.0
blow = False
for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    t += dt
    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        print(f"BLEW UP at step {step}, t={t:.4f}")
        blow = True
        break
    if step % snap_every == 0 or step == n_steps:
        snapshots.append(np.stack([u.copy(), v.copy()]))
        umax = float(np.max(np.abs(u)))
        vmax = float(np.max(v))
        if step % (snap_every*4) == 0 or step == n_steps:
            print(f"  step {step}/{n_steps} t={t:.3f} |u|_max={umax:.3f} v_max={vmax:.3f}")

out = np.stack(snapshots, axis=0)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", out)

u_fin = out[-1, 0]; v_fin = out[-1, 1]
print(f"shape = {out.shape}")
print(f"final |u|_max = {np.max(np.abs(u_fin)):.4f}")
print(f"final v_max  = {np.max(v_fin):.4f}")
print(f"final v_min  = {np.min(v_fin):.4f}")
# locate v peak
ix = int(np.argmax(v_fin))
print(f"final v peak: x={x[ix]:.2f}, value={v_fin[ix]:.4f}")
print(f"all finite   = {np.all(np.isfinite(out))}")
print(f"blew up      = {blow}")
print(f"u mass = {np.sum(u_fin)*dx:.4f}  v mass = {np.sum(v_fin)*dx:.4f}")
print(f"initial u mass = {np.sum(u0)*dx:.4f}  initial v mass = {np.sum(v0)*dx:.4f}")
