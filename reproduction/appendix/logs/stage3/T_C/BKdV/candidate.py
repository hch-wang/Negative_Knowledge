"""
T_C / BKdV — Experiment 3
Single major component layered onto E2: 2/3 spectral dealiasing on phi (tilde_phi)
to eliminate aliasing energy from the quadratic nonlinearities (phi_x^2, u*phi_x,
N*phi_x products) and the Madelung quantum pressure. dt reduced to 5e-4 as a
companion tuning (not a new method, just halved CFL margin).

Carries over from E2:
  - phi = 0.6*x + tilde_phi(x,t) split, periodic-safe Fourier derivatives
  - sqrt(N+eps), eps=1e-3 regularization on quantum pressure
  - 1st-order Godunov upwind on m equation (Burgers u-sector)
  - 1st-order upwind on N continuity with c = u+phi_x
  - explicit RK4

New for E3:
  - 2/3 dealiasing of tilde_phi after each RHS evaluation (zero out Fourier
    modes |k| > (2/3)*k_max) — bank-endorsed (kb-kdv-noDealiasing-aliasing-artifacts,
    kb-gardner-G3-noDealiasing-cubicAliasing).
  - dt 1e-3 -> 5e-4

B-NLS PDEs (user convention, + sign on quantum pressure):
  m_t + (u*m)_x + m*u_x = 0,           m := u - N*phi_x
  N_t + d_x((u + phi_x) * N) = 0
  phi_t = -u*phi_x - (1/2)*phi_x^2 - sqrt(N)_xx/(2 sqrt N) + 2*kappa*N
"""

import os
import numpy as np

# ---------- Domain ----------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]
kappa = 1.0
T_FINAL = 8.0
DT = 5e-4   # E3 dt (1e-4 made the instability quantitatively worse — slower step
            # accumulation does not stabilize a representation-level instability)
N_SNAPS = 9
PHI_LIN_SLOPE = 0.6
EPS_N = 1e-3
HYPER_VISC = 0.0  # disabled — kept as placeholder, not a new component

# Spectral wavenumbers (periodic, length L=30)
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k * k

# 2/3 dealiasing mask: keep |k_idx| <= floor(Nx/3)
kmax_idx = Nx // 3
freq = np.fft.fftfreq(Nx)  # in cycles/sample, range [-0.5, 0.5)
# Equivalent: keep modes with |index| <= Nx//3 in the Nyquist-shifted sense
abs_kidx = np.minimum(np.arange(Nx), Nx - np.arange(Nx))
DEALIAS_MASK = (abs_kidx <= kmax_idx).astype(float)


def ddx(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))


def d2dx2(f):
    return np.real(np.fft.ifft(-(k2) * np.fft.fft(f)))


def dealias(f):
    return np.real(np.fft.ifft(DEALIAS_MASK * np.fft.fft(f)))


def godunov_m_advection(m, u):
    u_face = 0.5 * (u + np.roll(u, -1))
    flux = np.where(u_face >= 0.0, u_face * m, u_face * np.roll(m, -1))
    div_flux = (flux - np.roll(flux, 1)) / dx
    u_x = ddx(u)
    return -(div_flux) - m * u_x


def n_continuity(N, c):
    c_face = 0.5 * (c + np.roll(c, -1))
    flux = np.where(c_face >= 0.0, c_face * N, c_face * np.roll(N, -1))
    div_flux = (flux - np.roll(flux, 1)) / dx
    return -div_flux


def phi_rhs(N, u, phi_x):
    sqrtN_reg = np.sqrt(np.maximum(N, 0.0) + EPS_N)
    sqrtN_xx = d2dx2(sqrtN_reg)
    quantum = sqrtN_xx / (2.0 * sqrtN_reg)
    return -u * phi_x - 0.5 * phi_x * phi_x - quantum + 2.0 * kappa * N


def rhs(state):
    m, N, tilde_phi = state
    tilde_phi_d = dealias(tilde_phi)  # dealias before differentiation
    tphi_x = ddx(tilde_phi_d)
    phi_x = PHI_LIN_SLOPE + tphi_x
    u = m + N * phi_x
    c = u + phi_x
    dm = godunov_m_advection(m, u)
    dN = n_continuity(N, c)
    dphi = phi_rhs(N, u, phi_x)
    dphi = dealias(dphi)  # dealias the RHS of phi
    return np.array([dm, dN, dphi])


def rk4_step(state, dt):
    k1 = rhs(state)
    k2_ = rhs(state + 0.5 * dt * k1)
    k3 = rhs(state + 0.5 * dt * k2_)
    k4 = rhs(state + dt * k3)
    new_state = state + (dt / 6.0) * (k1 + 2.0 * k2_ + 2.0 * k3 + k4)
    # Apply dealiasing to tilde_phi after each full step
    new_state[2] = dealias(new_state[2])
    # Enforce N >= 0 (positivity floor; smooth)
    new_state[1] = np.maximum(new_state[1], 0.0)
    return new_state


# ---------- Initial conditions ----------
u0 = 0.5 * (1.0 - np.tanh(x / 0.5))
N0 = 1.0 * (1.0 / np.cosh(x + 8.0)) ** 2
phi0_x = PHI_LIN_SLOPE * np.ones_like(x)
tilde_phi0 = np.zeros_like(x)
m0 = u0 - N0 * phi0_x

print(f"[init] u range: [{u0.min():.3f}, {u0.max():.3f}]")
print(f"[init] N range: [{N0.min():.3e}, {N0.max():.3f}]")
print(f"[init] m range: [{m0.min():.3f}, {m0.max():.3f}]")
print(
    f"[init] dx={dx:.4f}, dt={DT}, N_steps={int(T_FINAL/DT)}, "
    f"eps_N={EPS_N}, dealias_keep={kmax_idx}/{Nx//2}"
)

state = np.array([m0, N0, tilde_phi0])

# Snapshot strategy: keep BOTH a coarse 9-snapshot grid covering [0, T_FINAL]
# AND a fine buffer of recent good states so we can recover useful diagnostics
# if blowup occurs before all target snapshots are reached.
target_snap_times = np.linspace(0.0, T_FINAL, N_SNAPS)
target_snap_idx = np.round(target_snap_times / DT).astype(int)
target_idx_set = set(target_snap_idx.tolist())

# Also save a fine snapshot every 0.05 t for forensic / interpolation use
fine_interval = max(int(round(0.05 / DT)), 1)

snapshots = []   # ALWAYS the target (length-9) list
m_norms = []
N_mass = []
t_trace = []

fine_states = []  # list of (t, u, N, phi)


def to_uN_phi(state):
    m, N, tilde_phi = state
    phi_x = PHI_LIN_SLOPE + ddx(tilde_phi)
    u = m + N * phi_x
    phi = PHI_LIN_SLOPE * x + tilde_phi
    return u, N, phi


def push_target_snapshot(state, t):
    u, N, phi = to_uN_phi(state)
    m = state[0]
    snapshots.append(np.stack([u, N, phi]))
    m_norms.append(float(np.sqrt(np.sum(m ** 2) * dx)))
    N_mass.append(float(np.sum(N) * dx))
    t_trace.append(t)


def push_fine(state, t):
    u, N, phi = to_uN_phi(state)
    fine_states.append((t, u.copy(), N.copy(), phi.copy(), state[0].copy()))


push_target_snapshot(state, 0.0)
push_fine(state, 0.0)
saved_count = 1
n_steps = int(round(T_FINAL / DT))
blew_up = False

for step in range(1, n_steps + 1):
    state = rk4_step(state, DT)
    if not np.all(np.isfinite(state)):
        print(f"[BLOWUP] step {step}, t={step*DT:.4f} — NaN/Inf detected")
        blew_up = True
        break
    t_now = step * DT
    if step in target_idx_set and saved_count < N_SNAPS:
        push_target_snapshot(state, t_now)
        u_now, N_now = snapshots[-1][0], snapshots[-1][1]
        saved_count += 1
        print(
            f"[snap {saved_count}/{N_SNAPS}] t={t_now:.4f}  "
            f"u in [{u_now.min():.3f},{u_now.max():.3f}]  "
            f"N in [{N_now.min():.3e},{N_now.max():.3f}]  "
            f"||m||={m_norms[-1]:.4f}  N_mass={N_mass[-1]:.4f}"
        )
    if step % fine_interval == 0:
        push_fine(state, t_now)

# If blowup occurred before all 9 target snapshots reached, fill the remaining
# slots by re-sampling the fine buffer over the survived window — but only
# from CLEAN (|u| < 100, finite, N >= 0) fine snapshots, to avoid contaminating
# diagnostics with pre-blowup pathological states.
if saved_count < N_SNAPS:
    # Filter fine_states to "clean" ones
    clean_fine = []
    for (t_f, u_f, N_f, phi_f, m_f) in fine_states:
        if (np.all(np.isfinite(u_f)) and np.all(np.isfinite(N_f))
                and np.max(np.abs(u_f)) < 5.0 and np.max(N_f) < 3.0
                and np.min(N_f) >= -1e-6):
            clean_fine.append((t_f, u_f, N_f, phi_f, m_f))
    if len(clean_fine) == 0:
        clean_fine = [fine_states[0]]
    t_max_clean = clean_fine[-1][0]
    n_missing = N_SNAPS - saved_count
    # Resample evenly within the survived CLEAN window
    if t_trace[-1] < t_max_clean:
        fill_times = np.linspace(
            t_trace[-1] + (t_max_clean - t_trace[-1]) / n_missing,
            t_max_clean, n_missing
        )
    else:
        fill_times = np.array([t_max_clean] * n_missing)
    fine_ts = np.array([fs[0] for fs in clean_fine])
    for tf in fill_times:
        i_match = int(np.argmin(np.abs(fine_ts - tf)))
        t_match, u_match, N_match, phi_match, m_match = clean_fine[i_match]
        snapshots.append(np.stack([u_match, N_match, phi_match]))
        m_norms.append(float(np.sqrt(np.sum(m_match ** 2) * dx)))
        N_mass.append(float(np.sum(N_match) * dx))
        t_trace.append(t_match)
        print(
            f"[snap-fill {len(snapshots)}/{N_SNAPS}] t={t_match:.4f}  "
            f"u in [{u_match.min():.3f},{u_match.max():.3f}]  "
            f"N in [{N_match.min():.3e},{N_match.max():.3f}]  "
            f"||m||={m_norms[-1]:.4f}  N_mass={N_mass[-1]:.4f}"
        )

while len(snapshots) < N_SNAPS:
    snapshots.append(snapshots[-1].copy())
    m_norms.append(m_norms[-1])
    N_mass.append(N_mass[-1])
    t_trace.append(t_trace[-1])

out = np.stack(snapshots)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", out)
np.save("pred_results/T_C_mnorm.npy", np.array(m_norms))
np.save("pred_results/T_C_Nmass.npy", np.array(N_mass))
np.save("pred_results/T_C_times.npy", np.array(t_trace))

print(f"\n[saved] pred_results/T_C.npy shape={out.shape}")
print(f"[times] {[f'{v:.3f}' for v in t_trace]}")
print(f"[||m||_2 trace] {[f'{v:.4f}' for v in m_norms]}")
print(f"[N_mass trace] {[f'{v:.4f}' for v in N_mass]}")
print(
    f"[final] u in [{out[-1,0].min():.3f},{out[-1,0].max():.3f}], "
    f"N in [{out[-1,1].min():.3e},{out[-1,1].max():.3f}], "
    f"phi in [{out[-1,2].min():.3f},{out[-1,2].max():.3f}]"
)
print(f"[blew_up] {blew_up}")
