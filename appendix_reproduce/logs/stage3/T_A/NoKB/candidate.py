"""
E3 — B-NLS task T_A: periodic-compatible (u, N, psi) Fourier pseudospectral + RK4.

Key insight from F2: phi(x,0)=0.5*x is NOT periodic. A direct Fourier derivative
of phi produces Gibbs spikes (~80) at the boundary, instantly blowing up the system.
Fix: track psi := phi - v*x where v = 0.5 (the constant phi_x boost), so psi is
periodic (psi(x,0) = 0). Then phi_x = psi_x + v is computed correctly everywhere.
For output we reconstruct phi = psi + v*x.

Cumulative changes vs E1:
  E1 -> E2:  add N-floor regularization for Q (eps_N=1e-6)        [from F1 diagnosis]
  E2 -> E3:  add periodic representation phi -> psi+v*x           [from F2 diagnosis]

System (user's convention; sign of quantum pressure is OPPOSITE to standard NLS):
    m_t + (u*m)_x + m*u_x = 0,        m := u - N*phi_x
    N_t + ((u + phi_x)*N)_x = 0
    phi_t + u*phi_x + (1/2)*phi_x^2 + (sqrt(N))_xx/(2*sqrt(N)) - 2*kappa*N = 0

In psi variables (phi = psi + v*x, phi_x = psi_x + v, phi_t = psi_t):
    N_t + ((u + psi_x + v)*N)_x = 0
    psi_t + u*(psi_x + v) + (1/2)*(psi_x + v)^2 + Q - 2*kappa*N = 0
    u_t  : same algebraic relation u_t = m_t + N_t*(psi_x+v) + N*(psi_xt)
           where m_t = -(u m)_x - m u_x and m = u - N*(psi_x+v).
"""

import numpy as np
import os

# ---------- Parameters ----------
L = 30.0
Nx = 256
kappa = 1.0
T_final = 8.0
dt = 1e-3
n_steps = int(round(T_final / dt))
n_snapshots = 17
EPS_N = 1e-6      # floor for sqrt(N) regularization in Q
V_BOOST = 0.5     # constant phi_x at t=0

x = np.linspace(-L / 2.0, L / 2.0, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = -(k ** 2)

_trapz = getattr(np, "trapezoid", None) or getattr(np, "trapz")

def dx_f(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def d2x_f(f):
    return np.real(np.fft.ifft(k2 * np.fft.fft(f)))

def quantum_potential(N):
    sN = np.sqrt(np.maximum(N + EPS_N, EPS_N))
    return d2x_f(sN) / (2.0 * sN)

def rhs(u, N, psi):
    psi_x = dx_f(psi)
    phi_x = psi_x + V_BOOST
    u_x = dx_f(u)
    m = u - N * phi_x
    flux_N = (u + phi_x) * N
    Nt = -dx_f(flux_N)
    mt = -dx_f(u * m) - m * u_x
    Q = quantum_potential(N)
    psit = -(u * phi_x + 0.5 * phi_x ** 2 + Q - 2.0 * kappa * N)
    psi_xt = dx_f(psit)              # = phi_xt since v is constant
    ut = mt + Nt * phi_x + N * psi_xt
    return ut, Nt, psit

# ---------- Initial condition (psi = phi - v*x = 0 initially) ----------
A = 1.5
x0 = -5.0
N0 = (A ** 2) * (1.0 / np.cosh(A * (x - x0))) ** 2
psi0 = np.zeros_like(x)
u0 = V_BOOST * N0

m0 = u0 - N0 * V_BOOST
print(f"Init: max|m|={np.max(np.abs(m0)):.3e}, "
      f"mass={_trapz(N0, x):.6f}, "
      f"peak N={N0.max():.4f}, "
      f"min N={N0.min():.3e}")
print(f"psi_x at boundary (should be ~0): {dx_f(psi0)[:3]}, mid: {dx_f(psi0)[Nx//2]}")

snap_idx = np.linspace(0, n_steps, n_snapshots).astype(int)
snap_set = set(snap_idx.tolist())
snaps = []

u, N, psi = u0.copy(), N0.copy(), psi0.copy()

def reconstruct_phi(psi_arr):
    return psi_arr + V_BOOST * x

def take_snapshot(step):
    phi_out = reconstruct_phi(psi)
    snaps.append(np.stack([u.copy(), N.copy(), phi_out.copy()], axis=0))
    phi_x_eff = dx_f(psi) + V_BOOST
    m_now = u - N * phi_x_eff
    print(f" step={step:6d}  t={step*dt:7.3f}  "
          f"N_peak={N.max():.4f}  N_min={N.min():.4e}  "
          f"|u|max={np.max(np.abs(u)):.4f}  |phi|max={np.max(np.abs(phi_out)):.3f}  "
          f"mass={_trapz(N, x):.5f}  ||m||={np.linalg.norm(m_now):.4f}")

take_snapshot(0)

for step in range(1, n_steps + 1):
    k1u, k1N, k1p = rhs(u, N, psi)
    k2u, k2N, k2p = rhs(u + 0.5 * dt * k1u, N + 0.5 * dt * k1N, psi + 0.5 * dt * k1p)
    k3u, k3N, k3p = rhs(u + 0.5 * dt * k2u, N + 0.5 * dt * k2N, psi + 0.5 * dt * k2p)
    k4u, k4N, k4p = rhs(u + dt * k3u, N + dt * k3N, psi + dt * k3p)
    u = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    N = N + (dt / 6.0) * (k1N + 2 * k2N + 2 * k3N + k4N)
    psi = psi + (dt / 6.0) * (k1p + 2 * k2p + 2 * k3p + k4p)

    if step in snap_set:
        take_snapshot(step)

    if not (np.isfinite(N).all() and np.isfinite(u).all() and np.isfinite(psi).all()):
        print(f"NaN/Inf at step {step}, t={step*dt:.4f}")
        while len(snaps) < n_snapshots:
            phi_out = reconstruct_phi(psi)
            snaps.append(np.stack([u, N, phi_out], axis=0))
        break
    if np.max(np.abs(u)) > 1e3 or N.max() > 1e3 or np.max(np.abs(psi)) > 1e4:
        print(f"Blow-up at step {step}, t={step*dt:.4f}: "
              f"|u|max={np.max(np.abs(u)):.3e}  Nmax={N.max():.3e}")
        while len(snaps) < n_snapshots:
            phi_out = reconstruct_phi(psi)
            snaps.append(np.stack([u, N, phi_out], axis=0))
        break

out = np.stack(snaps, axis=0)
print(f"Output shape: {out.shape}")
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", out)
print("Saved pred_results/T_A.npy")

u_f, N_f, phi_f = out[-1]
phi_x_f = dx_f(phi_f - V_BOOST * x) + V_BOOST   # i.e. dx(psi) + v   (avoids Gibbs on phi)
m_f = u_f - N_f * phi_x_f
mass_f = _trapz(N_f, x)
mass_0 = _trapz(N0, x)
print(f"\nFINAL DIAGNOSTICS at t={T_final}:")
print(f"  N peak final     = {N_f.max():.4f}  (target >= 1.125)")
print(f"  Mass drift       = {abs(mass_f - mass_0)/mass_0*100:.3f}%  (target <5%)")
print(f"  |u|max           = {np.max(np.abs(u_f)):.4f}")
print(f"  |N|max           = {np.max(np.abs(N_f)):.4f}")
print(f"  |phi|max         = {np.max(np.abs(phi_f)):.4f}  (bounds <25)")
print(f"  ||m||_2 / ||N*phi_x||_2 = {np.linalg.norm(m_f) / max(np.linalg.norm(N_f*phi_x_f), 1e-12):.4f}  (target <0.2)")
