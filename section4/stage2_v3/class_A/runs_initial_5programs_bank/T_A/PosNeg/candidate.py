"""
E3: E2 stack + single-component upgrade: switch RK4-over-full-RHS to
    IMEX scheme with CN on the stiff linear v_xxx and explicit midpoint-RK2 on
    the nonlinear remainder (matches kb-kdv-IMEX-CN-spectral-pass and BKdV-S2
    solver used by the deep-synthesis positive entries).

Single component change vs E2:
  - Time integrator: explicit RK4 over full RHS  ->  IMEX-CN on v_xxx + midpoint-RK2 on nonlinear
  - Everything else identical: Fourier pseudospectral, 2/3 dealiasing, dt=2.5e-4, Nx=256, IC, T

dt: post-dealias RK4 dispersion CFL ~ 4.94e-4; CN denominator |1 - dt/2 ik^3| >= 1 so unconditionally
stable for v_xxx; we use dt=2.5e-4 (BKdV-S2 pilot value) — explicit nonlinear CFL satisfied since
midpoint-RK2 is more conservative than RK4 only on the nonlinear advection rate ~6 v + 1.5 v^2
(at amp=2, max ~12+6=18). Nonlinear-CFL = dt * 18 * k_max_eff. With k_max_eff = (2/3)*kmax = 17.87,
NL-CFL ~ 2.5e-4 * 18 * 17.87 = 0.080 << 1. Safe.

Bank citations:
  positive: kb-kdv-IMEX-CN-spectral-pass (CN denominator |1 - dt/2 ik^3| >=1 unconditionally stable
            for dispersive stiffness), kb-gardner-G2-IMEX-CN-dealiased-stableRadiation,
            BKdV-S1-positive (Fourier+2/3+RK4 ran cleanly — preserved structure; we keep dealias + Fourier),
            BKdV-S2 solver stack (IMEX-CN + midpoint RK2 + 2/3 dealias)
  rejected: kb-kdv-IFRK4-blowup (IF-RK4 overflows at high k), kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup
            (warns dt must shrink with amplitude — at amp=2 our NL-CFL bound is 0.08 << 1, safe).
"""
import numpy as np

# Grid
L = 30.0
Nx = 256
x = np.linspace(-L/2, L/2, Nx, endpoint=False)
dx = L / Nx
k = 2*np.pi*np.fft.fftfreq(Nx, d=dx)
ik = 1j*k

# 2/3 dealias mask
k_idx = np.fft.fftfreq(Nx, d=1.0) * Nx
dealias = (np.abs(k_idx) <= Nx/3).astype(np.float64)

# IC
v0 = 2.0 * (1.0/np.cosh(x + 5.0))**2
u0 = 0.5 * v0**2 + 0.2 * v0

# Time params
T_final = 8.0
dt = 2.5e-4
nsteps = int(round(T_final/dt))
snap_times = np.linspace(0.0, T_final, 5)
snap_steps = [int(round(t/dt)) for t in snap_times]
snapshots = []

# Linear operator for v: dv_hat/dt = (+i k^3) v_hat + N_hat  (since -v_xxx contributes +ik^3 in spectral)
L_v = 1j * (k**3)
half = 0.5 * dt * L_v
cn_num = 1.0 + half       # multiply v_hat^n
cn_den = 1.0 - half       # divide


def filt(field):
    fh = np.fft.fft(field) * dealias
    return np.real(np.fft.ifft(fh))


def fft_d(field, k_factor):
    fh = np.fft.fft(field) * dealias
    return np.real(np.fft.ifft(k_factor * fh))


def nonlinear_rhs(u, v):
    """Return (Nu, Nv) where du/dt = Nu (fully nonlinear here, no stiff linear),
       dv/dt = +ik^3 v_hat (handled implicitly elsewhere) + Nv."""
    u = filt(u)
    v = filt(v)
    u_x = fft_d(u, ik)
    v_x = fft_d(v, ik)
    v_xx = fft_d(v, -(k**2))
    # 3 v^2 + v_xx
    inner_u = 3.0*v*v + v_xx
    d_inner_u = fft_d(inner_u, ik)
    uux = u*u_x
    uux = filt(uux)
    Nu = -3.0*uux - d_inner_u
    vvx = v*v_x
    vvx = filt(vvx)
    uv = u*v
    d_uv = fft_d(uv, ik)
    Nv = -6.0*vvx - d_uv
    return filt(Nu), filt(Nv)


def step_imex_midpoint(u, v, dt):
    """One IMEX step: midpoint-RK2 on the nonlinear part, CN on the linear v_xxx.

    Stage 1: predict half-step quantities.
      v_hat_half = ( cn_num_half * v_hat^n + 0.5*dt * N_v_hat^n ) / cn_den_half
      where cn_num_half = 1 + 0.5*(dt/2)*L_v, cn_den_half = 1 - 0.5*(dt/2)*L_v
      u_half = u^n + (dt/2) * N_u^n
    Stage 2: evaluate at half-step, then advance full step with CN on linear.
      v_hat^{n+1} = ( cn_num * v_hat^n + dt * N_v_hat_half ) / cn_den
      u^{n+1} = u^n + dt * N_u_half
    """
    # Stage 1: nonlinear at t^n
    Nu1, Nv1 = nonlinear_rhs(u, v)
    # half-step linear weights (CN with dt/2)
    half_half = 0.25 * dt * L_v
    cnH_num = 1.0 + half_half
    cnH_den = 1.0 - half_half
    v_hat = np.fft.fft(v)
    Nv1_hat = np.fft.fft(Nv1)
    v_hat_half = (cnH_num * v_hat + 0.5*dt * Nv1_hat) / cnH_den
    v_half = np.real(np.fft.ifft(v_hat_half * dealias))
    u_half = u + 0.5*dt * Nu1

    # Stage 2: nonlinear at half-step
    Nu2, Nv2 = nonlinear_rhs(u_half, v_half)
    Nv2_hat = np.fft.fft(Nv2)
    v_hat_new = (cn_num * v_hat + dt * Nv2_hat) / cn_den
    v_new = np.real(np.fft.ifft(v_hat_new * dealias))
    u_new = u + dt * Nu2
    u_new = filt(u_new)
    return u_new, v_new


# Main loop
u = u0.copy()
v = v0.copy()
snapshots.append(np.stack([u.copy(), v.copy()]))
saved_idx = 1
mass_v0 = np.trapezoid(v, x)
print(f"t=0  mass_v0={mass_v0:.6g}  max|u|={np.max(np.abs(u)):.4g}  max|v|={np.max(np.abs(v)):.4g}")

blowup_step = None
for step in range(1, nsteps+1):
    u, v = step_imex_midpoint(u, v, dt)
    if (not np.all(np.isfinite(u))) or (not np.all(np.isfinite(v))):
        blowup_step = step
        print(f"BLOWUP at step={step}, t={step*dt:.4f}")
        break
    if saved_idx < 5 and step == snap_steps[saved_idx]:
        snapshots.append(np.stack([u.copy(), v.copy()]))
        mv = np.trapezoid(v, x)
        print(f"snap t={step*dt:.3f}  max|u|={np.max(np.abs(u)):.4g}  max|v|={np.max(np.abs(v)):.4g}  mass_v={mv:.6g}  drift={(mv-mass_v0)/mass_v0*100:.4f}%")
        saved_idx += 1

while len(snapshots) < 5:
    snapshots.append(np.full((2, Nx), np.nan))

arr = np.stack(snapshots, axis=0)
print("output shape:", arr.shape)
print("final max|u|:", np.nanmax(np.abs(arr[-1, 0])))
print("final max|v|:", np.nanmax(np.abs(arr[-1, 1])))
np.save('pred_results/T_A.npy', arr)
print("saved pred_results/T_A.npy")
