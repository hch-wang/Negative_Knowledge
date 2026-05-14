"""
E3 — Robustness/falsification test of the working hypothesis H_BALANCE

Background from E1+E2
=====================
* E1 falsified H_A (Gardner-manifold m=0 attraction): ||m|| GREW from 0.06 to 1.20
  even for an on-manifold IC. The asymptotic ||m|| does NOT depend on whether the
  IC was on or off the Gardner manifold.
* E2 showed BOTH the Burgers self-flux 3 u u_x and the KdV dispersion v_xxx are
  essential: removing v_xxx -> blow-up, removing 3 u u_x -> uncontrolled growth.

H_BALANCE (working hypothesis): compound coherent states are the basin attractor
because of a cooperative balance between (a) u's Burgers self-advection (which
transports/dissipates v^2-forced amplitude through fronts and absorbs energy via
hyperviscous tail) and (b) v's KdV dispersion (which radiates high-k content
away from v). Neither alone produces the attractor; together they do.

E3 design
=========
Two goals (one ablation, multiple ICs, on a single round to maximize information).

(1) ROBUSTNESS: run M0 (full BKdV) with FOUR distinct ICs and check whether
    the late-time observable (||m||_L2, L2_u, L2_v, lock) is the same up to IC.
    H_BALANCE predicts a 1-parameter family (parameterized by total v-mass) of
    asymptotic states; with the same v-mass, two ICs should converge to similar
    L2_u, L2_v.

    IC_C : random noise on u; v = clean sech^2 same envelope, same v-mass.
    IC_D : double-bump in v (two separated v sech^2 pulses); flat u.
    IC_E : tall narrow v; flat u (different amplitude regime).
    IC_F : same as IC_B from E1 (baseline) but with hyperviscosity coefficient
           multiplied by 100. If the answer changes much, the attractor was an
           artifact of hyperviscosity (H_BALANCE WEAKENED — this is the falsifier).

(2) FALSIFICATION FOCUS: compare IC_F (high-hyperviscosity) to IC_B baseline.
    If the late-time ||m||_L2 / L2_u / L2_v differ by more than ~10%, the result
    of E1+E2 was hyperviscosity-driven, NOT physics.

Outputs: same diagnostics suite; we also save full snapshots so we can visualise
spatial structures and check whether they are genuine compound solitons (single
moving peaks with locked u-component).
"""

import numpy as np
import os, json, time

# -----------------------------------------------------------------------------
# Spatial grid
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

# Hyperviscosity (param sweepable)
HYPER_P = 8
def hyper_op(coef):
    return -coef * (k ** (2 * HYPER_P))

def fft(a): return np.fft.fft(a)
def ifft(A): return np.real(np.fft.ifft(A))
def nl_hat(a, b): return dealias * fft(a * b)

def rhs_full(u_hat, w_hat, t, hyper):
    phase = np.exp(ik3 * t)
    v_hat = phase * w_hat
    u = ifft(u_hat); v = ifft(v_hat)
    u2_h = nl_hat(u, u); v2_h = nl_hat(v, v); uv_h = nl_hat(u, v)
    v_xx_h = (ik ** 2) * v_hat
    u_hat_t = -ik * (1.5 * u2_h + 3.0 * v2_h + v_xx_h) + hyper * u_hat
    v_hat_t_nl = -ik * (3.0 * v2_h + uv_h)
    w_hat_t = np.exp(-ik3 * t) * v_hat_t_nl
    return u_hat_t, w_hat_t

def rk4_step(rhs_fn, u_hat, w_hat, t, dt, hyper):
    k1a, k1b = rhs_fn(u_hat, w_hat, t, hyper)
    k2a, k2b = rhs_fn(u_hat + 0.5 * dt * k1a, w_hat + 0.5 * dt * k1b, t + 0.5 * dt, hyper)
    k3a, k3b = rhs_fn(u_hat + 0.5 * dt * k2a, w_hat + 0.5 * dt * k2b, t + 0.5 * dt, hyper)
    k4a, k4b = rhs_fn(u_hat + dt * k3a,       w_hat + dt * k3b,       t + dt, hyper)
    return (u_hat + dt / 6.0 * (k1a + 2.0 * k2a + 2.0 * k3a + k4a),
            w_hat + dt / 6.0 * (k1b + 2.0 * k2b + 2.0 * k3b + k4b))

def m_field(u, v): return u - 0.5 * v * v

def spectrum_partition(field, k_split=2.0):
    F = np.fft.fft(field) / Nx
    P = np.abs(F) ** 2
    mask_low = np.abs(k) <= k_split
    return float(np.sum(P[mask_low])), float(np.sum(P[~mask_low]))

def lock_corr(u, v):
    a = u - np.mean(u); b = 0.5 * v * v - np.mean(0.5 * v * v)
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    return float('nan') if (na < 1e-12 or nb < 1e-12) else float(np.dot(a, b) / (na * nb))

def cons_estim(u, v):
    return (np.sum(u) * dx, np.sum(v) * dx,
            np.sqrt(np.sum(u * u) * dx), np.sqrt(np.sum(v * v) * dx))

def integrate(u0, v0, T, dt, tag, hyper_coef):
    hyper = hyper_op(hyper_coef)
    u_hat = fft(u0); v_hat = fft(v0)
    w_hat = v_hat.copy()
    nsteps = int(round(T / dt))
    n_diag = 81; diag_stride = max(1, nsteps // (n_diag - 1))
    n_snap = 21; snap_stride = max(1, nsteps // (n_snap - 1))

    times = [0.0]
    m_l2 = [float(np.sqrt(np.sum(m_field(u0, v0) ** 2) * dx))]
    m_inf = [float(np.max(np.abs(m_field(u0, v0))))]
    el_u, eh_u, el_v, eh_v = [], [], [], []
    elu, ehu = spectrum_partition(u0); el_u.append(elu); eh_u.append(ehu)
    elv, ehv = spectrum_partition(v0); el_v.append(elv); eh_v.append(ehv)
    locks = [lock_corr(u0, v0)]
    masses = [cons_estim(u0, v0)]
    snaps = [np.stack([u0.copy(), v0.copy()], axis=0)]
    snap_times = [0.0]

    t = 0.0; blew_up = False
    for step in range(1, nsteps + 1):
        u_hat, w_hat = rk4_step(rhs_full, u_hat, w_hat, t, dt, hyper)
        t += dt
        if not np.all(np.isfinite(u_hat)) or not np.all(np.isfinite(w_hat)):
            print(f"[{tag}] NaN at step {step}, t={t:.4f}")
            blew_up = True; break
        if step % diag_stride == 0:
            v_hat_now = np.exp(ik3 * t) * w_hat
            u_now = ifft(u_hat); v_now = ifft(v_hat_now)
            m_now = m_field(u_now, v_now)
            times.append(t)
            m_l2.append(float(np.sqrt(np.sum(m_now ** 2) * dx)))
            m_inf.append(float(np.max(np.abs(m_now))))
            elu, ehu = spectrum_partition(u_now); el_u.append(elu); eh_u.append(ehu)
            elv, ehv = spectrum_partition(v_now); el_v.append(elv); eh_v.append(ehv)
            locks.append(lock_corr(u_now, v_now))
            masses.append(cons_estim(u_now, v_now))
        if step % snap_stride == 0 and len(snaps) < n_snap:
            v_hat_now = np.exp(ik3 * t) * w_hat
            u_now = ifft(u_hat); v_now = ifft(v_hat_now)
            snaps.append(np.stack([u_now.copy(), v_now.copy()], axis=0))
            snap_times.append(t)
    while len(snaps) < n_snap:
        snaps.append(snaps[-1].copy())
    return {
        "tag": tag, "T": T, "dt": dt,
        "times": np.array(times),
        "m_l2": np.array(m_l2), "m_inf": np.array(m_inf),
        "el_u": np.array(el_u), "eh_u": np.array(eh_u),
        "el_v": np.array(el_v), "eh_v": np.array(eh_v),
        "lock": np.array(locks),
        "masses": np.array(masses),
        "snaps": np.array(snaps), "snap_times": np.array(snap_times),
        "blew_up": blew_up, "hyper": hyper_coef,
    }

# -----------------------------------------------------------------------------
# Four initial conditions, each with v-mass adjusted to be the same (=1.6) so we
# can ask whether ASYMPTOTIC L2_u / L2_v depend on initial L2 partition alone.
# -----------------------------------------------------------------------------
rng = np.random.default_rng(7)

# IC_C : noisy u + clean sech^2 v
v0_C = 0.8 / np.cosh(x + 5.0) ** 2
u0_C = 0.15 * rng.standard_normal(Nx)  # zero-mean noise, modest amplitude

# IC_D : two-pulse v + flat u
v0_D = 0.6 / np.cosh((x + 7.0)) ** 2 + 0.5 / np.cosh((x - 1.0)) ** 2
# rescale v0_D so mass_v = 1.6
v0_D = v0_D * (1.6 / (np.sum(v0_D) * dx))
u0_D = np.zeros_like(x)

# IC_E : tall narrow v
v0_E = 1.6 / np.cosh((x + 3.0) * 1.5) ** 2
v0_E = v0_E * (1.6 / (np.sum(v0_E) * dx))
u0_E = np.zeros_like(x)

# IC_F : same as the E1 IC_B baseline, but with 100x hyperviscosity
v0_F = 0.8 / np.cosh(x + 5.0) ** 2
u0_F = 0.3 * np.exp(-((x + 5.0) / 2.0) ** 2) - 0.2 * np.exp(-((x - 3.0) / 3.0) ** 2)

print(f"IC_C v-mass={np.sum(v0_C)*dx:.4f},  u-mass={np.sum(u0_C)*dx:.4f},  L2_v={np.sqrt(np.sum(v0_C**2)*dx):.4f}")
print(f"IC_D v-mass={np.sum(v0_D)*dx:.4f},  u-mass={np.sum(u0_D)*dx:.4f},  L2_v={np.sqrt(np.sum(v0_D**2)*dx):.4f}")
print(f"IC_E v-mass={np.sum(v0_E)*dx:.4f},  u-mass={np.sum(u0_E)*dx:.4f},  L2_v={np.sqrt(np.sum(v0_E**2)*dx):.4f}")
print(f"IC_F v-mass={np.sum(v0_F)*dx:.4f},  u-mass={np.sum(u0_F)*dx:.4f},  L2_v={np.sqrt(np.sum(v0_F**2)*dx):.4f}")

T_FINAL = 20.0
DT = 5e-4

# baseline hyperviscosity (E1+E2 used 1e-22)
HYPER_BASE = 1.0e-22
HYPER_HIGH = 1.0e-20    # 100x larger

t0 = time.time()
print("\n=== IC_C  noisy u, clean v ===")
res_C = integrate(u0_C, v0_C, T_FINAL, DT, "C_noiseU", HYPER_BASE)
print(f"  done in {time.time()-t0:.1f}s")

t1 = time.time()
print("\n=== IC_D  two-pulse v ===")
res_D = integrate(u0_D, v0_D, T_FINAL, DT, "D_twoV", HYPER_BASE)
print(f"  done in {time.time()-t1:.1f}s")

t2 = time.time()
print("\n=== IC_E  tall narrow v ===")
res_E = integrate(u0_E, v0_E, T_FINAL, DT, "E_tallV", HYPER_BASE)
print(f"  done in {time.time()-t2:.1f}s")

t3 = time.time()
print("\n=== IC_F  E1 baseline with HIGHER hyperviscosity (100x) ===")
res_F = integrate(u0_F, v0_F, T_FINAL, DT, "F_highHV", HYPER_HIGH)
print(f"  done in {time.time()-t3:.1f}s")

os.makedirs("pred_results", exist_ok=True)
os.makedirs("evidence", exist_ok=True)
for res in (res_C, res_D, res_E, res_F):
    np.savez(
        f"pred_results/E3_{res['tag']}.npz",
        times=res["times"],
        m_l2=res["m_l2"], m_inf=res["m_inf"],
        el_u=res["el_u"], eh_u=res["eh_u"],
        el_v=res["el_v"], eh_v=res["eh_v"],
        lock=res["lock"],
        masses=res["masses"],
        snaps=res["snaps"], snap_times=res["snap_times"],
        x=x, k=k, hyper=res["hyper"],
    )

def summarize(res):
    print(f"\n--- {res['tag']} (hyper={res['hyper']:.2e}, blew_up={res['blew_up']}) ---")
    t = res["times"]
    print(f"  T_end={t[-1]:.3f},  Npts={len(t)}")
    print(f"  ||m||_L2:   t=0 -> {res['m_l2'][0]:.4f}, t_end -> {res['m_l2'][-1]:.4f}")
    print(f"  ||m||_inf:  t=0 -> {res['m_inf'][0]:.4f}, t_end -> {res['m_inf'][-1]:.4f}")
    print(f"  lock:       t=0 -> {res['lock'][0]:.3f}, t_end -> {res['lock'][-1]:.3f}")
    m0 = res["masses"][0]; mF = res["masses"][-1]
    print(f"  mass_u: {m0[0]:.4f} -> {mF[0]:.4f}")
    print(f"  mass_v: {m0[1]:.4f} -> {mF[1]:.4f}")
    print(f"  L2_u  : {m0[2]:.4f} -> {mF[2]:.4f}")
    print(f"  L2_v  : {m0[3]:.4f} -> {mF[3]:.4f}")

summarize(res_C); summarize(res_D); summarize(res_E); summarize(res_F)

out = {
    "round": 3,
    "T": T_FINAL, "dt": DT, "Nx": Nx,
    "ICs": {
        "C": {"m_l2_T": float(res_C["m_l2"][-1]), "lock_T": float(res_C["lock"][-1]),
              "L2_u_T": float(res_C["masses"][-1][2]), "L2_v_T": float(res_C["masses"][-1][3]),
              "blew_up": res_C["blew_up"]},
        "D": {"m_l2_T": float(res_D["m_l2"][-1]), "lock_T": float(res_D["lock"][-1]),
              "L2_u_T": float(res_D["masses"][-1][2]), "L2_v_T": float(res_D["masses"][-1][3]),
              "blew_up": res_D["blew_up"]},
        "E": {"m_l2_T": float(res_E["m_l2"][-1]), "lock_T": float(res_E["lock"][-1]),
              "L2_u_T": float(res_E["masses"][-1][2]), "L2_v_T": float(res_E["masses"][-1][3]),
              "blew_up": res_E["blew_up"]},
        "F_highHV": {"m_l2_T": float(res_F["m_l2"][-1]), "lock_T": float(res_F["lock"][-1]),
              "L2_u_T": float(res_F["masses"][-1][2]), "L2_v_T": float(res_F["masses"][-1][3]),
              "blew_up": res_F["blew_up"], "hyper": HYPER_HIGH},
    }
}
with open("evidence/E3_summary.json", "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved evidence/E3_summary.json")
