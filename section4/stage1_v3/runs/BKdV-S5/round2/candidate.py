"""
BKdV-S5  Round 2 (E2): baseline + small STRUCTURED perturbation on v.

Same solver stack as round1 (MUSCL-Godunov on u self-flux, IMEX-CN on v_xxx,
spectral coupling with 2/3 dealiasing), same IC family, same T=15.

Compared to E1 we change exactly ONE thing: add  delta_v(x, 0) = eps * sin(k_0 x)
with eps = 0.05 and k_0 = 2*pi*5/L  (mode 5).  u(x,0) is left as in E1: u = v_0^2/2,
where v_0 is the unperturbed sech^2.  We do NOT modify u to keep m=0; the small v
perturbation is treated as a structured deviation injected into the v field only.

Diagnostic of interest: spectral content of (v - v_E1) over time, and L^2 norm of
the deviation. Compare to E1.
"""

import os
import sys
import time
import numpy as np

ROUND_DIR = os.path.dirname(os.path.abspath(__file__))
E1_NPZ = os.path.join(os.path.dirname(ROUND_DIR), "round1", "snapshots.npz")

# ------------------------------------------------------------
# Grid & spectral operators (identical to round1)
# ------------------------------------------------------------
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


# ---------- MUSCL Burgers ----------
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


# ---------- explicit RHS ----------
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


# ---------- diagnostics ----------
def diagnostics(u, v):
    mass_u = float(np.sum(u) * dx)
    mass_v = float(np.sum(v) * dx)
    energy = float(0.5 * np.sum(u * u + v * v) * dx)
    m = u - 0.5 * v ** 2
    m_norm = float(np.sqrt(np.sum(m * m) * dx))
    v_peak = float(np.max(v))
    v_peak_x = float(x[int(np.argmax(v))])
    sup = float(max(np.max(np.abs(u)), np.max(np.abs(v))))
    finite = bool(np.all(np.isfinite(u)) and np.all(np.isfinite(v)))
    return dict(mass_u=mass_u, mass_v=mass_v, energy=energy,
                m_norm=m_norm, v_peak=v_peak, v_peak_x=v_peak_x,
                sup=sup, finite=finite)


# ============================================================
# IC: same baseline + structured sin perturbation on v
# ============================================================
amp = 1.0
v_base = amp * (1.0 / np.cosh(x + 5.0)) ** 2
u_base = 0.5 * v_base ** 2

# Structured perturbation
eps = 0.05
mode = 5
k0 = 2.0 * np.pi * mode / L  # i.e. wavenumber index 5
delta_v0 = eps * np.sin(k0 * x)
v = v_base + delta_v0
u = u_base.copy()  # keep u as in E1; the perturbation is on v only

print(f"[grid]  Nx={Nx}  L={L}  dx={dx:.4e}", flush=True)
print(f"[time]  T=15  dt=1e-4", flush=True)
print(f"[IC]    amp={amp}  delta_v = {eps}*sin({mode}*2pi*x/L), mode={mode}", flush=True)
print(f"[IC]    ||delta_v0||_L2 = {np.sqrt(np.sum(delta_v0**2)*dx):.4e}", flush=True)

d0 = diagnostics(u, v)
print(f"[init]  mass_v={d0['mass_v']:+.6e} energy={d0['energy']:.6e} "
      f"m_norm={d0['m_norm']:.4e} v_peak={d0['v_peak']:.4f}", flush=True)

# ---------- Load E1 baseline snapshots ----------
e1 = np.load(E1_NPZ)
e1_x = e1["x"]
e1_times = e1["times"]
e1_u = e1["u"]
e1_v = e1["v"]
assert np.allclose(e1_x, x), "E1 grid mismatch"
print(f"[E1 ref] loaded {len(e1_times)} snapshots from {E1_NPZ}", flush=True)

# ---------- Time integration ----------
T = 15.0
dt = 1.0e-4
nsteps = int(round(T / dt))
cn_denom, cn_numer = make_cn_factors(dt)

snap_steps = np.linspace(0, nsteps, len(e1_times), dtype=int)
snap_set = set(int(s) for s in snap_steps)

# Index of snapshot for syncing with E1
snap_idx_map = {int(s): i for i, s in enumerate(snap_steps)}

snapshots_u = [u.copy()]
snapshots_v = [v.copy()]
snapshot_times = [0.0]
diag_log = [{'t': 0.0, **d0}]
# deviation diagnostics: norm of v - v_E1
dev_log = [{
    't': 0.0,
    'delta_v_L2': float(np.sqrt(np.sum((v - e1_v[0]) ** 2) * dx)),
    'delta_u_L2': float(np.sqrt(np.sum((u - e1_u[0]) ** 2) * dx)),
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
        delta_v = v - v_e1
        delta_u = u - u_e1
        snapshots_u.append(u.copy())
        snapshots_v.append(v.copy())
        snapshot_times.append(t)
        d = diagnostics(u, v)
        diag_log.append({'t': t, **d})
        dev_log.append({
            't': t,
            'delta_v_L2': float(np.sqrt(np.sum(delta_v ** 2) * dx)),
            'delta_u_L2': float(np.sqrt(np.sum(delta_u ** 2) * dx)),
        })
    if n % report_every == 0 or n == nsteps:
        d = diagnostics(u, v)
        # current deviation norms
        # pick nearest E1 snapshot index for printing
        nearest_i = int(np.argmin(np.abs(e1_times - t)))
        dvn = np.sqrt(np.sum((v - e1_v[nearest_i]) ** 2) * dx)
        dun = np.sqrt(np.sum((u - e1_u[nearest_i]) ** 2) * dx)
        print(f"[t={t:7.4f}] energy={d['energy']:.3e} m_norm={d['m_norm']:.3e} "
              f"v_peak={d['v_peak']:.3f} sup={d['sup']:.3e} "
              f"||dv||={dvn:.4e} ||du||={dun:.4e}", flush=True)
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

# ---------- Summary: deviation growth ----------
ts = np.array([d['t'] for d in dev_log])
dv = np.array([d['delta_v_L2'] for d in dev_log])
du = np.array([d['delta_u_L2'] for d in dev_log])

print(f"[saved] {out_npz}", flush=True)
print(f"\n[deviation series]", flush=True)
for tp, dvp, dup in zip(ts, dv, du):
    print(f"  t={tp:6.3f}  ||delta_v||_L2={dvp:.4e}  ||delta_u||_L2={dup:.4e}", flush=True)

# Fit log of dev_v vs t for an effective growth rate (excluding t=0 if dv0=0)
mask = dv > 0
if np.sum(mask) >= 3:
    coeff = np.polyfit(ts[mask], np.log(dv[mask]), 1)
    growth_rate = coeff[0]
    print(f"[summary] effective exponential growth rate of ||dv||_L2: "
          f"{growth_rate:+.4f} (1/time-unit)", flush=True)

print(f"[summary] init ||dv||={dv[0]:.3e} -> final ||dv||={dv[-1]:.3e}", flush=True)
print(f"[summary] init ||du||={du[0]:.3e} -> final ||du||={du[-1]:.3e}", flush=True)
print(f"[summary] elapsed={elapsed:.1f}s", flush=True)

# Save deviation arrays too
np.savez(os.path.join(ROUND_DIR, "deviations.npz"),
         t=ts, delta_v_L2=dv, delta_u_L2=du,
         eps=eps, mode=mode, k0=k0)

print("[done] E2 structured-perturbation complete.", flush=True)
