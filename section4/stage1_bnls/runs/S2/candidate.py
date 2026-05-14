"""
S2: NLS focusing — direct (N, phi) vs Madelung-Psi methods comparison.

Bright sech soliton IC (same as S1):
    Psi(x,0) = sqrt(2) * sech(sqrt(2)*(x+5)) * exp(i*0.25*x)
    => N(x,0) = 2 * sech^2(sqrt(2)*(x+5))
    => phi(x,0) = 0.25 * x
Final time T = 4.0, domain x in [-15, 15], Nx = 256, kappa = +1 (focusing).
Ground truth: bright soliton translates at speed v = 0.25 with shape preserved;
exact mass M = integral N dx = 2*sqrt(2).

This script consolidates THREE experiments:
  E1: Madelung-Psi split-step Fourier (gold-standard reference).
  E2: Direct (N, phi) RK4 spectral with HARD-FLOOR regularization
      sqrt(max(N, eps)) at eps in {0, 1e-12, 1e-6, 1e-3}.
  E3: Direct (N, phi) RK4 spectral with SMOOTH regularization
      sqrt(N + eps) at eps in {1e-6, 1e-3, 1e-1}, with and without
      2/3-rule dealiasing.

The final candidate.py is this file because it produces the full S2.npz
output (snapshots + diagnostics) needed for downstream analysis.

Diagnostics: mass_drift, min_N, max|Q|, blowup step/time, peak amplitude
and position at t=T, and where direct results deviate from Madelung.
"""

import os
import time
import numpy as np

# -----------------------
# Problem setup
# -----------------------
L = 30.0
xmin, xmax = -15.0, 15.0
Nx = 256
dx = (xmax - xmin) / Nx
x = xmin + dx * np.arange(Nx)
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k * k

# 2/3-rule dealiasing mask
kmax = np.max(np.abs(k))
dealias_mask = (np.abs(k) <= (2.0 / 3.0) * kmax).astype(float)

kappa = 1.0
T_final = 4.0
dt = 0.001
n_steps = int(round(T_final / dt))
sample_every = max(1, n_steps // 200)

amp = np.sqrt(2.0)
def initial_Psi(x):
    return amp * (1.0 / np.cosh(np.sqrt(2.0) * (x + 5.0))) * np.exp(1j * 0.25 * x)

Psi0 = initial_Psi(x)
N0 = np.abs(Psi0) ** 2
phi0 = np.angle(Psi0)
M_exact = 2.0 * np.sqrt(2.0)

print(f"=== S2: NLS focusing direct (N,phi) vs Madelung-Psi ===")
print(f"Nx={Nx}, dx={dx:.4e}, dt={dt}, T={T_final}, n_steps={n_steps}")
print(f"Initial mass (numerical): {np.sum(N0) * dx:.10f}")
print(f"Initial mass (exact):     {M_exact:.10f}")
print(f"max N0 = {np.max(N0):.6f}, min N0 = {np.min(N0):.6e}")
print()


# -----------------------
# Method A: Madelung-Psi split-step Fourier
# -----------------------
def run_madelung(Psi_init, dt, n_steps, sample_every):
    Psi = Psi_init.copy()
    half_lin = np.exp(-1j * (k2 / 2.0) * (dt / 2.0))

    masses, min_Ns, times = [], [], []
    snapshots_N, snapshots_phi = [], []

    t = 0.0
    for step in range(n_steps + 1):
        N_cur = np.abs(Psi) ** 2
        masses.append(np.sum(N_cur) * dx)
        min_Ns.append(float(np.min(N_cur)))
        times.append(t)
        if step % sample_every == 0:
            snapshots_N.append(N_cur.copy())
            snapshots_phi.append(np.angle(Psi).copy())
        if step == n_steps:
            break
        Psi_hat = np.fft.fft(Psi); Psi_hat *= half_lin
        Psi = np.fft.ifft(Psi_hat)
        Psi = Psi * np.exp(1j * kappa * (np.abs(Psi) ** 2) * dt)
        Psi_hat = np.fft.fft(Psi); Psi_hat *= half_lin
        Psi = np.fft.ifft(Psi_hat)
        t += dt
        if not np.all(np.isfinite(Psi)):
            print(f"  Madelung NaN at step {step}, t={t}")
            break

    return {
        "Psi_final": Psi,
        "N_final": np.abs(Psi) ** 2,
        "phi_final": np.angle(Psi),
        "masses": np.array(masses),
        "min_Ns": np.array(min_Ns),
        "times": np.array(times),
        "snapshots_N": np.array(snapshots_N),
        "snapshots_phi": np.array(snapshots_phi),
    }


# -----------------------
# Method B: direct (N, phi) spectral FFT, RK4
# -----------------------
def make_rhs(reg_type, eps, dealias):
    """Build a RHS closure with regularization choices baked in.

    reg_type: "hard" -> Nsafe = max(N, eps); "soft" -> Nsafe = N + eps.
    dealias: apply 2/3-rule mask to fourier products.
    """
    def rhs(N, phi):
        phi_hat = np.fft.fft(phi)
        if dealias:
            phi_hat = phi_hat * dealias_mask
        phi_x = np.real(np.fft.ifft(ik * phi_hat))

        flux = phi_x * N
        flux_hat = np.fft.fft(flux)
        if dealias:
            flux_hat = flux_hat * dealias_mask
        dflux_dx = np.real(np.fft.ifft(ik * flux_hat))

        if reg_type == "hard":
            if eps == 0.0:
                Nsafe = np.maximum(N, 0.0)
            else:
                Nsafe = np.maximum(N, eps)
        else:  # soft
            Nsafe = N + eps  # may be <0 only if N very negative; allow.
            Nsafe = np.where(Nsafe > 0, Nsafe, eps)

        sqrtN = np.sqrt(Nsafe)
        sqrtN_hat = np.fft.fft(sqrtN)
        if dealias:
            sqrtN_hat = sqrtN_hat * dealias_mask
        sqrtN_xx = np.real(np.fft.ifft(-k2 * sqrtN_hat))
        with np.errstate(divide="ignore", invalid="ignore"):
            Q = sqrtN_xx / (2.0 * sqrtN)
            Q = np.where(sqrtN > 1e-300, Q, 0.0)

        dN_dt = -dflux_dx
        dphi_dt = -0.5 * phi_x * phi_x - Q + 2.0 * kappa * N
        return dN_dt, dphi_dt, Q
    return rhs


def run_direct(N_init, phi_init, dt, n_steps, sample_every, rhs):
    N = N_init.copy()
    phi = phi_init.copy()
    masses, min_Ns, qmax_history, times = [], [], [], []
    snapshots_N, snapshots_phi = [], []
    t = 0.0
    blew_up = False
    blowup_step = -1
    blowup_reason = ""
    for step in range(n_steps + 1):
        masses.append(np.sum(N) * dx)
        min_Ns.append(float(np.min(N)))
        _, _, Q_diag = rhs(N, phi)
        qmax_history.append(float(np.max(np.abs(Q_diag))))
        times.append(t)
        if step % sample_every == 0:
            snapshots_N.append(N.copy())
            snapshots_phi.append(phi.copy())
        if (not np.all(np.isfinite(N))) or (not np.all(np.isfinite(phi))):
            blew_up = True; blowup_step = step; blowup_reason = "NaN/Inf"; break
        if np.max(np.abs(N)) > 1e6:
            blew_up = True; blowup_step = step
            blowup_reason = f"|N| > 1e6 (max={np.max(np.abs(N)):.3e})"
            break
        if step == n_steps:
            break
        k1N, k1p, _ = rhs(N, phi)
        k2N, k2p, _ = rhs(N + 0.5 * dt * k1N, phi + 0.5 * dt * k1p)
        k3N, k3p, _ = rhs(N + 0.5 * dt * k2N, phi + 0.5 * dt * k2p)
        k4N, k4p, _ = rhs(N + dt * k3N, phi + dt * k3p)
        N = N + (dt / 6.0) * (k1N + 2 * k2N + 2 * k3N + k4N)
        phi = phi + (dt / 6.0) * (k1p + 2 * k2p + 2 * k3p + k4p)
        t += dt
    return {
        "N_final": N, "phi_final": phi,
        "masses": np.array(masses), "min_Ns": np.array(min_Ns),
        "qmax_history": np.array(qmax_history), "times": np.array(times),
        "snapshots_N": np.array(snapshots_N), "snapshots_phi": np.array(snapshots_phi),
        "blew_up": blew_up, "blowup_step": blowup_step, "blowup_reason": blowup_reason,
    }


# -----------------------
# Run Method A
# -----------------------
print("--- Method A: Madelung-Psi split-step Fourier (reference) ---")
t0 = time.time()
resA = run_madelung(Psi0, dt, n_steps, sample_every)
print(f"  wall time: {time.time() - t0:.2f}s")
mA_drift = (resA["masses"][-1] - resA["masses"][0]) / resA["masses"][0]
print(f"  final mass: {resA['masses'][-1]:.12f}")
print(f"  mass drift vs initial: {mA_drift:.3e}")
print(f"  mass drift vs exact:   {(resA['masses'][-1] - M_exact) / M_exact:.3e}")
print(f"  min N over run:        {np.min(resA['min_Ns']):.3e}")
print(f"  max N final:           {np.max(resA['N_final']):.6f}")
peak_idx_A = int(np.argmax(resA["N_final"]))
print(f"  peak position final:   x = {x[peak_idx_A]:.4f} (expected -4)")
print()

n_snap_max = len(resA["snapshots_N"])
snapshot_times = np.array([i * sample_every * dt for i in range(n_snap_max)])

# -----------------------
# Run Method B variants
# -----------------------
variants = [
    {"tag": "hard_eps0",      "reg": "hard", "eps": 0.0,    "dealias": False},
    {"tag": "hard_eps1em12",  "reg": "hard", "eps": 1e-12,  "dealias": False},
    {"tag": "hard_eps1em6",   "reg": "hard", "eps": 1e-6,   "dealias": False},
    {"tag": "hard_eps1em3",   "reg": "hard", "eps": 1e-3,   "dealias": False},
    {"tag": "soft_eps1em6",   "reg": "soft", "eps": 1e-6,   "dealias": False},
    {"tag": "soft_eps1em3",   "reg": "soft", "eps": 1e-3,   "dealias": False},
    {"tag": "soft_eps1em1",   "reg": "soft", "eps": 1e-1,   "dealias": False},
    {"tag": "soft_eps1em3_dealias", "reg": "soft", "eps": 1e-3, "dealias": True},
]

resB_all = {}
for v in variants:
    label = f"reg={v['reg']}, eps={v['eps']:g}, dealias={v['dealias']}"
    print(f"--- Method B: {label} ---")
    rhs = make_rhs(v["reg"], v["eps"], v["dealias"])
    t0 = time.time()
    resB = run_direct(N0, phi0, dt, n_steps, sample_every, rhs)
    print(f"  wall time: {time.time() - t0:.2f}s")
    if resB["blew_up"]:
        bt = resB["times"][resB["blowup_step"]]
        print(f"  *** BLEW UP *** at step {resB['blowup_step']}, t={bt:.4f}: {resB['blowup_reason']}")
    final_mass = resB["masses"][-1] if not resB["blew_up"] else resB["masses"][max(0, resB["blowup_step"] - 1)]
    mB_drift = (final_mass - resB["masses"][0]) / resB["masses"][0]
    print(f"  final/last-good mass:  {final_mass:.12f}")
    print(f"  mass drift vs init:    {mB_drift:.3e}")
    print(f"  min N over run:        {np.min(resB['min_Ns']):.3e}")
    print(f"  max |Q| over run:      {np.max(resB['qmax_history']):.3e}")
    if (not resB["blew_up"]) and np.all(np.isfinite(resB["N_final"])):
        peak_idx_B = int(np.argmax(resB["N_final"]))
        print(f"  max N final:           {np.max(resB['N_final']):.6f}")
        print(f"  peak position final:   x = {x[peak_idx_B]:.4f}")

    n_snap_B = len(resB["snapshots_N"])
    n_snap = min(n_snap_max, n_snap_B)
    where_fails_first = -1.0
    max_diff = 0.0
    last_finite_diff = 0.0
    for i in range(n_snap):
        d = np.max(np.abs(resA["snapshots_N"][i] - resB["snapshots_N"][i]))
        if np.isfinite(d):
            max_diff = max(max_diff, d)
            last_finite_diff = d
        if ((not np.isfinite(d)) or d > 0.1) and where_fails_first < 0:
            where_fails_first = snapshot_times[i]
    print(f"  where deviates>0.1 from Madelung: t = {where_fails_first}")
    print(f"  max diff vs Madelung (finite): {max_diff:.3e}")
    print()
    resB_all[v["tag"]] = {
        **resB,
        "variant": v,
        "mass_drift": mB_drift,
        "where_fails_first": where_fails_first,
        "max_diff_vs_madelung": max_diff,
    }

# -----------------------
# Save results
# -----------------------
os.makedirs("pred_results", exist_ok=True)
save_kwargs = dict(
    x=x,
    t_A=resA["times"],
    snapshot_times=snapshot_times,
    N_init=N0,
    phi_init=phi0,
    # method A
    N_madelung=resA["N_final"],
    phi_madelung=resA["phi_final"],
    masses_madelung=resA["masses"],
    minN_madelung=resA["min_Ns"],
    snapshots_N_madelung=resA["snapshots_N"],
    snapshots_phi_madelung=resA["snapshots_phi"],
    M_exact=M_exact,
    dt=dt,
    Nx=Nx,
    kappa=kappa,
    T_final=T_final,
)
for tag, r in resB_all.items():
    save_kwargs[f"masses_direct_{tag}"] = r["masses"]
    save_kwargs[f"minN_direct_{tag}"] = r["min_Ns"]
    save_kwargs[f"qmax_direct_{tag}"] = r["qmax_history"]
    save_kwargs[f"snapshots_N_direct_{tag}"] = r["snapshots_N"]
    save_kwargs[f"snapshots_phi_direct_{tag}"] = r["snapshots_phi"]
    save_kwargs[f"N_final_direct_{tag}"] = r["N_final"]
    save_kwargs[f"phi_final_direct_{tag}"] = r["phi_final"]
    save_kwargs[f"blew_up_{tag}"] = int(r["blew_up"])
    save_kwargs[f"blowup_step_{tag}"] = r["blowup_step"]
    save_kwargs[f"where_fails_first_{tag}"] = float(r["where_fails_first"])
np.savez("pred_results/S2.npz", **save_kwargs)
print("Saved pred_results/S2.npz")

# -----------------------
# Concise summary
# -----------------------
print()
print("=== SUMMARY ===")
print(f"mass_drift_madelung    = {mA_drift:.3e}  (over T={T_final})")
print(f"min_N_madelung         = {np.min(resA['min_Ns']):.3e}")
print()
print(f"{'variant':<28} {'blew_up':<8} {'b.step':<7} {'qmax':<10} {'mass_drift':<12} {'minN':<11} {'where_fails':<10}")
for tag, r in resB_all.items():
    print(f"{tag:<28} "
          f"{str(r['blew_up']):<8} "
          f"{r['blowup_step']:<7} "
          f"{np.max(r['qmax_history']):<10.2e} "
          f"{r['mass_drift']:<12.2e} "
          f"{np.min(r['min_Ns']):<11.2e} "
          f"{r['where_fails_first']:<10}")
