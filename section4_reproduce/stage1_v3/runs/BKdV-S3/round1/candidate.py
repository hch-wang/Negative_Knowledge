"""
BKdV-S3 / E1 — Initial Condition family scan at moderate amplitude.

Research question (program): From which IC families does BKdV produce
coherent (long-lived localized) structures, and from which does it produce
incoherent radiation? Is there a phase boundary?

E1 design (smallest meaningful first probe)
-------------------------------------------
* Use the pre-validated solver stack (Fourier pseudospectral, 2/3 dealiasing,
  RK4 on nonlinear, integrating-factor on KdV linear dispersion v_xxx,
  spectral hyperviscosity tail for stability) — unchanged from BKdV-S2-NoKB.
* Scan 5 IC families at "moderate" amplitude (A=0.8 for v, paired flat or
  small-noise u). Same v-mass NOT enforced this round — we want to see the
  qualitative response of each family at its native scale.
* Late-time coherence diagnostic (post-transient, t >= 0.8 T):
    - npeaks_v  : number of local v-peaks above height 0.3 (after smoothing)
    - vmax      : max |v|
    - lock      : Pearson corr between (u - mean) and (0.5 v^2 - mean)
    - frac_low_v: fraction of v's energy at |k| <= 2
  Coherent label heuristic (loose; tightened in E3): npeaks_v <= 3 AND
  vmax >= 0.5 AND frac_low_v >= 0.5. Incoherent: high npeaks_v, low frac_low_v.
* Five ICs:
    G  : single Gaussian on v, flat u                (smooth, localized)
    S  : sech^2 on v, flat u                         (KdV-soliton-like seed)
    N  : Gaussian envelope * white noise on v, flat u (incoherent seed)
    P2 : two well-separated sech^2 pulses on v       (collision test)
    K  : sinusoidal v = A cos(k0 x), flat u          (periodic / non-localized)

Outputs: pred_results/E1_<tag>.npz per IC, evidence/E1_summary.json, stdout.
"""

import numpy as np
import os, json, time

# -----------------------------------------------------------------------------
# Spatial grid + spectral operators (identical to pre-validated stack)
# -----------------------------------------------------------------------------
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

# Integrating factor on v_xxx: w_hat(t) = e^{-i k^3 t} v_hat(t)
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

# -----------------------------------------------------------------------------
# Diagnostics
# -----------------------------------------------------------------------------
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
    return low, tot - low, low / max(tot, 1e-30)

def count_peaks(field, height=0.3, smooth_window=3):
    f = field.copy()
    if smooth_window > 1:
        w = smooth_window
        kernel = np.ones(w) / w
        f = np.convolve(np.concatenate([f[-w:], f, f[:w]]), kernel, mode="same")[w:-w]
    # periodic local maxima above threshold
    npts = len(f)
    peaks = 0
    for i in range(npts):
        if f[i] < height: continue
        if f[i] >= f[(i - 1) % npts] and f[i] >= f[(i + 1) % npts] and \
           (f[i] > f[(i - 1) % npts] or f[i] > f[(i + 1) % npts]):
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
    umax_t = [float(np.max(np.abs(u0)))]
    lock_t = [lock_corr(u0, v0)]
    fracL_v = [spectrum_partition(v0)[2]]
    fracL_u = [spectrum_partition(u0)[2]]
    npk_t = [count_peaks(v0)]
    snaps_u = [u0.copy()]; snaps_v = [v0.copy()]; snap_t = [0.0]

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
            umax_t.append(float(np.max(np.abs(u_now))))
            lock_t.append(lock_corr(u_now, v_now))
            fracL_v.append(spectrum_partition(v_now)[2])
            fracL_u.append(spectrum_partition(u_now)[2])
            npk_t.append(count_peaks(v_now))
            if len(snaps_u) < 9:
                snaps_u.append(u_now.copy()); snaps_v.append(v_now.copy()); snap_t.append(t)
    # always store final snapshot
    v_hat_now = np.exp(ik3 * t) * w_hat
    u_now = ifft(u_hat); v_now = ifft(v_hat_now)
    snaps_u.append(u_now.copy()); snaps_v.append(v_now.copy()); snap_t.append(t)

    return {
        "tag": tag, "T": T, "dt": dt,
        "times": np.array(times),
        "vmax": np.array(vmax_t), "umax": np.array(umax_t),
        "lock": np.array(lock_t),
        "fracL_v": np.array(fracL_v), "fracL_u": np.array(fracL_u),
        "npeaks_v": np.array(npk_t),
        "snaps_u": np.array(snaps_u), "snaps_v": np.array(snaps_v),
        "snap_t": np.array(snap_t),
        "u_final": u_now, "v_final": v_now,
        "blew_up": blew_up,
    }

# -----------------------------------------------------------------------------
# IC families (moderate amplitude A=0.8 for v)
# -----------------------------------------------------------------------------
A = 0.8
rng = np.random.default_rng(1234)

# G : single Gaussian
v0_G = A * np.exp(-((x + 2.0) / 2.0) ** 2)
u0_G = np.zeros_like(x)

# S : sech^2 (classic KdV soliton shape)
v0_S = A / np.cosh((x + 2.0) / 1.5) ** 2
u0_S = np.zeros_like(x)

# N : Gaussian-envelope * white noise
env = np.exp(-((x) / 5.0) ** 2)
noise = rng.standard_normal(Nx)
v0_N = A * env * noise / np.std(noise * env)
v0_N = v0_N - np.mean(v0_N)  # remove mean so periodic
u0_N = np.zeros_like(x)

# P2 : two sech^2 pulses
v0_P2 = A / np.cosh((x + 6.0) / 1.5) ** 2 + (0.8 * A) / np.cosh((x - 3.0) / 1.5) ** 2
u0_P2 = np.zeros_like(x)

# K : sinusoidal (commensurate with periodic box, k0=2)
k0_per = 2 * np.pi * 2 / L  # 2 wavelengths in box
v0_K = A * np.cos(k0_per * x)
u0_K = np.zeros_like(x)

ICs = {
    "G_gauss":   (u0_G,  v0_G),
    "S_sech2":   (u0_S,  v0_S),
    "N_noise":   (u0_N,  v0_N),
    "P2_twopulse": (u0_P2, v0_P2),
    "K_sin":     (u0_K,  v0_K),
}

T_FINAL = 12.0
DT = 2.5e-4

os.makedirs("pred_results", exist_ok=True)
os.makedirs("evidence", exist_ok=True)
summary = {"round": 1, "T": T_FINAL, "dt": DT, "Nx": Nx, "A": A, "ICs": {}}

for tag, (u0, v0) in ICs.items():
    t0 = time.time()
    print(f"\n=== IC {tag} : vmax0={np.max(np.abs(v0)):.3f}, "
          f"L2_v0={np.sqrt(np.sum(v0**2)*dx):.3f} ===")
    res = integrate(u0, v0, T_FINAL, DT, tag)
    print(f"  done in {time.time()-t0:.1f}s  blew_up={res['blew_up']}")
    np.savez(f"pred_results/E1_{tag}.npz",
             times=res["times"], vmax=res["vmax"], umax=res["umax"],
             lock=res["lock"], fracL_v=res["fracL_v"], fracL_u=res["fracL_u"],
             npeaks_v=res["npeaks_v"],
             snaps_u=res["snaps_u"], snaps_v=res["snaps_v"], snap_t=res["snap_t"],
             u_final=res["u_final"], v_final=res["v_final"], x=x)
    # Coherence label from final 20% of trajectory
    n = len(res["times"])
    idx_late = slice(int(0.8 * n), n)
    vmax_late = float(np.mean(res["vmax"][idx_late]))
    npk_late = int(np.round(np.mean(res["npeaks_v"][idx_late])))
    fracL_late = float(np.mean(res["fracL_v"][idx_late]))
    lock_late = float(np.nanmean(res["lock"][idx_late]))
    coherent = (npk_late <= 3) and (vmax_late >= 0.5) and (fracL_late >= 0.5)
    label = "COHERENT" if coherent else "INCOHERENT"
    print(f"  late: vmax={vmax_late:.3f}, npeaks_v={npk_late}, "
          f"frac_low_v={fracL_late:.3f}, lock={lock_late:.3f} -> {label}")
    summary["ICs"][tag] = dict(
        vmax_late=vmax_late, npeaks_v_late=npk_late,
        fracL_v_late=fracL_late, lock_late=lock_late,
        coherent=bool(coherent), blew_up=bool(res["blew_up"]),
        vmax0=float(np.max(np.abs(v0))),
        L2_v0=float(np.sqrt(np.sum(v0**2)*dx)),
    )

with open("evidence/E1_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("\nSaved evidence/E1_summary.json")
print(json.dumps(summary["ICs"], indent=2))
