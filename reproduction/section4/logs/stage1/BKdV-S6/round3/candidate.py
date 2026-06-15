"""
BKdV-S6 Round 3 (E3, single-component upgrade): sweep u-side dissipation
to identify the minimum practical level that bounds u_max and TV(u) over T=6.

Two families are compared, all atop the same pre-validated stack (Fourier +
2/3 dealias + classical RK4, dt=1e-4):
    (A) Linear viscosity:   nu * u_xx,    nu in {1e-3, 1e-2, 5e-2, 1e-1}
    (B) Hyperviscosity k^8: -nu_h * F^-1(k^8 u_hat),  nu_h in {1e-20, 1e-18, 1e-16}

For each (nu, nu_h) we record the same diagnostics as E1/E2:
    u_max, u_min, v_max, TV(u), E_midk/E_total over time.

The criterion of "practical bound":
    u_max(t) stays below ~1.6 (~7% above IC bound 1.5),
    AND TV(u) stays below ~10 (~3x IC TV, allowing some shock-front sharpening
    that the bore physically does experience),
    AND v_max stays "near IC" -- not poisoned by Gibbs cascade through coupling.

We then identify the minimum dissipation level in each family that satisfies
the criterion (or, if none do at T=6, the level that comes closest).
"""

import os
import sys
import time
import numpy as np

ROUND_DIR = os.path.dirname(os.path.abspath(__file__))

# Grid & spectral operators
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
k2 = k ** 2
k8 = k ** 8

k_abs = np.abs(k)
k_max = float(np.max(k_abs))
dealias_mask = (k_abs <= (2.0 / 3.0) * k_max).astype(float)
mid_band_mask = ((k_abs > k_max / 3.0) & (k_abs <= 2.0 / 3.0 * k_max)).astype(float)


def fft_dealias(a):
    return np.fft.fft(a) * dealias_mask


def make_rhs(nu_linear, nu_hyper):
    """Build an RHS callable with the prescribed dissipation coefficients."""
    use_hyper = (nu_hyper is not None) and (nu_hyper > 0.0)
    use_linear = (nu_linear is not None) and (nu_linear > 0.0)

    def rhs(u, v):
        uh = fft_dealias(u)
        vh = fft_dealias(v)
        u_d = np.real(np.fft.ifft(uh))
        v_d = np.real(np.fft.ifft(vh))

        u_x = np.real(np.fft.ifft(ik * uh))
        v_x = np.real(np.fft.ifft(ik * vh))
        v_xx = np.real(np.fft.ifft(-k2 * vh))
        v_xxx = np.real(np.fft.ifft(-1j * (k ** 3) * vh))

        # Nonlinear flux terms
        uux = np.real(np.fft.ifft(np.fft.fft(u_d * u_x) * dealias_mask))
        coupling_field = 3.0 * (v_d ** 2) + v_xx
        dcoupling = np.real(np.fft.ifft(ik * (np.fft.fft(coupling_field) * dealias_mask)))
        rhs_u = -3.0 * uux - dcoupling

        # u-dissipation
        if use_linear:
            u_xx = np.real(np.fft.ifft(-k2 * uh))
            rhs_u = rhs_u + nu_linear * u_xx
        if use_hyper:
            # u_t += -nu_hyper * F^-1(k^8 u_hat)  (with dealias applied)
            rhs_u = rhs_u - nu_hyper * np.real(np.fft.ifft(k8 * uh))

        # v-equation (unchanged)
        vvx = np.real(np.fft.ifft(np.fft.fft(v_d * v_x) * dealias_mask))
        uv = u_d * v_d
        duv = np.real(np.fft.ifft(ik * (np.fft.fft(uv) * dealias_mask)))
        rhs_v = -6.0 * vvx - v_xxx - duv

        return rhs_u, rhs_v

    return rhs


def rk4_step(rhs, u, v, dt):
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
    E_mid = float(np.sum(power * mid_band_mask))
    ratio = E_mid / E_total if E_total > 0 else 0.0
    return dict(mass_u=mass_u, mass_v=mass_v, energy=energy,
                u_max=u_max, u_min=u_min, v_max=v_max, sup=sup,
                TV_u=TV_u, u_mid_k_energy_ratio=ratio, finite=True)


# Fixed IC
v0 = 1.5 * (1.0 / np.cosh(x + 5.0)) ** 2
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0

T = 6.0
dt = 1.0e-4
nsteps = int(round(T / dt))
n_snap = 25
snap_steps = np.linspace(0, nsteps, n_snap, dtype=int)
snap_set = set(int(s) for s in snap_steps)


def run_case(label, nu_linear=0.0, nu_hyper=0.0):
    """Run one dissipation case and return summary diagnostics."""
    rhs = make_rhs(nu_linear, nu_hyper)
    u = u0.copy()
    v = v0.copy()
    diag_log = [{'t': 0.0, **diagnostics(u, v)}]
    snapshots_u = [u.copy()]
    snapshots_v = [v.copy()]
    snapshot_times = [0.0]
    t_start = time.time()
    blowup_t = None
    for n in range(1, nsteps + 1):
        u, v = rk4_step(rhs, u, v, dt)
        t = n * dt
        if n in snap_set:
            d = diagnostics(u, v)
            snapshots_u.append(u.copy())
            snapshots_v.append(v.copy())
            snapshot_times.append(t)
            diag_log.append({'t': t, **d})
            if (not d['finite']) or d['sup'] > 1e6:
                blowup_t = t
                break
    elapsed = time.time() - t_start

    # Summary
    u_maxs = np.array([d['u_max'] for d in diag_log])
    u_mins = np.array([d['u_min'] for d in diag_log])
    v_maxs = np.array([d['v_max'] for d in diag_log])
    TVs = np.array([d['TV_u'] for d in diag_log])
    ratios = np.array([d['u_mid_k_energy_ratio'] for d in diag_log])
    ts_arr = np.array([d['t'] for d in diag_log])
    summary = dict(
        label=label, nu_linear=nu_linear, nu_hyper=nu_hyper,
        u_max_t0=float(u_maxs[0]), u_max_max=float(np.nanmax(u_maxs)),
        u_max_final=float(u_maxs[-1]),
        u_min_min=float(np.nanmin(u_mins)), u_min_final=float(u_mins[-1]),
        TV_u_max=float(np.nanmax(TVs)), TV_u_final=float(TVs[-1]),
        v_max_final=float(v_maxs[-1]), v_max_t0=float(v_maxs[0]),
        ratio_max=float(np.nanmax(ratios)), ratio_final=float(ratios[-1]),
        elapsed_s=float(elapsed),
        blowup_t=(blowup_t if blowup_t is not None else None),
        nsnap=len(snapshot_times),
        t_arr=ts_arr.tolist(),
        u_max_traj=u_maxs.tolist(),
        u_min_traj=u_mins.tolist(),
        TV_u_traj=TVs.tolist(),
        v_max_traj=v_maxs.tolist(),
    )
    print(f"\n=== Case {label}  nu_lin={nu_linear:.3e}  nu_hyp={nu_hyper:.3e} ===",
          flush=True)
    print(f"  u_max:  t0={u_maxs[0]:.4f}  max={u_maxs.max():.4f}  final={u_maxs[-1]:.4f}",
          flush=True)
    print(f"  u_min:  min={u_mins.min():+.4f}  final={u_mins[-1]:+.4f}", flush=True)
    print(f"  TV(u):  max={TVs.max():.3f}  final={TVs[-1]:.3f}", flush=True)
    print(f"  v_max:  final={v_maxs[-1]:.4f}  (IC {v_maxs[0]:.4f})", flush=True)
    print(f"  mid-k:  max={ratios.max():.3e}  final={ratios[-1]:.3e}", flush=True)
    print(f"  elapsed={elapsed:.1f}s  blowup_t={blowup_t}", flush=True)

    # Persist final snapshots for this case
    np.savez(os.path.join(ROUND_DIR, f"snapshots_{label}.npz"),
             x=x, times=np.array(snapshot_times),
             u=np.array(snapshots_u), v=np.array(snapshots_v))
    return summary


# Cases to sweep
# Linear viscosity progressively tames u up to nu=1e-1 (final u_max~=1.54).
# For hyperviscosity, the stability constraint is nu_h * k_max^8 * dt < O(1),
# k_max^8 ~ 2.6e11 with k_max~26.8, dt=1e-4 -> nu_h < ~4e-8. So we sweep up to
# the stability ceiling and look for the practical-bound passing case.
cases = [
    ("lin_1e-3", 1.0e-3, 0.0),
    ("lin_1e-2", 1.0e-2, 0.0),
    ("lin_2e-2", 2.0e-2, 0.0),
    ("lin_5e-2", 5.0e-2, 0.0),
    ("lin_1e-1", 1.0e-1, 0.0),
    ("hyp_1e-14", 0.0, 1.0e-14),
    ("hyp_1e-12", 0.0, 1.0e-12),
    ("hyp_1e-10", 0.0, 1.0e-10),
    ("hyp_1e-9",  0.0, 1.0e-9),
]

print(f"[grid]  Nx={Nx}  L={L}  dx={dx:.4e}", flush=True)
print(f"[time]  T={T}  dt={dt:.4e}  nsteps={nsteps}", flush=True)
print(f"[IC]    v0=1.5 sech^2(x+5)  u0=1.5(1-tanh(x/0.5))/2", flush=True)
print(f"[sweep] {len(cases)} cases (linear + k^8 hyperviscosity)", flush=True)

summaries = []
for (label, nu_l, nu_h) in cases:
    summaries.append(run_case(label, nu_linear=nu_l, nu_hyper=nu_h))

# Save full sweep summary
import json
sweep_path = os.path.join(ROUND_DIR, "sweep_summary.json")
with open(sweep_path, "w") as f:
    json.dump(summaries, f, indent=2)
print(f"\n[saved sweep] {sweep_path}", flush=True)

# Practical-bound analysis
print("\n=== Practical-bound analysis ===", flush=True)
print(f"  Criterion: u_max_max < 1.65 AND TV_u_max < 10 AND v_max_final > 1.2", flush=True)
print(f"  (IC: u_max=1.5  TV(u)=3.0  v_max=1.50)", flush=True)
print(f"  {'label':<10} {'u_max_max':>10} {'TV_u_max':>10} {'v_max_fin':>10} "
      f"{'u_min_min':>10}  PASS?", flush=True)
for s in summaries:
    passed = (s['u_max_max'] < 1.65 and s['TV_u_max'] < 10.0
              and s['v_max_final'] > 1.2)
    print(f"  {s['label']:<10} {s['u_max_max']:10.4f} {s['TV_u_max']:10.3f} "
          f"{s['v_max_final']:10.4f} {s['u_min_min']:+10.4f}  "
          f"{'YES' if passed else 'no'}", flush=True)

# A more relaxed criterion (we expect at least to PARTIALLY tame the artifact)
print(f"\n  Relaxed criterion: u_max_max < 2.0 AND TV_u_max < 30 AND v_max_final > 0.9",
      flush=True)
for s in summaries:
    passed = (s['u_max_max'] < 2.0 and s['TV_u_max'] < 30.0
              and s['v_max_final'] > 0.9)
    print(f"  {s['label']:<10} {s['u_max_max']:10.4f} {s['TV_u_max']:10.3f} "
          f"{s['v_max_final']:10.4f}  {'YES' if passed else 'no'}", flush=True)

print("\n[done] E3 sweep complete.", flush=True)
