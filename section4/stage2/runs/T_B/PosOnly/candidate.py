"""
T_B / PosOnly — Experiment E2.

Single-component upgrade over E1: ADD 2/3-rule dealiasing on every
nonlinear product. Everything else (Fourier-pseudospectral derivatives,
explicit classical RK4 time stepper, dt set by dispersive CFL) is
unchanged from E1.

Rationale:
  E1 (no dealiasing) blew up at t=0.42 with the first overflow in v*v
  — classic aliasing-driven nonlinear instability. The bank consistently
  pairs spectral KdV-type solvers with the 2/3 rule
  (kb-gardner-G2-IMEX-CN-dealiased-stableRadiation,
   kb-kdv-spectral-solitonAmplitude-conservation).

PDE:
    u_t + 3 u u_x = -d_x (3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -d_x (u v)

Output: pred_results/T_B.npy, shape (n_snap, 2, Nx).
"""

import os
import numpy as np

# ---------------- domain & grid ----------------
L   = 30.0
Nx  = 256
dx  = L / Nx
x   = -15.0 + dx * np.arange(Nx)

k   = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik  = 1j * k
ik2 = -(k**2)
ik3 = -1j * (k**3)
kmax = np.max(np.abs(k))

# 2/3-rule dealiasing mask in spectral space.
# Keep |k| <= (2/3) * k_max.
dealias = (np.abs(k) <= (2.0/3.0) * kmax).astype(np.float64)

def fft(f):
    return np.fft.fft(f)

def ifft(F):
    return np.fft.ifft(F)

def deriv_spec(f, multiplier):
    return np.real(ifft(multiplier * fft(f)))

def dealias_prod(*fields):
    """Pseudospectral product with 2/3-rule dealiasing.

    Compute the pointwise product in real space then zero out spectral
    modes outside the 2/3 retention band.
    """
    p = fields[0].copy()
    for fi in fields[1:]:
        p = p * fi
    P = fft(p) * dealias
    return np.real(ifft(P))

def dx_dealiased(f):
    """d/dx applied to a (possibly aliased) field, with 2/3 mask."""
    F = fft(f) * dealias
    return np.real(ifft(ik * F))

def dxx(f):
    return np.real(ifft(ik2 * fft(f)))

def dxxx(f):
    return np.real(ifft(ik3 * fft(f)))

def dx_plain(f):
    return np.real(ifft(ik * fft(f)))

# ---------------- initial condition ----------------
v = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
u = np.zeros_like(x)

# ---------------- time stepping setup ----------------
T_final = 6.0
dt_disp = 0.4 * 2.83 / (kmax**3 + 1e-30)
dt_adv  = 0.4 * dx / max(6.0 * np.max(np.abs(v)), 1.0)
dt = float(min(dt_disp, dt_adv))
n_steps = int(np.ceil(T_final / dt))
dt = T_final / n_steps

print(f"E2: explicit RK4 + Fourier-pseudospectral WITH 2/3 dealiasing.")
print(f"Nx={Nx}, dx={dx:.4f}, kmax={kmax:.3f}")
print(f"dt_disp={dt_disp:.2e}, dt_adv={dt_adv:.2e}, chosen dt={dt:.2e}, n_steps={n_steps}")

# ---------------- RHS ----------------
def rhs(u, v):
    # u_t = -3 u u_x - d_x(3 v^2 + v_xx)
    # v_t = -6 v v_x - v_xxx - d_x(u v)
    ux  = dx_plain(u)
    vx  = dx_plain(v)
    vxx_ = dxx(v)
    vxxx_= dxxx(v)
    uux  = dealias_prod(u, ux)        # u*u_x  dealiased
    vvx  = dealias_prod(v, vx)        # v*v_x  dealiased
    v2   = dealias_prod(v, v)         # v^2    dealiased
    uv   = dealias_prod(u, v)         # u*v    dealiased
    g    = 3.0 * v2 + vxx_
    gx   = dx_plain(g)
    hx   = dx_plain(uv)
    du = -3.0 * uux - gx
    dv = -6.0 * vvx - vxxx_ - hx
    return du, dv

# ---------------- snapshot schedule ----------------
n_snap = 7
t_snaps = np.linspace(0.0, T_final, n_snap)
snap_steps = np.round(t_snaps / dt).astype(int)
snap_steps[-1] = n_steps
snapshots = np.zeros((n_snap, 2, Nx), dtype=np.float64)
snapshots[0, 0] = u
snapshots[0, 1] = v
next_snap_idx = 1

# ---------------- main RK4 loop ----------------
abort = False
for step in range(1, n_steps + 1):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u +     dt*k3u, v +     dt*k3v)
    u = u + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v = v + (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v)

    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        print(f"BLOW-UP at step {step}, t={step*dt:.4f}")
        for j in range(next_snap_idx, n_snap):
            snapshots[j, 0] = u
            snapshots[j, 1] = v
        abort = True
        break

    if next_snap_idx < n_snap and step >= snap_steps[next_snap_idx]:
        snapshots[next_snap_idx, 0] = u
        snapshots[next_snap_idx, 1] = v
        print(f"  snap {next_snap_idx} at step {step}, t={step*dt:.4f}, "
              f"max|v|={np.max(np.abs(v)):.3f}, max|u|={np.max(np.abs(u)):.3f}")
        next_snap_idx += 1

# ---------------- diagnostics ----------------
def trapezoid(y, xv):
    # numpy 2.0 renamed trapz -> trapezoid
    if hasattr(np, "trapezoid"):
        return np.trapezoid(y, xv)
    return np.trapz(y, xv)

mass_v0 = trapezoid(snapshots[0, 1], x)
mass_vT = trapezoid(snapshots[-1, 1], x)
print(f"\nmass(v) initial = {mass_v0:.4f}")
print(f"mass(v) final   = {mass_vT:.4f}")
print(f"mass drift      = {(mass_vT-mass_v0)/abs(mass_v0)*100:.3f} %")
print(f"max|v| final    = {np.max(np.abs(snapshots[-1,1])):.4f}")
print(f"max|u| final    = {np.max(np.abs(snapshots[-1,0])):.4f}")
print(f"any NaN/Inf?    = {(not np.all(np.isfinite(snapshots)))}")

# quick peak count on final v
v_final = snapshots[-1, 1]
if np.all(np.isfinite(v_final)):
    # interior local maxima
    is_peak = (v_final[1:-1] > v_final[:-2]) & (v_final[1:-1] > v_final[2:])
    peak_idx = np.where(is_peak)[0] + 1
    peak_amps = v_final[peak_idx]
    big = peak_amps >= 0.8
    print(f"final v peaks: {len(peak_idx)} interior local maxima; "
          f"{int(big.sum())} have amp>=0.8")
    for i, (ix, amp) in enumerate(zip(peak_idx, peak_amps)):
        if amp >= 0.8:
            print(f"  peak {i}: x={x[ix]:.3f}, amp={amp:.4f}")

# ---------------- save ----------------
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", snapshots)
print("Saved pred_results/T_B.npy  shape =", snapshots.shape)
