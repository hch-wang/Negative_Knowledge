"""
T_D / NLSBKdV  --  Experiment E3
Compound-Soliton attractor under user's +sqrt(N)_xx/(2 sqrt(N)) sign convention.

E3 method: Strang split-step on (Psi_tilde, m).
  - LINEAR step in Fourier:  Psi_k -> exp(+i k^2 dt/2) Psi_k  (user's flipped kinetic).
    This is unitary, |Psi|^2 mass conserved exactly, no division by N.
  - NONLINEAR step (pointwise with FROZEN coefficients):
        Psi -> Psi * exp(-(1/2)(u_x + u N_x/N) dt) * exp(-i (2 Q + u phi_x - 2 kappa N) dt)
    The real-exponent factor accounts for the off-Mcs continuity (u_x + u N_x/N is bounded
    analytically as O(1) in tails); the imaginary-exponent factor is the user's-sign Q,
    advection and chemical-potential term.  Coefficients are frozen at the start of the
    sub-step (Strang accuracy O(dt^2)).
  - m equation handled with RK4 in real space:  m_t = -u m_x - 2 u_x m.

Differences from E2 (single component upgrade per discipline):
  - Time scheme: RK4 -> Strang split-step Fourier + pointwise nonlinear.
  - Plus: aggressive spectral filter exp(-36 (k/k_max)^36) on Psi to suppress aliasing
    in low-N tails (this complements 2/3 dealiasing).

Bank citations (full set):
  - kb-nls-strang-splitstep-bright-soliton, kb-nls-cfl-split-step, kb-nls-madelung-psi-handles-zero-density,
    kb-nls-23-dealiasing-cubic, kb-nls-sign-convention, kb-nls-mcs-not-attractor-standard-sign,
    kb-nls-hard-floor-counterproductive, kb-nls-split-linear-phase, kb-nls-mass-conservation-not-sufficient,
    kb-nls-mcs-not-sufficient, kb-nls-energy-drift-vs-mass-drift, kb-nls-recommended-default-bnls.
  - BKdV: rejects MUSCL (no shock), rejects IFRK4 (kb-kdv-IFRK4-blowup) — Strang is more robust
    for split-step Fourier; kb-kdv-noDealiasing-aliasing-artifacts supports dealiasing.
"""

import numpy as np
import os, sys, time

# ----- domain & parameters -----
L_box = 30.0
Nx = 256
x = np.linspace(-L_box / 2, L_box / 2, Nx, endpoint=False)
dx = L_box / Nx
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k * k

k_max = np.max(np.abs(k))
dealias_mask = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)
# exponential smoothing filter as extra defense against aliasing in tails
expfilter = np.exp(-36.0 * (np.abs(k) / k_max) ** 36)

# ----- IC parameters -----
kappa = 1.0
A_sol = 1.5
x0_soliton = -5.0
v_boost = 0.5
eps_perturb = 0.1
eps_reg = 1e-3   # raised aggressively to keep 1/N reconstruction bounded in tails
alpha_clip = 50.0  # alpha*dt clipped to +/- 50 to avoid overflow in exp

T_final = 12.0
dt = 5e-4
n_steps = int(round(T_final / dt))
n_snapshots = 25
snap_stride = max(1, n_steps // (n_snapshots - 1))

# Linear-step kinetic propagator under user's sign: i Psi_t = -(1/2) Psi_xx  =>  Psi_k *= exp(+i k^2 dt/2)
kin_half = np.exp(1j * 0.5 * k2 * (dt / 2.0))
kin_full = np.exp(1j * 0.5 * k2 * dt)

# ----- initial condition -----
N0 = (A_sol ** 2) / np.cosh(A_sol * (x - x0_soliton)) ** 2
phi_tilde0 = np.zeros_like(x)
u0 = v_boost * N0 + eps_perturb * np.cos(2.0 * np.pi * x / L_box)
m0 = u0 - N0 * (v_boost + 0.0)

# Psi_tilde
Psi = np.sqrt(N0 + 1e-30) * np.exp(1j * phi_tilde0)
m = m0.copy()

# ----- helpers -----
def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def d2x_spec(f):
    return np.real(np.fft.ifft(-k2 * np.fft.fft(f)))

def dx_spec_complex(f):
    return np.fft.ifft(ik * np.fft.fft(f))

def dealias(f):
    if np.iscomplexobj(f):
        return np.fft.ifft(np.fft.fft(f) * dealias_mask)
    return np.real(np.fft.ifft(np.fft.fft(f) * dealias_mask))

def linear_step(Psi, prop):
    Pk = np.fft.fft(Psi) * prop * expfilter
    return np.fft.ifft(Pk)

def compute_coefs(Psi, m):
    """Compute the real-valued coefficients alpha (continuity divergence) and
       beta (potential phase) for the nonlinear pointwise step.
       alpha = (1/2)(u_x + u N_x/N) computed safely via (1/2) (u N)_x / N
       beta  = 2 Q + u phi_x - 2 kappa N
       Q = (sqrt(N))_xx / (2 sqrt(N))   [soft-regularized]
       phi_x = v_boost + Im(conj(Psi) Psi_x) / N
    """
    N = np.abs(Psi) ** 2
    Psi_x = dx_spec_complex(Psi)
    N_phi_tilde_x = np.imag(np.conj(Psi) * Psi_x)
    safe_N = np.maximum(N, eps_reg)
    phi_x = v_boost + N_phi_tilde_x / safe_N
    u = m + N * phi_x

    # alpha: (1/2)(u N)_x / N, evaluated via spectral derivative
    uN = dealias(u * N)
    uN_x = dx_spec(uN)
    alpha = 0.5 * uN_x / safe_N

    # Q
    sN = np.sqrt(N + eps_reg)
    Q = d2x_spec(sN) / (2.0 * sN)

    # beta
    u_phi_x = dealias(u * phi_x)
    beta = 2.0 * Q + u_phi_x - 2.0 * kappa * N

    return alpha, beta, u, N, phi_x

def safe_alpha(alpha, dt):
    """Clip alpha*dt to +/- alpha_clip so exp(-alpha*dt) stays bounded."""
    return np.clip(alpha * dt, -alpha_clip, alpha_clip)

def nonlinear_step(Psi, m, dt):
    """Pointwise Psi update with frozen coefficients, plus RK4 on m for the same dt."""
    # Freeze coefficients at start
    alpha, beta, u_init, N_init, phi_x_init = compute_coefs(Psi, m)
    # Apply pointwise Psi update (alpha*dt clipped to avoid overflow)
    real_factor = np.exp(-safe_alpha(alpha, dt))
    phase_factor = np.exp(-1j * beta * dt)
    Psi_new = Psi * real_factor * phase_factor

    # RK4 on m: m_t = -u m_x - 2 u_x m  with u evaluated at start (frozen)
    u_x_init = dx_spec(u_init)
    def m_rhs(m_arg, u_arg, u_x_arg):
        m_x = dx_spec(m_arg)
        return -dealias(u_arg * m_x) - 2.0 * dealias(u_x_arg * m_arg)
    k1 = m_rhs(m, u_init, u_x_init)
    Psi_mid = Psi * np.exp(-safe_alpha(alpha, dt/2)) * np.exp(-1j * beta * dt/2)
    m_mid = m + 0.5 * dt * k1
    _, _, u_mid, _, _ = compute_coefs(Psi_mid, m_mid)
    u_x_mid = dx_spec(u_mid)
    k2 = m_rhs(m_mid, u_mid, u_x_mid)
    m_mid2 = m + 0.5 * dt * k2
    _, _, u_mid2, _, _ = compute_coefs(Psi_mid, m_mid2)
    u_x_mid2 = dx_spec(u_mid2)
    k3 = m_rhs(m_mid2, u_mid2, u_x_mid2)
    m_end = m + dt * k3
    _, _, u_end, _, _ = compute_coefs(Psi_new, m_end)
    u_x_end = dx_spec(u_end)
    k4 = m_rhs(m_end, u_end, u_x_end)
    m_new = m + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    return Psi_new, m_new

def strang_step(Psi, m, dt):
    """Strang split: L(dt/2) - NL(dt) - L(dt/2)."""
    Psi = linear_step(Psi, kin_half)
    Psi, m = nonlinear_step(Psi, m, dt)
    Psi = linear_step(Psi, kin_half)
    # filter m too
    m = dealias(m)
    return Psi, m

# ----- snapshots & diagnostics -----
snaps_N, snaps_phi, snaps_u, snap_times = [], [], [], []
diag_t, diag_mass, diag_m_l2, diag_minN, diag_maxabs_u, diag_Q_max = [], [], [], [], [], []

def m_l2_norm(m):
    return np.sqrt(np.sum(m ** 2) * dx)

def mass_of(Psi):
    return np.sum(np.abs(Psi) ** 2) * dx

def take_snapshot(t_now, Psi, m):
    N = np.abs(Psi) ** 2
    Psi_x = dx_spec_complex(Psi)
    N_phi_tilde_x = np.imag(np.conj(Psi) * Psi_x)
    safe_N = np.maximum(N, eps_reg)
    phi_tilde = np.angle(Psi)
    phi_full = 0.5 * x + phi_tilde
    phi_x = v_boost + N_phi_tilde_x / safe_N
    u = m + N * phi_x
    snaps_N.append(N.copy())
    snaps_phi.append(phi_full.copy())
    snaps_u.append(u.copy())
    snap_times.append(t_now)
    sN = np.sqrt(N + eps_reg)
    Q = d2x_spec(sN) / (2.0 * sN)
    diag_t.append(t_now)
    diag_mass.append(mass_of(Psi))
    diag_m_l2.append(m_l2_norm(m))
    diag_minN.append(np.min(N))
    diag_maxabs_u.append(np.max(np.abs(u)))
    diag_Q_max.append(np.max(np.abs(Q)))

take_snapshot(0.0, Psi, m)
print(f"[E3] start: Nx={Nx}, L={L_box}, dt={dt}, n_steps={n_steps}, T={T_final}, eps={eps_perturb}", flush=True)
print(f"[E3] IC: mass={diag_mass[0]:.4e}, ||m||={diag_m_l2[0]:.4e}, minN={diag_minN[0]:.2e}, Q_max={diag_Q_max[0]:.2e}", flush=True)

t_start = time.time()
blowup = False
for step in range(1, n_steps + 1):
    try:
        Psi, m = strang_step(Psi, m, dt)
    except Exception as e:
        print(f"[E3] exception step {step}, t={step*dt:.4f}: {e}", flush=True)
        blowup = True
        break

    if not np.all(np.isfinite(np.abs(Psi))) or not np.all(np.isfinite(m)):
        print(f"[E3] NaN/Inf at step {step}, t={step*dt:.4f}", flush=True)
        blowup = True
        break

    if step % snap_stride == 0 or step == n_steps:
        t_now = step * dt
        take_snapshot(t_now, Psi, m)
        if step % (snap_stride * 2) == 0 or step == n_steps:
            print(f"  step {step:6d}  t={t_now:6.3f}  mass={diag_mass[-1]:.4e}  ||m||={diag_m_l2[-1]:.4e}  "
                  f"min N={diag_minN[-1]:.2e}  Q_max={diag_Q_max[-1]:.2e}  u_max={diag_maxabs_u[-1]:.3f}",
                  flush=True)

elapsed = time.time() - t_start
print(f"[E3] elapsed {elapsed:.2f} s, blowup={blowup}, snapshots={len(snaps_N)}", flush=True)

# ----- save -----
os.makedirs("pred_results", exist_ok=True)
arr = np.stack([np.stack([sN, sp, su], axis=0) for sN, sp, su in zip(snaps_N, snaps_phi, snaps_u)], axis=0)
print(f"[E3] output shape {arr.shape}", flush=True)
np.save("pred_results/T_D.npy", arr.astype(np.float64))
np.savez(
    "pred_results/T_D_diag.npz",
    t=np.asarray(diag_t),
    mass=np.asarray(diag_mass),
    m_l2=np.asarray(diag_m_l2),
    minN=np.asarray(diag_minN),
    maxabs_u=np.asarray(diag_maxabs_u),
    Q_max=np.asarray(diag_Q_max),
    eps=eps_perturb,
    x=x,
)
print(f"[E3] saved pred_results/T_D.npy and T_D_diag.npz", flush=True)
