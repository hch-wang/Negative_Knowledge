"""
B-NLS T_C  (NoKB)  -- Experiment E2
Single representation upgrade over E1: Madelung-Psi for the N-phi sector.

State variables now: (u, Psi) with Psi = sqrt(N) * exp(i phi),
so N = |Psi|^2 and phi_x is replaced by the current J = Im(conj(Psi)*Psi_x).

Why this helps over E1: in E1 we needed phi_t (which contains the singular
quantum pressure Q = (sqrt(N))_xx / (2 sqrt(N))) and its spatial derivative
phi_xt to recover u_t.  In tails where N ~ 1e-20, division by sqrt(N) made
Q diverge spectrally and instantly blew up u_t.  In Psi-form Psi itself is
a smooth complex number even when |Psi|~0, so we never directly divide by
sqrt(N) except in the 2Q*Psi term, which we regularize.

Equations (user's variational sign convention, kappa = +1):
  Continuity:        N_t = -((u + phi_x)*N)_x
  Hamilton-Jacobi:   phi_t = -u*phi_x - (1/2)*phi_x^2 - Q + 2*kappa*N,
                     Q := + (sqrt(N))_xx / (2 sqrt(N))
  Momentum:          m_t = -(u*m)_x - m*u_x,   m = u - N*phi_x

Derived Madelung-Psi (substituting Psi = sqrt(N) e^{i phi}, careful with sign):
  i Psi_t = -(1/2) Psi_xx + (2 Q - kappa N) Psi - i u Psi_x - i (u_x/2) Psi
where the 2Q*Psi term we compute via:
  2 Q Psi = (1/2) (|Psi|)_xx * exp(i phi) = (1/2) (|Psi|)_xx * (Psi/|Psi|)
with a soft regularization Psi/|Psi| ~ Psi/sqrt(|Psi|^2 + eps^2).

We then evolve (u, Psi) jointly via explicit RK4.  At each stage we compute:
  - J = Im(conj(Psi) Psi_x)        [= N phi_x, the momentum density]
  - m = u - J
  - Psi_t  from above
  - J_t   = Im(conj(Psi_t) Psi_x + conj(Psi) d_x(Psi_t))
  - m_t  = -(u m)_x - m u_x
  - u_t  = m_t + J_t            [since u = m + J]

Output:
  pred_results/T_C.npy  shape (n_snapshots, 3, 256), each frame [u, N, phi].
"""
import os
import numpy as np

# ---------------- Domain / params ----------------
Nx   = 256
L    = 30.0          # x in [-15, 15]
xL   = -15.0
xR   =  15.0
x    = np.linspace(xL, xR, Nx, endpoint=False)
dx   = x[1] - x[0]
kappa = 1.0

k     = 2.0*np.pi*np.fft.fftfreq(Nx, d=dx)
ik    = 1j * k
k2    = -k*k

# ---------------- Time integration ----------------
T_final     = 8.0
dt          = 1e-3
n_steps     = int(round(T_final / dt))
n_snapshots = 17
snap_steps  = np.linspace(0, n_steps, n_snapshots).astype(int)

EPS = 1e-4      # regularization for |Psi| in 2Q*Psi term

# ---------------- Helpers ----------------
def dx_fft(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def d2x_fft(f):
    return np.real(np.fft.ifft(k2 * np.fft.fft(f)))

def dx_fft_c(f):
    """First spatial derivative via FFT, complex-valued input."""
    return np.fft.ifft(ik * np.fft.fft(f))

def d2x_fft_c(f):
    """Second spatial derivative via FFT, complex-valued input."""
    return np.fft.ifft(k2 * np.fft.fft(f))

def rhs(u, Psi):
    """
    Compute (u_t, Psi_t) for the Madelung-Psi formulation.
    u    : (Nx,) real
    Psi  : (Nx,) complex
    """
    # Derivatives
    u_x      = dx_fft(u)
    Psi_x    = dx_fft_c(Psi)
    Psi_xx   = d2x_fft_c(Psi)
    absPsi   = np.abs(Psi)
    absPsi2  = absPsi*absPsi                 # = N
    abs_xx   = d2x_fft(absPsi)               # (|Psi|)_xx, real

    # Regularized phase factor for the 2Q*Psi term: Psi / sqrt(|Psi|^2 + eps^2)
    phase_reg = Psi / np.sqrt(absPsi2 + EPS*EPS)

    # 2 Q Psi = (1/2) (|Psi|)_xx * exp(i phi)  ~  (1/2) abs_xx * phase_reg
    twoQ_Psi = 0.5 * abs_xx * phase_reg

    # i Psi_t = -(1/2) Psi_xx + (2Q - kappa N) Psi - i u Psi_x - i (u_x/2) Psi
    # => Psi_t = -i * [ ... ]
    rhs_Psi_eq = -0.5*Psi_xx + twoQ_Psi - kappa*absPsi2*Psi - 1j*u*Psi_x - 1j*(u_x/2.0)*Psi
    Psi_t = -1j * rhs_Psi_eq

    # Current J = Im(conj(Psi) Psi_x) = N phi_x
    J = np.imag(np.conjugate(Psi) * Psi_x)

    # Momentum m = u - J
    m = u - J
    m_t = -dx_fft(u*m) - m*u_x

    # J_t = Im(conj(Psi_t) Psi_x + conj(Psi) Psi_xt)
    Psi_xt = dx_fft_c(Psi_t)
    J_t = np.imag(np.conjugate(Psi_t)*Psi_x + np.conjugate(Psi)*Psi_xt)

    u_t = m_t + J_t
    return u_t, Psi_t

def rk4_step(u, Psi, dt):
    k1u, k1P = rhs(u, Psi)
    k2u, k2P = rhs(u + 0.5*dt*k1u, Psi + 0.5*dt*k1P)
    k3u, k3P = rhs(u + 0.5*dt*k2u, Psi + 0.5*dt*k2P)
    k4u, k4P = rhs(u + dt*k3u,     Psi + dt*k3P)
    u_new   = u   + (dt/6.0)*(k1u + 2*k2u + 2*k3u + k4u)
    Psi_new = Psi + (dt/6.0)*(k1P + 2*k2P + 2*k3P + k4P)
    return u_new, Psi_new

# ---------------- Initial conditions ----------------
u0    = 1.0 * (1.0 - np.tanh(x / 0.5)) / 2.0      # smoothed bore
N0    = 1.0 / np.cosh(x + 8.0)**2                 # bright soliton at x=-8
phi0  = 0.6 * x                                   # phi_x = 0.6 (rightward speed)

# Initial Psi = sqrt(N) * exp(i phi).
# phi = 0.6 x is NOT periodic across [-15, 15].  But Psi = sqrt(N) e^{i 0.6 x}
# is itself NOT periodic either (the phase wraps differently at the ends).
# Since sqrt(N0) is essentially zero at x = -15 and at x = 15 (sech^2 at the
# boundaries is ~1e-19), the discontinuity in Psi at the periodic boundary is
# of size ~ |Psi| ~ sqrt(1e-19) ~ 3e-10, well below numerical precision.
# So initializing Psi = sqrt(N0)*exp(i*0.6*x) directly is safe.
Psi0  = np.sqrt(N0) * np.exp(1j * phi0)

# Verify periodicity:
periodic_jump = np.abs(Psi0[0] - Psi0[-1])
print(f"[E2-init] |Psi[0] - Psi[-1]| = {periodic_jump:.3e}  (should be ~ 0)", flush=True)

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
def diag(u_now, Psi_now, t_now):
    N_now = np.abs(Psi_now)**2
    Psi_x = dx_fft_c(Psi_now)
    J = np.imag(np.conjugate(Psi_now)*Psi_x)
    m = u_now - J
    m_norms.append((t_now, float(np.linalg.norm(m)*np.sqrt(dx))))
    N_total.append((t_now, float(np.sum(N_now)*dx)))
diag(u, Psi, 0.0)

blown_up = False
for step in range(1, n_steps + 1):
    u, Psi = rk4_step(u, Psi, dt)

    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(Psi))):
        print(f"[E2] NaN at step={step}, t={step*dt:.4f}", flush=True)
        blown_up = True
        break
    max_u = float(np.max(np.abs(u)))
    max_N = float(np.max(np.abs(Psi))**2)
    if max_u > 1e3 or max_N > 1e3:
        print(f"[E2] DIVERGENCE at step={step}, t={step*dt:.4f}  max|u|={max_u:.3e}  max N={max_N:.3e}", flush=True)
        blown_up = True
        break

    if step in snap_set:
        snapshots[snap_idx] = snap_pack(u, Psi)
        snap_idx += 1
        diag(u, Psi, step*dt)

# Pad after blow-up
if snap_idx < n_snapshots:
    print(f"[E2] padding {n_snapshots - snap_idx} snapshots after blow-up", flush=True)
    last = snapshots[snap_idx-1].copy() if snap_idx > 0 else snap_pack(u0, Psi0)
    for j in range(snap_idx, n_snapshots):
        snapshots[j] = last

# ---------------- Save ----------------
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_C.npy")
np.save(out_path, snapshots)

# ---------------- Diagnostics ----------------
print(f"[E2] Saved {out_path}, shape={snapshots.shape}", flush=True)
print(f"[E2] dt={dt}, n_steps={n_steps}, n_snapshots={n_snapshots}", flush=True)
print(f"[E2] blown_up={blown_up}", flush=True)

uf, Nf, phif = snapshots[-1]
print(f"[E2] final |u|max={np.max(np.abs(uf)):.4f}  N_max={np.max(Nf):.4f}  N_min={np.min(Nf):.4e}", flush=True)
print(f"[E2] final any NaN? u:{np.any(np.isnan(uf))} N:{np.any(np.isnan(Nf))} phi:{np.any(np.isnan(phif))}", flush=True)
print(f"[E2] ||m||_2(t) trace:", flush=True)
for t_now, mn in m_norms:
    print(f"      t={t_now:6.3f}  ||m||_2={mn:.4f}", flush=True)
print(f"[E2] Total N (mass) trace:", flush=True)
for t_now, NT in N_total:
    print(f"      t={t_now:6.3f}  sum(N)*dx={NT:.6f}", flush=True)
