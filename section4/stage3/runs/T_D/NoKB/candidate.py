"""
E3 — T_D NoKB: Strang split-step with Madelung-Psi linear half (UNITARY) +
residual (m, N, chi) RK4 sub-step. Single substantive change from E2 is the
split-step representation: the destabilizing high-k Bohm term is folded into
an EXACT Fourier-exponential propagator that is unitary regardless of sign
convention, removing the anti-diffusive blow-up that killed E2.

Decomposition (kappa=1):
  Let Psi(x,t) = sqrt(N(x,t)) * exp(i*phi(x,t)) be the Madelung wavefunction.
  Define tilde_Psi(x,t) = sqrt(N) * exp(i*chi(x,t)) with phi = c*x + chi
  (c=0.5 background slope, chi periodic).

  Standard-NLS linear+focusing evolution corresponds to:
      i Psi_t = -(1/2) Psi_xx - |Psi|^2 Psi
  Madelung: phi_t = +Q - (1/2)phi_x^2 + N
            N_t  = -(N phi_x)_x

  User's PDE (kappa=1):
      phi_t = -u phi_x - (1/2)phi_x^2 - Q + 2 N
      N_t   = -((u + phi_x) N)_x = -(N phi_x)_x - (u N)_x
      m_t   = -(u m)_x - m u_x

  Residual (user - standard) ODE: handled in a real-space RK4 substep:
      phi_t_resid = -u phi_x - 2 Q + N       [-Q user - (+Q NLS) = -2Q; 2N - N = +N]
      N_t_resid   = -(u N)_x
      m_t_resid   = -(u m)_x - m u_x         [m has no NLS counterpart]

Strang split per dt:
  step 1: Linear half (dt/2): hat_tilde_Psi *= exp(-i ((k+c)^2/2) (dt/2))
  step 2: Focusing half (dt/2): tilde_Psi *= exp(+i N (dt/2))     (N = |tilde_Psi|^2)
  step 3: Residual RK4 (dt) on (m, N, chi)   — N, chi extracted from tilde_Psi
                                              before, then put back after
  step 4: Focusing half (dt/2)
  step 5: Linear half (dt/2)

After every full step we also apply a mild exponential filter on (m, N, chi)
to suppress accumulating round-off; this is precautionary, not load-bearing.

dt=2e-3 (we can afford a larger dt now because the linear half is exact).
"""

import numpy as np
import os
import time

# ---------- Parameters ----------
L = 30.0
Nx = 256
kappa = 1.0
T_final = 12.0
dt = 2e-3            # larger dt now feasible thanks to exact linear half
n_steps = int(round(T_final / dt))
n_snapshots = 121
eps = 0.1

c_bg = 0.5
DELTA_REG = 1e-3     # floor for sqrt(N) in Q computation

# Grid
x = np.linspace(-L / 2.0, L / 2.0, Nx, endpoint=False)
dx = x[1] - x[0]
k_vec = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k_vec
k2 = -(k_vec ** 2)
k_max_grid = np.max(np.abs(k_vec))

_trapz = getattr(np, "trapezoid", None) or getattr(np, "trapz")

# Mild exponential filter (24 power on (k/kmax)) — kills only the very top
ALPHA_FILT = 36.0
P_FILT     = 24
filt = np.exp(-ALPHA_FILT * (np.abs(k_vec) / k_max_grid) ** P_FILT)

# 2/3 dealias mask for products in residual RHS
mask_23 = (np.abs(k_vec) <= (2.0 / 3.0) * k_max_grid).astype(float)

# Precompute linear propagator: exp(-i (k+c)^2/2 * dt/2)
lin_prop_half = np.exp(-1j * ((k_vec + c_bg) ** 2 / 2.0) * (dt / 2.0))

def fft_filter(f):
    return np.real(np.fft.ifft(filt * np.fft.fft(f)))

def dealias(f):
    return np.real(np.fft.ifft(mask_23 * np.fft.fft(f)))

def dx_f(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def d2x_f(f):
    return np.real(np.fft.ifft(k2 * np.fft.fft(f)))

def quantum_potential(N, delta=DELTA_REG):
    sN = np.sqrt(np.abs(N) + delta * delta)
    return d2x_f(sN) / (2.0 * sN)

def residual_rhs(m, N, chi):
    """RHS of (m, N, chi) residual ODE = user PDE minus standard NLS part."""
    chi_x = dx_f(chi)
    phi_x = c_bg + chi_x
    u     = m + N * phi_x
    u_x   = dx_f(u)
    # m equation: full user m_t (no NLS counterpart for m)
    um    = dealias(u * m)
    mt    = -dx_f(um) - m * u_x
    # N residual: -(u N)_x  (standard NLS already advances -(N phi_x)_x in linear)
    uN    = dealias(u * N)
    Nt    = -dx_f(uN)
    # phi residual: -u phi_x - 2Q + N
    u_phix = dealias(u * phi_x)
    Q      = quantum_potential(N)
    chit   = -u_phix - 2.0 * Q + N
    return mt, Nt, chit

# ---------- Initial condition ----------
A = 1.5
x0 = -5.0
N0   = (A ** 2) * (1.0 / np.cosh(A * (x - x0))) ** 2
chi0 = np.zeros_like(x)
m0   = eps * np.cos(2.0 * np.pi * x / L)
u0   = m0 + N0 * c_bg

mass_0 = _trapz(N0, x)
m_l2_0 = np.linalg.norm(m0) * np.sqrt(dx)
print(f"Init eps={eps}: ||m||_2={m_l2_0:.4e}  max|m|={np.max(np.abs(m0)):.4e}  "
      f"mass={mass_0:.4f}  peak N={N0.max():.4f}  Nmin={N0.min():.3e}")

# ---------- Snapshots ----------
snap_steps = np.linspace(0, n_steps, n_snapshots).astype(int)
snap_set = set(snap_steps.tolist())
snaps_t  = []
snaps    = []
m_l2     = []
peakN    = []
massT    = []
umax     = []
Nmin     = []
phimax   = []
chimax   = []

# State: keep tilde_Psi (complex), and m (real) and chi (real for diagnostics)
# tilde_Psi = sqrt(max(N,0) + delta^2 - delta^2) ... actually we work with raw sqrt(N) exp(i chi)
m_arr   = m0.copy()
N_arr   = N0.copy()
chi_arr = chi0.copy()
# Build tilde_Psi (with positivity-safe sqrt to handle any negative N during evolution)
def build_tilde_Psi(N, chi):
    return np.sqrt(np.maximum(N, 0.0)) * np.exp(1j * chi)
def split_tilde_Psi(tp):
    N_new = np.abs(tp) ** 2
    chi_new = np.angle(tp)   # principal branch; suitable since chi stays small
    return N_new, chi_new

tilde_Psi = build_tilde_Psi(N_arr, chi_arr)

def take_snapshot(step):
    t = step * dt
    chi_x = dx_f(chi_arr)
    phi_x = c_bg + chi_x
    u_now = m_arr + N_arr * phi_x
    phi_now = c_bg * x + chi_arr
    snaps.append(np.stack([u_now.copy(), N_arr.copy(), phi_now.copy()], axis=0))
    snaps_t.append(t)
    m_l2.append(np.linalg.norm(m_arr) * np.sqrt(dx))
    peakN.append(N_arr.max())
    massT.append(_trapz(N_arr, x))
    umax.append(np.max(np.abs(u_now)))
    Nmin.append(N_arr.min())
    phimax.append(np.max(np.abs(phi_now)))
    chimax.append(np.max(np.abs(chi_arr)))
    if (len(snaps) - 1) % 10 == 0:
        print(f" step={step:7d}  t={t:6.3f}  ||m||_2={m_l2[-1]:.4e}  "
              f"N_peak={N_arr.max():.4f}  N_min={N_arr.min():.3e}  "
              f"|u|max={umax[-1]:.4f}  |chi|max={chimax[-1]:.3f}  mass={massT[-1]:.5f}")

take_snapshot(0)
t_start = time.time()

aborted_step = None
for step in range(1, n_steps + 1):
    # ---- linear half ----
    tp_hat = np.fft.fft(tilde_Psi)
    tp_hat *= lin_prop_half
    tilde_Psi = np.fft.ifft(tp_hat)
    # ---- focusing half (dt/2) ----
    Nloc = np.abs(tilde_Psi) ** 2
    tilde_Psi = tilde_Psi * np.exp(1j * Nloc * (dt / 2.0))
    # Extract (N, chi) for residual ODE
    N_arr, chi_arr = split_tilde_Psi(tilde_Psi)
    # ---- residual RK4 (full dt) ----
    k1m, k1N, k1c = residual_rhs(m_arr, N_arr, chi_arr)
    k2m, k2N, k2c = residual_rhs(m_arr + 0.5 * dt * k1m,
                                 N_arr + 0.5 * dt * k1N,
                                 chi_arr + 0.5 * dt * k1c)
    k3m, k3N, k3c = residual_rhs(m_arr + 0.5 * dt * k2m,
                                 N_arr + 0.5 * dt * k2N,
                                 chi_arr + 0.5 * dt * k2c)
    k4m, k4N, k4c = residual_rhs(m_arr + dt * k3m,
                                 N_arr + dt * k3N,
                                 chi_arr + dt * k3c)
    m_arr   = m_arr   + (dt / 6.0) * (k1m + 2 * k2m + 2 * k3m + k4m)
    N_arr   = N_arr   + (dt / 6.0) * (k1N + 2 * k2N + 2 * k3N + k4N)
    chi_arr = chi_arr + (dt / 6.0) * (k1c + 2 * k2c + 2 * k3c + k4c)
    # Re-pack tilde_Psi from updated (N, chi)
    tilde_Psi = build_tilde_Psi(N_arr, chi_arr)
    # ---- focusing half (dt/2) ----
    Nloc = np.abs(tilde_Psi) ** 2
    tilde_Psi = tilde_Psi * np.exp(1j * Nloc * (dt / 2.0))
    # ---- linear half ----
    tp_hat = np.fft.fft(tilde_Psi)
    tp_hat *= lin_prop_half
    tilde_Psi = np.fft.ifft(tp_hat)
    # Mild filter on each state (precautionary; should be ~no-op)
    N_arr, chi_arr = split_tilde_Psi(tilde_Psi)
    m_arr   = fft_filter(m_arr)
    N_arr   = fft_filter(np.maximum(N_arr, 0.0))   # also enforce N>=0
    chi_arr = fft_filter(chi_arr)
    tilde_Psi = build_tilde_Psi(N_arr, chi_arr)

    if step in snap_set:
        take_snapshot(step)

    if not (np.isfinite(N_arr).all() and np.isfinite(m_arr).all() and np.isfinite(chi_arr).all()):
        print(f"NaN/Inf at step {step}, t={step*dt:.4f}")
        aborted_step = step
        break
    if np.max(np.abs(m_arr)) > 1e4 or N_arr.max() > 1e4 or np.max(np.abs(chi_arr)) > 1e4:
        print(f"Blow-up at step {step}, t={step*dt:.4f}: |m|max={np.max(np.abs(m_arr)):.3e}  "
              f"N_max={N_arr.max():.3e}  |chi|max={np.max(np.abs(chi_arr)):.3e}")
        aborted_step = step
        break

if aborted_step is not None:
    last_snap = snaps[-1] if snaps else None
    while len(snaps) < n_snapshots:
        snaps.append(last_snap.copy())
        snaps_t.append(np.nan)

elapsed = time.time() - t_start
print(f"\nElapsed {elapsed:.1f} s. Snapshots collected: {len(snaps)}.  aborted_step={aborted_step}")

# ---------- Save ----------
out = np.stack(snaps, axis=0)
print(f"Output shape: {out.shape}")
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_D.npy", out)
print("Saved pred_results/T_D.npy")

np.savez("pred_results/T_D_diag.npz",
         t=np.asarray(snaps_t),
         m_l2=np.asarray(m_l2),
         peakN=np.asarray(peakN),
         mass=np.asarray(massT),
         umax=np.asarray(umax),
         Nmin=np.asarray(Nmin),
         phimax=np.asarray(phimax),
         chimax=np.asarray(chimax),
         eps=eps,
         dt=dt,
         aborted_step=-1 if aborted_step is None else aborted_step)

print(f"\nFINAL DIAGNOSTICS at t={snaps_t[-1] if snaps_t else 'NA'}:")
chi_x_f = dx_f(chi_arr)
phi_x_f = c_bg + chi_x_f
u_f = m_arr + N_arr * phi_x_f
print(f"  N peak final     = {N_arr.max():.4f}")
print(f"  N min  final     = {N_arr.min():.4e}")
print(f"  Mass drift       = {abs(massT[-1] - mass_0)/mass_0*100:.3f}%")
print(f"  |u|max           = {np.max(np.abs(u_f)):.4f}")
print(f"  |chi|max final   = {np.max(np.abs(chi_arr)):.4f}")
print(f"  ||m||_2 init     = {m_l2[0]:.4e}")
print(f"  ||m||_2 final    = {m_l2[-1]:.4e}")
print(f"  ||m||_2 ratio    = {m_l2[-1]/m_l2[0]:.4f}")
