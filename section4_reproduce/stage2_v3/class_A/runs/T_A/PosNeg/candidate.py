"""
E3 candidate solver for T_A: coupled Burgers-swept-KdV soliton stability.

E3 = E2 + IMEX-CN treatment of the stiff dispersive v_xxx term.
Single-component upgrade from E2 per kb-kdv-IMEX-CN-spectral-pass and BKdV-S4-positive.

PDE (with linear stiff part isolated for v):
    u_t = -3 u u_x - 6 v v_x - v_xxx                       (no linear stiff term in u-eq)
    v_t = -6 v v_x - v_xxx - d/dx(u v)
         = L_v(v) + N_v(u, v) ,  L_v(v) = -v_xxx ,  N_v(u,v) = -6 v v_x - d/dx(u v)

In Fourier: (v_hat)_t = +i k^3 v_hat + N_v_hat (linear ~ +ik^3 v_hat, treated implicitly via CN)

Scheme: IMEX-CN/Midpoint (2nd-order on both linear and nonlinear)
  Stage 1 (predictor to t^{n+1/2}):
      (1 - dt/4 * ik^3) v_hat^{n+1/2} = (1 + dt/4 * ik^3) v_hat^n + (dt/2)*N_v(u^n,v^n)_hat
      u^{n+1/2} = u^n + (dt/2)*N_u(u^n, v^n)
  Stage 2 (full step):
      (1 - dt/2 * ik^3) v_hat^{n+1} = (1 + dt/2 * ik^3) v_hat^n + dt*N_v(u^{n+1/2}, v^{n+1/2})_hat
      u^{n+1} = u^n + dt*N_u(u^{n+1/2}, v^{n+1/2})

N_u(u,v) = -3 u u_x - 6 v v_x - v_xxx_explicit ... wait, the v_xxx in u-eq is NOT v_xxx of u; it's v_xxx of v
  i.e. u_t has term -v_xxx. This is a derivative of v, not stiff in u.
  So N_u(u, v) = -3 u u_x - 6 v v_x - v_xxx  (all explicit in u-variable, the v_xxx is a forcing).

The cubic-derivative forcing v_xxx of v in u-equation has explicit-stability constraint dt < 2.83/k_max^3
At Nx=256 with 2/3 dealias, k_eff = (2/3)*pi/dx = (2/3)*pi*Nx/L = (2/3)*pi*256/30 ~ 17.87
dt < 2.83/k_eff^3 = 2.83/5707 = 4.96e-4 -> dt=2e-4 safe.

IC: v0 = 2 sech^2(x+5), u0 = 0.5 v0^2 + 0.2 v0
Domain: x in [-15, 15], Nx = 256, periodic
T = 8.0
"""

import os
import time
import numpy as np

# --- Grid setup ---
L = 30.0
Nx = 256
x = np.linspace(-L / 2.0, L / 2.0, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k        # multiplier for d/dx
D3 = -1j * k**3    # multiplier for d^3/dx^3 (since (ik)^3 = -ik^3)
mk2 = -k**2        # multiplier for d^2/dx^2
# Linear stiff coefficient for v_hat_t from BKdV: v_t = -v_xxx + N_v
# => v_hat_t = -D3 * v_hat + N_v_hat = (+i k^3) * v_hat + N_v_hat
L_v = -D3          # = +1j*k^3

# 2/3-rule dealiasing mask
k_idx = np.fft.fftfreq(Nx, d=1.0 / Nx)
dealias_mask = (np.abs(k_idx) <= Nx // 3).astype(np.float64)


def dealias_real(field):
    hat = np.fft.fft(field)
    hat *= dealias_mask
    return np.real(np.fft.ifft(hat))


# Precompute CN factors for v's linear stiff part:
# (v_hat)_t_linear = +ik^3 v_hat
# CN half-step:  (1 - 0.25*dt*ik^3) v* = (1 + 0.25*dt*ik^3) v_n + 0.5*dt*N
# CN full-step:  (1 - 0.5*dt*ik^3) v_{n+1} = (1 + 0.5*dt*ik^3) v_n + dt*N
# We'll precompute denom and numer factors

dt = 2.0e-4
# CN: (1 - 0.5*dt*L_v) v_new = (1 + 0.5*dt*L_v) v_old + dt*N
cn_num_half = (1.0 + 0.25 * dt * L_v)
cn_den_half = (1.0 - 0.25 * dt * L_v)
cn_num_full = (1.0 + 0.5 * dt * L_v)
cn_den_full = (1.0 - 0.5 * dt * L_v)


# --- IC ---
v0 = 2.0 * (1.0 / np.cosh(x + 5.0))**2
u0 = 0.5 * v0**2 + 0.2 * v0


def nonlinear_terms(u, v):
    """Compute N_u(u, v) and N_v_hat(u, v).

    N_u = -3 u u_x - 6 v v_x - v_xxx              (real)
    N_v_hat = FFT(N_v),  N_v = -6 v v_x - d/dx(u v)  (returned in Fourier space, dealiased)
    """
    # Dealias inputs (cheap consistency)
    u = dealias_real(u)
    v = dealias_real(v)

    u_hat = np.fft.fft(u)
    v_hat = np.fft.fft(v)
    u_x = np.real(np.fft.ifft(ik * u_hat))
    v_x = np.real(np.fft.ifft(ik * v_hat))
    v_xxx = np.real(np.fft.ifft(D3 * v_hat))

    # u*u_x dealiased
    uu_x_hat = np.fft.fft(u * u_x) * dealias_mask
    uu_x = np.real(np.fft.ifft(uu_x_hat))
    # v*v_x dealiased
    vv_x_hat = np.fft.fft(v * v_x) * dealias_mask
    vv_x = np.real(np.fft.ifft(vv_x_hat))
    # u*v dealiased then differentiated
    uv_hat = np.fft.fft(u * v) * dealias_mask
    uv_x = np.real(np.fft.ifft(ik * uv_hat))

    N_u = -3.0 * uu_x - 6.0 * vv_x - v_xxx
    N_v = -6.0 * vv_x - uv_x
    N_v_hat = np.fft.fft(N_v) * dealias_mask
    return N_u, N_v_hat


def imex_step(u, v, dt):
    """One IMEX-CN/midpoint step, dt is the full step size."""
    v_hat = np.fft.fft(v)

    # Stage 1: predictor at t^{n+1/2}
    N_u_n, N_v_hat_n = nonlinear_terms(u, v)
    v_hat_star = (cn_num_half * v_hat + 0.5 * dt * N_v_hat_n) / cn_den_half
    u_star = u + 0.5 * dt * N_u_n
    v_star = np.real(np.fft.ifft(v_hat_star))

    # Stage 2: full step using midpoint nonlinear
    N_u_mid, N_v_hat_mid = nonlinear_terms(u_star, v_star)
    v_hat_new = (cn_num_full * v_hat + dt * N_v_hat_mid) / cn_den_full
    u_new = u + dt * N_u_mid
    v_new = np.real(np.fft.ifft(v_hat_new))
    return u_new, v_new


# --- Time stepping ---
T_final = 8.0
n_steps = int(round(T_final / dt))

n_snapshots = 21
snapshot_steps = np.linspace(0, n_steps, n_snapshots).astype(int)
snapshots = np.empty((n_snapshots, 2, Nx), dtype=np.float64)
snap_times = np.empty(n_snapshots, dtype=np.float64)

u = u0.copy()
v = v0.copy()
snap_idx = 0
snapshots[snap_idx, 0, :] = u
snapshots[snap_idx, 1, :] = v
snap_times[snap_idx] = 0.0
snap_idx += 1

t0 = time.time()
blowup_step = -1
for step in range(1, n_steps + 1):
    u, v = imex_step(u, v, dt)
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        blowup_step = step
        print(f"BLOW-UP at step {step} (t={step*dt:.4f}): non-finite values detected.")
        while snap_idx < n_snapshots:
            snapshots[snap_idx, 0, :] = np.nan
            snapshots[snap_idx, 1, :] = np.nan
            snap_times[snap_idx] = step * dt
            snap_idx += 1
        break
    if snap_idx < n_snapshots and step == snapshot_steps[snap_idx]:
        snapshots[snap_idx, 0, :] = u
        snapshots[snap_idx, 1, :] = v
        snap_times[snap_idx] = step * dt
        snap_idx += 1

elapsed = time.time() - t0
print(f"Integration done in {elapsed:.2f}s, blowup_step={blowup_step}, snapshots written={snap_idx}")


def trapz(y, xs):
    return float(np.trapezoid(y, xs)) if hasattr(np, "trapezoid") else float(np.sum(y) * (xs[1] - xs[0]))


def diag(field, name):
    finite = np.all(np.isfinite(field))
    n_nan = int(np.sum(~np.isfinite(field)))
    if finite:
        print(f"  {name}: max={np.max(field):.4f}, min={np.min(field):.4f}, L2={np.sqrt(np.mean(field**2)):.4f}")
    else:
        print(f"  {name}: NOT FINITE (n_nan/inf={n_nan})")
    return finite


print("\nIC diagnostics:")
diag(snapshots[0, 0], "u(0)")
diag(snapshots[0, 1], "v(0)")
print("\nFinal-state diagnostics:")
finite_u = diag(snapshots[-1, 0], "u(T)")
finite_v = diag(snapshots[-1, 1], "v(T)")
if finite_v:
    mass_v_0 = trapz(snapshots[0, 1], x)
    mass_v_T = trapz(snapshots[-1, 1], x)
    print(f"  mass(v): 0->T  {mass_v_0:.6f} -> {mass_v_T:.6f}, rel_drift={(mass_v_T-mass_v_0)/mass_v_0*100:.4f}%")
    vT = snapshots[-1, 1]
    is_peak = (vT > np.roll(vT, 1)) & (vT > np.roll(vT, -1))
    n_peaks = int(np.sum(is_peak))
    v_max = float(np.max(vT))
    x_at_max = float(x[np.argmax(vT)])
    print(f"  v_max(T)={v_max:.4f}  x_at_vmax={x_at_max:.3f}  n_peaks(T)={n_peaks}")
    print("\nSnapshot trace (t, v_max, |u|_max, mass_v):")
    for i, t in enumerate(snap_times):
        if np.all(np.isfinite(snapshots[i])):
            vmax_i = np.max(snapshots[i, 1])
            umax_i = np.max(np.abs(snapshots[i, 0]))
            mv = trapz(snapshots[i, 1], x)
            print(f"  t={t:.3f}  v_max={vmax_i:.4f}  |u|_max={umax_i:.4f}  mass_v={mv:.6f}")
        else:
            print(f"  t={t:.3f}  NaN")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", snapshots)
print(f"\nSaved pred_results/T_A.npy with shape {snapshots.shape}")
