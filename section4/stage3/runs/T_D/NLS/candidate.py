"""
T_D Compound-soliton attractor — E1 simplest meaningful baseline.

Method: Pseudospectral on primitive (u, N, phi_tilde), explicit RK4 in time.
        Soft regularization sqrt(N+eps) for the +Q term (user's sign).
        Linear phase split: phi = c*x + phi_tilde with phi_tilde periodic
        (c=0.5 from T_A IC).
        Periodic Fourier on x in [-15,15], Nx=256.

Sign convention: USER'S variational sign — +sqrt(N)_xx/(2 sqrt(N)) in HJ.
                 This is the WHOLE POINT of T_D under NLS condition.

Bank rationale: kb-nls-recommended-default-bnls suggests Madelung-Psi default
for smooth IC. BUT here u is independent off-Mcs so Psi alone cannot represent
the state. E1 starts with the next-simplest physically meaningful method:
direct primitive (u, N, phi) RK4 with soft floor + linear phase split.
kb-nls-direct-n-phi-structural-failure warns this may blow up; we run it
to observe failure mode and then escalate.

IC (inherited from T_A spec):
  kappa=1, A=1.5, x in [-15, 15], Nx=256.
  N(x,0) = A^2 * sech^2(A*(x+5))         # bright soliton density, centred x=-5
  phi(x,0) = 0.5*x                       # constant phase gradient phi_x=0.5
  u(x,0) = N*phi_x + eps*cos(2*pi*x/L)   # off-Mcs perturbation
  eps = 0.1 (single epsilon for E1 — extend if budget permits)
  m(x,0) = u - N*phi_x = eps*cos(2*pi*x/L)

T_final = 12.0.  Save 25 snapshots.
Output: pred_results/T_D.npy with shape (n_snapshots, 3, Nx)
        channels = (u, N, phi) where phi = 0.5*x + phi_tilde
"""

import numpy as np
import os
import time

# --------------------------- Domain & grid ---------------------------
Lhalf = 15.0
Nx = 256
L = 2 * Lhalf
x = np.linspace(-Lhalf, Lhalf, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k**2

# Periodic spectral derivative
def dx_sp(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def dxx_sp(f):
    return np.real(np.fft.ifft(-k2 * np.fft.fft(f)))

# --------------------------- Parameters ---------------------------
kappa = 1.0
A = 1.5
c_phase = 0.5
eps_perturb = 0.1
eps_mad = 1e-8           # soft floor sqrt(N + eps_mad)

T_final = 12.0
dt = 1e-3
n_steps = int(round(T_final / dt))
n_snapshots = 25         # 25 snapshots over T=12
snap_every = max(1, n_steps // (n_snapshots - 1))

# --------------------------- Initial condition ---------------------------
N0 = A**2 * (1.0 / np.cosh(A * (x + 5.0)))**2
phi0 = c_phase * x                       # full phi (linear)
phi_tilde0 = phi0 - c_phase * x          # = 0
u0 = N0 * c_phase + eps_perturb * np.cos(2.0 * np.pi * x / L)

print(f"E1 sim: kappa={kappa}, A={A}, eps_perturb={eps_perturb}, dt={dt}, T={T_final}")
print(f"        Nx={Nx}, L={L}, dx={dx:.4f}, n_steps={n_steps}, snap_every={snap_every}")
print(f"        IC: N_max={N0.max():.4f}, N_min={N0.min():.3e}, ||m0||={np.linalg.norm(eps_perturb*np.cos(2*np.pi*x/L))*np.sqrt(dx):.4f}")

# CFL diagnostics
phase_budget = np.pi**2 * Nx**2 * dt / (2 * L**2)
print(f"        Linear-step phase budget pi^2 Nx^2 dt / (2 L^2) = {phase_budget:.3f}")

# --------------------------- RHS function (primitive) ---------------------------
def rhs(u, N, phi_tilde):
    """Compute time derivatives under the user's sign convention:
       m_t + (u m)_x + m u_x = 0,     m = u - N*phi_x
       N_t + d_x((u+phi_x) N) = 0
       phi_t = -u*phi_x - (1/2) phi_x^2 - Q_user + 2*kappa*N
       where Q_user = +(sqrt(N))_xx / (2 sqrt(N)).
    """
    # full phi gradient: phi = c*x + phi_tilde, phi_x = c + phi_tilde_x
    phi_x = c_phase + dx_sp(phi_tilde)
    phi_xx = dxx_sp(phi_tilde)
    m = u - N * phi_x
    u_x = dx_sp(u)
    # Continuity: N_t = -d_x((u+phi_x) * N)
    v = u + phi_x
    Nt = -dx_sp(v * N)
    # Madelung quantum pressure with soft regularization (user's +sign)
    sqrtN = np.sqrt(N + eps_mad)
    sqrtN_xx = dxx_sp(sqrtN)
    Q_user = +sqrtN_xx / (2.0 * sqrtN)
    # HJ: phi_t = -u phi_x - (1/2) phi_x^2 - Q_user + 2*kappa*N
    phit = -u * phi_x - 0.5 * phi_x**2 - Q_user + 2.0 * kappa * N
    # phi_tilde_t = phi_t  (since c*x is time-independent)
    phi_tilde_t = phit
    # m: m_t = -(u m)_x - m u_x = -(u m)_x - m u_x. We can derive u_t from m_t and (Nphi_x)_t.
    # Use: u = m + N*phi_x.  u_t = m_t + N_t*phi_x + N*phi_x_t = m_t + N_t*phi_x + N*phit_x.
    # m_t = -(u m)_x - m u_x  (per system eqn). Expand: d_x(u m) = u_x m + u m_x. So:
    # m_t = -u_x m - u m_x - m u_x = -2 u_x m - u m_x
    mt = -2.0 * u_x * m - u * dx_sp(m)
    phit_x = dx_sp(phit)
    ut = mt + Nt * phi_x + N * phit_x
    return ut, Nt, phi_tilde_t

# --------------------------- RK4 step ---------------------------
def rk4_step(u, N, phi_tilde, dt):
    k1u, k1N, k1p = rhs(u, N, phi_tilde)
    k2u, k2N, k2p = rhs(u + 0.5*dt*k1u, N + 0.5*dt*k1N, phi_tilde + 0.5*dt*k1p)
    k3u, k3N, k3p = rhs(u + 0.5*dt*k2u, N + 0.5*dt*k2N, phi_tilde + 0.5*dt*k2p)
    k4u, k4N, k4p = rhs(u + dt*k3u,     N + dt*k3N,     phi_tilde + dt*k3p)
    u_new = u + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    N_new = N + (dt/6.0) * (k1N + 2*k2N + 2*k3N + k4N)
    p_new = phi_tilde + (dt/6.0) * (k1p + 2*k2p + 2*k3p + k4p)
    return u_new, N_new, p_new

# --------------------------- Integrate ---------------------------
snap_indices = []
snaps_u = []
snaps_N = []
snaps_phi = []
ts = []

u = u0.copy()
N = N0.copy()
phi_tilde = phi_tilde0.copy()

# initial snapshot
def save_snap(step, t):
    snap_indices.append(step)
    snaps_u.append(u.copy())
    snaps_N.append(N.copy())
    snaps_phi.append(c_phase * x + phi_tilde)
    ts.append(t)

save_snap(0, 0.0)

t_start = time.time()
t = 0.0
mass0 = np.sum(N) * dx
blowup = False
for step in range(1, n_steps + 1):
    u, N, phi_tilde = rk4_step(u, N, phi_tilde, dt)
    t = step * dt
    # blowup check
    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(N)) or not np.all(np.isfinite(phi_tilde)):
        print(f"  BLOWUP detected at step {step}, t={t:.4f}")
        blowup = True
        break
    if np.max(np.abs(u)) > 1e6 or np.max(np.abs(N)) > 1e6 or np.max(np.abs(phi_tilde)) > 1e6:
        print(f"  RUNAWAY detected at step {step}, t={t:.4f}: |u|max={np.max(np.abs(u)):.3e}, |N|max={np.max(np.abs(N)):.3e}, |phi_tilde|max={np.max(np.abs(phi_tilde)):.3e}")
        blowup = True
        break
    # mass drift check
    mass_t = np.sum(N) * dx
    if abs(mass_t - mass0) / abs(mass0) > 1.0:  # 100% drift — give up
        print(f"  MASS BLOWUP at step {step}, t={t:.4f}: mass = {mass_t:.3f} vs {mass0:.3f}")
        blowup = True
        break
    if step % snap_every == 0 and len(snap_indices) < n_snapshots:
        save_snap(step, t)
        # progress diagnostic
        phi_x_now = c_phase + dx_sp(phi_tilde)
        m_now = u - N * phi_x_now
        mnorm = np.sqrt(np.sum(m_now**2) * dx)
        print(f"  t={t:.3f}: ||m||_2={mnorm:.4f}, max|u|={np.max(np.abs(u)):.3f}, max(N)={N.max():.3f}, min(N)={N.min():.3e}, mass_drift={(mass_t-mass0)/mass0:.3e}")

# ensure final snapshot
if not blowup and len(snap_indices) < n_snapshots:
    save_snap(n_steps, t)

t_wall = time.time() - t_start
print(f"E1 done: t_final={t:.3f}, wall={t_wall:.2f}s, blowup={blowup}, n_snaps={len(snap_indices)}")

# --------------------------- Save output ---------------------------
out = np.stack([
    np.array(snaps_u),
    np.array(snaps_N),
    np.array(snaps_phi),
], axis=1)
# Reshape to (n_snapshots, 3, Nx) — currently it's (n_snapshots, 3, Nx)
print(f"Output shape: {out.shape}")
print(f"ts: {ts}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_D.npy", out)

# Also save ts and basic diagnostics for reasoning.md
diag = {
    'ts': np.array(ts),
    'blowup': blowup,
    't_final': t,
    'mass0': mass0,
    'mass_final': np.sum(snaps_N[-1]) * dx,
}
np.savez("pred_results/T_D_diag.npz", **diag)

print("Saved pred_results/T_D.npy")
