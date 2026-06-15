"""
BKdV-S3 / E3 — Phase-boundary scan: noise injection σ on a localized sech^2 seed.

Background
----------
* E1 found localized ICs (Gauss, sech^2, P2) -> coherent; broadband ICs
  (noise, sinusoid) -> blow-up at A=0.8.
* E2 swept A on sech^2 and found that structural coherence (npeaks=1, fracL_v
  ~ 0.99) is universal. The amplitude axis alone does not produce a phase
  transition inside the localized family.

E3 design (one new axis: noise level σ)
---------------------------------------
Build IC: v0 = A * sech^2((x+2)/1.5) + σ * η * env, where η is white noise,
env is a wide gaussian envelope (so periodic and non-zero-mean removed),
and (η,env) are normalized so the maximum of σ*env*η equals σ. This places
σ on the same vmax scale as A. Fix A = 0.6 (moderate, comfortably inside
the coherent basin per E2).

Sweep σ ∈ {0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.60, 0.80}. Run to T=12.

We watch:
- vmax_late       : amplitude survival
- npeaks_v        : pulse count (small => coherent)
- fracL_v_late    : energy at |k|<=2
- frac_high_v_max : maximum over time of energy at |k|>=4 (radiation marker)
- lock_late       : u-v lock
- blew_up         : numerical blow-up indicates incoherent/cascade regime

Phase boundary σ_c is the smallest σ at which any of:
  (a) blew_up
  (b) npeaks_v_late > 5
  (c) fracL_v_late < 0.5
becomes true.

Same pre-validated solver stack (Fourier pseudospectral / 2/3 dealias / RK4 /
integrating-factor on v_xxx / spectral hyperviscosity). dt=2.5e-4 baseline,
1e-4 fallback if blow-up.
"""

import numpy as np
import os, json, time

L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=L / Nx)
kmax = np.max(np.abs(k))
ik = 1j * k
ik3 = 1j * (k ** 3)
kcut = (2.0 / 3.0) * kmax
dealias = (np.abs(k) < kcut).astype(np.float64)

HYPER_P = 8
HYPER_COEF = 1.0e-22
hyper = -HYPER_COEF * (k ** (2 * HYPER_P))

def fft(a): return np.fft.fft(a)
def ifft(A): return np.real(np.fft.ifft(A))
def nl_hat(a, b): return dealias * fft(a * b)

def rhs_full(u_hat, w_hat, t):
    phase = np.exp(ik3 * t)
    v_hat = phase * w_hat
    u = ifft(u_hat); v = ifft(v_hat)
    u2_h = nl_hat(u, u); v2_h = nl_hat(v, v); uv_h = nl_hat(u, v)
    v_xx_h = (ik ** 2) * v_hat
    u_hat_t = -ik * (1.5 * u2_h + 3.0 * v2_h + v_xx_h) + hyper * u_hat
    v_hat_t_nl = -ik * (3.0 * v2_h + uv_h)
    w_hat_t = np.exp(-ik3 * t) * v_hat_t_nl
    return u_hat_t, w_hat_t

def rk4_step(u_hat, w_hat, t, dt):
    k1a, k1b = rhs_full(u_hat, w_hat, t)
    k2a, k2b = rhs_full(u_hat + 0.5 * dt * k1a, w_hat + 0.5 * dt * k1b, t + 0.5 * dt)
    k3a, k3b = rhs_full(u_hat + 0.5 * dt * k2a, w_hat + 0.5 * dt * k2b, t + 0.5 * dt)
    k4a, k4b = rhs_full(u_hat + dt * k3a,       w_hat + dt * k3b,       t + dt)
    return (u_hat + dt / 6.0 * (k1a + 2.0 * k2a + 2.0 * k3a + k4a),
            w_hat + dt / 6.0 * (k1b + 2.0 * k2b + 2.0 * k3b + k4b))

def lock_corr(u, v):
    a = u - np.mean(u); b = 0.5 * v * v - np.mean(0.5 * v * v)
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    return float('nan') if (na < 1e-12 or nb < 1e-12) else float(np.dot(a, b) / (na * nb))

def spec_bands(field):
    F = np.fft.fft(field) / Nx
    P = np.abs(F) ** 2
    tot = float(np.sum(P))
    low = float(np.sum(P[np.abs(k) <= 2.0]))
    high = float(np.sum(P[np.abs(k) >= 4.0]))
    return low / max(tot, 1e-30), high / max(tot, 1e-30)

def count_peaks(field, height_frac=0.5, min_floor=0.02):
    npts = len(field)
    fmax = float(np.max(field))
    if fmax <= 0: return 0
    height = max(min_floor, height_frac * fmax)
    peaks = 0
    for i in range(npts):
        if field[i] < height: continue
        l = field[(i - 1) % npts]; r = field[(i + 1) % npts]
        if field[i] >= l and field[i] >= r and (field[i] > l or field[i] > r):
            peaks += 1
    return peaks

def integrate(u0, v0, T, dt, tag):
    u_hat = fft(u0); v_hat = fft(v0)
    w_hat = v_hat.copy()
    nsteps = int(round(T / dt))
    n_diag = 41
    diag_stride = max(1, nsteps // (n_diag - 1))
    times = [0.0]
    fL, fH = spec_bands(v0)
    vmax_t = [float(np.max(np.abs(v0)))]
    lock_t = [lock_corr(u0, v0)]
    fracL_v = [fL]; fracH_v = [fH]
    npk_t = [count_peaks(v0)]
    u_final = u0.copy(); v_final = v0.copy()
    t = 0.0; blew_up = False
    for step in range(1, nsteps + 1):
        u_hat, w_hat = rk4_step(u_hat, w_hat, t, dt)
        t += dt
        if not (np.all(np.isfinite(u_hat)) and np.all(np.isfinite(w_hat))):
            print(f"[{tag}] NaN at step {step}, t={t:.4f}")
            blew_up = True; break
        if step % diag_stride == 0:
            v_hat_now = np.exp(ik3 * t) * w_hat
            u_now = ifft(u_hat); v_now = ifft(v_hat_now)
            times.append(t)
            vmax_t.append(float(np.max(np.abs(v_now))))
            lock_t.append(lock_corr(u_now, v_now))
            fL, fH = spec_bands(v_now)
            fracL_v.append(fL); fracH_v.append(fH)
            npk_t.append(count_peaks(v_now))
            u_final = u_now; v_final = v_now
    return dict(
        tag=tag, blew_up=blew_up,
        times=np.array(times), vmax=np.array(vmax_t),
        lock=np.array(lock_t),
        fracL_v=np.array(fracL_v), fracH_v=np.array(fracH_v),
        npeaks_v=np.array(npk_t),
        u_final=u_final, v_final=v_final,
    )

# ----------------------------------------------------------
# Noise-level sweep
# ----------------------------------------------------------
A_BASE = 0.6
sigmas = [0.00, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.60, 0.80]
T_FINAL = 12.0
DT_DEFAULT = 2.5e-4
DT_FALLBACK = 1.0e-4

# Common noise envelope: keep noise (mostly) inside the support of the seed
# so we are testing radiation that overlaps the soliton, not far-away noise.
env = np.exp(-((x + 2.0) / 4.0) ** 2)

rng = np.random.default_rng(2025)

os.makedirs("pred_results", exist_ok=True)
os.makedirs("evidence", exist_ok=True)
summary = {"round": 3, "T": T_FINAL, "A_base": A_BASE, "ICs": {}}

phase_table = []

for sigma in sigmas:
    eta = rng.standard_normal(Nx)
    # Normalize so max(|sigma * env * eta|) == sigma (puts σ on vmax-scale)
    raw_noise = env * eta
    raw_noise = raw_noise - np.mean(raw_noise)  # remove DC
    nmax = np.max(np.abs(raw_noise))
    if nmax < 1e-12:
        noise_field = np.zeros_like(x)
    else:
        noise_field = sigma * raw_noise / nmax
    v0 = A_BASE / np.cosh((x + 2.0) / 1.5) ** 2 + noise_field
    u0 = np.zeros_like(x)
    tag = f"sigma{sigma:.2f}"
    fL0, fH0 = spec_bands(v0)
    dt_use = DT_DEFAULT
    t0 = time.time()
    print(f"\n=== {tag} vmax0={np.max(np.abs(v0)):.3f}, "
          f"fL0={fL0:.3f}, fH0={fH0:.3f} ===")
    res = integrate(u0, v0, T_FINAL, dt_use, tag)
    if res["blew_up"] and dt_use == DT_DEFAULT:
        print(f"  retry with dt={DT_FALLBACK}")
        res = integrate(u0, v0, T_FINAL, DT_FALLBACK, tag)
    print(f"  done in {time.time()-t0:.1f}s  blew_up={res['blew_up']}")
    n = len(res["times"])
    idx_late = slice(int(0.8 * n), n)
    vmax_late = float(np.mean(res["vmax"][idx_late]))
    npk_late = int(np.round(np.mean(res["npeaks_v"][idx_late])))
    fracL_late = float(np.mean(res["fracL_v"][idx_late]))
    fracH_late = float(np.mean(res["fracH_v"][idx_late]))
    fracH_max = float(np.max(res["fracH_v"]))
    lock_late = float(np.nanmean(res["lock"][idx_late]))
    coherent = (not res["blew_up"]) and (npk_late <= 5) and (fracL_late >= 0.5)
    np.savez(f"pred_results/E3_{tag}.npz",
             times=res["times"], vmax=res["vmax"],
             lock=res["lock"], fracL_v=res["fracL_v"], fracH_v=res["fracH_v"],
             npeaks_v=res["npeaks_v"], sigma=sigma, x=x,
             u_final=res["u_final"], v_final=res["v_final"])
    summary["ICs"][tag] = dict(
        sigma=sigma, vmax_late=vmax_late, npeaks_v_late=npk_late,
        fracL_v_late=fracL_late, fracH_v_late=fracH_late,
        fracH_v_max=fracH_max, lock_late=lock_late,
        coherent=bool(coherent), blew_up=bool(res["blew_up"]),
    )
    phase_table.append((sigma, coherent, res["blew_up"], npk_late, fracL_late))
    print(f"  late: vmax={vmax_late:.3f}, npk={npk_late}, "
          f"fracL_v={fracL_late:.3f}, fracH_v={fracH_late:.3f}, "
          f"fracH_max={fracH_max:.3f}, lock={lock_late:.3f}, COHERENT={coherent}")

# Phase boundary σ_c: smallest sigma where coherent==False
sigma_c = None
for sigma, coh, blow, npk, fL in phase_table:
    if not coh:
        sigma_c = sigma; break
summary["sigma_c"] = sigma_c
summary["phase_table"] = phase_table

with open("evidence/E3_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\n\nPhase table (sigma, coherent, blew_up, npk, fL):")
for row in phase_table:
    print(f"  sigma={row[0]:.2f}  coherent={row[1]}  blew_up={row[2]}  "
          f"npk_late={row[3]}  fracL_v_late={row[4]:.3f}")
print(f"\nestimated sigma_c (boundary into incoherent regime) = {sigma_c}")
print("\nSaved evidence/E3_summary.json")
