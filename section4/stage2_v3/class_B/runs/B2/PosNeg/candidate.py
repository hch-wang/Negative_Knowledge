"""B2 / PosNeg — Round 3 (E3).

Mechanism inquiry: bore-soliton interaction regimes in BKdV.

Pre-validated solver stack (BKdV-S1, BKdV-S6, BKdV-S7):
    Fourier pseudospectral, Nx=256, periodic L=30
    2/3-rule dealiasing, classical RK4, dt=1e-4
    nu=5e-2 explicit viscosity on u-equation

E2 findings that drive E3 design
--------------------------------
1) Outcome is dominated by SOLITON AMPLITUDE A; u_L modulates magnitude
   but not qualitative class. This FALSIFIES H_beta (amplitude-ratio gate).
2) PHASE SHIFT (interaction - free) flips sign near A~1.2-1.5:
       A < 1.0  -> dx_centroid > 0 (soliton ACCELERATED through bore)
       A > 1.5  -> dx_centroid < 0 (soliton DECELERATED by bore)
   The transition coincides with BKdV-S5 deep prediction:
       m_t|_{m=0} = (v-1)(6 v v_x + v_xxx)
   has a sign flip when v exceeds 1 over the soliton core. Below A=1 the
   source is dispersive-dominated (loglog slope 0.22); above A=1 cubic
   (slope 2.49). This identifies a PHYSICAL mechanism for the boundary.
3) RETENTION v_peak/v_free is non-monotonic: drops from 1.0 (A=0.3) to
   0.58 (A~1.8) then rises again to 0.79 (A=2.5). Interpretable as
   competing effects: bore-induced damping vs cubic self-focusing at
   large A reasserting coherence.
4) At T=2 the soliton has NOT yet crossed the bore front (x=+7).
   We need either (a) longer T or (b) smaller initial separation to
   complete the encounter and observe transmission/reflection.

E3 design
---------
Two-pronged final round:

A. PHASE-SHIFT TRANSITION REFINEMENT (sharp vs smooth, A axis):
   Sweep A finely across the candidate boundary A in [0.7..1.7] x 6
   points x 2 bore levels (uL=0.5, 1.5). Same geometry as E2; T=2.
   If transition is SHARP we expect kink in dx_centroid(A); if SMOOTH
   we see continuous variation.

B. ENCOUNTER COMPLETION (transmission vs reflection, T axis):
   At fixed A=1.5 (transition region) and uL in {0.5, 1.5}, extend
   T to 3.0 and reduce X0_BORE to +3 (closer to soliton) so the
   soliton fully encounters the bore front before periodic wrap.
   Also vary BORE_W in {0.25 (sharper), 0.5, 1.0 (smoother)} to test
   whether the bore-front sharpness changes the regime ("sharp vs
   smooth" in the *boundary-thickness* sense).

C. KINEMATIC GATE CONTROL (H_alpha):
   At fixed A=1.5, uL=0.5, vary INITIAL SEPARATION d in {6, 9, 12}
   (X0_SOL = X0_BORE - d) at T=2; if outcome is driven by ENCOUNTER
   PHYSICS (Holm coupling), it should be d-invariant; if driven by
   FREE-PROPAGATION DRIFT, d strongly modulates apparent regime.

We DELIBERATELY span only 3 cases for B and C to leave budget for the
6+12=18 cells in A.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks


# ----------------- grid and parameters -----------------
Nx = 256
L = 30.0
dx = L / Nx
x = np.linspace(-L / 2, L / 2, Nx, endpoint=False)
k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
k_max = np.max(np.abs(k))
DEALIAS = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)
ik = 1j * k

dt = 1e-4
NU = 5e-2

DEFAULT_T = 2.0
DEFAULT_X0_BORE = 7.0
DEFAULT_BORE_W = 0.5
DEFAULT_X0_SOL = -5.0
SOL_W = 1.0


# ----------------- spectral utilities -----------------
def fft(arr):
    return np.fft.fft(arr)


def ifft(arr_hat):
    return np.real(np.fft.ifft(arr_hat))


def dealias(f_hat):
    return f_hat * DEALIAS


def rhs(u, v):
    u_hat = fft(u)
    v_hat = fft(v)
    vv_hat = dealias(fft(v * v))
    uv_hat = dealias(fft(u * v))
    u_x = ifft(ik * u_hat)
    v_x = ifft(ik * v_hat)
    v_xx_hat = -k * k * v_hat
    v_xxx_hat = ik * v_xx_hat
    u_xx_hat = -k * k * u_hat
    du_dt = (
        -3.0 * ifft(dealias(fft(u * u_x)))
        - ifft(ik * (3.0 * vv_hat + v_xx_hat))
        + NU * ifft(u_xx_hat)
    )
    dv_dt = (
        -6.0 * ifft(dealias(fft(v * v_x)))
        - ifft(v_xxx_hat)
        - ifft(ik * uv_hat)
    )
    return du_dt, dv_dt


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new


# ----------------- ICs -----------------
def make_bore(uL, x0=DEFAULT_X0_BORE, w=DEFAULT_BORE_W):
    return 0.5 * uL * (1.0 - np.tanh((x - x0) / w))


def make_soliton(A, x0=DEFAULT_X0_SOL, w=SOL_W):
    return A / np.cosh((x - x0) / w) ** 2


def soliton_diagnostics(v, A_ref):
    if A_ref <= 0:
        return dict(v_peak=float(np.max(v)), n_peaks=0, v_centroid=0.0)
    prom = max(0.2 * A_ref, 0.05)
    pk, _ = find_peaks(v, prominence=prom, distance=max(Nx // 32, 4))
    n_peaks = int(len(pk))
    v_peak = float(v[pk].max()) if n_peaks > 0 else float(np.max(v))
    v_sq = v * v
    v_centroid = float(np.sum(x * v_sq) / max(np.sum(v_sq), 1e-30))
    return dict(v_peak=v_peak, n_peaks=n_peaks, v_centroid=v_centroid)


def full_diagnostics(u, v, A_ref):
    sd = soliton_diagnostics(v, A_ref)
    m = u - 0.5 * v * v
    sd["bore_height"] = float(np.max(u))
    sd["bore_TV"] = float(np.sum(np.abs(np.diff(np.concatenate([u, u[:1]])))))
    sd["m_l2"] = float(np.sqrt(np.sum(m * m) * dx))
    sd["mass_v"] = float(np.sum(v) * dx)
    sd["v_retention"] = (sd["v_peak"] / A_ref) if A_ref > 0 else float("nan")
    return sd


# ----------------- driver -----------------
def run_one(uL, A, label, save_dir,
            T=DEFAULT_T, x0_bore=DEFAULT_X0_BORE, x0_sol=DEFAULT_X0_SOL,
            bore_w=DEFAULT_BORE_W):
    if A > 0 and uL > 0:
        v0 = make_soliton(A, x0=x0_sol)
        u0 = 0.5 * v0 * v0 + make_bore(uL, x0=x0_bore, w=bore_w)
    elif A > 0 and uL == 0:
        v0 = make_soliton(A, x0=x0_sol)
        u0 = 0.5 * v0 * v0
    elif A == 0 and uL > 0:
        v0 = np.zeros_like(x)
        u0 = make_bore(uL, x0=x0_bore, w=bore_w)
    else:
        v0 = np.zeros_like(x)
        u0 = np.zeros_like(x)
    u = u0.copy()
    v = v0.copy()
    n_steps = int(round(T / dt))
    centroid_t, vpeak_t, npeak_t, times = [], [], [], []
    sd = soliton_diagnostics(v, A_ref=A if A > 0 else 1.0)
    centroid_t.append(sd["v_centroid"])
    vpeak_t.append(sd["v_peak"])
    npeak_t.append(sd["n_peaks"])
    times.append(0.0)
    DIAG_EVERY = 100
    diverged = False
    snap_times = [0.0]
    snaps_v = [v0.copy()]
    snaps_u = [u0.copy()]
    snap_grid = [0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    snap_grid = [s for s in snap_grid if s <= T + 1e-9]
    snap_idx = 0
    t = 0.0
    for step in range(1, n_steps + 1):
        u, v = rk4_step(u, v, dt)
        t = step * dt
        if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
            diverged = True
            break
        if snap_idx < len(snap_grid) and t + 1e-9 >= snap_grid[snap_idx]:
            snaps_v.append(v.copy())
            snaps_u.append(u.copy())
            snap_times.append(t)
            snap_idx += 1
        if step % DIAG_EVERY == 0:
            sd = soliton_diagnostics(v, A_ref=A if A > 0 else 1.0)
            centroid_t.append(sd["v_centroid"])
            vpeak_t.append(sd["v_peak"])
            npeak_t.append(sd["n_peaks"])
            times.append(t)
    diag = full_diagnostics(u, v, A_ref=A if A > 0 else 1.0)
    np.savez(
        save_dir / f"E3_{label}.npz",
        x=x,
        u_final=u,
        v_final=v,
        u_init=u0,
        v_init=v0,
        snaps_v=np.array(snaps_v),
        snaps_u=np.array(snaps_u),
        snap_times=np.array(snap_times),
        centroid_t=np.array(centroid_t),
        vpeak_t=np.array(vpeak_t),
        npeak_t=np.array(npeak_t, dtype=int),
        times=np.array(times),
        uL=uL,
        A=A,
        T=T,
        x0_bore=x0_bore,
        x0_sol=x0_sol,
        bore_w=bore_w,
        diverged=diverged,
    )
    diag["diverged"] = diverged
    diag["uL"] = uL
    diag["A"] = A
    diag["T"] = T
    diag["x0_bore"] = x0_bore
    diag["x0_sol"] = x0_sol
    diag["bore_w"] = bore_w
    return diag


def main():
    save_dir = Path(__file__).parent / "evidence"
    save_dir.mkdir(exist_ok=True)
    print(f"# B2/PosNeg E3: Nx={Nx}, L={L}, dt={dt}, nu={NU}")
    print(f"# 2/3 dealias kept {int(DEALIAS.sum())} / {Nx} modes")
    t0 = time.time()

    out = {}

    # --- PART A: fine A sweep across phase-shift transition ---
    print("# Part A: fine A-sweep at uL in {0.5, 1.5}, T=2.0")
    A_fine = [0.7, 0.85, 1.0, 1.15, 1.3, 1.45, 1.6, 1.75]
    # Free-propagation references for each A_fine
    sol_only = {}
    for A in A_fine:
        label = f"sol_only_A{A:.2f}"
        print(f"  run {label}", flush=True)
        sol_only[A] = run_one(0.0, A, label, save_dir, T=2.0)
    out["partA_sol_only"] = {f"A{A}": sol_only[A] for A in A_fine}

    inter_A = {}
    for uL in [0.5, 1.5]:
        for A in A_fine:
            label = f"partA_uL{uL:.2f}_A{A:.2f}"
            print(f"  run {label}", flush=True)
            d = run_one(uL, A, label, save_dir, T=2.0)
            dx = d["v_centroid"] - sol_only[A]["v_centroid"]
            d["dx_centroid"] = dx
            d["retention_vs_free"] = (
                d["v_peak"] / max(sol_only[A]["v_peak"], 1e-9)
            )
            inter_A[(uL, A)] = d
            print(
                f"    -> vp={d['v_peak']:.3f} vp0={sol_only[A]['v_peak']:.3f} "
                f"npk={d['n_peaks']} xc={d['v_centroid']:.2f} "
                f"dx_centroid={dx:+.3f} "
                f"retent={d['retention_vs_free']:.3f}",
                flush=True,
            )
    out["partA_inter"] = {
        f"uL{u}_A{A}": inter_A[(u, A)] for u in [0.5, 1.5] for A in A_fine
    }

    # --- PART B: encounter completion at A=1.5, T=3, vary bore_w ---
    print("# Part B: encounter completion at A=1.5, T=3.0, vary bore_w")
    A_B = 1.5
    bore_w_list = [0.25, 0.5, 1.0]
    # closer initial separation: bore at +3, soliton at -7 (separation 10)
    x0_bore_B = 3.0
    x0_sol_B = -7.0
    T_B = 3.0
    free_B = run_one(
        0.0, A_B, "partB_sol_only", save_dir,
        T=T_B, x0_sol=x0_sol_B,
    )
    out["partB_sol_only"] = free_B
    partB = {}
    for uL in [0.5, 1.5]:
        for bw in bore_w_list:
            label = f"partB_uL{uL:.2f}_bw{bw:.2f}"
            print(f"  run {label}", flush=True)
            d = run_one(
                uL, A_B, label, save_dir,
                T=T_B, x0_bore=x0_bore_B, x0_sol=x0_sol_B, bore_w=bw,
            )
            dx = d["v_centroid"] - free_B["v_centroid"]
            d["dx_centroid"] = dx
            d["retention_vs_free"] = (
                d["v_peak"] / max(free_B["v_peak"], 1e-9)
            )
            partB[(uL, bw)] = d
            print(
                f"    -> vp={d['v_peak']:.3f} npk={d['n_peaks']} "
                f"xc={d['v_centroid']:.2f} dx={dx:+.3f} "
                f"retent={d['retention_vs_free']:.3f}",
                flush=True,
            )
    out["partB_inter"] = {
        f"uL{u}_bw{b}": partB[(u, b)] for u in [0.5, 1.5] for b in bore_w_list
    }

    # --- PART C: kinematic gate control via initial separation ---
    print("# Part C: vary initial separation d, A=1.5, uL=0.5, T=2.0")
    A_C = 1.5
    uL_C = 0.5
    sep_list = [6.0, 9.0, 12.0]
    partC = {}
    for sep in sep_list:
        x0_bore_C = +5.0
        x0_sol_C = x0_bore_C - sep
        label = f"partC_sep{sep:.1f}"
        # free reference
        label_free = f"partC_free_sep{sep:.1f}"
        print(f"  run {label_free}", flush=True)
        free_C = run_one(
            0.0, A_C, label_free, save_dir,
            T=2.0, x0_sol=x0_sol_C,
        )
        print(f"  run {label}", flush=True)
        d = run_one(
            uL_C, A_C, label, save_dir,
            T=2.0, x0_bore=x0_bore_C, x0_sol=x0_sol_C,
        )
        dx = d["v_centroid"] - free_C["v_centroid"]
        d["dx_centroid"] = dx
        d["retention_vs_free"] = d["v_peak"] / max(free_C["v_peak"], 1e-9)
        partC[sep] = (d, free_C)
        print(
            f"    -> vp={d['v_peak']:.3f} npk={d['n_peaks']} "
            f"xc={d['v_centroid']:.2f} free_xc={free_C['v_centroid']:.2f} "
            f"dx={dx:+.3f} retent={d['retention_vs_free']:.3f}",
            flush=True,
        )
    out["partC"] = {
        f"sep{s}": {"inter": partC[s][0], "free": partC[s][1]} for s in sep_list
    }

    elapsed = time.time() - t0
    out["elapsed_sec"] = elapsed
    out["params"] = dict(
        Nx=Nx, L=L, dt=dt, nu=NU, A_fine=A_fine, bore_w_list=bore_w_list,
        sep_list=sep_list, T_B=T_B,
    )
    (save_dir / "E3_summary.json").write_text(json.dumps(out, indent=2))

    # ---- Print summary tables ----
    print()
    print("# PART A summary -- dx_centroid (interaction - free) vs A")
    print("A      | uL=0.5 dx_centroid | uL=1.5 dx_centroid | "
          "uL=0.5 retention | uL=1.5 retention")
    for A in A_fine:
        d05 = inter_A[(0.5, A)]
        d15 = inter_A[(1.5, A)]
        print(
            f"{A:5.2f}  | {d05['dx_centroid']:+.3f}             | "
            f"{d15['dx_centroid']:+.3f}             | "
            f"{d05['retention_vs_free']:.3f}           | "
            f"{d15['retention_vs_free']:.3f}"
        )

    print()
    print("# PART B summary -- A=1.5 long-T encounter; bore_w sweep")
    print("uL  bore_w  vp   npk  xc       dx_centroid  retention  bore_h")
    for uL in [0.5, 1.5]:
        for bw in bore_w_list:
            d = partB[(uL, bw)]
            print(
                f"{uL:.1f}  {bw:.2f}    {d['v_peak']:.3f}  "
                f"{d['n_peaks']}   {d['v_centroid']:+.2f}   "
                f"{d['dx_centroid']:+.3f}      "
                f"{d['retention_vs_free']:.3f}      "
                f"{d['bore_height']:.3f}"
            )

    print()
    print("# PART C summary -- vary initial separation, A=1.5, uL=0.5, T=2")
    print("sep  vp   npk  xc       free_xc   dx_centroid  retention")
    for sep in sep_list:
        d, fr = partC[sep]
        print(
            f"{sep:.0f}    {d['v_peak']:.3f}  {d['n_peaks']}   "
            f"{d['v_centroid']:+.2f}   {fr['v_centroid']:+.2f}    "
            f"{d['dx_centroid']:+.3f}      {d['retention_vs_free']:.3f}"
        )

    print()
    print(f"# Wall time: {elapsed:.1f}s")
    print(f"# Saved: {save_dir / 'E3_summary.json'}")


if __name__ == "__main__":
    main()
