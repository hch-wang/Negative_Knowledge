"""
B2 E3: Dense A-sweep at fixed u_L (sharpness test) + bore-stabilization scaling.

E2 findings:
  - Destruction emerges at A ≳ 1.5 over T=10 — but it's INTRINSIC to BKdV with
    sech^2 IC, not bore-induced (u_L=0 row also shows destruction).
  - The bore actually IMPROVES soliton survival: L2_ratio at (A=1.5) goes
    0.436 (u_L=0) → 0.588 (u_L=1) → 0.640 (u_L=2). Bore stabilizes.
  - Viscosity ablation: ν∈{0.025, 0.05, 0.1} produces final v_peak within 6% —
    the finding is physics, not numerical.

E3 design has two parts, testing the BKdV-S7 R3 prediction:
  Part A: dense A-sweep at u_L=0 with T=10. BKdV-S7 R3 says (v-1) source flips at
          A=1, with logslope 0.22 for A<1 and 2.49 for A>1. We measure soliton
          L2_ratio at T=10 across A ∈ {0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.7, 2.0}
          and look for a kink near A=1.
          Sharp vs smooth: a sharp jump in d(L2_ratio)/dA at A=1 indicates the
          v=1 sign-flip is a true phase boundary. A smooth curve indicates only
          a continuous strength-dependent shedding.

  Part B: bore-stabilization scaling. At fixed A=1.5 (a robust destruction case
          at u_L=0), sweep u_L ∈ {0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0}, measure
          L2_ratio. Test prediction: bore should monotonically stabilize. If a
          REVERSAL appears (very large u_L re-destabilizes), that locates a
          counter-regime.
"""
import numpy as np
import os
import json
import time

OUT_DIR = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B2/PosOnly/evidence"
os.makedirs(OUT_DIR, exist_ok=True)


def make_grid(Nx=256, L=30.0):
    dx = L / Nx
    x = np.linspace(-L/2, L/2, Nx, endpoint=False)
    k = 2*np.pi*np.fft.fftfreq(Nx, d=dx)
    ik = 1j * k
    kmax = Nx // 3
    freq_idx = np.fft.fftfreq(Nx, d=1.0) * Nx
    mask = np.abs(freq_idx) <= kmax
    return x, k, ik, mask, dx


def dx_spec(f, ik, mask):
    F = np.fft.fft(f) * mask
    return np.real(np.fft.ifft(ik * F))


def dxxx_spec(f, ik, mask):
    F = np.fft.fft(f) * mask
    return np.real(np.fft.ifft(ik**3 * F))


def dxx_spec(f, ik, mask):
    F = np.fft.fft(f) * mask
    return np.real(np.fft.ifft((ik**2) * F))


def dealias(f, mask):
    F = np.fft.fft(f) * mask
    return np.real(np.fft.ifft(F))


def rhs(u, v, ik, mask, nu_u):
    u_d = dealias(u, mask)
    v_d = dealias(v, mask)
    uu = dealias(u_d * u_d, mask)
    advU = 1.5 * dx_spec(uu, ik, mask)
    v2 = dealias(v_d * v_d, mask)
    v2_x = dx_spec(v2, ik, mask)
    vxx = dxx_spec(v_d, ik, mask)
    vxx_x = dx_spec(vxx, ik, mask)
    coupling_u = 3.0 * v2_x + vxx_x
    u_xx = dxx_spec(u_d, ik, mask)
    u_t = -advU - coupling_u + nu_u * u_xx
    advV = 3.0 * dx_spec(v2, ik, mask)
    vxxx = dxxx_spec(v_d, ik, mask)
    uv = dealias(u_d * v_d, mask)
    uv_x = dx_spec(uv, ik, mask)
    v_t = -advV - vxxx - uv_x
    return u_t, v_t


def rk4_step(u, v, dt, ik, mask, nu_u):
    k1u, k1v = rhs(u, v, ik, mask, nu_u)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v, ik, mask, nu_u)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v, ik, mask, nu_u)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v, ik, mask, nu_u)
    return (u + dt/6 * (k1u + 2*k2u + 2*k3u + k4u),
            v + dt/6 * (k1v + 2*k2v + 2*k3v + k4v))


def make_ic(x, u_L, A, x_b=+3.0, w_b=0.5, x_s=0.0):
    u0 = u_L * 0.5 * (1.0 - np.tanh((x - x_b) / w_b))
    kappa = np.sqrt(max(A, 1e-9) / 2.0)
    v0 = A / np.cosh(kappa * (x - x_s))**2
    return u0, v0


def diagnose(v, x, A, Nx):
    idx_max = int(np.argmax(v))
    vpa = float(v[idx_max]); vpx = float(x[idx_max])
    thr = max(0.15 * A, 0.05)
    n_peaks = 0
    for i in range(Nx):
        im = (i-1) % Nx; ip = (i+1) % Nx
        if v[i] > thr and v[i] > v[im] and v[i] > v[ip]:
            n_peaks += 1
    return vpa, vpx, n_peaks


def run_one(u_L, A, T=10.0, dt=1e-4, Nx=256, L=30.0, nu_u=5e-2,
            snap_save=False, tag="", n_snap=5):
    x, k, ik, mask, dx = make_grid(Nx, L)
    u0, v0 = make_ic(x, u_L, A)
    u, v = u0.copy(), v0.copy()
    n_steps = int(round(T / dt))
    snap_idx = np.linspace(0, n_steps, n_snap, dtype=int)
    snaps_u, snaps_v, snap_t = [], [], []
    diag = {'time': [], 'l2_v': [], 'sup_u': [], 'sup_v': [],
            'v_peak_x': [], 'v_peak_amp': [], 'n_peaks_v': []}
    diag_every = max(1, n_steps // 30)
    for n in range(n_steps + 1):
        if n in snap_idx:
            snaps_u.append(u.copy()); snaps_v.append(v.copy())
            snap_t.append(n * dt)
        if n % diag_every == 0 or n == n_steps:
            t = n * dt
            l2v = float(np.sqrt(np.sum(v*v) * dx))
            su = float(np.max(np.abs(u))); sv = float(np.max(np.abs(v)))
            vpa, vpx, npk = diagnose(v, x, A, Nx)
            diag['time'].append(t); diag['l2_v'].append(l2v)
            diag['sup_u'].append(su); diag['sup_v'].append(sv)
            diag['v_peak_x'].append(vpx); diag['v_peak_amp'].append(vpa)
            diag['n_peaks_v'].append(npk)
            if not np.isfinite(sv) or sv > 1e3:
                diag['blowup'] = True; break
        if n == n_steps: break
        u, v = rk4_step(u, v, dt, ik, mask, nu_u)
    s = {'u_L': u_L, 'A': A, 'T': T, 'dt': dt, 'nu_u': nu_u,
         'final_v_peak_amp': diag['v_peak_amp'][-1],
         'final_v_peak_x': diag['v_peak_x'][-1],
         'final_n_peaks': diag['n_peaks_v'][-1],
         'max_n_peaks': max(diag['n_peaks_v']),
         'final_l2_v': diag['l2_v'][-1],
         'init_l2_v': diag['l2_v'][0],
         'l2_v_ratio': diag['l2_v'][-1] / max(diag['l2_v'][0], 1e-12),
         'v_peak_x_trajectory': diag['v_peak_x'],
         'v_peak_amp_trajectory': diag['v_peak_amp'],
         'l2_v_trajectory': diag['l2_v'],
         'n_peaks_trajectory': diag['n_peaks_v'],
         'time_trajectory': diag['time']}
    if snap_save:
        np.savez(os.path.join(OUT_DIR, f"snap_{tag}.npz"),
                 x=x, t=np.array(snap_t), u=np.array(snaps_u),
                 v=np.array(snaps_v), u0=u0, v0=v0)
    return s


def main():
    print("="*70); print("E3 part A: dense A-sweep at u_L=0, T=10 (sharpness)")
    print("="*70)
    A_grid = [0.30, 0.50, 0.70, 0.90, 1.10, 1.30, 1.50, 1.70, 2.00]
    T = 10.0
    res_A = []
    t0 = time.time()
    for A in A_grid:
        tag = f"E3A_uL0_A{A:.2f}"
        print(f"=== {tag} ===", flush=True)
        t_run = time.time()
        snap_save = A in [0.50, 0.90, 1.10, 1.50, 2.00]
        s = run_one(0.0, A, T=T, snap_save=snap_save, tag=tag)
        s['tag'] = tag; s['elapsed'] = time.time() - t_run
        res_A.append(s)
        print(f"  L2r={s['l2_v_ratio']:.4f} vpeak/A={s['final_v_peak_amp']/A:.4f} "
              f"npk_max={s['max_n_peaks']} t={s['elapsed']:.1f}s", flush=True)
    print(f"\nPart A total: {time.time() - t0:.1f}s")

    # discrete derivative of l2_v_ratio wrt A
    print("\n  A     L2_ratio    d(L2_ratio)/dA")
    print("  ---   --------    ----------------")
    for i, s in enumerate(res_A):
        slope_str = ""
        if i > 0:
            dA = res_A[i]['A'] - res_A[i-1]['A']
            dR = res_A[i]['l2_v_ratio'] - res_A[i-1]['l2_v_ratio']
            slope_str = f"  {dR/dA:+.4f}"
        print(f"  {s['A']:.2f}    {s['l2_v_ratio']:.4f}{slope_str}")

    print("\n" + "="*70); print("E3 part B: u_L-sweep at A=1.5, T=10 (bore stabilization)")
    print("="*70)
    u_L_grid = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
    res_uL = []
    t0 = time.time()
    for u_L in u_L_grid:
        tag = f"E3B_uL{u_L:.2f}_A1.50"
        print(f"=== {tag} ===", flush=True)
        t_run = time.time()
        snap_save = u_L in [0.0, 1.0, 3.0]
        s = run_one(u_L, 1.5, T=T, snap_save=snap_save, tag=tag)
        s['tag'] = tag; s['elapsed'] = time.time() - t_run
        res_uL.append(s)
        print(f"  L2r={s['l2_v_ratio']:.4f} vpeak/A={s['final_v_peak_amp']/1.5:.4f} "
              f"npk_max={s['max_n_peaks']} t={s['elapsed']:.1f}s", flush=True)
    print(f"\nPart B total: {time.time() - t0:.1f}s")
    print("\n  u_L   L2_ratio")
    for s in res_uL:
        print(f"  {s['u_L']:.2f}    {s['l2_v_ratio']:.4f}")

    out = []
    for r in res_A + res_uL:
        out.append({k: r[k] for k in [
            'tag','u_L','A','T','nu_u','final_v_peak_amp','final_v_peak_x',
            'final_n_peaks','max_n_peaks','l2_v_ratio',
            'l2_v_trajectory','v_peak_amp_trajectory','v_peak_x_trajectory',
            'n_peaks_trajectory','time_trajectory'] if k in r})
    with open(os.path.join(OUT_DIR, "E3_sharpness.json"), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
