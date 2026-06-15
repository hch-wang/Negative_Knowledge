"""
B-NLS T_C  (NoKB)  -- Experiment E3
Single change over E2: explicit RK4 -> Strang split-step for the
dispersive Schrödinger part.

State: (u, Psi) with N = |Psi|^2, J = Im(conj(Psi)*Psi_x).

Schrödinger equation in Madelung-Psi form (user's +Q sign):
  i Psi_t = -(1/2) Psi_xx   +   V Psi
            \---- L -----/      \-- N --/
where
  V = 2Q - kappa*N    +    nonlinear transport  - i u Psi_x - i (u_x/2) Psi

Strang split per timestep dt:
  1) Half-step nonlinear sub-step: evolve (u, Psi) under N alone for dt/2.
  2) Full-step linear sub-step: Psi <- IFFT[ exp(i*(k^2/2)*dt) FFT[Psi] ].
     (This corresponds to i Psi_t = -(1/2) Psi_xx, exact in time.)
     u is held fixed during this linear step (no dispersion in u).
  3) Half-step nonlinear sub-step: evolve (u, Psi) under N alone for dt/2.

The nonlinear sub-step is integrated by RK2 (Heun).  In the nonlinear sub-step
we evolve:
  Psi_t |_N    =  -i V Psi  - u Psi_x - (u_x/2) Psi
                   ^ here V = 2Q - kappa N, with 2Q*Psi computed as
                     (1/2)(|Psi|)_xx exp(i phi) ~ (1/2)(|Psi|)_xx * Psi/|Psi|_reg
  u_t           = m_t + J_t        (full u eqn -- includes BOTH nonlinear and
                                    linear-Schrödinger contributions to J_t)

Note u_t couples to ALL of Psi_t (including the linear piece) via J_t.  We
handle this by computing J_t in the nonlinear sub-step using the COMPLETE
Psi_t (linear + nonlinear).  This way u evolves on a "full" Psi_t,
while Psi itself uses the Strang split.  This is a hybrid Strang-on-Psi /
RK2-on-u scheme.
"""
import os
import numpy as np

# ---------------- Domain / params ----------------
Nx   = 256
L    = 30.0
xL   = -15.0
xR   =  15.0
x    = np.linspace(xL, xR, Nx, endpoint=False)
dx   = x[1] - x[0]
kappa = 1.0

k     = 2.0*np.pi*np.fft.fftfreq(Nx, d=dx)
ik    = 1j * k
k2    = -k*k                  # = -k^2

# ---------------- Time integration ----------------
T_final     = 8.0
dt          = 2e-3
n_steps     = int(round(T_final / dt))
n_snapshots = 17
snap_steps  = np.linspace(0, n_steps, n_snapshots).astype(int)

EPS = 1e-4

# Linear propagator: i Psi_t = -(1/2) Psi_xx
#   In Fourier: i Psi^_t = (k^2/2) Psi^   => Psi^(t+dt) = exp(-i (k^2/2) dt) Psi^(t)
LIN_FULL = np.exp(-1j * (-k2/2.0) * dt)     # full-step linear propagator (k2 = -k^2)
# Equivalent: np.exp(-1j * (k**2/2.0) * dt)

# ---------------- Helpers ----------------
def dx_fft(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def d2x_fft(f):
    return np.real(np.fft.ifft(k2 * np.fft.fft(f)))

def dx_fft_c(f):
    return np.fft.ifft(ik * np.fft.fft(f))

def d2x_fft_c(f):
    return np.fft.ifft(k2 * np.fft.fft(f))

def linear_step_psi(Psi):
    return np.fft.ifft(LIN_FULL * np.fft.fft(Psi))

# ---------------- RHS terms ----------------
def rhs_psi_nonlin(u, Psi):
    """Psi_t under the nonlinear-only sub-step.
       Psi_t |_N = -i V Psi - u Psi_x - (u_x/2) Psi,
       V = 2Q - kappa N.
    """
    u_x      = dx_fft(u)
    Psi_x    = dx_fft_c(Psi)
    absPsi   = np.abs(Psi)
    absPsi2  = absPsi*absPsi          # N
    abs_xx   = d2x_fft(absPsi)        # (|Psi|)_xx, real

    # 2 Q Psi = (1/2) abs_xx * Psi / |Psi|  (regularized)
    twoQ_Psi = 0.5 * abs_xx * (Psi / np.sqrt(absPsi2 + EPS*EPS))

    V_Psi = twoQ_Psi - kappa*absPsi2*Psi
    Psi_t = -1j*V_Psi - u*Psi_x - 0.5*u_x*Psi
    return Psi_t, Psi_x, u_x

def rhs_psi_linear(Psi):
    """Psi_t under the linear-only sub-step (would be used for analytic;
       used here only to assemble full Psi_t for u-equation J_t)."""
    Psi_xx = d2x_fft_c(Psi)
    # i Psi_t = -(1/2) Psi_xx  =>  Psi_t = (i/2) Psi_xx
    return 0.5j * Psi_xx

def rhs_u_from_Psi_t(u, Psi, Psi_t_total):
    """Compute u_t given the FULL Psi_t (linear + nonlinear)."""
    u_x   = dx_fft(u)
    Psi_x = dx_fft_c(Psi)
    J     = np.imag(np.conjugate(Psi)*Psi_x)
    m     = u - J
    m_t   = -dx_fft(u*m) - m*u_x
    Psi_xt = dx_fft_c(Psi_t_total)
    J_t = np.imag(np.conjugate(Psi_t_total)*Psi_x + np.conjugate(Psi)*Psi_xt)
    u_t = m_t + J_t
    return u_t

def nonlinear_half_step(u, Psi, h):
    """RK2 (Heun) for the nonlinear sub-step of length h.
       u uses the FULL Psi_t for its J_t contribution, while Psi uses only nonlinear part."""
    # Stage 1
    Psi_t_NL1 = rhs_psi_nonlin(u, Psi)[0]
    Psi_t_LIN1 = rhs_psi_linear(Psi)
    Psi_t_FULL1 = Psi_t_NL1 + Psi_t_LIN1
    u_t1   = rhs_u_from_Psi_t(u, Psi, Psi_t_FULL1)
    u_mid  = u   + h*u_t1
    Psi_mid = Psi + h*Psi_t_NL1

    # Stage 2 at end
    Psi_t_NL2 = rhs_psi_nonlin(u_mid, Psi_mid)[0]
    Psi_t_LIN2 = rhs_psi_linear(Psi_mid)
    Psi_t_FULL2 = Psi_t_NL2 + Psi_t_LIN2
    u_t2   = rhs_u_from_Psi_t(u_mid, Psi_mid, Psi_t_FULL2)

    u_new   = u   + 0.5*h*(u_t1   + u_t2)
    Psi_new = Psi + 0.5*h*(Psi_t_NL1 + Psi_t_NL2)
    return u_new, Psi_new

def strang_step(u, Psi, dt):
    # half nonlinear
    u, Psi = nonlinear_half_step(u, Psi, 0.5*dt)
    # full linear (Psi only; u unchanged here -- the linear Schrödinger
    # would affect u via J_t inside the nonlinear sub-step, where we
    # already included it through Psi_t_FULL)
    Psi = linear_step_psi(Psi)
    # half nonlinear
    u, Psi = nonlinear_half_step(u, Psi, 0.5*dt)
    return u, Psi

# ---------------- Initial conditions ----------------
u0    = 1.0 * (1.0 - np.tanh(x / 0.5)) / 2.0
N0    = 1.0 / np.cosh(x + 8.0)**2
phi0  = 0.6 * x

# To suppress the periodic-boundary jump in Psi (|Psi[0]-Psi[-1]| ~ 1.8e-3),
# we apply a smooth cosine taper to N near the boundaries.  This keeps the
# soliton at x=-8 intact (taper region is |x|>13) and just kills the tail
# that wraps to the wrong side of the domain.  This is purely a numerical
# regularization of an unphysical periodic-image residue.
taper = np.ones_like(x)
mask  = np.abs(x) > 13.0          # |x| in (13, 15)
taper[mask] = 0.5 * (1.0 + np.cos(np.pi*(np.abs(x[mask]) - 13.0)/2.0))
N0_t  = N0 * taper                # tapered N

# We do NOT taper phi (it's just 0.6 x), but Psi = sqrt(N_t)*exp(i phi)
# will be O(0) at boundary, so Psi is now truly periodic to round-off.
Psi0 = np.sqrt(N0_t) * np.exp(1j * phi0)

periodic_jump = np.abs(Psi0[0] - Psi0[-1])
print(f"[E3-init] taper applied; |Psi[0]-Psi[-1]| = {periodic_jump:.3e}", flush=True)
print(f"[E3-init] sum(N)*dx (mass) = {np.sum(np.abs(Psi0)**2)*dx:.6f}", flush=True)

# ---------------- Run ----------------
u   = u0.copy()
Psi = Psi0.copy()

snapshots = np.zeros((n_snapshots, 3, Nx))
def snap_pack(u_now, Psi_now):
    N_now   = np.abs(Psi_now)**2
    phi_now = np.angle(Psi_now)
    return np.stack([u_now, N_now, phi_now], axis=0)

snapshots[0] = snap_pack(u, Psi)
snap_set = set(snap_steps.tolist())
snap_idx = 1

# Diagnostics
m_norms = []
N_total = []
u_peaks = []
N_peaks = []
def diag(u_now, Psi_now, t_now):
    N_now = np.abs(Psi_now)**2
    Psi_x = dx_fft_c(Psi_now)
    J = np.imag(np.conjugate(Psi_now)*Psi_x)
    m = u_now - J
    m_norms.append((t_now, float(np.linalg.norm(m)*np.sqrt(dx))))
    N_total.append((t_now, float(np.sum(N_now)*dx)))
    u_peaks.append((t_now, float(np.max(np.abs(u_now)))))
    N_peaks.append((t_now, float(np.max(N_now))))
diag(u, Psi, 0.0)

blown_up = False
for step in range(1, n_steps + 1):
    u, Psi = strang_step(u, Psi, dt)

    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(Psi))):
        print(f"[E3] NaN at step={step}, t={step*dt:.4f}", flush=True)
        blown_up = True
        break
    max_u = float(np.max(np.abs(u)))
    max_N = float(np.max(np.abs(Psi))**2)
    if max_u > 1e3 or max_N > 1e3:
        print(f"[E3] DIVERGENCE at step={step}, t={step*dt:.4f}  max|u|={max_u:.3e}  max N={max_N:.3e}", flush=True)
        blown_up = True
        break

    if step in snap_set:
        snapshots[snap_idx] = snap_pack(u, Psi)
        snap_idx += 1
        diag(u, Psi, step*dt)

# Pad
if snap_idx < n_snapshots:
    print(f"[E3] padding {n_snapshots - snap_idx} snapshots after blow-up", flush=True)
    last = snapshots[snap_idx-1].copy() if snap_idx > 0 else snap_pack(u0, Psi0)
    for j in range(snap_idx, n_snapshots):
        snapshots[j] = last

# Save
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_C.npy")
np.save(out_path, snapshots)

print(f"[E3] Saved {out_path}, shape={snapshots.shape}", flush=True)
print(f"[E3] dt={dt}, n_steps={n_steps}, n_snapshots={n_snapshots}", flush=True)
print(f"[E3] blown_up={blown_up}", flush=True)

uf, Nf, phif = snapshots[-1]
print(f"[E3] final |u|max={np.max(np.abs(uf)):.4f}  N_max={np.max(Nf):.4f}  N_min={np.min(Nf):.4e}", flush=True)
print(f"[E3] final any NaN? u:{np.any(np.isnan(uf))} N:{np.any(np.isnan(Nf))} phi:{np.any(np.isnan(phif))}", flush=True)
print(f"[E3] ||m||_2(t) trace:", flush=True)
for t_now, mn in m_norms:
    print(f"      t={t_now:6.3f}  ||m||_2={mn:.4f}", flush=True)
print(f"[E3] Total N (mass) trace:", flush=True)
for t_now, NT in N_total:
    print(f"      t={t_now:6.3f}  sum(N)*dx={NT:.6f}", flush=True)
print(f"[E3] peak |u| and N over time:", flush=True)
for (t, pu), (_, pN) in zip(u_peaks, N_peaks):
    print(f"      t={t:6.3f}  max|u|={pu:.4f}  max N={pN:.4f}", flush=True)
