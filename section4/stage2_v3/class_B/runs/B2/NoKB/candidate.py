"""
E3 — Test sharpness of the bore-stabilised boundary; convergence + reflection probe.

Where we stand after E2
=======================
* The v IC = A sech^2 is NOT a BKdV soliton: at u_L=0 it intrinsically fissions
  (A=0.5 -> 3 peaks, A=1.0 -> 4 peaks).
* Strong bore (u_L = 1.0) SUPPRESSES this fission: A in {0.3, 0.4, 0.6, 0.7,
  0.8, 1.0} all give n_peaks=1; at A=1.2 we see 3 peaks; A=1.5 gives 4-5.
* So a clear boundary lies somewhere in A in [1.0, 1.2] at u_L=1.0. We do not
  yet know whether the transition is a SHARP step (n_peaks: 1 -> 3 abruptly at
  some A*) or a SMOOTH ramp (1 -> 2 -> 3 -> ... as A increases).

Three hypotheses we want to discriminate
========================================
H_SHARP    : there exists A* such that n_peaks(A < A*) = 1 and n_peaks(A > A*) >= 2,
             with no intermediate states.
H_SMOOTH   : n_peaks increases in a stair-step fashion as A grows, with each step
             of size 1 (KdV-style soliton ladder).
H_ARTIFACT : the observed "regime" structure depends on dt / domain / T, i.e. it
             is partially numerical artifact.

Also: in E1+E2 we did NOT see textbook "reflection" (soliton bouncing leftward).
H_REFLECT : a large bore can reflect a small soliton. To falsify if possible.

E3 design (8 runs ~ 3 min)
==========================
Arm A (sharpness):  finer A grid at u_L=1.0:  A in {0.90, 1.00, 1.05, 1.10, 1.15}.
                    (we already have 1.00 from E1 and 1.20 from E2; we re-include
                    1.00 here to bind to identical numerical setup in a single
                    sweep)  --> 5 runs.
Arm B (T-asymptote):   rerun (u_L=1.0, A=1.00) with T=24 to see whether n_peaks
                    eventually evolves; if it stays =1, asymptotic state confirmed.
                    --> 1 run.
Arm C (dt convergence): rerun (u_L=1.0, A=1.10) with dt=5e-5 (half). If regime
                    changes, the boundary is dt-dependent (H_ARTIFACT supported).
                    --> 1 run.
Arm D (reflection probe): (u_L=2.0, A=0.2): very large bore, very small soliton.
                    If soliton's x_peak at T moves LEFT of its initial position,
                    we have reflection. --> 1 run.

NOTE: Arm A uses the SAME parameters as E2 Arm B for the runs A in {0.9,...,1.15}.
Treating this as the same hypothesis with different design (NOT a new round in
the "bug-fix re-run" sense). E3 IS a new round because it tests new hypotheses
(sharpness / convergence / reflection).
"""

import numpy as np
import os, json, time

# -------------------------------------------------------------
# Grid + solver (identical to E1/E2)
# -------------------------------------------------------------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=L / Nx)
kmax = np.max(np.abs(k))
ik = 1j * k
ksq = k ** 2
kcut = (2.0 / 3.0) * kmax
dealias = (np.abs(k) < kcut).astype(np.float64)
NU_VISC = 5e-2

def fft(a): return np.fft.fft(a)
def ifft(A): return np.real(np.fft.ifft(A))
def nl_hat(a, b): return dealias * fft(a * b)

def rhs(u_hat, v_hat):
    u = ifft(u_hat); v = ifft(v_hat)
    u2_h = nl_hat(u, u); v2_h = nl_hat(v, v); uv_h = nl_hat(u, v)
    v_xx_h = -ksq * v_hat
    v_xxx_h = -1j * (k ** 3) * v_hat
    u_hat_t = - ik * (1.5 * u2_h + 3.0 * v2_h + v_xx_h) - NU_VISC * ksq * u_hat
    v_hat_t = - ik * (3.0 * v2_h + uv_h) - v_xxx_h
    return u_hat_t, v_hat_t

def rk4_step(u_hat, v_hat, dt):
    k1a, k1b = rhs(u_hat,                 v_hat)
    k2a, k2b = rhs(u_hat + 0.5 * dt * k1a, v_hat + 0.5 * dt * k1b)
    k3a, k3b = rhs(u_hat + 0.5 * dt * k2a, v_hat + 0.5 * dt * k2b)
    k4a, k4b = rhs(u_hat +       dt * k3a, v_hat +       dt * k3b)
    return (u_hat + dt / 6.0 * (k1a + 2.0 * k2a + 2.0 * k3a + k4a),
            v_hat + dt / 6.0 * (k1b + 2.0 * k2b + 2.0 * k3b + k4b))

def make_bore(uL, x0=+6.0, width=1.0):
    return 0.5 * uL * (1.0 - np.tanh((x - x0) / width)) if uL > 0 else np.zeros_like(x)

def make_soliton(A, x0=-6.0):
    return A * (1.0 / np.cosh(np.sqrt(A / 2.0) * (x - x0))) ** 2

def find_peaks(field, x_arr, height_thresh):
    peaks = []
    N = len(field)
    for i in range(N):
        ip = (i + 1) % N; im = (i - 1) % N
        if field[i] > field[ip] and field[i] > field[im] and field[i] > height_thresh:
            peaks.append((float(x_arr[i]), float(field[i])))
    return peaks

def spectrum_high_frac(field):
    F = np.fft.fft(field) / Nx
    P = np.abs(F) ** 2
    total = float(np.sum(P))
    return float(np.sum(P[np.abs(k) > 3.0])) / total if total >= 1e-30 else 0.0

def run_one(uL, A, T=12.0, dt=1e-4, n_snaps=13, tag_suffix=""):
    u0 = make_bore(uL); v0 = make_soliton(A)
    u_hat = fft(u0); v_hat = fft(v0)
    nsteps = int(round(T / dt))
    snap_stride = max(1, nsteps // (n_snaps - 1))
    snaps_u = [u0.copy()]; snaps_v = [v0.copy()]; snap_t = [0.0]
    diag_stride = max(1, nsteps // 40)
    times = [0.0]
    L2_v = [float(np.sqrt(np.sum(v0 * v0) * dx))]
    max_v = [float(np.max(v0))]
    npeaks_t = [1]
    blew_up = False
    t = 0.0
    for step in range(1, nsteps + 1):
        u_hat, v_hat = rk4_step(u_hat, v_hat, dt)
        t += dt
        if not (np.all(np.isfinite(u_hat)) and np.all(np.isfinite(v_hat))):
            blew_up = True; break
        if step % diag_stride == 0:
            v_now = ifft(v_hat)
            times.append(t)
            L2_v.append(float(np.sqrt(np.sum(v_now * v_now) * dx)))
            max_v.append(float(np.max(v_now)))
            npeaks_t.append(len(find_peaks(v_now, x, max(0.1 * A, 0.05))))
        if step % snap_stride == 0 and len(snaps_u) < n_snaps:
            u_now = ifft(u_hat); v_now = ifft(v_hat)
            snaps_u.append(u_now.copy()); snaps_v.append(v_now.copy()); snap_t.append(t)
    while len(snaps_u) < n_snaps:
        snaps_u.append(snaps_u[-1].copy()); snaps_v.append(snaps_v[-1].copy()); snap_t.append(snap_t[-1])
    u_T = ifft(u_hat); v_T = ifft(v_hat)
    peak_thresh = max(0.1 * A, 0.05)
    peaks = find_peaks(v_T, x, peak_thresh)
    n_peaks = len(peaks)
    if n_peaks > 0:
        x_peak, h_peak = max(peaks, key=lambda p: p[1])
    else:
        x_peak, h_peak = float('nan'), float(np.max(v_T))
    return {
        "uL": uL, "A": A, "T": t, "dt": dt, "blew_up": blew_up,
        "L2_v_T": float(np.sqrt(np.sum(v_T * v_T) * dx)),
        "max_v_T": float(np.max(v_T)),
        "min_v_T": float(np.min(v_T)),
        "x_peak_T": x_peak,
        "h_peak_T": h_peak,
        "n_peaks_T": n_peaks,
        "u_max_T": float(np.max(u_T)),
        "u_min_T": float(np.min(u_T)),
        "high_v_T": spectrum_high_frac(v_T),
        "times": np.array(times),
        "L2_v_t": np.array(L2_v),
        "max_v_t": np.array(max_v),
        "npeaks_t": np.array(npeaks_t),
        "snaps_u": np.array(snaps_u),
        "snaps_v": np.array(snaps_v),
        "snap_t": np.array(snap_t),
        "tag_suffix": tag_suffix,
    }

# -------------------------------------------------------------
# Driver
# -------------------------------------------------------------
os.makedirs("pred_results", exist_ok=True)
os.makedirs("evidence", exist_ok=True)

T_FINAL = 12.0
DT = 1e-4

print(f"E3: sharpness + falsification.  T={T_FINAL}, dt={DT}, NU={NU_VISC}")

summary_rows = []
t0 = time.time()

# Arm A: finer A grid at u_L=1.0
print("\n=== Arm A: sharpness of A-boundary at u_L=1.0 ===")
ARM_A = [(1.0, A) for A in [0.90, 1.00, 1.05, 1.10, 1.15]]
for (uL, A) in ARM_A:
    tag = f"A_uL{uL:.2f}_A{A:.2f}"
    t_run = time.time()
    res = run_one(uL, A, T=T_FINAL, dt=DT, tag_suffix="A_sharpness")
    wall = time.time() - t_run
    print(f"  uL={uL:.2f} A={A:.3f}  n_peaks={res['n_peaks_T']}  max_v_T={res['max_v_T']:.3f}  "
          f"x_peak={res['x_peak_T']:.2f}  L2_v_T={res['L2_v_T']:.3f}  t={wall:.1f}s")
    summary_rows.append({**{k: res[k] for k in ['uL','A','L2_v_T','max_v_T','x_peak_T',
                       'h_peak_T','n_peaks_T','u_max_T','u_min_T','high_v_T','blew_up']},
                        'arm': 'A_sharpness', 'dt': DT, 'T': T_FINAL, 'wall_s': wall})
    np.savez_compressed(f"pred_results/E3_{tag}.npz",
        x=x, snaps_u=res["snaps_u"], snaps_v=res["snaps_v"], snap_t=res["snap_t"],
        times=res["times"], L2_v_t=res["L2_v_t"], max_v_t=res["max_v_t"],
        npeaks_t=res["npeaks_t"], uL=uL, A=A, nu_visc=NU_VISC, dt=DT)

# Arm B: T=24 asymptote check
print("\n=== Arm B: long-time asymptote at (u_L=1.0, A=1.0) ===")
t_run = time.time()
res = run_one(1.0, 1.0, T=24.0, dt=DT, tag_suffix="B_long_T")
wall = time.time() - t_run
print(f"  uL=1.00 A=1.00 T=24  n_peaks={res['n_peaks_T']}  max_v_T={res['max_v_T']:.3f}  "
      f"x_peak={res['x_peak_T']:.2f}  t={wall:.1f}s")
print(f"  npeaks(t) traj: {res['npeaks_t'].tolist()}")
summary_rows.append({**{k: res[k] for k in ['uL','A','L2_v_T','max_v_T','x_peak_T',
                   'h_peak_T','n_peaks_T','u_max_T','u_min_T','high_v_T','blew_up']},
                    'arm': 'B_long_T', 'dt': DT, 'T': 24.0, 'wall_s': wall})
np.savez_compressed(f"pred_results/E3_B_long_T.npz",
    x=x, snaps_u=res["snaps_u"], snaps_v=res["snaps_v"], snap_t=res["snap_t"],
    times=res["times"], L2_v_t=res["L2_v_t"], max_v_t=res["max_v_t"],
    npeaks_t=res["npeaks_t"], uL=1.0, A=1.0, nu_visc=NU_VISC, dt=DT)

# Arm C: dt = 5e-5 convergence
print("\n=== Arm C: dt convergence at (u_L=1.0, A=1.10) ===")
t_run = time.time()
res = run_one(1.0, 1.10, T=T_FINAL, dt=5e-5, tag_suffix="C_dt_half")
wall = time.time() - t_run
print(f"  uL=1.00 A=1.10 dt=5e-5  n_peaks={res['n_peaks_T']}  max_v_T={res['max_v_T']:.3f}  "
      f"x_peak={res['x_peak_T']:.2f}  L2_v_T={res['L2_v_T']:.3f}  t={wall:.1f}s")
summary_rows.append({**{k: res[k] for k in ['uL','A','L2_v_T','max_v_T','x_peak_T',
                   'h_peak_T','n_peaks_T','u_max_T','u_min_T','high_v_T','blew_up']},
                    'arm': 'C_dt_half', 'dt': 5e-5, 'T': T_FINAL, 'wall_s': wall})
np.savez_compressed(f"pred_results/E3_C_dt_half.npz",
    x=x, snaps_u=res["snaps_u"], snaps_v=res["snaps_v"], snap_t=res["snap_t"],
    times=res["times"], L2_v_t=res["L2_v_t"], max_v_t=res["max_v_t"],
    npeaks_t=res["npeaks_t"], uL=1.0, A=1.10, nu_visc=NU_VISC, dt=5e-5)

# Arm D: Reflection probe -- very tall bore + small soliton
print("\n=== Arm D: reflection probe (u_L=2.0, A=0.2) ===")
# Need a quick benchmark: u_L=2.0 means u_xx Gibbs is harder. Should still work
# with NU=5e-2 (diffusion balances bore).
t_run = time.time()
res = run_one(2.0, 0.2, T=T_FINAL, dt=DT, tag_suffix="D_reflect")
wall = time.time() - t_run
print(f"  uL=2.00 A=0.20  n_peaks={res['n_peaks_T']}  max_v_T={res['max_v_T']:.3f}  "
      f"x_peak={res['x_peak_T']:.2f}  L2_v_T={res['L2_v_T']:.3f}  "
      f"u_max={res['u_max_T']:.2f}  t={wall:.1f}s")
summary_rows.append({**{k: res[k] for k in ['uL','A','L2_v_T','max_v_T','x_peak_T',
                   'h_peak_T','n_peaks_T','u_max_T','u_min_T','high_v_T','blew_up']},
                    'arm': 'D_reflect', 'dt': DT, 'T': T_FINAL, 'wall_s': wall})
np.savez_compressed(f"pred_results/E3_D_reflect.npz",
    x=x, snaps_u=res["snaps_u"], snaps_v=res["snaps_v"], snap_t=res["snap_t"],
    times=res["times"], L2_v_t=res["L2_v_t"], max_v_t=res["max_v_t"],
    npeaks_t=res["npeaks_t"], uL=2.0, A=0.2, nu_visc=NU_VISC, dt=DT)

print(f"\nTotal wall: {time.time()-t0:.1f}s")

with open("evidence/E3_summary.json", "w") as f:
    json.dump({
        "round": 3,
        "T": T_FINAL, "dt_default": DT, "Nx": Nx, "L": L, "nu_visc": NU_VISC,
        "rows": summary_rows,
    }, f, indent=2)
print("Saved evidence/E3_summary.json")
