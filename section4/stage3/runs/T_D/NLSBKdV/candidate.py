"""
T_D / NLSBKdV  --  Experiment E1
Compound-Soliton attractor study under user's +sqrt(N)_xx/(2 sqrt(N)) sign convention.

E1: simplest meaningful baseline = direct (N, phi_tilde, u) Fourier pseudospectral + explicit RK4
    with 2/3 dealiasing and soft regularization sqrt(N + eps_reg).

Bank notes (cited in research_state.jsonl, E1):
  - kb-nls-direct-n-phi-structural-failure: warns this approach is unstable for low-N tails;
    we still try it as the prompt mandates "even if bank says E1 will fail, you MUST run it first
    to observe failure mode."  (Prompt also allows skipping a known dead-end; here we treat it as
    the dead-end-to-be-confirmed under the user's literal sign, since that case has not been tested.)
  - kb-nls-quantum-pressure-central-failure-mode: Q can reach 1e7+ near tails.  We soft-floor.
  - kb-nls-hard-floor-counterproductive: use SOFT eps regularization (sqrt(N + eps_reg)).
  - kb-nls-split-linear-phase: split phi = 0.5*x + phi_tilde and integrate only phi_tilde spectrally.
  - kb-nls-23-dealiasing-cubic: 2/3 dealias on nonlinear products.
  - kb-nls-mass-conservation-not-sufficient: also monitor energy and peak position.
  - kb-nls-mcs-not-attractor-standard-sign: under STANDARD sign m grew to ~eps^0.33 plateau;
    the question here is what happens under user's literal +sign.

IC (eps=0.1 chosen as a midpoint; budget allows characterizing one carefully):
  kappa=1, A=1.5, N0(x) = A^2 sech^2(A(x+5)), phi0(x) = 0.5 x,  u0(x) = 0.5 N0(x) + eps cos(2 pi x / L).
  m0(x) = eps cos(2 pi x / L).
"""

import numpy as np
import os, sys, time

# ----- domain & parameters -----
L_box = 30.0          # x in [-15, 15], periodic
Nx = 256
x = np.linspace(-L_box/2, L_box/2, Nx, endpoint=False)
dx = L_box / Nx
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k * k

# dealiasing mask 2/3 rule
k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0/3.0) * k_max).astype(float)

# IC parameters
kappa = 1.0
A_sol = 1.5
x0 = -5.0
v_boost = 0.5
eps_perturb = 0.1
eps_reg = 1e-12       # soft regularization for sqrt(N + eps_reg)

T_final = 12.0
dt = 1e-3
n_steps = int(round(T_final / dt))
n_snapshots = 25
snap_stride = max(1, n_steps // (n_snapshots - 1))
snap_times = []

# ----- initial condition -----
N0 = (A_sol ** 2) * (1.0 / np.cosh(A_sol * (x - x0))) ** 2
phi0_tilde = np.zeros_like(x)          # phi_full = 0.5 x + phi_tilde, phi_tilde=0 at t=0
u0 = v_boost * N0 + eps_perturb * np.cos(2.0 * np.pi * x / L_box)

# state vector: (N, phi_tilde, u)
N = N0.copy()
phi_t = phi0_tilde.copy()
u = u0.copy()

# helpers
def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def d2x_spec(f):
    return np.real(np.fft.ifft(-k2 * np.fft.fft(f)))

def dealias_field(f):
    fk = np.fft.fft(f) * dealias
    return np.real(np.fft.ifft(fk))

def Q_term(N_field):
    """quantum pressure (sqrt(N))_xx / (2 sqrt(N)) with soft regularization."""
    sN = np.sqrt(N_field + eps_reg)
    return d2x_spec(sN) / (2.0 * sN)

def rhs(N, phi_t, u):
    """
    RHS of user's B-NLS in primitive (N, phi_tilde, u) form with phi = 0.5 x + phi_tilde.
    phi_x = 0.5 + phi_tilde_x
    Equations (user's variational, kappa=+1):
        N_t  = -((u + phi_x) N)_x
        phi_t = -u*phi_x - (1/2) phi_x^2 - Q(N) + 2 kappa N
        u-equation derived from m_t + (u m)_x + m u_x = 0 with m = u - N phi_x.
            d/dt(u - N phi_x) + (u (u - N phi_x))_x + (u - N phi_x) u_x = 0
        Equivalently:  u_t = (N phi_x)_t - (u m)_x - m u_x
        (N phi_x)_t = N_t phi_x + N phi_t,x
    """
    # derived spatial fields
    phi_x = 0.5 + dx_spec(phi_t)
    u_x = dx_spec(u)
    N_x = dx_spec(N)

    # currents (dealiased)
    flux_N = dealias_field((u + phi_x) * N)
    N_t = -dx_spec(flux_N)

    # phi_t
    Q = Q_term(N)
    nonlin_phi = dealias_field(u * phi_x + 0.5 * phi_x ** 2)
    phi_t_rhs = -nonlin_phi - Q + 2.0 * kappa * N
    # we integrate phi_tilde = phi - 0.5 x.  Since 0.5 x is time-independent, phi_tilde_t = phi_t.
    phi_tilde_t = phi_t_rhs

    # m equation: m_t = -u m_x - 2 u_x m (derivation:  m_t + (u m)_x + m u_x = 0
    #     => m_t + u m_x + u_x m + m u_x = m_t + u m_x + 2 m u_x = 0 )
    m = u - N * phi_x
    m_x = dx_spec(m)
    m_t = -dealias_field(u * m_x) - 2.0 * dealias_field(u_x * m)

    # u_t = m_t + (N phi_x)_t = m_t + N_t phi_x + N * d/dt(phi_x)
    # d/dt(phi_x) = d/dx(phi_t)
    dphi_tdx = dx_spec(phi_tilde_t)   # = (phi_x)_t since 0.5 is constant
    u_t = m_t + N_t * phi_x + N * dphi_tdx

    return N_t, phi_tilde_t, u_t

def rk4_step(N, phi_t, u, dt):
    k1N, k1p, k1u = rhs(N, phi_t, u)
    k2N, k2p, k2u = rhs(N + 0.5 * dt * k1N, phi_t + 0.5 * dt * k1p, u + 0.5 * dt * k1u)
    k3N, k3p, k3u = rhs(N + 0.5 * dt * k2N, phi_t + 0.5 * dt * k2p, u + 0.5 * dt * k2u)
    k4N, k4p, k4u = rhs(N + dt * k3N, phi_t + dt * k3p, u + dt * k3u)
    N_new = N + (dt / 6.0) * (k1N + 2 * k2N + 2 * k3N + k4N)
    p_new = phi_t + (dt / 6.0) * (k1p + 2 * k2p + 2 * k3p + k4p)
    u_new = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    return N_new, p_new, u_new

# ----- snapshots -----
snaps_N = [N.copy()]
snaps_phi = [phi_t.copy() + 0.5 * x]  # store full phi for output
snaps_u = [u.copy()]
snap_times.append(0.0)

# diagnostics over time
diag_t = [0.0]
diag_mass = [np.sum(N) * dx]
diag_energy = []
diag_m_l2 = [np.sqrt(np.sum((u - N * (0.5 + dx_spec(phi_t))) ** 2) * dx)]
diag_minN = [np.min(N)]
diag_maxabs_u = [np.max(np.abs(u))]
diag_Q_max = [np.max(np.abs(Q_term(N)))]

def total_energy(N, phi_t, u):
    phi_x = 0.5 + dx_spec(phi_t)
    sN = np.sqrt(N + eps_reg)
    kinetic_q = np.sum(((dx_spec(sN)) ** 2) * 0.5) * dx  # quantum pressure energy
    kinetic_p = np.sum(0.5 * N * phi_x ** 2) * dx
    interaction = np.sum(0.5 * u ** 2 * N) * dx          # rough proxy
    pot = -np.sum(kappa * N * N) * dx
    return kinetic_q + kinetic_p + interaction + pot

E0 = total_energy(N, phi_t, u)
diag_energy.append(E0)

t_start = time.time()
blowup = False
step_log = []

# ----- main loop -----
print(f"[E1] starting integration: Nx={Nx}, dt={dt}, n_steps={n_steps}, T_final={T_final}", flush=True)
for step in range(1, n_steps + 1):
    try:
        N, phi_t, u = rk4_step(N, phi_t, u, dt)
    except Exception as e:
        print(f"[E1] exception at step {step}, t={step*dt:.4f}: {e}", flush=True)
        blowup = True
        break

    if not np.all(np.isfinite(N)) or not np.all(np.isfinite(phi_t)) or not np.all(np.isfinite(u)):
        print(f"[E1] NaN/Inf detected at step {step}, t={step*dt:.4f}", flush=True)
        blowup = True
        break

    if step % snap_stride == 0 or step == n_steps:
        t_now = step * dt
        snaps_N.append(N.copy())
        snaps_phi.append(phi_t.copy() + 0.5 * x)
        snaps_u.append(u.copy())
        snap_times.append(t_now)

        m_now = u - N * (0.5 + dx_spec(phi_t))
        m_l2 = np.sqrt(np.sum(m_now ** 2) * dx)
        mass = np.sum(N) * dx
        Q_max_now = np.max(np.abs(Q_term(N)))
        Estep = total_energy(N, phi_t, u)
        diag_t.append(t_now)
        diag_mass.append(mass)
        diag_energy.append(Estep)
        diag_m_l2.append(m_l2)
        diag_minN.append(np.min(N))
        diag_maxabs_u.append(np.max(np.abs(u)))
        diag_Q_max.append(Q_max_now)
        if step % (snap_stride * 4) == 0 or step == n_steps:
            print(f"  step {step:6d}  t={t_now:6.3f}  mass={mass:.6e}  ||m||_2={m_l2:.4e}  "
                  f"minN={np.min(N):.3e}  Q_max={Q_max_now:.2e}", flush=True)

elapsed = time.time() - t_start
print(f"[E1] elapsed {elapsed:.2f} s  blowup={blowup}", flush=True)

# ----- final output -----
# while loop above appends already; make sure we have at least 5 snapshots
if len(snaps_N) < 5:
    print(f"[E1] WARNING only {len(snaps_N)} snapshots — fewer than 5 (blowup={blowup})", flush=True)

# pad / truncate to a uniform shape (n_snapshots, 3, 256)
arr = np.stack([np.stack([sN, sp, su], axis=0) for sN, sp, su in zip(snaps_N, snaps_phi, snaps_u)], axis=0)
print(f"[E1] output shape {arr.shape}", flush=True)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_D.npy", arr.astype(np.float64))

# also write small diagnostic npz for reasoning
np.savez(
    "pred_results/T_D_diag.npz",
    t=np.asarray(diag_t),
    mass=np.asarray(diag_mass),
    energy=np.asarray(diag_energy),
    m_l2=np.asarray(diag_m_l2),
    minN=np.asarray(diag_minN),
    maxabs_u=np.asarray(diag_maxabs_u),
    Q_max=np.asarray(diag_Q_max),
    eps=eps_perturb,
    x=x,
)
print(f"[E1] saved pred_results/T_D.npy and T_D_diag.npz", flush=True)
