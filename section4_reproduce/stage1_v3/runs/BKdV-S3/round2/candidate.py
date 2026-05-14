"""
BKdV-S3 / E2 — Amplitude scan on the coherent IC family.

Background from E1
------------------
Smooth localized ICs (Gaussian, sech^2, two-pulse) stayed coherent: one or two
peaks, almost all energy at |k|<=2. Broadband ICs (noise, sinusoid) blew up.

Among the localized family, sech^2 is the cleanest single-pulse seed (it is
the canonical KdV soliton shape). E1's A=0.8 sech^2 already drops to vmax≈0.42
late-time — close to the programme threshold. We now sweep amplitude A to
locate the lower threshold below which a coherent localized state fails to
emerge from a sech^2 seed.

E2 design (one major escalation over E1: amplitude axis)
--------------------------------------------------------
* Same solver stack as E1 (no method changes).
* Single IC family: sech^2 on v centered at x=-2, width 1.5, flat u.
* Sweep A in {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2}.
* Same diagnostics as E1; same coherence heuristic (npeaks_v <= 3, vmax>=0.5,
  frac_low_v >= 0.5) plus a *retention* metric:
    retention_v = vmax_late / vmax_initial      (how much amplitude survived)
* Run to T=12 with dt=2.5e-4. If a large A is unstable, fall back to dt=1e-4
  for that run (still pre-validated).
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

def spectrum_partition(field, k_split=2.0):
    F = np.fft.fft(field) / Nx
    P = np.abs(F) ** 2
    mask_low = np.abs(k) <= k_split
    tot = float(np.sum(P))
    low = float(np.sum(P[mask_low]))
    return low / max(tot, 1e-30)

def count_peaks(field, height_frac=0.5, min_height_floor=0.02):
    f = field.copy()
    npts = len(f)
    fmax = float(np.max(f))
    if fmax <= 0: return 0
    height = max(min_height_floor, height_frac * fmax)
    peaks = 0
    for i in range(npts):
        if f[i] < height: continue
        l = f[(i - 1) % npts]; r = f[(i + 1) % npts]
        if f[i] >= l and f[i] >= r and (f[i] > l or f[i] > r):
            peaks += 1
    return peaks

def integrate(u0, v0, T, dt, tag):
    u_hat = fft(u0); v_hat = fft(v0)
    w_hat = v_hat.copy()
    nsteps = int(round(T / dt))
    n_diag = 41
    diag_stride = max(1, nsteps // (n_diag - 1))
    times = [0.0]
    vmax_t = [float(np.max(np.abs(v0)))]
    lock_t = [lock_corr(u0, v0)]
    fracL_v = [spectrum_partition(v0)]
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
            fracL_v.append(spectrum_partition(v_now))
            npk_t.append(count_peaks(v_now))
            u_final = u_now; v_final = v_now
    return dict(
        tag=tag, blew_up=blew_up,
        times=np.array(times), vmax=np.array(vmax_t),
        lock=np.array(lock_t), fracL_v=np.array(fracL_v),
        npeaks_v=np.array(npk_t),
        u_final=u_final, v_final=v_final,
    )

# -----------------------------------------------------------------------------
# Amplitude sweep on sech^2 IC
# -----------------------------------------------------------------------------
amps = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.80, 1.00, 1.20]
T_FINAL = 12.0
DT_DEFAULT = 2.5e-4
DT_FALLBACK = 1.0e-4

os.makedirs("pred_results", exist_ok=True)
os.makedirs("evidence", exist_ok=True)
summary = {"round": 2, "T": T_FINAL, "ICs": {}}

for A in amps:
    v0 = A / np.cosh((x + 2.0) / 1.5) ** 2
    u0 = np.zeros_like(x)
    tag = f"sech2_A{A:.2f}"
    t0 = time.time()
    dt_use = DT_DEFAULT if A < 1.0 else DT_FALLBACK
    print(f"\n=== {tag} (vmax0={A:.2f}, L2_v0={np.sqrt(np.sum(v0**2)*dx):.3f}, dt={dt_use}) ===")
    res = integrate(u0, v0, T_FINAL, dt_use, tag)
    if res["blew_up"] and dt_use == DT_DEFAULT:
        print(f"  retry with dt={DT_FALLBACK}")
        res = integrate(u0, v0, T_FINAL, DT_FALLBACK, tag)
    print(f"  done in {time.time()-t0:.1f}s  blew_up={res['blew_up']}")
    np.savez(f"pred_results/E2_{tag}.npz",
             times=res["times"], vmax=res["vmax"],
             lock=res["lock"], fracL_v=res["fracL_v"],
             npeaks_v=res["npeaks_v"], x=x,
             u_final=res["u_final"], v_final=res["v_final"])
    n = len(res["times"])
    idx_late = slice(int(0.8 * n), n)
    vmax_late = float(np.mean(res["vmax"][idx_late]))
    npk_late = int(np.round(np.mean(res["npeaks_v"][idx_late])))
    fracL_late = float(np.mean(res["fracL_v"][idx_late]))
    lock_late = float(np.nanmean(res["lock"][idx_late]))
    retention = vmax_late / max(A, 1e-12)
    coherent_strict = (npk_late <= 3) and (vmax_late >= 0.5) and (fracL_late >= 0.5)
    coherent_relaxed = (npk_late <= 3) and (fracL_late >= 0.5) and (retention >= 0.4)
    print(f"  late: vmax={vmax_late:.3f}, npk={npk_late}, fracL={fracL_late:.3f}, "
          f"lock={lock_late:.3f}, retention={retention:.3f} -> "
          f"strict={coherent_strict} relaxed={coherent_relaxed}")
    summary["ICs"][tag] = dict(
        A=A, vmax_late=vmax_late, npeaks_v_late=npk_late,
        fracL_v_late=fracL_late, lock_late=lock_late,
        retention=retention,
        coherent_strict=bool(coherent_strict),
        coherent_relaxed=bool(coherent_relaxed),
        blew_up=bool(res["blew_up"]),
    )

with open("evidence/E2_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\nSaved evidence/E2_summary.json")
print(json.dumps(summary["ICs"], indent=2))
