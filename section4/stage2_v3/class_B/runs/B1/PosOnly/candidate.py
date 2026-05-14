"""
B1 / PosOnly — Round 3 Experiment (E3)

E1+E2 findings:
  - Compound soliton is TRANSIENT (locking R drops 1.0 -> ~0.5 by t=0.5 for
    A=1.5 sech^2 m0=0) — it does NOT persist as the task statement suggests.
  - However, in the early window t in [0, 0.5] the locking R stays 0.9+
    across ALL amplitudes A in [0.4, 2.0] — there IS a quasi-locked phase.
  - The duration of the locked phase shrinks with amplitude (consistent with
    BKdV-S7-deep A-sweep: slope 0.22 for A<1, slope 2.49 for A>=1).
  - Nx=256 vs Nx=512 (dt=2.5e-5) agree to <2% on all diagnostics through
    t=2: the dynamics is physical, not numerical.

E3 distinguishes 3 mechanism hypotheses:
  H_alpha (algebraic source dominated): the compound soliton exists ONLY in
    the linear window where the BKdV-S5 source m_t|_{m=0} = (v-1)*(6 v v_x
    + v_xxx) is small/small-times integrated, and its lifetime is set by
    when ||t * S||_L2 / ||v^2/2||_L2 = O(1). Predicts: with VISCOSITY damping
    the dispersive piece v_xxx of S, locked phase EXTENDS modestly but
    cannot persist forever.
  H_beta (radiative cleansing): m is generated globally but gets advected
    AWAY from v-peak by linear dispersion (radiation moves at group velocity
    -3k^2 != soliton phase speed). Predicts: ratio
      r_local = ||m||_in / ||m||_global
    DROPS over time as fast radiation escapes the compound support, even
    while ||m||_global grows. Locking R inside compound should hold even
    after locking R averaged over all space drops.
  H_gamma (Gardner-IC selection / bound state): a proper Gardner-soliton IC
    sustains the compound soliton far longer than a KdV-sech^2 IC at the
    same amplitude. Predicts: BKdV with v0 = Gardner soliton shows longer-
    lived R~1 phase than sech^2 IC at the same v_max.

E3 design — 3 BKdV runs at fixed amp A_eff=1.5 over T=2.0, dt=1e-4, Nx=256
with 2/3 dealias + RK4:
  R1) sech^2 A=1.5 m0=0, nu_u=0     [E2 baseline, reused as control]
  R2) sech^2 A=1.5 m0=0, nu_u=5e-2  [global viscosity per BKdV-S6]
  R3) Gardner-soliton IC v0=v_G(x;c=Cstar) with peak ~1.5, u0=v_G^2/2, nu_u=0

Diagnostics:
  - locking R, R^2 inside v > 0.3*v_max support (LOCAL test)
  - locking R_all over full domain (GLOBAL test for contrast)
  - ratio r_local = ||m||_in / ||m||_global
  - peak position x_peak(t) and phase speed c_emp = dx_peak/dt
  - Gardner-predicted speed c_G for the instantaneous v_peak from the
    Gardner-soliton dispersion: for v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0,
    the soliton at peak v_p propagates at c_G(v_p) = 6*<v>_peak +
    (3/2)*<v^2>_peak (effective speed of a single-hump solution; we
    measure this by averaging v near peak)
  - decay of m_outside vs m_inside (basin)
"""

import os
import time
import numpy as np
import scipy.signal as sps

OUT_DIR = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/PosOnly/evidence/E3"
os.makedirs(OUT_DIR, exist_ok=True)

# Domain
L = 30.0
Nx = 256
x = np.linspace(-L / 2, L / 2, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = 1j * k ** 3
mk2 = -k ** 2
kmax = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * kmax).astype(float)

T_END = 2.0
dt = 1.0e-4
nt = int(round(T_END / dt))
SNAP_TIMES = np.array([
    0.0, 0.01, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.2, 0.25, 0.3,
    0.4, 0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0
])
SNAP_STEPS = np.round(SNAP_TIMES / dt).astype(int).tolist()


def dx_(f):
    return np.real(np.fft.ifft(ik * (np.fft.fft(f) * dealias)))


def d2x_(f):
    return np.real(np.fft.ifft(mk2 * (np.fft.fft(f) * dealias)))


def d3x_(f):
    return np.real(np.fft.ifft(ik3 * (np.fft.fft(f) * dealias)))


def prod_(a, b):
    ah = np.fft.fft(a) * dealias
    bh = np.fft.fft(b) * dealias
    ad = np.real(np.fft.ifft(ah))
    bd = np.real(np.fft.ifft(bh))
    return np.real(np.fft.ifft(np.fft.fft(ad * bd) * dealias))


def rhs(u, v, nu_u=0.0):
    uux = prod_(u, dx_(u))
    v2 = prod_(v, v)
    rhs_inner = 3.0 * v2 + d2x_(v)
    du = -3.0 * uux - dx_(rhs_inner)
    if nu_u > 0:
        du += nu_u * d2x_(u)
    vvx = prod_(v, dx_(v))
    uv = prod_(u, v)
    dv = -6.0 * vvx - d3x_(v) - dx_(uv)
    return du, dv


def rk4(u, v, dt_, nu_u=0.0):
    k1u, k1v = rhs(u, v, nu_u)
    k2u, k2v = rhs(u + 0.5 * dt_ * k1u, v + 0.5 * dt_ * k1v, nu_u)
    k3u, k3v = rhs(u + 0.5 * dt_ * k2u, v + 0.5 * dt_ * k2v, nu_u)
    k4u, k4v = rhs(u + dt_ * k3u, v + dt_ * k3v, nu_u)
    return (
        u + (dt_ / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u),
        v + (dt_ / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v),
    )


def gardner_soliton(x, A, x0):
    """
    For the Gardner equation v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0,
    the single-soliton family has the form
        v(x,t) = A / (1 + B cosh(k(x - c t - x0)))
    with k = sqrt(6 A / (3 A + 4)), B = sqrt(1 + A/2)/(1 + A/4),
    c = 3 A + (3/2) A^2 / (...).
    Rather than derive exactly, we use the known KdV-Gardner mapping for an
    approximate single-hump shape: we take a tanh-modulated sech profile
    that matches the algebraic Gardner kink-soliton form for A<2:
        v(x) = A * sech^2(k*(x-x0)) / (1 + delta*tanh^2(k*(x-x0)))
    with delta = A/(A+4) (so for small A this -> sech^2, like KdV).
    This is an approximate single-bump shape consistent with the Gardner
    soliton kernel. We document this is approximate.
    """
    k_ = np.sqrt(max(A, 0.01))  # width scale
    s = 1.0 / np.cosh(k_ * (x - x0))
    delta = A / (A + 4.0)
    profile = A * s ** 2 / (1.0 + delta * (1.0 - s ** 2))
    return profile


def diagnostics(u, v):
    m = u - 0.5 * v ** 2
    vmax = float(np.max(v))
    norm_m_global = float(np.sqrt(np.sum(m ** 2) * dx))
    if vmax > 0.05:
        inside = v > 0.3 * vmax
    else:
        inside = np.zeros_like(v, dtype=bool)
    if inside.any():
        m_in = m[inside]
        norm_m_inside = float(np.sqrt(np.sum(m_in ** 2) * dx))
        w = 0.5 * v[inside] ** 2
        denom = float(np.sum(w ** 2))
        R = float(np.sum(u[inside] * w) / denom) if denom > 0 else float("nan")
        u_hat = R * w
        ss_res = float(np.sum((u[inside] - u_hat) ** 2))
        ss_tot = float(np.sum((u[inside] - np.mean(u[inside])) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else float("nan")
        n_in = int(inside.sum())
    else:
        norm_m_inside = float("nan")
        R = float("nan")
        r2 = float("nan")
        n_in = 0
    outside = ~inside
    norm_m_outside = (
        float(np.sqrt(np.sum(m[outside] ** 2) * dx))
        if outside.any() else float("nan")
    )
    # global R over full domain
    w_g = 0.5 * v ** 2
    denom_g = float(np.sum(w_g ** 2))
    R_global = (
        float(np.sum(u * w_g) / denom_g) if denom_g > 0 else float("nan")
    )
    if vmax > 0.1:
        peaks, _ = sps.find_peaks(v, prominence=0.05 * vmax)
    else:
        peaks = np.array([], dtype=int)
    x_peak = float(x[int(np.argmax(v))])
    # average v and v^2 inside support (for Gardner c_pred)
    if inside.any():
        v_avg = float(np.mean(v[inside]))
        v2_avg = float(np.mean(v[inside] ** 2))
    else:
        v_avg = float("nan")
        v2_avg = float("nan")
    return {
        "vmax": vmax,
        "umax": float(np.max(u)),
        "umin": float(np.min(u)),
        "norm_m_global": norm_m_global,
        "norm_m_inside": norm_m_inside,
        "norm_m_outside": norm_m_outside,
        "R_locking": R,
        "R2_locking": r2,
        "R_global": R_global,
        "n_inside_pts": n_in,
        "n_peaks": int(len(peaks)),
        "x_peak": x_peak,
        "mass_v": float(np.sum(v) * dx),
        "L2v": float(np.sqrt(np.sum(v ** 2) * dx)),
        "L2u": float(np.sqrt(np.sum(u ** 2) * dx)),
        "v_avg_inside": v_avg,
        "v2_avg_inside": v2_avg,
    }


def run(u0, v0, T, dt_, snap_steps, nu_u=0.0, label=""):
    print(f"\n--- {label} (nu_u={nu_u}) ---", flush=True)
    u = u0.copy()
    v = v0.copy()
    snap_steps_set = set(int(s) for s in snap_steps)
    ts = []
    us = []
    vs = []
    diags = []
    if 0 in snap_steps_set:
        ts.append(0.0)
        us.append(u.copy())
        vs.append(v.copy())
        d = diagnostics(u, v)
        d["t"] = 0.0
        diags.append(d)
    nt_loc = int(round(T / dt_))
    t0 = time.time()
    for step in range(1, nt_loc + 1):
        u, v = rk4(u, v, dt_, nu_u=nu_u)
        if step in snap_steps_set:
            ts.append(step * dt_)
            us.append(u.copy())
            vs.append(v.copy())
            d = diagnostics(u, v)
            d["t"] = step * dt_
            diags.append(d)
            if not np.isfinite(np.max(np.abs(v))) or np.max(np.abs(v)) > 1e6:
                print(f"   ! diverging at t={step*dt_:.3f}", flush=True)
                break
    print(f"  done in {time.time()-t0:.1f}s",
          f"vmax_f={diags[-1]['vmax']:.3f}",
          f"R_f={diags[-1]['R_locking']:.3f}",
          f"m_in_f={diags[-1]['norm_m_inside']:.3f}", flush=True)
    return np.array(ts), np.stack(us), np.stack(vs), diags


def main():
    # R1: control sech^2 A=1.5, no viscosity
    v01 = 1.5 * (1.0 / np.cosh(x + 5.0)) ** 2
    u01 = 0.5 * v01 ** 2
    ts1, us1, vs1, d1 = run(u01, v01, T_END, dt, SNAP_STEPS, nu_u=0.0,
                            label="R1_sech2_A1.5_nu0")
    np.savez(os.path.join(OUT_DIR, "R1_sech2_nu0.npz"),
             x=x, t=ts1, u=us1, v=vs1,
             diagnostics=np.array(d1, dtype=object))

    # R2: sech^2 A=1.5 with global viscosity
    v02 = 1.5 * (1.0 / np.cosh(x + 5.0)) ** 2
    u02 = 0.5 * v02 ** 2
    ts2, us2, vs2, d2 = run(u02, v02, T_END, dt, SNAP_STEPS, nu_u=5.0e-2,
                            label="R2_sech2_A1.5_nu5e-2")
    np.savez(os.path.join(OUT_DIR, "R2_sech2_nu0.05.npz"),
             x=x, t=ts2, u=us2, v=vs2,
             diagnostics=np.array(d2, dtype=object))

    # R3: Gardner-shape IC, no viscosity
    v03 = gardner_soliton(x, 1.5, -5.0)
    u03 = 0.5 * v03 ** 2
    print(f"  Gardner IC: vmax={v03.max():.3f}, mass={np.sum(v03)*dx:.3f}")
    ts3, us3, vs3, d3 = run(u03, v03, T_END, dt, SNAP_STEPS, nu_u=0.0,
                            label="R3_gardnerShape_A1.5_nu0")
    np.savez(os.path.join(OUT_DIR, "R3_gardner_nu0.npz"),
             x=x, t=ts3, u=us3, v=vs3,
             diagnostics=np.array(d3, dtype=object))

    # Phase-speed analysis on R1 (the cleanest case)
    # During locked phase t<=0.5, the v-peak position should track Gardner
    # soliton velocity c_G ~ 2 v_peak + (1/2)*v_peak^2 (very rough, from
    # Gardner dispersion for sech-shaped pulse). We'll fit empirically.
    print("\n=== Phase-speed analysis: R1 (locked phase t<=0.5) ===")
    locked_idx = [i for i, t in enumerate(ts1) if 0.0 <= t <= 0.5]
    # Unwrap x_peak with periodic BC
    xp1 = np.array([d1[i]["x_peak"] for i in locked_idx])
    t1 = np.array([d1[i]["t"] for i in locked_idx])
    vmax1 = np.array([d1[i]["vmax"] for i in locked_idx])
    # Empirical velocity by finite difference
    c_emp = np.gradient(xp1, t1)
    # Gardner prediction for soliton speed at instantaneous v_peak:
    # From v_t + 6 v v_x + (3/2) v^2 v_x = ..., quasi-linear c ~ 6 v + (3/2) v^2
    # at the peak (which is the leading coefficient seen by the peak)
    c_gardner = 6.0 * vmax1 + 1.5 * vmax1 ** 2
    # Also a simpler "KdV-only" prediction: c_KdV ~ 6 v_peak
    c_kdv = 6.0 * vmax1
    print(f"{'t':>5s} {'x_peak':>8s} {'c_emp':>8s} {'v_peak':>7s} "
          f"{'c_kdv':>7s} {'c_gardner':>10s}")
    for i in range(len(t1)):
        print(f"{t1[i]:5.3f} {xp1[i]:8.3f} {c_emp[i]:8.3f} {vmax1[i]:7.3f} "
              f"{c_kdv[i]:7.3f} {c_gardner[i]:10.3f}")

    # Summary
    sum_path = os.path.join(OUT_DIR, "E3_summary.txt")
    with open(sum_path, "w") as f:
        f.write("# E3 summary: viscosity & Gardner-IC tests, T=2\n")
        f.write("=" * 130 + "\n")
        for label, dd in [("R1_sech2_nu0", d1),
                          ("R2_sech2_nu5e-2", d2),
                          ("R3_gardner_nu0", d3)]:
            f.write(f"\n-- {label} --\n")
            f.write(
                f"{'t':>6s} {'vmax':>7s} {'umax':>7s} "
                f"{'m_glob':>7s} {'m_in':>6s} {'m_out':>7s} "
                f"{'R':>7s} {'R2':>7s} {'R_glob':>7s} {'np':>3s} "
                f"{'x_peak':>7s}\n"
            )
            for d in dd:
                r_loc_over_glob = (d["norm_m_inside"] / d["norm_m_global"]
                                   if d["norm_m_global"] > 1e-10 else float("nan"))
                f.write(
                    f"{d['t']:6.3f} {d['vmax']:7.3f} {d['umax']:7.3f} "
                    f"{d['norm_m_global']:7.3f} {d['norm_m_inside']:6.3f} "
                    f"{d['norm_m_outside']:7.3f} {d['R_locking']:7.3f} "
                    f"{d['R2_locking']:7.3f} {d['R_global']:7.3f} "
                    f"{d['n_peaks']:3d} {d['x_peak']:7.3f}\n"
                )
        # Phase-speed
        f.write("\n-- Phase-speed analysis R1 (locked phase t<=0.5) --\n")
        f.write(f"{'t':>6s} {'x_peak':>8s} {'c_emp':>8s} {'v_peak':>7s} "
                f"{'c_kdv':>7s} {'c_gardner':>10s}\n")
        for i in range(len(t1)):
            f.write(f"{t1[i]:6.3f} {xp1[i]:8.3f} {c_emp[i]:8.3f} "
                    f"{vmax1[i]:7.3f} {c_kdv[i]:7.3f} {c_gardner[i]:10.3f}\n")
    print("\nSummary written to:", sum_path)

    # Quick comparison print
    print("\n=== Quick R1 vs R2 vs R3 comparison at key times ===")
    print(f"{'t':>6s} | {'R1_R':>7s} {'R1_min':>7s} | {'R2_R':>7s} {'R2_min':>7s} | {'R3_R':>7s} {'R3_min':>7s}")
    target_ts = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
    for tt in target_ts:
        idx1 = int(np.argmin(np.abs(ts1 - tt)))
        idx2 = int(np.argmin(np.abs(ts2 - tt)))
        idx3 = int(np.argmin(np.abs(ts3 - tt)))
        print(f"{tt:6.2f} | {d1[idx1]['R_locking']:7.3f} {d1[idx1]['norm_m_inside']:7.3f} | "
              f"{d2[idx2]['R_locking']:7.3f} {d2[idx2]['norm_m_inside']:7.3f} | "
              f"{d3[idx3]['R_locking']:7.3f} {d3[idx3]['norm_m_inside']:7.3f}")


if __name__ == "__main__":
    main()
