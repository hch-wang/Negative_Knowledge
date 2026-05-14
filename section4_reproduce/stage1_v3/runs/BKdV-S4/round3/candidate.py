"""
BKdV-S4 / Round 3 / E3 — hyperviscosity probe (ν_h at fixed Nx=256, dt=5e-4)

Single-parameter change vs E1: vary the hyperviscosity coefficient ν_h while
holding Nx=256 and dt=5e-4 at baseline. This is the DIFFERENT numerical
parameter from E2 (which probed Nx). Together E2+E3 give a partial picture
of which of (Nx, ν_h) is more sensitive in the pre-validated stack.

ν_h values probed (E1 baseline is 1e-22):
  E3a  ν_h = 1e-18   (prompt-suggested 1e4× stronger HV)
  E3b  ν_h = 1e-26   (1e4× weaker HV — towards essentially no HV)

These are both well inside the explicit-RK4 stability cone at Nx=256:
  ν_h*k_max^16 at ν_h=1e-18: 7.1e4 → stab dt ≲ 4e-5   ← VIOLATED by dt=5e-4
  ν_h*k_max^16 at ν_h=1e-22: 7.1                       (E1, OK)
  ν_h*k_max^16 at ν_h=1e-26: 7.1e-4 → stab dt ≲ 4e3   (OK)

So ν_h=1e-18 with dt=5e-4 ALSO violates the explicit-HV stability bound!
We add E3c, the bug-fix re-run with ν_h=1e-18 at dt=1e-5 to obtain a stable
strong-HV comparison.

Interpretation:
  - E3a expected to blow up (educates on the ν_h/dt coupling).
  - E3b stable. If %-shift vs E1 < 5 % on all diagnostics → ν_h is ROBUST in
    the weak direction (essentially the HV does nothing more at 1e-26 than
    at 1e-22 with this Nx).
  - E3c (rescued strong-HV) stable. %-shift tells us whether AGGRESSIVE HV
    changes the answer beyond the quantitative threshold.
"""

import numpy as np
import os, json, time

OUTDIR = os.path.dirname(os.path.abspath(__file__))
E1_NPZ = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S4/round1/E1_baseline.npz"
T_FINAL  = 10.0
NX       = 256                    # held at baseline
DT_BASE  = 5.0e-4                 # baseline dt

# -----------------------------------------------------------------------------
# Solver (identical to E1, only ν_h and dt vary across sub-runs)
# -----------------------------------------------------------------------------
def make_solver(NX, HYPER):
    L  = 30.0
    x  = np.linspace(-15.0, 15.0, NX, endpoint=False)
    dx = x[1] - x[0]
    k  = 2.0 * np.pi * np.fft.fftfreq(NX, d=L / NX)
    kmax = np.max(np.abs(k))
    ik   = 1j * k
    ik3  = 1j * (k ** 3)
    kcut = (2.0 / 3.0) * kmax
    dealias = (np.abs(k) < kcut).astype(np.float64)
    HYPER_P = 8
    hyper_op = -HYPER * (k ** (2 * HYPER_P))

    def fft(a):  return np.fft.fft(a)
    def ifft(A): return np.real(np.fft.ifft(A))
    def nl_hat(a, b): return dealias * fft(a * b)

    def rhs(u_hat, w_hat, t):
        phase = np.exp(ik3 * t)
        v_hat = phase * w_hat
        u = ifft(u_hat); v = ifft(v_hat)
        u2_h = nl_hat(u, u); v2_h = nl_hat(v, v); uv_h = nl_hat(u, v)
        v_xx_h = (ik ** 2) * v_hat
        u_hat_t = -ik * (1.5 * u2_h + 3.0 * v2_h + v_xx_h) + hyper_op * u_hat
        v_hat_t_nl = -ik * (3.0 * v2_h + uv_h)
        w_hat_t = np.exp(-ik3 * t) * v_hat_t_nl
        return u_hat_t, w_hat_t

    def rk4_step(u_hat, w_hat, t, dt):
        k1a, k1b = rhs(u_hat, w_hat, t)
        k2a, k2b = rhs(u_hat + 0.5*dt*k1a, w_hat + 0.5*dt*k1b, t + 0.5*dt)
        k3a, k3b = rhs(u_hat + 0.5*dt*k2a, w_hat + 0.5*dt*k2b, t + 0.5*dt)
        k4a, k4b = rhs(u_hat + dt*k3a,    w_hat + dt*k3b,    t + dt)
        return (u_hat + dt/6.0*(k1a + 2*k2a + 2*k3a + k4a),
                w_hat + dt/6.0*(k1b + 2*k2b + 2*k3b + k4b))

    return dict(NX=NX, HYPER=HYPER, x=x, dx=dx, k=k, ik=ik, ik3=ik3, kmax=kmax,
                fft=fft, ifft=ifft, rk4_step=rk4_step)

def m_field(u, v): return u - 0.5 * v * v
def lock_corr(u, v):
    a = u - np.mean(u); b = 0.5 * v * v - np.mean(0.5 * v * v)
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    return float('nan') if (na < 1e-12 or nb < 1e-12) else float(np.dot(a, b) / (na * nb))
def spectrum_partition(S, field, k_split=2.0):
    F = np.fft.fft(field) / S["NX"]; P = np.abs(F) ** 2
    mask_low = np.abs(S["k"]) <= k_split
    return float(np.sum(P[mask_low])), float(np.sum(P[~mask_low]))
def cons_estim(S, u, v):
    dx = S["dx"]
    return (float(np.sum(u) * dx), float(np.sum(v) * dx),
            float(np.sqrt(np.sum(u * u) * dx)), float(np.sqrt(np.sum(v * v) * dx)))
def energy_estim(S, u, v):
    v_hat = np.fft.fft(v); v_x = np.real(np.fft.ifft(S["ik"] * v_hat))
    dx = S["dx"]
    return float(0.5 * np.sum(u*u)*dx + 0.5 * np.sum(v*v)*dx + 0.5 * np.sum(v_x*v_x)*dx)

def run(NX, HYPER, DT, tag):
    S = make_solver(NX, HYPER)
    x = S["x"]; ik3 = S["ik3"]; fft = S["fft"]; ifft = S["ifft"]; rk4_step = S["rk4_step"]
    v0 = 1.5 / np.cosh(x + 5.0) ** 2
    u0 = 0.5 * v0 * v0
    print(f"\n-- {tag}: Nx={NX}, dt={DT}, ν_h={HYPER:.3e}")
    print(f"   kmax={S['kmax']:.3f}, ν_h*kmax^16={HYPER*S['kmax']**16:.3e}, "
          f"explicit-RK4 stab dt ≈ {2.0/(HYPER*S['kmax']**16):.2e}")
    u_hat = fft(u0); v_hat = fft(v0); w_hat = v_hat.copy()
    nsteps = int(round(T_FINAL / DT))
    n_diag = 101; diag_stride = max(1, nsteps // (n_diag - 1))
    n_snap = 11;  snap_stride = max(1, nsteps // (n_snap - 1))
    times = [0.0]; m_l2 = [float(np.sqrt(np.sum(m_field(u0,v0)**2)*S["dx"]))]
    m_inf = [float(np.max(np.abs(m_field(u0,v0))))]
    el_u, eh_u, el_v, eh_v = [], [], [], []
    elu, ehu = spectrum_partition(S, u0); el_u.append(elu); eh_u.append(ehu)
    elv, ehv = spectrum_partition(S, v0); el_v.append(elv); eh_v.append(ehv)
    locks = [lock_corr(u0, v0)]
    masses = [cons_estim(S, u0, v0)]
    energies = [energy_estim(S, u0, v0)]
    snaps = [np.stack([u0.copy(), v0.copy()], axis=0)]; snap_times = [0.0]
    t = 0.0; t0 = time.time(); blew_up = False; blow_t = None; blow_step = None
    for step in range(1, nsteps + 1):
        u_hat, w_hat = rk4_step(u_hat, w_hat, t, DT)
        t += DT
        if not np.all(np.isfinite(u_hat)) or not np.all(np.isfinite(w_hat)):
            print(f"   NaN at step {step}, t={t:.4f}")
            blew_up = True; blow_t = t; blow_step = step; break
        if step % diag_stride == 0:
            v_hat_now = np.exp(ik3 * t) * w_hat
            u_now = ifft(u_hat); v_now = ifft(v_hat_now)
            m_now = m_field(u_now, v_now)
            times.append(t)
            m_l2.append(float(np.sqrt(np.sum(m_now**2)*S["dx"])))
            m_inf.append(float(np.max(np.abs(m_now))))
            elu, ehu = spectrum_partition(S, u_now); el_u.append(elu); eh_u.append(ehu)
            elv, ehv = spectrum_partition(S, v_now); el_v.append(elv); eh_v.append(ehv)
            locks.append(lock_corr(u_now, v_now))
            masses.append(cons_estim(S, u_now, v_now))
            energies.append(energy_estim(S, u_now, v_now))
        if step % snap_stride == 0 and len(snaps) < n_snap:
            v_hat_now = np.exp(ik3 * t) * w_hat
            u_now = ifft(u_hat); v_now = ifft(v_hat_now)
            snaps.append(np.stack([u_now.copy(), v_now.copy()], axis=0))
            snap_times.append(t)
    while len(snaps) < n_snap:
        snaps.append(snaps[-1].copy()); snap_times.append(snap_times[-1])
    wall = time.time() - t0
    print(f"   wall={wall:.1f}s, blew_up={blew_up}")
    return dict(tag=tag, NX=NX, HYPER=HYPER, DT=DT,
                wall=wall, blew_up=blew_up, blow_t=blow_t, blow_step=blow_step,
                times=np.array(times), m_l2=np.array(m_l2), m_inf=np.array(m_inf),
                el_u=np.array(el_u), eh_u=np.array(eh_u),
                el_v=np.array(el_v), eh_v=np.array(eh_v),
                lock=np.array(locks), masses=np.array(masses), energies=np.array(energies),
                snaps=np.array(snaps), snap_times=np.array(snap_times),
                x=S["x"], k=S["k"])

print(f"== BKdV-S4 / E3 — vary ν_h at Nx={NX}, dt={DT_BASE}, T={T_FINAL} ==")

# E3a: prompt-suggested 1e4× stronger HV. Predicted to blow up because at
# Nx=256 the explicit-RK4 hyperviscous stability dt ≲ 2/(1e-18 * 26.8^16) ≈
# 2.8e-5, well below dt=5e-4.
res_a = run(NX=NX, HYPER=1.0e-18, DT=DT_BASE, tag="E3a_nu1e-18_dt5e-4")
# E3b: 1e4× weaker HV (almost no HV — explicit stability bound is dt ≲ 2.8e3, fine).
res_b = run(NX=NX, HYPER=1.0e-26, DT=DT_BASE, tag="E3b_nu1e-26_dt5e-4")
# E3c: rescued E3a — drop dt to 1e-5 (inside the strong-HV stability cone).
res_c = run(NX=NX, HYPER=1.0e-18, DT=1.0e-5,  tag="E3c_nu1e-18_dt1e-5_RESCUED")
# E3d: explicit dt-convergence check at baseline (Nx=256, ν_h=1e-22): dt 5e-4 → 1e-4.
# The prompt explicitly flags this as a TRIVIAL-FINDING-EXPECTED case — included so
# the trivial flag is grounded in data rather than just declared.
res_d = run(NX=NX, HYPER=1.0e-22, DT=1.0e-4,  tag="E3d_dt1e-4_at_baseline_TRIVIAL_CHECK")

np.savez(os.path.join(OUTDIR, "E3a_strongHV_naive.npz"),
         **{k_: v for k_, v in res_a.items() if isinstance(v, np.ndarray)})
np.savez(os.path.join(OUTDIR, "E3b_weakHV.npz"),
         **{k_: v for k_, v in res_b.items() if isinstance(v, np.ndarray)})
np.savez(os.path.join(OUTDIR, "E3c_strongHV_rescued.npz"),
         **{k_: v for k_, v in res_c.items() if isinstance(v, np.ndarray)})
np.savez(os.path.join(OUTDIR, "E3d_dt_triv_check.npz"),
         **{k_: v for k_, v in res_d.items() if isinstance(v, np.ndarray)})

# Compare
e1 = np.load(E1_NPZ)
def shift_pct(a, b):
    if not np.isfinite(a) or abs(b) < 1e-14: return float('nan')
    return 100.0 * (a - b) / b

def diag_end(r):
    return {
        "m_l2_T":   float(r["m_l2"][-1]),
        "m_inf_T":  float(r["m_inf"][-1]),
        "lock_T":   float(r["lock"][-1]),
        "L2_u_T":   float(r["masses"][-1][2]),
        "L2_v_T":   float(r["masses"][-1][3]),
        "energy_T": float(r["energies"][-1]),
        "u_peak_T": float(np.max(np.abs(r["snaps"][-1][0]))),
        "v_peak_T": float(np.max(np.abs(r["snaps"][-1][1]))),
        "eh_u_T":   float(r["eh_u"][-1]),
        "eh_v_T":   float(r["eh_v"][-1]),
    }

e1_raw = {k_: e1[k_] for k_ in ["m_l2","m_inf","lock","masses","energies","snaps","eh_u","eh_v"]}
d_e1 = diag_end(e1_raw)
d_a = diag_end(res_a); d_b = diag_end(res_b); d_c = diag_end(res_c); d_d = diag_end(res_d)
shifts_a = {k_: shift_pct(d_a[k_], d_e1[k_]) for k_ in d_e1}
shifts_b = {k_: shift_pct(d_b[k_], d_e1[k_]) for k_ in d_e1}
shifts_c = {k_: shift_pct(d_c[k_], d_e1[k_]) for k_ in d_e1}
shifts_d = {k_: shift_pct(d_d[k_], d_e1[k_]) for k_ in d_e1}

print("\n=== End-state diagnostics (E3 vs E1) ===")
print(f"{'diag':<10s}{'E1':>12s}"
      f"{'E3a HV=1e-18':>16s}{'Δ%':>9s}"
      f"{'E3b HV=1e-26':>16s}{'Δ%':>9s}"
      f"{'E3c rescued':>16s}{'Δ%':>9s}"
      f"{'E3d dt=1e-4':>16s}{'Δ%':>9s}")
for k_ in d_e1:
    print(f"{k_:<10s}{d_e1[k_]:>12.4g}"
          f"{d_a[k_]:>16.4g}{shifts_a[k_]:>+9.2f}"
          f"{d_b[k_]:>16.4g}{shifts_b[k_]:>+9.2f}"
          f"{d_c[k_]:>16.4g}{shifts_c[k_]:>+9.2f}"
          f"{d_d[k_]:>16.4g}{shifts_d[k_]:>+9.2f}")

summary = {
    "tag": "E3_HV_sweep",
    "compared_to": "E1_baseline (Nx=256, dt=5e-4, ν_h=1e-22)",
    "params_common": {"Nx": NX, "T_final": T_FINAL},
    "E1_end": d_e1,
    "E3a_strongHV_naive": {
        "ν_h": 1.0e-18, "dt": DT_BASE,
        "blew_up": bool(res_a["blew_up"]),
        "blow_t": res_a["blow_t"], "blow_step": res_a["blow_step"],
        "interpretation": "1e4× larger ν_h at fixed dt=5e-4 also violates the explicit-HV stability bound (≈ 2.8e-5 at this ν_h). Ν_h-only change is INADMISSIBLE in the strong direction.",
        "end": d_a, "pct_shift_vs_E1": shifts_a,
    },
    "E3b_weakHV": {
        "ν_h": 1.0e-26, "dt": DT_BASE,
        "blew_up": bool(res_b["blew_up"]),
        "interpretation": "Weakening HV by 1e4× at the same (Nx,dt). Probes whether the HV regularization itself shapes the answer at Nx=256.",
        "end": d_b, "pct_shift_vs_E1": shifts_b,
        "max_abs_shift_pct_finite": float(max(abs(s) for s in shifts_b.values() if np.isfinite(s)))
        if any(np.isfinite(s) for s in shifts_b.values()) else None,
    },
    "E3c_strongHV_rescued": {
        "ν_h": 1.0e-18, "dt": 1.0e-5,
        "blew_up": bool(res_c["blew_up"]),
        "interpretation": "Stable strong-HV comparison (dt below the HV stability bound). Tests the physics effect of ν_h being 1e4× stronger.",
        "end": d_c, "pct_shift_vs_E1": shifts_c,
        "max_abs_shift_pct_finite": float(max(abs(s) for s in shifts_c.values() if np.isfinite(s)))
        if any(np.isfinite(s) for s in shifts_c.values()) else None,
    },
    "E3d_dt_trivial_check": {
        "ν_h": 1.0e-22, "dt": 1.0e-4,
        "blew_up": bool(res_d["blew_up"]),
        "interpretation": "TRIVIAL-FINDING check: dt 5e-4 → 1e-4 at baseline. Anticipated to give essentially no shift, as the prompt explicitly flags. Reported here to GROUND the trivial flag in data rather than declare it.",
        "end": d_d, "pct_shift_vs_E1": shifts_d,
        "max_abs_shift_pct_finite": float(max(abs(s) for s in shifts_d.values() if np.isfinite(s)))
        if any(np.isfinite(s) for s in shifts_d.values()) else None,
    },
    "stability_note": ("Explicit-RK4 HV stability bound: dt ≲ 2/(ν_h k_max^16). At Nx=256: ν_h=1e-18 → bound ≈ 2.8e-5 (dt=5e-4 violates); ν_h=1e-22 → bound ≈ 0.28 (dt=5e-4 fine); ν_h=1e-26 → bound ≈ 2.8e3 (dt=5e-4 trivially fine)."),
}
print("\nE3 summary:")
print(json.dumps(summary, indent=2))
with open(os.path.join(OUTDIR, "E3_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print(f"saved {os.path.join(OUTDIR, 'E3_summary.json')}")
