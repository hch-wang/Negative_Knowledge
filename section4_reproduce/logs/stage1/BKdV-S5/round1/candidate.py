"""
BKdV-S5  Round 1 (E1): baseline Gardner-soliton-like configuration on the m=0 manifold.

PDE (periodic x in [-15, 15], Nx=256):
    u_t + 3 u u_x + d_x(3 v^2 + v_xx) = 0
    v_t + 6 v v_x + v_xxx + d_x(u v) = 0

Setting m = u - v^2/2, the IC v(x,0) = a sech^2(x+5), u(x,0) = v^2/2  has m_0 = 0.
On the m=0 invariant manifold this PDE reduces to the Gardner equation for v:
    v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0     (Gardner)

So an approximate Gardner soliton on this manifold should travel as a coherent
right-moving structure with little radiative shedding.

Solver stack (pre-validated):
- Fourier pseudospectral spatial derivatives for v's dispersive / coupling
- 2/3-rule dealiasing on every nonlinear product
- IMEX Crank-Nicolson on v_xxx (CN implicit), explicit Euler on v's nonlinear/coupling
- MUSCL + Godunov flux for u's self-flux 3 u u_x (handles shock formation in u),
  explicit Euler on u's coupling term -d_x(3 v^2 + v_xx) using spectral derivative
- dt = 1e-4 (within prescribed [1e-4, 5e-4] band, lower end for the coupled system)

Diagnostics every snapshot:
- mass_u, mass_v   (conservation checks)
- energy = 0.5 * integral(u^2 + v^2)
- m_norm = ||u - v^2/2||_{L^2}     (drift off the m=0 manifold)
- v_peak, v_peak_x  (peak amplitude and its x-location -> phase speed)
- u_peak, u_peak_x
- finite
- sup_max

Saves snapshots to round1/snapshots.npz for downstream rounds.
"""

import os
import sys
import time
import numpy as np

ROUND_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------
# Grid & spectral operators
# ------------------------------------------------------------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for periodic domain of length L
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
k2 = k ** 2
k3 = k ** 3

# 2/3 dealiasing mask
k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)


def fft_dealias(a):
    """FFT followed by dealiasing mask."""
    return np.fft.fft(a) * dealias


def dx_spec(f_phys):
    """Spectral first derivative with dealiasing applied to the field."""
    return np.real(np.fft.ifft(ik * fft_dealias(f_phys)))


def dxx_spec(f_phys):
    return np.real(np.fft.ifft(-k2 * fft_dealias(f_phys)))


# ------------------------------------------------------------
# IMEX-CN linear-implicit operator for v's dispersive term v_xxx
# v_t + v_xxx = ...   =>  in Fourier:  v^_t + (-i k^3) v^ = ...
# Linear multiplier Lhat = -i k^3
# CN form:  (I - dt/2 Lhat) v^_{n+1} = (I + dt/2 Lhat) v^_n + dt * NLhat_n
# where NL contains everything except v_xxx (nonlinear, coupling).
# ------------------------------------------------------------
def make_cn_factors(dt):
    Lhat = -1j * k ** 3
    denom = 1.0 - 0.5 * dt * Lhat
    numer = 1.0 + 0.5 * dt * Lhat
    return denom, numer


# ------------------------------------------------------------
# MUSCL-Godunov on u's self-flux 3 u u_x  =  d_x(3/2 u^2).
# Conservative form f(u) = 1.5 u^2; standard Burgers Riemann solver.
# ------------------------------------------------------------
def muscl_burgers_div(w):
    """Return  - d_x [ (3/2) w^2 ]  approximated by a MUSCL+Godunov scheme.
    Returns same shape as w. Periodic.
    """
    # van-Leer slope on cells
    dw_p = np.roll(w, -1) - w
    dw_m = w - np.roll(w, 1)
    # van Leer limiter on the ratio
    r = np.where(np.abs(dw_p) > 1e-14, dw_m / dw_p, 0.0)
    phi = (r + np.abs(r)) / (1.0 + np.abs(r) + 1e-14)
    slope = phi * dw_p

    # Reconstruct states at right face of cell i:  wL = state of cell i at right face,
    # wR = state of cell i+1 at left face
    wL = w + 0.5 * slope
    wR = np.roll(w - 0.5 * slope, -1)

    # Godunov flux for f(u) = (3/2) u^2 (a Burgers-like flux scaled by 3)
    # f(u) = (3/2) u^2,  f'(u) = 3 u.  s* = (3/2)(wL + wR)/... but standard Burgers Riemann:
    # For Burgers u_t + ( (3/2) u^2 )_x = 0,  the wave speed is 3u, sonic point at u=0.
    fL = 1.5 * wL ** 2
    fR = 1.5 * wR ** 2
    # Shock case (wL >= wR): flux is at upwind side determined by shock speed s=1.5(wL+wR)
    s_shock = 1.5 * (wL + wR)
    f_shock = np.where(s_shock >= 0.0, fL, fR)
    # Rarefaction (wL < wR): if sonic point (u=0) is inside the fan, flux = 0
    f_rare = np.where(wL >= 0.0, fL,
                      np.where(wR <= 0.0, fR, 0.0))
    flux_right = np.where(wL >= wR, f_shock, f_rare)
    flux_left = np.roll(flux_right, 1)
    return -(flux_right - flux_left) / dx


# ------------------------------------------------------------
# RHS for the explicit (nonlinear + coupling) parts.
# We split u-side into Burgers self-flux (MUSCL+Godunov) + coupling (spectral).
# ------------------------------------------------------------
def explicit_rhs(u, v):
    # Dealiased copies for nonlinear products
    uh_d = fft_dealias(u)
    vh_d = fft_dealias(v)
    u_d = np.real(np.fft.ifft(uh_d))
    v_d = np.real(np.fft.ifft(vh_d))

    v_x_d = np.real(np.fft.ifft(ik * vh_d))
    v_xx_d = np.real(np.fft.ifft(-k2 * vh_d))

    # --- u equation: u_t = -3 u u_x - d_x(3 v^2 + v_xx) ---
    # Self-flux via MUSCL-Godunov on original (un-dealiased) u; safer for shocks
    self_flux = muscl_burgers_div(u)         # = -d_x((3/2) u^2) which equals -3 u u_x for smooth u
    prod = 3.0 * v_d ** 2 + v_xx_d
    dprod = np.real(np.fft.ifft(ik * (np.fft.fft(prod) * dealias)))
    rhs_u = self_flux - dprod

    # --- v equation explicit part: -6 v v_x - d_x(u v) ---
    uv = u_d * v_d
    d_uv = np.real(np.fft.ifft(ik * (np.fft.fft(uv) * dealias)))
    rhs_v_expl = -6.0 * v_d * v_x_d - d_uv

    return rhs_u, rhs_v_expl


def step_imex(u, v, dt, cn_denom, cn_numer):
    """One IMEX-CN step.
    - u: forward Euler with explicit RHS (MUSCL-Godunov on self-flux,
         spectral on coupling); no stiff implicit term needed.
    - v: CN on v_xxx implicit, explicit Euler on nonlinear+coupling.
    """
    rhs_u, rhs_v_expl = explicit_rhs(u, v)

    # Update u with forward Euler. Apply mild dealiasing on the spectral part
    # implicitly: rhs_u from spectral coupling is already dealiased; the MUSCL
    # part is grid-conservative.
    u_new = u + dt * rhs_u

    # Update v with IMEX-CN
    vh = np.fft.fft(v)
    nlh = np.fft.fft(rhs_v_expl) * dealias
    vh_new = (cn_numer * vh + dt * nlh) / cn_denom
    vh_new *= dealias
    v_new = np.real(np.fft.ifft(vh_new))

    return u_new, v_new


# ------------------------------------------------------------
# Diagnostics
# ------------------------------------------------------------
def diagnostics(u, v):
    mass_u = float(np.sum(u) * dx)
    mass_v = float(np.sum(v) * dx)
    energy = float(0.5 * np.sum(u * u + v * v) * dx)
    m = u - 0.5 * v ** 2
    m_norm = float(np.sqrt(np.sum(m * m) * dx))
    v_peak = float(np.max(v))
    v_peak_x = float(x[int(np.argmax(v))])
    u_peak = float(np.max(np.abs(u)))
    sup = float(max(np.max(np.abs(u)), np.max(np.abs(v))))
    finite = bool(np.all(np.isfinite(u)) and np.all(np.isfinite(v)))
    return dict(
        mass_u=mass_u, mass_v=mass_v, energy=energy,
        m_norm=m_norm,
        v_peak=v_peak, v_peak_x=v_peak_x,
        u_peak=u_peak, sup=sup, finite=finite,
    )


# ------------------------------------------------------------
# Initial condition: v0 = a sech^2(x+5), u0 = v0^2/2 => m_0 = 0
# Algebra: m_t = u_t - v v_t. After substitution we get
#   m_t = -3 u u_x - 6 v v_x + 6 v^2 v_x + u_x v^2 + u v v_x + (v-1) v_xxx
# Evaluating ON m=0 (u=v^2/2):  m_t|_{m=0} = (v-1)(6 v v_x + v_xxx).
# This is NOT identically zero for sech^2. So the m=0 invariant set is NOT
# preserved for sech^2 ICs; we expect a slow drift off it. Smaller a => slower
# drift; here we use a=1 (low end of allowed band).
# ------------------------------------------------------------
amp = 1.0
v = amp * (1.0 / np.cosh(x + 5.0)) ** 2
u = 0.5 * v ** 2

# ------------------------------------------------------------
# Time integration
# ------------------------------------------------------------
T = 15.0
dt = 1.0e-4
nsteps = int(round(T / dt))
cn_denom, cn_numer = make_cn_factors(dt)

print(f"[grid]  Nx={Nx}  L={L}  dx={dx:.4e}", flush=True)
print(f"[time]  T={T}  dt={dt:.4e}  nsteps={nsteps}", flush=True)
print(f"[IC]    amp={amp}  v0=a sech^2(x+5)  u0=v0^2/2  -> m0=0", flush=True)

d0 = diagnostics(u, v)
print(f"[init]  mass_u={d0['mass_u']:+.6e} mass_v={d0['mass_v']:+.6e} "
      f"energy={d0['energy']:.6e} m_norm={d0['m_norm']:.4e} "
      f"v_peak={d0['v_peak']:.4f}@x={d0['v_peak_x']:+.3f}", flush=True)

# Snapshot schedule: 16 evenly-spaced snapshots including t=0 and t=T
n_snap = 16
snap_steps = np.linspace(0, nsteps, n_snap, dtype=int)
snap_set = set(int(s) for s in snap_steps)

snapshots_u = []
snapshots_v = []
snapshot_times = []
diag_log = []

# Save initial snapshot
snapshots_u.append(u.copy())
snapshots_v.append(v.copy())
snapshot_times.append(0.0)
diag_log.append({'t': 0.0, **d0})

t0 = time.time()
report_every = max(1, nsteps // 30)

for n in range(1, nsteps + 1):
    u, v = step_imex(u, v, dt, cn_denom, cn_numer)
    t = n * dt
    if n in snap_set:
        snapshots_u.append(u.copy())
        snapshots_v.append(v.copy())
        snapshot_times.append(t)
        d = diagnostics(u, v)
        diag_log.append({'t': t, **d})
    if n % report_every == 0 or n == nsteps:
        d = diagnostics(u, v)
        print(f"[t={t:7.4f}] mass_v={d['mass_v']:+.4e} energy={d['energy']:.4e} "
              f"m_norm={d['m_norm']:.4e} v_peak={d['v_peak']:.4f}@x={d['v_peak_x']:+.3f} "
              f"sup={d['sup']:.3e} finite={d['finite']}", flush=True)
        if not d['finite'] or d['sup'] > 1e4:
            print(f"[BLOWUP] at t={t:.4f}", flush=True)
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

# Persist diagnostics as a simple .npz for downstream
diag_keys = list(diag_log[0].keys())
diag_arrs = {k: np.array([d[k] for d in diag_log]) for k in diag_keys}
np.savez(os.path.join(ROUND_DIR, "diag.npz"), **diag_arrs)

print(f"[saved] {out_npz}  ({len(snapshot_times)} snapshots)", flush=True)
print(f"[final] t={T:.4f} v_peak={final['v_peak']:.5f}@x={final['v_peak_x']:+.3f} "
      f"m_norm={final['m_norm']:.4e} mass_v={final['mass_v']:+.5e} "
      f"energy={final['energy']:.5e} elapsed={elapsed:.1f}s", flush=True)

# --- Stability summary ---
v_peaks = np.array([d['v_peak'] for d in diag_log])
mass_vs = np.array([d['mass_v'] for d in diag_log])
energies = np.array([d['energy'] for d in diag_log])
m_norms = np.array([d['m_norm'] for d in diag_log])

print(f"[summary] v_peak range = [{v_peaks.min():.4f}, {v_peaks.max():.4f}]  "
      f"drift = {(v_peaks[-1]-v_peaks[0])/v_peaks[0]*100:+.2f}%", flush=True)
print(f"[summary] mass_v drift = "
      f"{(mass_vs[-1]-mass_vs[0])/mass_vs[0]*100:+.4f}%", flush=True)
print(f"[summary] energy drift = "
      f"{(energies[-1]-energies[0])/energies[0]*100:+.4f}%", flush=True)
print(f"[summary] m_norm: t0={m_norms[0]:.3e}  tT={m_norms[-1]:.3e}  "
      f"max={m_norms.max():.3e}", flush=True)

# Phase speed estimate from peak positions (taking accounting for periodic wrap)
v_peak_xs = np.array([d['v_peak_x'] for d in diag_log])
ts_arr = np.array([d['t'] for d in diag_log])
# unwrap modulo L
xs_unwrap = np.unwrap(v_peak_xs * 2 * np.pi / L) * L / (2 * np.pi)
if len(ts_arr) > 1:
    speed = np.polyfit(ts_arr, xs_unwrap, 1)[0]
    print(f"[summary] phase speed (peak fit) = {speed:.4f}   "
          f"(Gardner soliton c ~ 2 amp = {2*amp:.2f}, KdV-ish reference)", flush=True)

print("[done] E1 baseline complete.", flush=True)
