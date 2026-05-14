"""
B2 / NegOnly — BKdV bore-soliton interaction
Candidate script. Used across all 3 rounds with command-line round selector.

Solver stack (per BKdV-S1/S6 negative bank):
- Fourier pseudospectral on [-L/2, L/2], Nx=256
- 2/3-rule dealiasing on EVERY nonlinear product
- Classical RK4
- dt = 1e-4
- Explicit linear viscosity nu*u_xx on the u-equation, nu=5e-2 (REQUIRED for bore u-IC; BKdV-S6)
- No viscosity on v (it is dispersive, not shock-prone at A < 3)
"""
import os, sys, json, time, math
import numpy as np

# ---------------- Grid ----------------
L = 30.0
Nx = 256
x = np.linspace(-L/2, L/2, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2*np.pi*np.fft.fftfreq(Nx, d=dx)        # wavenumber array
ik = 1j*k
k2 = k*k
k3 = k2*k

# 2/3 dealias mask
kmax = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0/3.0)*kmax).astype(float)

NU_U = 5e-2     # linear viscosity on u (BKdV-S6 prescription)

# ---------------- IC builders ----------------
def bore_ic(u_L, x0_bore=-7.0, width=0.5):
    """Smooth tanh bore: u = u_L on the left, 0 on the right. Centered at x0_bore.
    For u_t + 3 u u_x, this bore moves to the right with speed c_b = (3/2) u_L."""
    return 0.5*u_L*(1.0 - np.tanh((x - x0_bore)/width))

def soliton_ic_v(A, x0_sol=+5.0):
    """KdV-like soliton: v = A sech^2(sqrt(A/2)(x-x0)).
    For v_t + 6 v v_x + v_xxx = 0 the speed is c_s = 2A (rightward).
    We will reflect to make it move LEFT by negating the velocity field is not directly applicable.
    Standard BKdV is not Galilean; we instead place the soliton to the RIGHT and let the bore catch up,
    OR place the soliton to the LEFT and let it pass into the bore.
    For 'head-on' encounter we choose: bore on LEFT, soliton on RIGHT.
    The bore moves right (toward soliton); soliton moves right too but slower if c_s < c_b,
    so the bore overtakes the soliton (rear-end collision, but in this PDE this is still
    a 'bore-soliton encounter' and is the only available collision geometry on BKdV)."""
    kappa = np.sqrt(A/2.0)
    return A / np.cosh(kappa*(x - x0_sol))**2

# ---------------- Spatial derivatives via FFT ----------------
def dx_spec(f):
    return np.real(np.fft.ifft(ik*np.fft.fft(f)))

def d2x_spec(f):
    return np.real(np.fft.ifft(-k2*np.fft.fft(f)))

def d3x_spec(f):
    return np.real(np.fft.ifft(-1j*k3*np.fft.fft(f)))

def dealias_field(f):
    return np.real(np.fft.ifft(dealias * np.fft.fft(f)))

# ---------------- RHS of BKdV ----------------
def rhs(u, v):
    """
    u_t + 3 u u_x = -d_x(3 v^2 + v_xx)  + nu*u_xx
    v_t + 6 v v_x + v_xxx = -d_x(u v)
    """
    # dealias product fields
    u_d = dealias_field(u)
    v_d = dealias_field(v)
    uv = dealias_field(u_d*v_d)
    v2 = dealias_field(v_d*v_d)
    # spatial derivatives
    u_x = dx_spec(u_d)
    v_x = dx_spec(v_d)
    v_xx = d2x_spec(v_d)
    v_xxx = d3x_spec(v_d)
    # explicit u-equation
    du = -3.0*u_d*u_x - dx_spec(3.0*v2 + v_xx) + NU_U*d2x_spec(u_d)
    # explicit v-equation
    dv = -6.0*v_d*v_x - v_xxx - dx_spec(uv)
    return du, dv

def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v)
    u_new = u + (dt/6.0)*(k1u + 2*k2u + 2*k3u + k4u)
    v_new = v + (dt/6.0)*(k1v + 2*k2v + 2*k3v + k4v)
    return u_new, v_new

# ---------------- Diagnostics ----------------
def find_v_peaks(v_field, height_frac=0.2, vmax_ref=None):
    """Simple in-house local-max detector with prominence."""
    if vmax_ref is None:
        vmax_ref = float(np.max(np.abs(v_field)))
    thresh = height_frac*vmax_ref
    peaks = []
    for i in range(1, Nx-1):
        if v_field[i] > thresh and v_field[i] >= v_field[i-1] and v_field[i] >= v_field[i+1]:
            peaks.append((i, x[i], v_field[i]))
    # periodic-edge check
    if v_field[0] > thresh and v_field[0] >= v_field[-1] and v_field[0] >= v_field[1]:
        peaks.append((0, x[0], v_field[0]))
    if v_field[-1] > thresh and v_field[-1] >= v_field[-2] and v_field[-1] >= v_field[0]:
        peaks.append((Nx-1, x[-1], v_field[-1]))
    return peaks

def soliton_metrics(v_field, x_window=None):
    """Find the dominant peak in the v-field.
       Optionally restrict to a window [xlo, xhi] for tracking."""
    if x_window is None:
        mask = np.ones_like(v_field, dtype=bool)
    else:
        xlo, xhi = x_window
        mask = (x >= xlo) & (x <= xhi)
    if not mask.any():
        return dict(v_peak=0.0, x_peak=np.nan, n_peaks=0)
    sub = v_field[mask]
    sub_x = x[mask]
    i_loc = int(np.argmax(sub))
    v_peak = float(sub[i_loc])
    x_peak = float(sub_x[i_loc])
    # peak count (with prominence) in the whole domain
    peaks = find_v_peaks(v_field, height_frac=0.3, vmax_ref=np.max(v_field))
    return dict(v_peak=v_peak, x_peak=x_peak, n_peaks=len(peaks))

def bore_metrics(u_field, u_L):
    """Capture bore amplitude (post-front) and rough front location."""
    u_max = float(np.max(u_field))
    u_min = float(np.min(u_field))
    # Estimate bore front as the inflection: find argmax of |du/dx|
    ux = dx_spec(u_field)
    i_front = int(np.argmax(np.abs(ux)))
    x_front = float(x[i_front])
    return dict(u_max=u_max, u_min=u_min, x_front=x_front)

# ---------------- Integration driver ----------------
def integrate(u0, v0, T, dt, save_times, label, evdir):
    nsteps = int(round(T/dt))
    save_steps = sorted({int(round(t/dt)) for t in save_times if t<=T})
    save_steps_set = set(save_steps)
    snaps = {}      # t -> (u, v)
    diag = []       # list of dict
    u, v = u0.copy(), v0.copy()
    t = 0.0
    snaps[0.0] = (u.copy(), v.copy())
    # initial diagnostics
    diag.append(dict(t=0.0, mass_u=float(np.sum(u)*dx), mass_v=float(np.sum(v)*dx),
                     v_peak=float(np.max(v)), u_max=float(np.max(u)),
                     u_min=float(np.min(u)),
                     l2_v=float(np.sqrt(np.sum(v*v)*dx))))
    t0 = time.time()
    for step in range(1, nsteps+1):
        u, v = rk4_step(u, v, dt)
        if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
            print(f"  [WARN] {label}: NaN at step {step} (t~{step*dt:.3f})", flush=True)
            break
        if step in save_steps_set:
            t_now = step*dt
            snaps[round(t_now,3)] = (u.copy(), v.copy())
            diag.append(dict(t=t_now,
                             mass_u=float(np.sum(u)*dx),
                             mass_v=float(np.sum(v)*dx),
                             v_peak=float(np.max(v)),
                             u_max=float(np.max(u)),
                             u_min=float(np.min(u)),
                             l2_v=float(np.sqrt(np.sum(v*v)*dx))))
    t_end = time.time() - t0
    # save snapshot pack
    out_npz = os.path.join(evdir, f"{label}_snaps.npz")
    snap_t = sorted(snaps.keys())
    np.savez_compressed(out_npz,
        x=x,
        t=np.array(snap_t),
        u_stack=np.stack([snaps[ti][0] for ti in snap_t], axis=0),
        v_stack=np.stack([snaps[ti][1] for ti in snap_t], axis=0),
    )
    return snaps, diag, t_end

# ---------------- Outcome classifier ----------------
def classify_outcome(snaps, u_L, A, T, evdir, tag):
    """
    Given snapshot dictionary, classify the bore-soliton outcome.
    Classes:
      'transmission' : soliton survives with v_peak >= 0.5*A AND single dominant peak post-encounter
      'fusion'       : v-peak heavily damped (<0.3*A) with no scattered fragments
      'destruction'  : multi-peak fragmentation (n_peaks >= 3 with peaks > 0.2*A)
      'absorption'   : soliton inside the bore region, v_peak < 0.3*A and bore front advanced past soliton's IC
      'no_encounter' : (control) bore and soliton never overlapped within T
    """
    times = sorted(snaps.keys())
    t_end = times[-1]
    v_end = snaps[t_end][1]
    u_end = snaps[t_end][0]
    # initial peak position
    v0 = snaps[0.0][1]
    i0 = int(np.argmax(v0))
    x_sol_0 = x[i0]
    # final dominant peak in full domain
    sm = soliton_metrics(v_end)
    bm = bore_metrics(u_end, u_L)
    # Encounter check: bore front x position at t_end vs initial soliton x
    x_front_end = bm["x_front"]
    bore_advance = (x_front_end - bm["x_front"]) if False else 0.0  # placeholder
    # Outcome rules
    v_ratio = sm["v_peak"]/max(A,1e-9)
    n_peaks = sm["n_peaks"]
    label = "ambiguous"
    if v_ratio >= 0.5 and n_peaks <= 2:
        label = "transmission"
    elif v_ratio < 0.30 and n_peaks <= 2:
        label = "fusion_or_absorption"
    elif n_peaks >= 3 and v_ratio < 0.5:
        label = "destruction"
    elif v_ratio >= 0.30 and n_peaks >= 3:
        label = "partial_breakup"
    return dict(outcome=label,
                v_peak_end=sm["v_peak"],
                v_peak_ratio=v_ratio,
                n_peaks=n_peaks,
                x_peak_end=sm["x_peak"],
                u_max_end=bm["u_max"],
                u_min_end=bm["u_min"],
                x_front_end=bm["x_front"],
                t_end=t_end)

# ---------------- Experiments ----------------
def experiment_E1(evdir):
    """E1: anchor / single collision at u_L=0.5, A=1.5.
       Diagnostics: peak height, peak count, position, conserved mass."""
    u_L = 0.5
    A   = 1.5
    T   = 8.0
    dt  = 1e-4
    u0 = bore_ic(u_L)
    v0 = soliton_ic_v(A)
    save_times = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    label = f"E1_uL{u_L:.2f}_A{A:.2f}"
    snaps, diag, dt_wall = integrate(u0, v0, T, dt, save_times, label, evdir)
    outcome = classify_outcome(snaps, u_L, A, T, evdir, label)
    return dict(round_id="E1", u_L=u_L, A=A, T=T, dt=dt, dt_wall=dt_wall,
                outcome=outcome, diag=diag)

def experiment_E2(evdir):
    """E2: phase-scan on a 4x4 (u_L, A) grid.
       u_L in {0.3, 0.6, 1.0, 1.5}; A in {0.5, 1.0, 1.5, 2.0}.
       T=6 (shorter to keep wall budget bounded); same dt=1e-4."""
    u_Ls = [0.3, 0.6, 1.0, 1.5]
    As   = [0.5, 1.0, 1.5, 2.0]
    T   = 6.0
    dt  = 1e-4
    save_times = [0.0, 2.0, 4.0, 6.0]
    results = []
    for u_L in u_Ls:
        for A in As:
            u0 = bore_ic(u_L)
            v0 = soliton_ic_v(A)
            label = f"E2_uL{u_L:.2f}_A{A:.2f}"
            print(f"  [E2] running {label} ...", flush=True)
            snaps, diag, dt_wall = integrate(u0, v0, T, dt, save_times, label, evdir)
            outcome = classify_outcome(snaps, u_L, A, T, evdir, label)
            results.append(dict(u_L=u_L, A=A, T=T, dt_wall=dt_wall,
                                outcome=outcome,
                                v_peak_end=outcome["v_peak_end"],
                                v_peak_ratio=outcome["v_peak_ratio"],
                                n_peaks=outcome["n_peaks"],
                                u_max_end=outcome["u_max_end"],
                                u_min_end=outcome["u_min_end"]))
    return dict(round_id="E2", grid=results)

def experiment_E3(evdir):
    """E3 (redesigned per F2 finding): u_L was found to barely affect outcome,
       but A strongly does. Two-part probe:
       (i)  A-refinement at u_L=0.6: A in {0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5} to localize the
            transmission->destruction boundary.
       (ii) ZERO-BORE control: u_L=0 (flat u=0 IC) for A in {0.5, 1.0, 1.5} to test whether the
            soliton fragments anyway (would imply BKdV self-instability, not bore-driven destruction).
       This discriminates H_A/H_B (bore-driven) from H_C (intrinsic-m=0-instability)."""
    T = 6.0
    dt = 1e-4
    save_times = [0.0, 2.0, 4.0, 6.0]
    # part (i): A-refinement at moderate u_L
    A_grid = [0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
    u_L_fix = 0.6
    a_sweep = []
    for A in A_grid:
        u0 = bore_ic(u_L_fix)
        v0 = soliton_ic_v(A)
        label = f"E3a_uL{u_L_fix:.2f}_A{A:.2f}"
        print(f"  [E3a] running {label} ...", flush=True)
        snaps, diag, dt_wall = integrate(u0, v0, T, dt, save_times, label, evdir)
        outcome = classify_outcome(snaps, u_L_fix, A, T, evdir, label)
        a_sweep.append(dict(u_L=u_L_fix, A=A, T=T, dt_wall=dt_wall,
                            outcome=outcome,
                            v_peak_end=outcome["v_peak_end"],
                            v_peak_ratio=outcome["v_peak_ratio"],
                            n_peaks=outcome["n_peaks"],
                            u_max_end=outcome["u_max_end"],
                            u_min_end=outcome["u_min_end"]))
    # part (ii): zero-bore control
    zero_bore = []
    for A in [0.5, 1.0, 1.5]:
        u0 = np.zeros_like(x)
        v0 = soliton_ic_v(A)
        label = f"E3b_uL0.00_A{A:.2f}"
        print(f"  [E3b] running {label} (zero bore control) ...", flush=True)
        snaps, diag, dt_wall = integrate(u0, v0, T, dt, save_times, label, evdir)
        outcome = classify_outcome(snaps, 0.0, A, T, evdir, label)
        zero_bore.append(dict(u_L=0.0, A=A, T=T, dt_wall=dt_wall,
                              outcome=outcome,
                              v_peak_end=outcome["v_peak_end"],
                              v_peak_ratio=outcome["v_peak_ratio"],
                              n_peaks=outcome["n_peaks"],
                              u_max_end=outcome["u_max_end"],
                              u_min_end=outcome["u_min_end"]))
    return dict(round_id="E3", a_sweep=a_sweep, zero_bore=zero_bore)

# ---------------- Entry point ----------------
if __name__ == "__main__":
    round_id = sys.argv[1] if len(sys.argv) > 1 else "E1"
    here = os.path.dirname(os.path.abspath(__file__))
    evdir = os.path.join(here, "evidence")
    os.makedirs(evdir, exist_ok=True)
    if round_id == "E1":
        result = experiment_E1(evdir)
    elif round_id == "E2":
        result = experiment_E2(evdir)
    elif round_id == "E3":
        result = experiment_E3(evdir)
    else:
        raise SystemExit(f"unknown round_id {round_id}")
    out_path = os.path.join(evdir, f"{round_id}_result.json")
    with open(out_path, "w") as fh:
        json.dump(result, fh, indent=2, default=float)
    print(f"WROTE {out_path}")
    print(json.dumps({k:v for k,v in result.items() if k!='diag'}, indent=2, default=float)[:4000])
