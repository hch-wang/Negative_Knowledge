"""
BKdV-S6 Round 2 (E2, single-component upgrade): add small linear viscosity
eps * u_xx to the u-equation, eps = 1e-4. Everything else identical to E1.

PDE actually integrated:
    u_t + 3 u u_x = -d_x(3 v^2 + v_xx) + eps * u_xx     (new term)
    v_t + 6 v v_x + v_xxx = -d_x(u v)

Solver stack (same pre-validated stack as E1):
    - Fourier pseudospectral for all spatial derivatives
    - 2/3-rule dealiasing on every nonlinear product
    - Classical explicit RK4 in time
    - dt = 1e-4
    - u_xx is treated explicitly inside the same RK4 RHS (eps*k^2 ~ 1e-4 * 720
      ~ 0.07 at the high-k end; eps*k^2*dt ~ 7e-6  no CFL trouble at all).

Question being answered: does this small eps suffice to suppress the Gibbs
ringing reported in E1 (TV(u) 3 -> 126, u_max 1.5 -> 3.4)?

Same IC and snapshot schedule as E1; we will compare side-by-side.
"""

import os
import sys
import time
import numpy as np

ROUND_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------
# Grid & spectral operators (identical to E1)
# ------------------------------------------------------------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
k2 = k ** 2

k_abs = np.abs(k)
k_max = float(np.max(k_abs))
dealias_mask = (k_abs <= (2.0 / 3.0) * k_max).astype(float)
high_k_mask_mid = ((k_abs > k_max / 3.0) & (k_abs <= 2.0 / 3.0 * k_max)).astype(float)


def fft_dealias(a):
    return np.fft.fft(a) * dealias_mask


# ------------------------------------------------------------
# Linear viscosity coefficient on u
# ------------------------------------------------------------
EPS_U = 1.0e-4


def rhs(u, v):
    uh = fft_dealias(u)
    vh = fft_dealias(v)
    u_d = np.real(np.fft.ifft(uh))
    v_d = np.real(np.fft.ifft(vh))

    u_x = np.real(np.fft.ifft(ik * uh))
    u_xx = np.real(np.fft.ifft(-k2 * uh))     # for eps*u_xx
    v_x = np.real(np.fft.ifft(ik * vh))
    v_xx = np.real(np.fft.ifft(-k2 * vh))
    v_xxx = np.real(np.fft.ifft(-1j * (k ** 3) * vh))

    # u_t = -3 u u_x - d_x(3 v^2 + v_xx) + EPS_U * u_xx
    uux = np.real(np.fft.ifft(np.fft.fft(u_d * u_x) * dealias_mask))
    coupling_field = 3.0 * (v_d ** 2) + v_xx
    dcoupling = np.real(np.fft.ifft(ik * (np.fft.fft(coupling_field) * dealias_mask)))
    rhs_u = -3.0 * uux - dcoupling + EPS_U * u_xx

    # v_t = -6 v v_x - v_xxx - d_x(u v)
    vvx = np.real(np.fft.ifft(np.fft.fft(v_d * v_x) * dealias_mask))
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


def diagnostics(u, v):
    finite = bool(np.all(np.isfinite(u)) and np.all(np.isfinite(v)))
    if not finite:
        return dict(mass_u=float('nan'), mass_v=float('nan'),
                    energy=float('nan'), u_max=float('nan'), u_min=float('nan'),
                    v_max=float('nan'), sup=float('nan'),
                    TV_u=float('nan'),
                    u_mid_k_energy_ratio=float('nan'), finite=False)
    mass_u = float(np.sum(u) * dx)
    mass_v = float(np.sum(v) * dx)
    energy = float(0.5 * np.sum(u * u + v * v) * dx)
    u_max = float(np.max(np.abs(u)))
    u_min = float(np.min(u))
    v_max = float(np.max(v))
    sup = float(max(np.max(np.abs(u)), np.max(np.abs(v))))
    TV_u = float(np.sum(np.abs(np.diff(u))) + abs(u[-1] - u[0]))
    uh = np.fft.fft(u)
    power = (np.abs(uh) ** 2) / (Nx * Nx)
    E_total = float(np.sum(power))
    E_mid = float(np.sum(power * high_k_mask_mid))
    ratio = E_mid / E_total if E_total > 0 else 0.0
    return dict(
        mass_u=mass_u, mass_v=mass_v, energy=energy,
        u_max=u_max, u_min=u_min, v_max=v_max, sup=sup,
        TV_u=TV_u, u_mid_k_energy_ratio=ratio, finite=True,
    )


# Fixed IC (same as E1)
v0 = 1.5 * (1.0 / np.cosh(x + 5.0)) ** 2
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
u = u0.copy()
v = v0.copy()

T = 6.0
dt = 1.0e-4
nsteps = int(round(T / dt))

print(f"[grid]  Nx={Nx}  L={L}  dx={dx:.4e}", flush=True)
print(f"[time]  T={T}  dt={dt:.4e}  nsteps={nsteps}", flush=True)
print(f"[stack] Fourier + 2/3 dealias + RK4 + linear visc eps_u={EPS_U:.2e} on u_xx",
      flush=True)
print(f"[IC]    v0=1.5 sech^2(x+5)   u0=1.5 (1-tanh(x/0.5))/2", flush=True)

d0 = diagnostics(u, v)
print(f"[init]  u_max={d0['u_max']:.4f}  v_max={d0['v_max']:.4f}  "
      f"TV(u)={d0['TV_u']:.3f}  E_midk/E_tot={d0['u_mid_k_energy_ratio']:.3e}",
      flush=True)

n_snap = 25
snap_steps = np.linspace(0, nsteps, n_snap, dtype=int)
snap_set = set(int(s) for s in snap_steps)

snapshots_u = [u.copy()]
snapshots_v = [v.copy()]
snapshot_times = [0.0]
diag_log = [{'t': 0.0, **d0}]

t0 = time.time()
report_every = max(1, nsteps // 30)

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
        print(f"[t={t:7.4f}] u_max={d['u_max']:.4f} u_min={d['u_min']:+.4f} "
              f"v_max={d['v_max']:.4f} TV(u)={d['TV_u']:.3f} "
              f"E_midk/E_tot={d['u_mid_k_energy_ratio']:.3e} finite={d['finite']}",
              flush=True)
        if (not d['finite']) or d['sup'] > 1e6:
            print(f"[BLOWUP] at t={t:.4f}", flush=True)
            break

elapsed = time.time() - t0

# Save snapshots
out_npz = os.path.join(ROUND_DIR, "snapshots.npz")
np.savez(out_npz, x=x, times=np.array(snapshot_times),
         u=np.array(snapshots_u), v=np.array(snapshots_v))
diag_keys = list(diag_log[0].keys())
diag_arrs = {kk: np.array([d[kk] for d in diag_log]) for kk in diag_keys}
np.savez(os.path.join(ROUND_DIR, "diag.npz"), **diag_arrs)

# Cross-check vs E1 if available
e1_path = os.path.join(os.path.dirname(ROUND_DIR), "round1", "snapshots.npz")
if os.path.exists(e1_path):
    e1 = np.load(e1_path)
    u_E1 = e1['u']; v_E1 = e1['v']; t_E1 = e1['times']
    print("[cmp E1->E2]", flush=True)
    for i, t_snap in enumerate(snapshot_times):
        # match index 1:1 since both used same snap schedule
        if i >= len(t_E1) or abs(t_E1[i] - t_snap) > 1e-9:
            continue
        u_e2 = snapshots_u[i]; u_e1 = u_E1[i]
        u_max_e1 = float(np.max(np.abs(u_e1)))
        u_max_e2 = float(np.max(np.abs(u_e2)))
        TV_e1 = float(np.sum(np.abs(np.diff(u_e1))) + abs(u_e1[-1] - u_e1[0]))
        TV_e2 = float(np.sum(np.abs(np.diff(u_e2))) + abs(u_e2[-1] - u_e2[0]))
        if i % 4 == 0 or i == len(snapshot_times) - 1:
            print(f"  t={t_snap:5.2f}  u_max  E1={u_max_e1:.3f} E2={u_max_e2:.3f}  "
                  f"TV(u)  E1={TV_e1:.2f}  E2={TV_e2:.2f}", flush=True)

u_maxs = np.array([d['u_max'] for d in diag_log])
u_mins = np.array([d['u_min'] for d in diag_log])
v_maxs = np.array([d['v_max'] for d in diag_log])
TVs = np.array([d['TV_u'] for d in diag_log])
ratios = np.array([d['u_mid_k_energy_ratio'] for d in diag_log])
ts_arr = np.array([d['t'] for d in diag_log])

print(f"[summary] u_max(t): t0={u_maxs[0]:.4f}  max={np.nanmax(u_maxs):.4f}  "
      f"final={u_maxs[-1]:.4f}", flush=True)
print(f"[summary] u_min(t): t0={u_mins[0]:+.4f}  min={np.nanmin(u_mins):+.4f}  "
      f"final={u_mins[-1]:+.4f}", flush=True)
print(f"[summary] TV(u):    t0={TVs[0]:.3f}  max={np.nanmax(TVs):.3f}  "
      f"final={TVs[-1]:.3f}", flush=True)
print(f"[summary] mid-k ratio: t0={ratios[0]:.3e}  max={np.nanmax(ratios):.3e}  "
      f"final={ratios[-1]:.3e}", flush=True)
print(f"[summary] v_max(t): t0={v_maxs[0]:.4f}  final={v_maxs[-1]:.4f}", flush=True)
print(f"[summary] elapsed={elapsed:.1f}s", flush=True)
print("[done] E2 (eps=1e-4 linear visc) complete.", flush=True)
