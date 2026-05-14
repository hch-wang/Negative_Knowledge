"""
E2 (continued) — T_D NoKB: advance (m, N, chi) where phi = c*x + chi, c=0.5, chi periodic.

KEY BUG FIX: original IC phi(x,0)=0.5*x is NOT periodic on [-15,15]; computing its
Fourier derivative gives spikes up to |88| instead of 0.5, which causes immediate
blow-up. Split phi into a linear background (c*x) + a periodic perturbation chi.
Then phi_x = c + chi_x, where chi_x is computed spectrally (and is 0 at t=0).

Same single-component change as E2: representation (u,N,phi) -> (m,N,phi_periodic).
RK4, dt=5e-4, Fourier pseudospectral, no dealiasing.

Equations (kappa=1):
    m_t  = -(u m)_x - m u_x,                 u = m + N (c + chi_x)
    N_t  = -((u + (c + chi_x)) N)_x
    chi_t = -[u (c+chi_x) + 0.5 (c+chi_x)^2 + Q - 2 N], Q = sqrt(N)_xx/(2 sqrt(N))
"""

import numpy as np
import os
import time

# ---------- Parameters ----------
L = 30.0
Nx = 256
kappa = 1.0
T_final = 12.0
dt = 5e-4
n_steps = int(round(T_final / dt))
n_snapshots = 121
eps = 0.1

# Background phi gradient
c_bg = 0.5

# Grid
x = np.linspace(-L / 2.0, L / 2.0, Nx, endpoint=False)
dx = x[1] - x[0]
k_vec = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k_vec
k2 = -(k_vec ** 2)

_trapz = getattr(np, "trapezoid", None) or getattr(np, "trapz")

def dx_f(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def d2x_f(f):
    return np.real(np.fft.ifft(k2 * np.fft.fft(f)))

def quantum_potential(N, eps_n=1e-12):
    sN = np.sqrt(np.maximum(N, eps_n))
    return d2x_f(sN) / (2.0 * sN)

def rhs(m, N, chi):
    chi_x = dx_f(chi)
    phi_x = c_bg + chi_x
    u     = m + N * phi_x
    u_x   = dx_f(u)
    flux_N = (u + phi_x) * N
    Nt    = -dx_f(flux_N)
    mt    = -dx_f(u * m) - m * u_x
    Q     = quantum_potential(N)
    chit  = -(u * phi_x + 0.5 * phi_x ** 2 + Q - 2.0 * kappa * N)
    return mt, Nt, chit

# ---------- Initial condition ----------
A = 1.5
x0 = -5.0
N0 = (A ** 2) * (1.0 / np.cosh(A * (x - x0))) ** 2
chi0 = np.zeros_like(x)                       # phi - c*x; periodic part initially zero
m0   = eps * np.cos(2.0 * np.pi * x / L)
u0   = m0 + N0 * c_bg                         # = N*phi_x + m

mass_0 = _trapz(N0, x)
m_l2_0 = np.linalg.norm(m0) * np.sqrt(dx)
print(f"Init eps={eps}: ||m||_2={m_l2_0:.4e}  max|m|={np.max(np.abs(m0)):.4e}  "
      f"mass={mass_0:.4f}  peak N={N0.max():.4f}  max|u|={np.max(np.abs(u0)):.4f}  "
      f"Nmin={N0.min():.3e}")

# ---------- Snapshots ----------
snap_steps = np.linspace(0, n_steps, n_snapshots).astype(int)
snap_set = set(snap_steps.tolist())
snaps_t  = []
snaps    = []   # (u, N, phi) at each snapshot (with phi = c*x + chi)
m_l2     = []
peakN    = []
massT    = []
umax     = []
Nmin     = []
phimax   = []
chimax   = []

m_arr, N_arr, chi_arr = m0.copy(), N0.copy(), chi0.copy()

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
    if (len(snaps) - 1) % 12 == 0:
        print(f" step={step:7d}  t={t:6.3f}  ||m||_2={m_l2[-1]:.4e}  "
              f"N_peak={N_arr.max():.4f}  N_min={N_arr.min():.3e}  "
              f"|u|max={umax[-1]:.4f}  |chi|max={chimax[-1]:.3f}  mass={massT[-1]:.5f}")

take_snapshot(0)
t_start = time.time()

aborted_step = None
for step in range(1, n_steps + 1):
    k1m, k1N, k1c = rhs(m_arr, N_arr, chi_arr)
    k2m, k2N, k2c = rhs(m_arr + 0.5 * dt * k1m, N_arr + 0.5 * dt * k1N, chi_arr + 0.5 * dt * k1c)
    k3m, k3N, k3c = rhs(m_arr + 0.5 * dt * k2m, N_arr + 0.5 * dt * k2N, chi_arr + 0.5 * dt * k2c)
    k4m, k4N, k4c = rhs(m_arr + dt * k3m,       N_arr + dt * k3N,       chi_arr + dt * k3c)
    m_arr   = m_arr   + (dt / 6.0) * (k1m + 2 * k2m + 2 * k3m + k4m)
    N_arr   = N_arr   + (dt / 6.0) * (k1N + 2 * k2N + 2 * k3N + k4N)
    chi_arr = chi_arr + (dt / 6.0) * (k1c + 2 * k2c + 2 * k3c + k4c)

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
