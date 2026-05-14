"""
BKdV-S5  Round 3 (E3): baseline + small BROADBAND-NOISE perturbation on v.

One-component escalation over E2: replace the structured single-mode sin
perturbation with broadband random noise at the SAME L^2 norm.  Everything else
(solver, IC, T, dt, snapshot cadence) is identical.

Purpose: test whether the deviation response from E2 is k-selective (specific to
mode 5) or general (any small-norm perturbation grows similarly).  This is a
two-experiment comparison: E2 (structured mode-5) vs E3 (broadband). If
||dv||_L2(t) trajectories are similar, the response is NOT k-selective; if
markedly different, it IS.

The noise is drawn from a fixed seed (=42) so the run is reproducible.
The noise is then projected to have ZERO mean (so mass_v is unchanged) and
rescaled to match the L^2 norm of E2's sin perturbation (||eps*sin(k0 x)||_L2 =
eps * sqrt(L/2) = 0.05 * sqrt(15) = 0.1936...).
"""

import os
import sys
import time
import numpy as np

ROUND_DIR = os.path.dirname(os.path.abspath(__file__))
E1_NPZ = os.path.join(os.path.dirname(ROUND_DIR), "round1", "snapshots.npz")
E2_NPZ = os.path.join(os.path.dirname(ROUND_DIR), "round2", "snapshots.npz")

# ============================================================
# Grid & spectral operators (identical to round1/round2)
# ============================================================
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
k2 = k ** 2
k3 = k ** 3

k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)


def fft_dealias(a):
    return np.fft.fft(a) * dealias


def muscl_burgers_div(w):
    dw_p = np.roll(w, -1) - w
    dw_m = w - np.roll(w, 1)
    r = np.where(np.abs(dw_p) > 1e-14, dw_m / dw_p, 0.0)
    phi = (r + np.abs(r)) / (1.0 + np.abs(r) + 1e-14)
    slope = phi * dw_p
    wL = w + 0.5 * slope
    wR = np.roll(w - 0.5 * slope, -1)
    fL = 1.5 * wL ** 2
    fR = 1.5 * wR ** 2
    s_shock = 1.5 * (wL + wR)
    f_shock = np.where(s_shock >= 0.0, fL, fR)
    f_rare = np.where(wL >= 0.0, fL,
                      np.where(wR <= 0.0, fR, 0.0))
    flux_right = np.where(wL >= wR, f_shock, f_rare)
    flux_left = np.roll(flux_right, 1)
    return -(flux_right - flux_left) / dx


def explicit_rhs(u, v):
    uh_d = fft_dealias(u)
    vh_d = fft_dealias(v)
    u_d = np.real(np.fft.ifft(uh_d))
    v_d = np.real(np.fft.ifft(vh_d))

    v_x_d = np.real(np.fft.ifft(ik * vh_d))
    v_xx_d = np.real(np.fft.ifft(-k2 * vh_d))

    self_flux = muscl_burgers_div(u)
    prod = 3.0 * v_d ** 2 + v_xx_d
    dprod = np.real(np.fft.ifft(ik * (np.fft.fft(prod) * dealias)))
    rhs_u = self_flux - dprod

    uv = u_d * v_d
    d_uv = np.real(np.fft.ifft(ik * (np.fft.fft(uv) * dealias)))
    rhs_v_expl = -6.0 * v_d * v_x_d - d_uv

    return rhs_u, rhs_v_expl


def make_cn_factors(dt):
    Lhat = -1j * k ** 3
    return 1.0 - 0.5 * dt * Lhat, 1.0 + 0.5 * dt * Lhat


def step_imex(u, v, dt, cn_denom, cn_numer):
    rhs_u, rhs_v_expl = explicit_rhs(u, v)
    u_new = u + dt * rhs_u

    vh = np.fft.fft(v)
    nlh = np.fft.fft(rhs_v_expl) * dealias
    vh_new = (cn_numer * vh + dt * nlh) / cn_denom
    vh_new *= dealias
    v_new = np.real(np.fft.ifft(vh_new))
    return u_new, v_new


def diagnostics(u, v):
    mass_v = float(np.sum(v) * dx)
    energy = float(0.5 * np.sum(u * u + v * v) * dx)
    m = u - 0.5 * v ** 2
    m_norm = float(np.sqrt(np.sum(m * m) * dx))
    v_peak = float(np.max(v))
    sup = float(max(np.max(np.abs(u)), np.max(np.abs(v))))
    finite = bool(np.all(np.isfinite(u)) and np.all(np.isfinite(v)))
    return dict(mass_v=mass_v, energy=energy, m_norm=m_norm,
                v_peak=v_peak, sup=sup, finite=finite)


# ============================================================
# IC: baseline + broadband random perturbation, matched in L^2 to E2
# ============================================================
amp = 1.0
v_base = amp * (1.0 / np.cosh(x + 5.0)) ** 2
u_base = 0.5 * v_base ** 2

# Reference E2 perturbation norm:
eps_e2 = 0.05
mode_e2 = 5
target_L2 = eps_e2 * np.sqrt(L / 2.0)  # ||sin(k0 x) * eps||_L2 over [-L/2, L/2]

rng = np.random.default_rng(seed=42)
white = rng.standard_normal(Nx)
# Zero-mean -> conserves mass_v
white -= np.mean(white)
# Rescale to target L^2 norm
norm_white = np.sqrt(np.sum(white ** 2) * dx)
delta_v0 = (target_L2 / norm_white) * white

v = v_base + delta_v0
u = u_base.copy()

print(f"[grid]  Nx={Nx}  L={L}  dx={dx:.4e}", flush=True)
print(f"[time]  T=15  dt=1e-4", flush=True)
print(f"[IC]    amp={amp}  delta_v = white noise (seed=42, zero-mean, ||.||_L2 matched to E2)", flush=True)
print(f"[IC]    target_L2 = {target_L2:.4e}  actual_L2 = "
      f"{np.sqrt(np.sum(delta_v0**2)*dx):.4e}", flush=True)
print(f"[IC]    delta_v0 sup = {np.max(np.abs(delta_v0)):.4e}", flush=True)

d0 = diagnostics(u, v)
print(f"[init]  mass_v={d0['mass_v']:+.6e} energy={d0['energy']:.6e} "
      f"m_norm={d0['m_norm']:.4e} v_peak={d0['v_peak']:.4f}", flush=True)

# Spectral content of delta_v0
d0_hat = np.fft.fft(delta_v0)
d0_power = np.abs(d0_hat) ** 2
# group by integer k-index
print(f"[IC]    delta_v0 spectral content (top 5 modes): ", flush=True)
top_modes = np.argsort(d0_power[:Nx // 2])[::-1][:5]
for m in top_modes:
    print(f"          k-index={m}  |hat|^2={d0_power[m]:.3e}", flush=True)

# ---------- Load E1 baseline ----------
e1 = np.load(E1_NPZ)
e1_x = e1["x"]
e1_times = e1["times"]
e1_u = e1["u"]
e1_v = e1["v"]
assert np.allclose(e1_x, x), "E1 grid mismatch"
print(f"[E1 ref] loaded {len(e1_times)} snapshots from {E1_NPZ}", flush=True)

# Load E2 too for direct comparison
e2 = np.load(E2_NPZ)
e2_v = e2["v"]
e2_u = e2["u"]
e2_times = e2["times"]

# ---------- Time integration ----------
T = 15.0
dt = 1.0e-4
nsteps = int(round(T / dt))
cn_denom, cn_numer = make_cn_factors(dt)

snap_steps = np.linspace(0, nsteps, len(e1_times), dtype=int)
snap_idx_map = {int(s): i for i, s in enumerate(snap_steps)}
snap_set = set(snap_idx_map.keys())

snapshots_u = [u.copy()]
snapshots_v = [v.copy()]
snapshot_times = [0.0]
diag_log = [{'t': 0.0, **d0}]

dev_log = [{
    't': 0.0,
    'delta_v_L2_vs_E1': float(np.sqrt(np.sum((v - e1_v[0]) ** 2) * dx)),
    'delta_u_L2_vs_E1': float(np.sqrt(np.sum((u - e1_u[0]) ** 2) * dx)),
    'delta_v_L2_vs_E2': float(np.sqrt(np.sum((v - e2_v[0]) ** 2) * dx)),
}]

t0 = time.time()
report_every = max(1, nsteps // 30)
for n in range(1, nsteps + 1):
    u, v = step_imex(u, v, dt, cn_denom, cn_numer)
    t = n * dt
    if n in snap_set:
        idx = snap_idx_map[n]
        v_e1 = e1_v[idx]
        u_e1 = e1_u[idx]
        v_e2 = e2_v[idx] if idx < len(e2_v) else None
        delta_v = v - v_e1
        delta_u = u - u_e1
        snapshots_u.append(u.copy())
        snapshots_v.append(v.copy())
        snapshot_times.append(t)
        d = diagnostics(u, v)
        diag_log.append({'t': t, **d})
        dvE1 = float(np.sqrt(np.sum(delta_v ** 2) * dx))
        duE1 = float(np.sqrt(np.sum(delta_u ** 2) * dx))
        dvE2 = float(np.sqrt(np.sum((v - v_e2) ** 2) * dx)) if v_e2 is not None else np.nan
        dev_log.append({
            't': t,
            'delta_v_L2_vs_E1': dvE1,
            'delta_u_L2_vs_E1': duE1,
            'delta_v_L2_vs_E2': dvE2,
        })
    if n % report_every == 0 or n == nsteps:
        d = diagnostics(u, v)
        nearest_i = int(np.argmin(np.abs(e1_times - t)))
        dvn = np.sqrt(np.sum((v - e1_v[nearest_i]) ** 2) * dx)
        print(f"[t={t:7.4f}] energy={d['energy']:.3e} m_norm={d['m_norm']:.3e} "
              f"v_peak={d['v_peak']:.3f} sup={d['sup']:.3e} "
              f"||dv vs E1||={dvn:.4e}", flush=True)
        if not d['finite'] or d['sup'] > 1e4:
            print(f"[BLOWUP] at t={t:.4f}", flush=True)
            break

elapsed = time.time() - t0

# ---------- Save ----------
out_npz = os.path.join(ROUND_DIR, "snapshots.npz")
np.savez(out_npz,
         x=x,
         times=np.array(snapshot_times),
         u=np.array(snapshots_u),
         v=np.array(snapshots_v))

# ---------- Summary ----------
ts = np.array([d['t'] for d in dev_log])
dv = np.array([d['delta_v_L2_vs_E1'] for d in dev_log])
du = np.array([d['delta_u_L2_vs_E1'] for d in dev_log])
dv2 = np.array([d['delta_v_L2_vs_E2'] for d in dev_log])

print(f"[saved] {out_npz}", flush=True)
print(f"\n[deviation series, E3 vs E1]", flush=True)
for tp, dvp, dup, dv2p in zip(ts, dv, du, dv2):
    print(f"  t={tp:6.3f}  ||dv vs E1||={dvp:.4e}  ||du vs E1||={dup:.4e}  "
          f"||dv vs E2||={dv2p:.4e}", flush=True)

mask = dv > 0
if np.sum(mask) >= 3:
    coeff = np.polyfit(ts[mask], np.log(dv[mask]), 1)
    growth_rate = coeff[0]
    print(f"[summary] effective exponential growth rate of ||dv vs E1||: "
          f"{growth_rate:+.4f} (1/time-unit)", flush=True)

# Load E2 deviations.npz for direct comparison
e2_dev_path = os.path.join(os.path.dirname(ROUND_DIR), "round2", "deviations.npz")
if os.path.exists(e2_dev_path):
    e2_dev = np.load(e2_dev_path)
    print(f"\n[E2 vs E3 deviation comparison (vs same baseline E1)]", flush=True)
    print(f"  Time |  E2 ||dv||  |  E3 ||dv||  |  ratio E3/E2", flush=True)
    for i, tp in enumerate(ts):
        ie2 = np.argmin(np.abs(e2_dev["t"] - tp))
        e2dv = float(e2_dev["delta_v_L2"][ie2])
        ratio = dv[i] / e2dv if e2dv > 0 else np.nan
        print(f"  t={tp:5.2f}  {e2dv:.4e}    {dv[i]:.4e}    {ratio:.3f}", flush=True)

print(f"\n[summary] init ||dv vs E1||={dv[0]:.3e} -> final ||dv vs E1||={dv[-1]:.3e}", flush=True)
print(f"[summary] elapsed={elapsed:.1f}s", flush=True)

np.savez(os.path.join(ROUND_DIR, "deviations.npz"),
         t=ts, delta_v_L2_vs_E1=dv, delta_u_L2_vs_E1=du,
         delta_v_L2_vs_E2=dv2,
         target_L2=target_L2)

print("[done] E3 broadband-perturbation complete.", flush=True)
