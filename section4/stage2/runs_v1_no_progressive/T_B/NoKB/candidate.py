"""
Candidate solver for T_B: Gaussian wave packet -> soliton train decomposition
PDE (modified with artificial viscosity in u):
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx) + epsilon * u_xx
  v_t + 6 v v_x + v_xxx = -d_x(u v)

Periodic domain x in [-15, 15], Nx=256
IC: v(x,0) = 4*exp(-((x+5)^2)/2.25), u(x,0) = 0  (as specified)
T = 6.0

Method: Fourier pseudospectral + IFRK4
  - v: integrating factor for v_xxx  => lam_v = ik^3
  - u: integrating factor for epsilon*u_xx  => lam_u = -epsilon*k^2
  - Both: IFRK4 removes stiff linear parts from each field
  - Dealiasing: 2/3 rule
  - dt = 5e-4 (CFL for nonlinear terms)

Note: The epsilon*u_xx term is a regularization to prevent Burgers shock
formation. Without it, u blows up. The soliton train in v is the target;
u is a secondary field whose behavior is of secondary interest.
"""

import numpy as np
import os
import time

# ============================================================
# Domain
# ============================================================
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

k_arr = np.zeros(Nx)
k_arr[:Nx//2+1] = np.arange(0, Nx//2+1)
k_arr[Nx//2+1:] = np.arange(-Nx//2+1, 0)
k = (2.0 * np.pi / L) * k_arr

# Dealiasing: 2/3 rule
k_cut = (2.0 * np.pi / L) * (Nx // 3)
dealias = np.abs(k) <= k_cut

# ============================================================
# Parameters
# ============================================================
epsilon = 0.05   # artificial viscosity for u
T_final = 6.0
dt = 5.0e-4
n_steps = int(round(T_final / dt))
n_snapshots = 61
snap_times = np.linspace(0.0, T_final, n_snapshots)

print(f"dt={dt}, n_steps={n_steps}, epsilon={epsilon}")

# ============================================================
# Linear eigenvalues and integrating factors
# ============================================================
lam_v = 1j * k**3            # for v: from -v_xxx => (ik)^3 v_hat => lam_v = -(ik)^3 = ik^3
                               # wait: v_t = -v_xxx + N  => dV/dt = -(ik)^3 V + N = ik^3 V + N
lam_u = -epsilon * k**2       # for u: epsilon*u_xx => in Fourier: -epsilon*k^2 * U_hat

for lam, name in [(lam_v, 'v'), (lam_u, 'u')]:
    E_test = np.exp(lam * dt)
    print(f"  IF for {name}: max|exp(lam*dt)|={np.max(np.abs(E_test)):.4f}, "
          f"max|lam|*dt={np.max(np.abs(lam))*dt:.4f}")

def make_IF_coeffs(lam, dt_):
    """Compute IFRK4 coefficients for given linear eigenvalue and step size."""
    E2 = np.exp(lam * dt_ / 2.0)
    E  = np.exp(lam * dt_)
    with np.errstate(divide='ignore', invalid='ignore'):
        Q_h = np.where(np.abs(lam) > 1e-14, (E2 - 1.0)/lam, (dt_/2.0)*np.ones(Nx, dtype=complex))
        Q_f = np.where(np.abs(lam) > 1e-14, (E - 1.0)/lam, dt_*np.ones(Nx, dtype=complex))
    return E, E2, Q_h, Q_f

Ev, Ev2, Qv_h, Qv_f = make_IF_coeffs(lam_v, dt)
Eu, Eu2, Qu_h, Qu_f = make_IF_coeffs(lam_u, dt)

# ============================================================
# Spectral operators (with dealiasing)
# ============================================================
def dfft(f, order):
    fhat = np.fft.fft(f)
    fhat[~dealias] = 0.0
    return np.real(np.fft.ifft((1j * k)**order * fhat))

def Nv_hat(u, v):
    """Nonlinear part of v RHS in Fourier (dealiased)."""
    vx = dfft(v, 1); ux = dfft(u, 1)
    nv = -6.0*v*vx - (ux*v + u*vx)
    h = np.fft.fft(nv); h[~dealias] = 0.0
    return h

def Nu_hat(u, v):
    """Nonlinear part of u RHS in Fourier (dealiased).
    Full RHS of u is epsilon*u_xx [linear, removed by IF] + N_u
    N_u = -3u u_x - 6v v_x - v_xxx
    """
    ux = dfft(u, 1); vx = dfft(v, 1); vxxx = dfft(v, 3)
    nu = -3.0*u*ux - 6.0*v*vx - vxxx
    h = np.fft.fft(nu); h[~dealias] = 0.0
    return h

# ============================================================
# IFRK4 step
# ============================================================
def ifrk4_step(Uh, Vh):
    """
    Advance spectral coefficients (Uh, Vh) by one dt.
    Uses integrating factor for lam_u (u viscosity) and lam_v (v dispersion).
    """
    u = np.real(np.fft.ifft(Uh))
    v = np.real(np.fft.ifft(Vh))

    nu1 = Nu_hat(u, v)
    nv1 = Nv_hat(u, v)

    Uh_b = Eu2 * Uh + Qu_h * nu1
    Vh_b = Ev2 * Vh + Qv_h * nv1
    u_b = np.real(np.fft.ifft(Uh_b))
    v_b = np.real(np.fft.ifft(Vh_b))
    nu2 = Nu_hat(u_b, v_b)
    nv2 = Nv_hat(u_b, v_b)

    Uh_c = Eu2 * Uh + Qu_h * nu2
    Vh_c = Ev2 * Vh + Qv_h * nv2
    u_c = np.real(np.fft.ifft(Uh_c))
    v_c = np.real(np.fft.ifft(Vh_c))
    nu3 = Nu_hat(u_c, v_c)
    nv3 = Nv_hat(u_c, v_c)

    Uh_d = Eu * Uh + Qu_f * nu3
    Vh_d = Ev * Vh + Qv_f * nv3
    u_d = np.real(np.fft.ifft(Uh_d))
    v_d = np.real(np.fft.ifft(Vh_d))
    nu4 = Nu_hat(u_d, v_d)
    nv4 = Nv_hat(u_d, v_d)

    # Final update (IFRK4)
    Uh_new = (Eu * Uh + (dt/6.0) * (Eu * nu1 + 2.0*Eu2 * nu2 + 2.0*Eu2 * nu3 + nu4))
    Vh_new = (Ev * Vh + (dt/6.0) * (Ev * nv1 + 2.0*Ev2 * nv2 + 2.0*Ev2 * nv3 + nv4))

    return Uh_new, Vh_new

# ============================================================
# Initial conditions
# ============================================================
v0 = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
u0 = np.zeros(Nx)

Uh = np.fft.fft(u0)
Vh = np.fft.fft(v0)

# ============================================================
# Time integration
# ============================================================
snapshots = []
snap_idx = 0
t = 0.0

snapshots.append(np.stack([u0.copy(), v0.copy()], axis=0))
snap_idx = 1

t0_wall = time.time()
print("Starting integration...")

for step in range(n_steps):
    Uh, Vh = ifrk4_step(Uh, Vh)
    t += dt

    if snap_idx < n_snapshots and t >= snap_times[snap_idx] - 1e-12:
        u_cur = np.real(np.fft.ifft(Uh))
        v_cur = np.real(np.fft.ifft(Vh))
        snapshots.append(np.stack([u_cur.copy(), v_cur.copy()], axis=0))
        snap_idx += 1

    if step % 2000 == 0:
        u_cur = np.real(np.fft.ifft(Uh))
        v_cur = np.real(np.fft.ifft(Vh))
        elapsed = time.time() - t0_wall
        print(f"  step={step:6d} t={t:.3f} |v|={np.max(np.abs(v_cur)):.4f} "
              f"|u|={np.max(np.abs(u_cur)):.4f} wall={elapsed:.1f}s")
        if not (np.isfinite(np.max(np.abs(v_cur))) and np.isfinite(np.max(np.abs(u_cur)))):
            print("  NaN/Inf! Aborting.")
            break

# Fill remaining snapshots
u_final = np.real(np.fft.ifft(Uh))
v_final = np.real(np.fft.ifft(Vh))
while snap_idx < n_snapshots:
    snapshots.append(np.stack([u_final.copy(), v_final.copy()], axis=0))
    snap_idx += 1

# ============================================================
# Diagnostics
# ============================================================
result = np.array(snapshots)
print(f"\nResult shape: {result.shape}")
print(f"Final v: max={result[-1,1].max():.4f}, min={result[-1,1].min():.4f}")
print(f"Final u: max={result[-1,0].max():.4f}, min={result[-1,0].min():.4f}")

mass_v_init = np.sum(result[0, 1]) * dx
mass_v_final = np.sum(result[-1, 1]) * dx
drift = abs(mass_v_final - mass_v_init) / (abs(mass_v_init) + 1e-12) * 100
print(f"Mass v: init={mass_v_init:.6f}, final={mass_v_final:.6f}, drift={drift:.2f}%")

from scipy.signal import find_peaks
v_fin = result[-1, 1]
peaks, _ = find_peaks(v_fin, height=0.8, distance=5)
print(f"Peaks >= 0.8 in final v: {len(peaks)}")
if len(peaks) > 0:
    print(f"  Amplitudes: {v_fin[peaks].round(4)}")
    print(f"  Positions:  {x[peaks].round(4)}")

if not np.all(np.isfinite(result)):
    print("WARNING: NaN or Inf!")
else:
    print("Clean: no NaN/Inf.")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", result)
print("Saved pred_results/T_B.npy")
