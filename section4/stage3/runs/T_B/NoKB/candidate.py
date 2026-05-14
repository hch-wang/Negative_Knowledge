"""
E2: E1 + quantum-pressure background regularization.

Single-component change from E1: replace
    Q = (sqrt N)_xx / (2 sqrt N)
with
    Q_reg = (sqrt(N + eps2))_xx / (2 sqrt(N + eps2))
where eps2 = 1e-4.  In regions where N >> eps2, Q_reg ~ Q.  In regions where
N -> 0, sqrt(N + eps2) ~ eps stays bounded away from zero, killing the
denominator singularity that destroyed E1.  The diagnostic at t=0 showed
Q_numerical ~ 22 vs Q_analytical ~ 1.2 due to N underflowing to ~1e-77 in
the Gaussian tails.

Spatial: Fourier pseudospectral on (u, N, phi_p), Nx=256, x in [-15,15].
Time: explicit RK4 with dt=2e-4 (same as bug-fixed E1 attempt).
phi = phi_lin + phi_p with phi_lin = 0.3 * x carried analytically.
"""

import os
import numpy as np

# ---------------- domain --------------------------------------------------
Lx = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = Lx / Nx
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k

def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def dxx_spec(f):
    return np.real(np.fft.ifft(-(k * k) * np.fft.fft(f)))

# ---------------- parameters ----------------------------------------------
kappa = 1.0
T = 6.0
dt = 2e-4
nsteps = int(round(T / dt))
n_snapshots = 21
snap_every = max(1, nsteps // (n_snapshots - 1))
EPS2 = 1e-4  # background regularization in sqrt argument
PHIX_LIN = 0.3

# ---------------- initial condition ---------------------------------------
N0 = 2.0 * np.exp(-(x + 5.0) ** 2 / 2.25)
phi_p0 = np.zeros_like(x)
u0 = PHIX_LIN * N0

# Diagnostic: regularized Q at t=0
sqrtN0_reg = np.sqrt(N0 + EPS2)
Q0 = dxx_spec(sqrtN0_reg) / (2.0 * sqrtN0_reg)
print(f"[E2 init] max N0 = {N0.max():.6f}, mass(N0) = {N0.sum()*dx:.6f}")
print(f"[E2 init] |Q_reg(t=0)| max = {np.max(np.abs(Q0)):.3f}  (was 21.7 in E1)")

# ---------------- RHS -----------------------------------------------------
def rhs(u, N, phi_p):
    ux = dx_spec(u)
    phix = PHIX_LIN + dx_spec(phi_p)
    sqrtN_reg = np.sqrt(N + EPS2)
    Q = dxx_spec(sqrtN_reg) / (2.0 * sqrtN_reg)

    phi_p_t = -(u * phix + 0.5 * phix * phix + Q - 2.0 * kappa * N)
    phi_xt = dx_spec(phi_p_t)

    flux_N = (u + phix) * N
    Nt = -dx_spec(flux_N)

    m = u - N * phix
    mt = -dx_spec(u * m) - m * ux
    ut = mt + Nt * phix + N * phi_xt
    return ut, Nt, phi_p_t

def rk4_step(u, N, phi_p, dt):
    k1u, k1N, k1p = rhs(u, N, phi_p)
    k2u, k2N, k2p = rhs(u + 0.5 * dt * k1u, N + 0.5 * dt * k1N, phi_p + 0.5 * dt * k1p)
    k3u, k3N, k3p = rhs(u + 0.5 * dt * k2u, N + 0.5 * dt * k2N, phi_p + 0.5 * dt * k2p)
    k4u, k4N, k4p = rhs(u + dt * k3u, N + dt * k3N, phi_p + dt * k3p)
    return (
        u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u),
        N + (dt / 6.0) * (k1N + 2 * k2N + 2 * k3N + k4N),
        phi_p + (dt / 6.0) * (k1p + 2 * k2p + 2 * k3p + k4p),
    )

# ---------------- run -----------------------------------------------------
phi_lin = PHIX_LIN * x
snapshots = []
times = []
u = u0.copy()
N = N0.copy()
phi_p = phi_p0.copy()

def snap(u, N, phi_p, t):
    snapshots.append(np.stack([u, N, phi_lin + phi_p], axis=0))
    times.append(t)

snap(u, N, phi_p, 0.0)

blown_up = False
for step in range(1, nsteps + 1):
    u, N, phi_p = rk4_step(u, N, phi_p, dt)
    if not (np.isfinite(N).all() and np.isfinite(u).all() and np.isfinite(phi_p).all()):
        print(f"[E2] BLOW UP at step {step}, t={step*dt:.4f}")
        blown_up = True
        break
    if step % snap_every == 0:
        t_now = step * dt
        snap(u, N, phi_p, t_now)
        print(f"[E2] t={t_now:6.3f}  maxN={N.max():8.4f}  minN={N.min():10.3e}  maxU={np.max(np.abs(u)):8.4f}  mass={N.sum()*dx:9.5f}  maxPhi={np.max(np.abs(phi_p+phi_lin)):8.4f}")

if not blown_up and times[-1] < T - 1e-9:
    snap(u, N, phi_p, nsteps * dt)

out = np.stack(snapshots, axis=0)
print(f"[E2] final shape = {out.shape}, blown_up={blown_up}, T_end={times[-1]:.4f}")
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", out)
np.save("pred_results/T_B_times.npy", np.asarray(times))
print(f"[E2] saved pred_results/T_B.npy ({out.shape[0]} snapshots)")
