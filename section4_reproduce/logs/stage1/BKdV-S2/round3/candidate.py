"""
BKdV-S2 Round 3 (E3): numerical-artifact control.

Goal: confirm which of the observed (non-)conservations are physical vs
numerical.  Vary the discretization, keep IC and physics identical to E1.

We run three configurations with the SAME IC (E1's soliton: v0=1.5sech^2(x+5),
u0=0) up to T=5:
  Config A : dt=5e-4,    Nx=256   (5x larger dt than baseline)
  Config B : dt=1e-4,    Nx=256   (5x smaller dt than baseline)
  Config C : dt=2.5e-4,  Nx=512   (2x finer grid)

Compare drift of each candidate quantity across configurations.  A drift
that scales with dt/Nx is a numerical artifact; an IC-invariant drift that
is *independent* of dt/Nx is physical non-conservation; a quantity whose
drift goes to machine zero under all configurations is structurally
conserved.

T = 5 (long enough to see C3/C4/C5 dynamics from E1, short enough that
3 configs run cheaply).
"""
import os, sys, time
import numpy as np

def run_config(Nx, dt, T, label):
    L  = 30.0
    dx = L / Nx
    x  = -15.0 + dx * np.arange(Nx)

    k   = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
    ik  = 1j * k

    kmax    = np.max(np.abs(k))
    mask_23 = (np.abs(k) <= (2.0/3.0) * kmax).astype(float)

    def fft(a):  return np.fft.fft(a)
    def ifft(A): return np.real(np.fft.ifft(A))

    def dx_real(a):  return ifft(ik * fft(a))
    def dxx_real(a): return ifft(-(k**2) * fft(a))
    def dealias_product(a, b):
        return ifft(fft(a * b) * mask_23)

    def N_u(u, v):
        u2     = dealias_product(u, u)
        v2     = dealias_product(v, v)
        v_xx   = dxx_real(v)
        d_u2   = ifft(ik * fft(u2))
        d_v2   = ifft(ik * fft(v2))
        d_vxx  = ifft(ik * fft(v_xx))
        return -1.5 * d_u2 - 3.0 * d_v2 - d_vxx

    def N_v(u, v):
        v2     = dealias_product(v, v)
        uv     = dealias_product(u, v)
        d_v2   = ifft(ik * fft(v2))
        d_uv   = ifft(ik * fft(uv))
        return -3.0 * d_v2 - d_uv

    L_op  = 1j * (k ** 3)

    def step(u, v):
        denom = 1.0 - 0.5 * dt * L_op
        num   = 1.0 + 0.5 * dt * L_op
        denom_h = 1.0 - 0.25 * dt * L_op
        num_h   = 1.0 + 0.25 * dt * L_op

        Nu0 = N_u(u, v)
        Nv0 = N_v(u, v)
        u_h = u + 0.5 * dt * Nu0
        v_hat = np.fft.fft(v)
        v_hat_h = (num_h * v_hat + 0.5 * dt * np.fft.fft(Nv0)) / denom_h
        v_h = ifft(v_hat_h)

        Nu1 = N_u(u_h, v_h)
        Nv1 = N_v(u_h, v_h)
        u_new = u + dt * Nu1
        v_hat_new = (num * v_hat + dt * np.fft.fft(Nv1)) / denom
        v_new = ifft(v_hat_new)
        return u_new, v_new

    def diag(u, v):
        v_x = dx_real(v)
        m   = u - 0.5 * v * v
        C1  = np.sum(u) * dx
        C2  = np.sum(v) * dx
        C3  = np.sum(u * v) * dx
        C4  = 0.5 * np.sum(u * u + v * v + v_x * v_x) * dx
        C5  = np.sum(m * m) * dx
        return (C1, C2, C3, C4, C5)

    # E1 IC, possibly remapped to finer grid
    v0 = 1.5 * (1.0 / np.cosh(x + 5.0)) ** 2
    u0 = np.zeros_like(v0)
    u, v = u0.copy(), v0.copy()

    nsteps = int(round(T / dt))
    sample_every = max(1, nsteps // 100)
    init = diag(u, v)
    history = [(0.0,) + init]
    t0 = time.time()
    for n in range(nsteps):
        u, v = step(u, v)
        if (n + 1) % sample_every == 0 or n == nsteps - 1:
            t_curr = (n + 1) * dt
            history.append((t_curr,) + diag(u, v))
    elapsed = time.time() - t0
    times = np.array([h[0] for h in history])
    Cs    = np.array([h[1:] for h in history])
    print(f"[{label}] Nx={Nx} dt={dt:.1e} T={T} nsteps={nsteps} elapsed={elapsed:.2f}s", flush=True)
    return times, Cs

# ---------------------------------------------------------------
# Run three configs
# ---------------------------------------------------------------
T = 5.0
configs = [
    ("A", 256, 5.0e-4),   # 5x baseline dt
    ("B", 256, 1.0e-4),   # 5x finer dt
    ("C", 512, 2.5e-4),   # 2x grid (baseline dt)
]

names = ["C1=int u dx", "C2=int v dx", "C3=int uv dx", "C4=energy", "C5=int m^2 dx"]
results = {}
for (label, Nx, dt) in configs:
    times, Cs = run_config(Nx, dt, T, label)
    results[label] = (times, Cs)

# ---------------------------------------------------------------
# Compare end-state drift across configs
# ---------------------------------------------------------------
print("\n=== Drift summary across configs (E1 IC, T={:.1f}) ===".format(T), flush=True)
print(f"{'quantity':18s} | {'A: dt=5e-4 Nx=256':>22s} | {'B: dt=1e-4 Nx=256':>22s} | {'C: dt=2.5e-4 Nx=512':>22s}", flush=True)
print("-" * 100, flush=True)
for i, nm in enumerate(names):
    line = f"{nm:18s} |"
    for label, _, _ in configs:
        times, Cs = results[label]
        init_val = Cs[0, i]
        final_val = Cs[-1, i]
        abs_drift = final_val - init_val
        line += f" init={init_val:+.3e} final={final_val:+.3e} drift={abs_drift:+.2e} |"
    print(line, flush=True)

# ---------------------------------------------------------------
# Quantitative comparison: how does drift scale with dt?
#   ratio_AB = drift(A) / drift(B)
#   if ratio ~ 1: drift is dt-independent => physical
#   if ratio ~ (dt_A/dt_B)^p for some p: numerical artifact of order p
# ---------------------------------------------------------------
print("\n=== dt-scaling check (config A vs B at same Nx=256) ===", flush=True)
print(f"dt ratio = dt_A/dt_B = 5e-4/1e-4 = 5", flush=True)
for i, nm in enumerate(names):
    dA = results["A"][1][-1, i] - results["A"][1][0, i]
    dB = results["B"][1][-1, i] - results["B"][1][0, i]
    if abs(dB) < 1e-10:
        # both essentially zero
        print(f"  {nm:18s} drift_A={dA:+.2e} drift_B={dB:+.2e}  -> both ~ machine zero; structurally conserved", flush=True)
    else:
        ratio = dA / dB
        # also report what order would explain it: dA/dB = (5)^p => p = log_5(ratio)
        if ratio > 0:
            p = np.log(ratio) / np.log(5.0)
            print(f"  {nm:18s} drift_A={dA:+.2e} drift_B={dB:+.2e} ratio={ratio:+.3f} -> order ~ {p:+.2f}", flush=True)
        else:
            print(f"  {nm:18s} drift_A={dA:+.2e} drift_B={dB:+.2e} ratio={ratio:+.3f} -> sign flips, drift is not a clean numerical artifact", flush=True)

print("\n=== Nx-scaling check (config A vs C at similar dt) ===", flush=True)
# A: dt=5e-4 Nx=256;  C: dt=2.5e-4 Nx=512  -- not the cleanest comparison
# Better: compare configs with identical dt and different Nx -> here only A and C with different dt and Nx,
# but B (dt=1e-4 Nx=256) vs C (dt=2.5e-4 Nx=512) lets us see Nx effect because both are at refined dt.
# We just print drift(C) vs drift(B) and note Nx differs but dt differs too (factor 2.5).
print("Configs use different (Nx, dt) tuples; report side-by-side raw drift:", flush=True)
for i, nm in enumerate(names):
    dA = results["A"][1][-1, i] - results["A"][1][0, i]
    dB = results["B"][1][-1, i] - results["B"][1][0, i]
    dC = results["C"][1][-1, i] - results["C"][1][0, i]
    print(f"  {nm:18s} drift_A={dA:+.3e} drift_B={dB:+.3e} drift_C={dC:+.3e}", flush=True)

# Save for transparency
out_npz = os.path.join(os.path.dirname(__file__), "history.npz")
np.savez(out_npz,
         tA=results["A"][0], CA=results["A"][1],
         tB=results["B"][0], CB=results["B"][1],
         tC=results["C"][0], CC=results["C"][1])
print(f"\n[save] history -> {out_npz}", flush=True)
