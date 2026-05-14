"""
BKdV-S6 Round 1 (E1, mandatory baseline): pre-validated stack with NO u-viscosity.

PDE (periodic x in [-15, 15], Nx=256):
    u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -d_x(u v)

IC (FIXED across BKdV-S6 rounds):
    v(x,0) = 1.5 * sech^2(x + 5)
    u(x,0) = 1.5 * (1 - tanh(x / 0.5)) / 2     (smoothed bore: u_L=1.5 -> u_R=0)

Solver stack (pre-validated, but DELIBERATELY w/o u-dissipation):
    - Fourier pseudospectral derivatives (all spatial derivatives, including u_x)
    - 2/3-rule dealiasing on every nonlinear product (u^2 here, u*v, v^2, v*v_x)
    - Classical explicit RK4 in time
    - dt = 1e-4
    - NO viscosity, NO hyperviscosity, NO low-pass filter on u

This is the negative-baseline experiment: expectation is that the bore-like u
develops a shock-front whose intrinsic high-k content is NOT absorbed by 2/3
dealiasing (dealiasing prevents aliasing of products into resolved modes, but
does not dissipate energy at high k). We anticipate Gibbs oscillations growing
at the bore, |u|_max(t) climbing well above the IC bound 1.5, and possibly
non-finite values before T=6.

Diagnostics saved per snapshot:
    t, mass_u, mass_v, energy=0.5*int(u^2+v^2), u_max=|u|_inf, u_min, v_max,
    sup, finite, u_high_k_energy (E_{|k|>k_max/3}), spectral_slope.
"""

import os
import sys
import time
import numpy as np

ROUND_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------
# Grid & spectral operators (periodic, Fourier)
# ------------------------------------------------------------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for periodic domain of length L
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
k2 = k ** 2

# 2/3 dealiasing mask
k_abs = np.abs(k)
k_max = float(np.max(k_abs))
dealias_mask = (k_abs <= (2.0 / 3.0) * k_max).astype(float)
high_k_mask = (k_abs > (2.0 / 3.0) * k_max).astype(float)  # for diagnostic only


def fft_dealias(a):
    """FFT followed by 2/3 dealiasing mask."""
    return np.fft.fft(a) * dealias_mask


def dx_spec(f_phys):
    """Spectral first derivative (with dealiasing applied to the input field)."""
    return np.real(np.fft.ifft(ik * fft_dealias(f_phys)))


def dxx_spec(f_phys):
    return np.real(np.fft.ifft(-k2 * fft_dealias(f_phys)))


def dxxx_spec(f_phys):
    return np.real(np.fft.ifft(-1j * (k ** 3) * fft_dealias(f_phys)))


# ------------------------------------------------------------
# RHS  (FULL right-hand-side; classical explicit RK4 in time)
# u_t = -3 u u_x - d_x(3 v^2 + v_xx)
# v_t = -6 v v_x - v_xxx - d_x(u v)
# All nonlinear products are formed in physical space then dealiased on FFT.
# NO u-viscosity / hyperviscosity / filter.
# ------------------------------------------------------------
def rhs(u, v):
    # Dealiased physical-space fields for products
    uh = fft_dealias(u)
    vh = fft_dealias(v)
    u_d = np.real(np.fft.ifft(uh))
    v_d = np.real(np.fft.ifft(vh))

    # Single-field spectral derivatives
    u_x = np.real(np.fft.ifft(ik * uh))
    v_x = np.real(np.fft.ifft(ik * vh))
    v_xx = np.real(np.fft.ifft(-k2 * vh))
    v_xxx = np.real(np.fft.ifft(-1j * (k ** 3) * vh))

    # u_t pieces
    # 3 u u_x  -> nonlinear product u*u_x dealiased
    uux = np.real(np.fft.ifft(np.fft.fft(u_d * u_x) * dealias_mask))
    # d_x(3 v^2 + v_xx): form 3 v^2 + v_xx then spectral d_x with dealias
    coupling_field = 3.0 * (v_d ** 2) + v_xx
    dcoupling = np.real(np.fft.ifft(ik * (np.fft.fft(coupling_field) * dealias_mask)))
    rhs_u = -3.0 * uux - dcoupling

    # v_t pieces
    # 6 v v_x dealiased
    vvx = np.real(np.fft.ifft(np.fft.fft(v_d * v_x) * dealias_mask))
    # d_x(u v) dealiased
    uv = u_d * v_d
    duv = np.real(np.fft.ifft(ik * (np.fft.fft(uv) * dealias_mask)))
    rhs_v = -6.0 * vvx - v_xxx - duv

    return rhs_u, rhs_v


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new


# ------------------------------------------------------------
# Diagnostics
# ------------------------------------------------------------
def diagnostics(u, v):
    finite = bool(np.all(np.isfinite(u)) and np.all(np.isfinite(v)))
    if not finite:
        return dict(
            mass_u=float('nan'), mass_v=float('nan'),
            energy=float('nan'), u_max=float('nan'), u_min=float('nan'),
            v_max=float('nan'), sup=float('nan'),
            u_high_k_energy=float('nan'), u_total_spec_energy=float('nan'),
            finite=False,
        )
    mass_u = float(np.sum(u) * dx)
    mass_v = float(np.sum(v) * dx)
    energy = float(0.5 * np.sum(u * u + v * v) * dx)
    u_max = float(np.max(np.abs(u)))
    u_min = float(np.min(u))
    v_max = float(np.max(v))
    sup = float(max(np.max(np.abs(u)), np.max(np.abs(v))))
    uh = np.fft.fft(u)
    # Parseval-normalized power spectrum
    power = (np.abs(uh) ** 2) / (Nx * Nx)
    u_total_spec_energy = float(np.sum(power))
    u_high_k_energy = float(np.sum(power * high_k_mask))
    return dict(
        mass_u=mass_u, mass_v=mass_v, energy=energy,
        u_max=u_max, u_min=u_min, v_max=v_max, sup=sup,
        u_high_k_energy=u_high_k_energy,
        u_total_spec_energy=u_total_spec_energy,
        finite=True,
    )


# ------------------------------------------------------------
# Initial condition (FIXED across S6 rounds)
# ------------------------------------------------------------
v0 = 1.5 * (1.0 / np.cosh(x + 5.0)) ** 2
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
u = u0.copy()
v = v0.copy()

# ------------------------------------------------------------
# Time integration
# ------------------------------------------------------------
T = 6.0
dt = 1.0e-4
nsteps = int(round(T / dt))

print(f"[grid]  Nx={Nx}  L={L}  dx={dx:.4e}", flush=True)
print(f"[time]  T={T}  dt={dt:.4e}  nsteps={nsteps}", flush=True)
print(f"[IC]    v0=1.5 sech^2(x+5)   u0=1.5(1-tanh(x/0.5))/2 (smoothed bore)", flush=True)
print(f"[stack] Fourier pseudospectral + 2/3 dealias + classical RK4 ; "
      f"NO u-viscosity/hyperviscosity/filter", flush=True)

d0 = diagnostics(u, v)
print(f"[init]  mass_u={d0['mass_u']:+.6e} mass_v={d0['mass_v']:+.6e} "
      f"energy={d0['energy']:.6e} u_max={d0['u_max']:.4f} v_max={d0['v_max']:.4f} "
      f"u_high_k_E={d0['u_high_k_energy']:.3e}", flush=True)

# Snapshot schedule: 25 evenly-spaced snapshots including t=0 and t=T (dt=0.25)
n_snap = 25
snap_steps = np.linspace(0, nsteps, n_snap, dtype=int)
snap_set = set(int(s) for s in snap_steps)

snapshots_u = [u.copy()]
snapshots_v = [v.copy()]
snapshot_times = [0.0]
diag_log = [{'t': 0.0, **d0}]

t0 = time.time()
report_every = max(1, nsteps // 30)
blowup_t = None
blowup_step = None

for n in range(1, nsteps + 1):
    u, v = rk4_step(u, v, dt)
    t = n * dt
    if n in snap_set:
        d = diagnostics(u, v)
        snapshots_u.append(u.copy())
        snapshots_v.append(v.copy())
        snapshot_times.append(t)
        diag_log.append({'t': t, **d})
    if n % report_every == 0 or n == nsteps:
        d = diagnostics(u, v)
        print(f"[t={t:7.4f}] mass_u={d['mass_u']:+.4e} u_max={d['u_max']:.4f} "
              f"u_min={d['u_min']:+.4f} v_max={d['v_max']:.4f} energy={d['energy']:.4e} "
              f"u_hk={d['u_high_k_energy']:.3e} finite={d['finite']}", flush=True)
        if (not d['finite']) or d['sup'] > 1e6:
            print(f"[BLOWUP] at t={t:.4f}  sup={d['sup']:.3e}", flush=True)
            blowup_t = t
            blowup_step = n
            break

elapsed = time.time() - t0
final = diagnostics(u, v)

# Save snapshots and diagnostics
out_npz = os.path.join(ROUND_DIR, "snapshots.npz")
np.savez(out_npz,
         x=x,
         times=np.array(snapshot_times),
         u=np.array(snapshots_u),
         v=np.array(snapshots_v))

diag_keys = list(diag_log[0].keys())
diag_arrs = {kk: np.array([d[kk] for d in diag_log]) for kk in diag_keys}
np.savez(os.path.join(ROUND_DIR, "diag.npz"), **diag_arrs)

print(f"[saved] {out_npz}  ({len(snapshot_times)} snapshots)", flush=True)

# --- Stability summary ---
u_maxs = np.array([d['u_max'] for d in diag_log])
v_maxs = np.array([d['v_max'] for d in diag_log])
u_mins = np.array([d['u_min'] for d in diag_log])
u_hk = np.array([d['u_high_k_energy'] for d in diag_log])
u_total_E = np.array([d['u_total_spec_energy'] for d in diag_log])
masses_u = np.array([d['mass_u'] for d in diag_log])
masses_v = np.array([d['mass_v'] for d in diag_log])
energies = np.array([d['energy'] for d in diag_log])
ts_arr = np.array([d['t'] for d in diag_log])

print(f"[summary] u_max(t): t0={u_maxs[0]:.4f}  tFinal={u_maxs[-1]:.4f}  "
      f"max_over_run={np.nanmax(u_maxs):.4f}  at t={ts_arr[np.nanargmax(u_maxs)]:.3f}",
      flush=True)
print(f"[summary] u_min(t): t0={u_mins[0]:+.4f}  tFinal={u_mins[-1]:+.4f}  "
      f"min_over_run={np.nanmin(u_mins):+.4f}", flush=True)
print(f"[summary] v_max(t): t0={v_maxs[0]:.4f}  max={np.nanmax(v_maxs):.4f}  "
      f"final={v_maxs[-1]:.4f}", flush=True)
print(f"[summary] u_high_k_E:  t0={u_hk[0]:.3e}  max={np.nanmax(u_hk):.3e}  "
      f"final={u_hk[-1]:.3e}", flush=True)
print(f"[summary] u_total_spec_E: t0={u_total_E[0]:.3e}  final={u_total_E[-1]:.3e}",
      flush=True)
print(f"[summary] energy(u,v): t0={energies[0]:.4e}  final={energies[-1]:.4e}", flush=True)
print(f"[summary] elapsed = {elapsed:.1f}s", flush=True)
if blowup_t is not None:
    print(f"[summary] BLOWUP at t={blowup_t:.4f} (step {blowup_step})", flush=True)
else:
    print(f"[summary] integrated to T={T:.4f} without IEEE blow-up", flush=True)

print("[done] E1 baseline complete.", flush=True)
