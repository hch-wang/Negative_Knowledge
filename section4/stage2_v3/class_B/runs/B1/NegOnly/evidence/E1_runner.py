"""
candidate.py — BKdV mechanism inquiry, B1/NegOnly.

Reusable solver shared across the 3-round protocol; main() below holds the
CURRENT round's driver. The script is overwritten between rounds so the
final committed version is for E3; intermediate versions are preserved in
evidence/<round>_runner.py.

Solver stack (per prompt; validated background, not our contribution):
  - Fourier pseudospectral derivatives (Nx=256, L=30, periodic)
  - 2/3-rule dealiasing on every nonlinear product
  - Classical RK4 on the full RHS, dt=1e-4
  - Explicit linear u-viscosity nu*u_xx with nu=5e-2 ONLY when IC has
    bore-like u-gradient (BKdV-S6 deep recommended_alternative).
    For smooth (sech^2)^2 / Gaussian u-IC we set nu=5e-2 too as a safe
    default, then verify it doesn't dominate by ablation.

PDE (Holm et al. 2025, BKdV):
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)
"""
import json
import os
import sys
import time
import numpy as np
from numpy.fft import fft, ifft, fftfreq

# ----------------------------- solver core ----------------------------------
NX = 256
L = 30.0
DX = L / NX
X = np.linspace(-L/2, L/2, NX, endpoint=False)
K = 2 * np.pi * fftfreq(NX, d=DX)
IK = 1j * K
K2 = K * K
K3 = K * K * K
# 2/3 dealias mask
DEALIAS = np.abs(K) <= (2.0/3.0) * (np.pi / DX)

def dx(f):
    return ifft(IK * fft(f)).real

def dxx(f):
    return ifft(-K2 * fft(f)).real

def dxxx(f):
    return ifft(-1j * K3 * fft(f)).real

def dealias(f):
    return ifft(DEALIAS * fft(f)).real

def rhs(u, v, nu_u=0.0):
    """RHS of BKdV; nu_u is explicit linear viscosity on u."""
    uu = dealias(u * u)
    vv = dealias(v * v)
    uv = dealias(u * v)
    # u-equation: u_t = -(3/2)(u^2)_x - 3 (v^2)_x - v_xxx + nu_u u_xx
    u_t = -1.5 * dx(uu) - 3.0 * dx(vv) - dxxx(v)
    if nu_u != 0.0:
        u_t = u_t + nu_u * dxx(u)
    # v-equation: v_t = -3 (v^2)_x - v_xxx - (u v)_x
    v_t = -3.0 * dx(vv) - dxxx(v) - dx(uv)
    return u_t, v_t

def rk4_step(u, v, dt, nu_u=0.0):
    k1u, k1v = rhs(u, v, nu_u)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v, nu_u)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v, nu_u)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v, nu_u)
    return (u + dt/6.0 * (k1u + 2*k2u + 2*k3u + k4u),
            v + dt/6.0 * (k1v + 2*k2v + 2*k3v + k4v))

# Gardner reference (isolated; the m=0 algebraic reduction)
def rhs_gardner(v):
    vv = dealias(v * v)
    vvv = dealias(v * vv)
    return -3.0 * dx(vv) - 0.5 * dx(vvv) - dxxx(v)

def rk4_gardner(v, dt):
    k1 = rhs_gardner(v)
    k2 = rhs_gardner(v + 0.5*dt*k1)
    k3 = rhs_gardner(v + 0.5*dt*k2)
    k4 = rhs_gardner(v + dt*k3)
    return v + dt/6.0 * (k1 + 2*k2 + 2*k3 + k4)

# ----------------------------- diagnostics ----------------------------------
def diagnostics(u, v):
    m = u - 0.5 * v * v
    L2_u = np.sqrt(np.sum(u*u) * DX)
    L2_v = np.sqrt(np.sum(v*v) * DX)
    L2_m = np.sqrt(np.sum(m*m) * DX)
    mass_u = np.sum(u) * DX
    mass_v = np.sum(v) * DX
    v_peak = float(np.max(v))
    u_peak = float(np.max(u))
    ix = int(np.argmax(v))
    # Support mask: where v > 0.3 * v_peak (inside compound core)
    if v_peak > 0.1:
        mask = v > 0.3 * v_peak
    else:
        mask = np.zeros_like(v, dtype=bool)
    if mask.sum() > 5:
        u_loc = u[mask]
        v2_loc = 0.5 * v[mask]**2
        denom = np.linalg.norm(u_loc - u_loc.mean()) * np.linalg.norm(v2_loc - v2_loc.mean())
        if denom > 1e-12:
            lock_loc = float(np.sum((u_loc - u_loc.mean()) * (v2_loc - v2_loc.mean())) / denom)
        else:
            lock_loc = 0.0
        m_loc = m[mask]
        L2_m_local = float(np.sqrt(np.sum(m_loc*m_loc) * DX))
        # signed local <m> inside support
        m_mean_local = float(np.mean(m_loc))
    else:
        lock_loc = 0.0
        L2_m_local = 0.0
        m_mean_local = 0.0
    Vhat = np.abs(fft(v))**2
    klow = np.abs(K) <= 2.0
    fracL_v = float(Vhat[klow].sum() / max(Vhat.sum(), 1e-30))
    return {
        "L2_u": float(L2_u), "L2_v": float(L2_v), "L2_m": float(L2_m),
        "L2_m_localPeak": L2_m_local, "m_mean_local": m_mean_local,
        "mass_u": float(mass_u), "mass_v": float(mass_v),
        "v_peak": v_peak, "u_peak": u_peak, "v_peak_x": float(X[ix]),
        "lock_corr_local": lock_loc, "fracL_v": fracL_v,
        "support_npts": int(mask.sum()),
    }

# ----------------------------- IC families ----------------------------------
def ic_sech2(amp=1.5, x0=-5.0, w=1.0):
    return amp / np.cosh((X - x0)/w)**2

def ic_gauss(amp=1.5, x0=-5.0, w=2.0):
    return amp * np.exp(-((X - x0)/w)**2)

def ic_twopulse(ampA=1.0, ampB=0.5, x0a=-5.0, x0b=2.0, wa=1.0, wb=1.5):
    return ampA / np.cosh((X-x0a)/wa)**2 + ampB / np.cosh((X-x0b)/wb)**2

def ic_sin(amp=0.6, kmode=2):
    return amp * np.cos(2*np.pi*kmode*X/L)

def ic_bore_u(amp=1.5, w=0.5):
    return amp * (1.0 - np.tanh(X/w))/2.0

# ----------------------------- evolver --------------------------------------
def run_bkdv(u0, v0, T, dt, nu_u, tag, save_dir,
             snap_times=(0.0, 1.0, 2.5, 5.0, 7.5, 10.0),
             also_gardner=False, store_full_fields=False):
    u = u0.copy(); v = v0.copy()
    if also_gardner:
        v_g = v0.copy()
    nsteps = int(round(T/dt))
    snaps = {"t": [], "u": [], "v": [], "m": []}
    if also_gardner:
        snaps["v_gardner"] = []
    diag_t = []
    diag_seq = []
    snap_times = list(snap_times)
    t = 0.0
    next_snap_idx = 0
    def maybe_snap():
        nonlocal next_snap_idx
        while next_snap_idx < len(snap_times) and t >= snap_times[next_snap_idx] - 0.5*dt:
            snaps["t"].append(t)
            snaps["u"].append(u.copy())
            snaps["v"].append(v.copy())
            snaps["m"].append((u - 0.5*v*v).copy())
            if also_gardner:
                snaps["v_gardner"].append(v_g.copy())
            next_snap_idx += 1
    maybe_snap()
    diag_t.append(t); diag_seq.append(diagnostics(u, v))
    t0 = time.time()
    blew_up_at = None
    for step in range(nsteps):
        u, v = rk4_step(u, v, dt, nu_u=nu_u)
        if also_gardner:
            v_g = rk4_gardner(v_g, dt)
        t = (step+1) * dt
        if not (np.isfinite(u).all() and np.isfinite(v).all()):
            blew_up_at = t
            print(f"[{tag}] NaN at step {step+1}, t={t:.4f}")
            break
        if (step+1) % max(1, int(0.1/dt)) == 0:
            diag_t.append(t)
            diag_seq.append(diagnostics(u, v))
        maybe_snap()
    elapsed = time.time() - t0
    os.makedirs(save_dir, exist_ok=True)
    np.savez_compressed(os.path.join(save_dir, f"{tag}_snapshots.npz"),
                        x=X,
                        t=np.array(snaps["t"]),
                        u=np.array(snaps["u"]),
                        v=np.array(snaps["v"]),
                        m=np.array(snaps["m"]),
                        **({"v_gardner": np.array(snaps["v_gardner"])} if also_gardner else {}))
    keys = sorted(diag_seq[0].keys()) if diag_seq else []
    diag_arr = {k: [d[k] for d in diag_seq] for k in keys}
    with open(os.path.join(save_dir, f"{tag}_diagnostics.json"), "w") as f:
        json.dump({"t": diag_t, "elapsed_s": elapsed,
                   "blew_up_at": blew_up_at,
                   "diagnostics": diag_arr}, f)
    return diag_t, diag_seq, snaps

# =============================================================================
# CURRENT ROUND DRIVER  (this section is rewritten each round)
# =============================================================================

def main():
    """
    E2 — basin scan + attractor test.

    F1 falsified H_alpha (local m=0 core lock) and weakened H_beta-as-Gardner.
    The compound emerged but is NOT pointwise Gardner. We now ask two
    related questions:
      Q-attractor: is the compound an attractor (formed from u_0=0 IC also,
                   not just u_0=v_0^2/2)?
      Q-basin:    does the same structure form from Gaussian / two-pulse v_0,
                  or do those fragment?

    Four sub-runs at matched v-L2 = 1.58 (target):
      E2a: sech^2 v_0 (A=1.0,w=1) + u_0=0           — off-m=0 IC
      E2b: Gaussian v_0 (A=0.94,w=1.18) + u0=v0^2/2 — same L2 alt shape
      E2c: two-pulse v_0 sech^2(x+7,w=1)+0.6 sech^2(x-2,w=1.3) + u0=v0^2/2
      E2d: sinusoidal v_0 = 0.35*cos(2pi*2*x/L) (broadband-ish; probes H_delta)
                   + u_0=0

    All on Nx=256, dt=1e-4, T=10, nu_u=5e-2.
    """
    save_dir = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/NegOnly/evidence"
    os.makedirs(save_dir, exist_ok=True)
    T = 10.0
    dt = 1e-4
    nu_u = 5e-2
    snap_times = (0.0, 1.0, 2.5, 5.0, 7.5, 10.0)
    # --- E2a: sech^2 + u_0=0 (attractor test)
    v0a = ic_sech2(amp=1.0, x0=-5.0, w=1.0)
    u0a = np.zeros_like(v0a)
    L2va = float(np.sqrt(np.sum(v0a*v0a) * DX))
    print(f"[E2a] sech^2 amp=1.0 + u0=0; v-L2={L2va:.4f}")
    run_bkdv(u0a, v0a, T, dt, nu_u, tag="E2a_sech2_u0zero",
             save_dir=save_dir, also_gardner=False, snap_times=snap_times)
    # --- E2b: Gaussian matched L2
    # Choose amp_g, w_g so that L2 = L2va; for Gaussian L2 = amp_g * (pi/2)^0.25 * sqrt(w_g)
    # Solve: amp_g * (pi/2)**0.25 * sqrt(w_g) = L2va; pick w_g=1.18
    w_g = 1.18
    amp_g = L2va / ((np.pi/2.0)**0.25 * np.sqrt(w_g))
    v0b = ic_gauss(amp=amp_g, x0=-5.0, w=w_g)
    u0b = 0.5 * v0b * v0b
    L2vb = float(np.sqrt(np.sum(v0b*v0b) * DX))
    print(f"[E2b] Gauss amp={amp_g:.4f}, w={w_g}; v-L2={L2vb:.4f}, peak_v={v0b.max():.3f}")
    run_bkdv(u0b, v0b, T, dt, nu_u, tag="E2b_gauss",
             save_dir=save_dir, also_gardner=False, snap_times=snap_times)
    # --- E2c: two-pulse
    v0c = ic_twopulse(ampA=1.0, ampB=0.6, x0a=-7.0, x0b=2.0, wa=1.0, wb=1.3)
    # rescale to match L2
    s = L2va / float(np.sqrt(np.sum(v0c*v0c) * DX))
    v0c = v0c * s
    u0c = 0.5 * v0c * v0c
    L2vc = float(np.sqrt(np.sum(v0c*v0c) * DX))
    print(f"[E2c] twopulse scaled by {s:.4f}; v-L2={L2vc:.4f}, peak_v={v0c.max():.3f}")
    run_bkdv(u0c, v0c, T, dt, nu_u, tag="E2c_twopulse",
             save_dir=save_dir, also_gardner=False, snap_times=snap_times)
    # --- E2d: low-k sinusoid (mode 2): broadband-ish in spatial spread
    v0d_raw = ic_sin(amp=1.0, kmode=2)
    s = L2va / float(np.sqrt(np.sum(v0d_raw*v0d_raw) * DX))
    v0d = v0d_raw * s
    u0d = np.zeros_like(v0d)
    L2vd = float(np.sqrt(np.sum(v0d*v0d) * DX))
    print(f"[E2d] sin mode=2 scaled by {s:.4f}; v-L2={L2vd:.4f}, peak_v={v0d.max():.3f}")
    run_bkdv(u0d, v0d, T, dt, nu_u, tag="E2d_sinmode2",
             save_dir=save_dir, also_gardner=False, snap_times=snap_times)
    print("[E2] done.")

if __name__ == "__main__":
    main()
