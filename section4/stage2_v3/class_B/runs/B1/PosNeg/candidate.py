"""
B1 / PosNeg / Experiment E3 — Compound-soliton traveling-wave structure
                                 and falsification of m=0 / pure-Gardner ansatz.

E2 produced:
  - In-peak slope of u vs v^2/2: alpha ~ 12.3 (sech^2 IC, R^2=0.94). So
    u != v^2/2 globally; in-peak correlation is linear but rescaled.
  - Broadband IC: no lock forms (R^2=0.09); basin requires localized seed.
  - Bore-u IC: in-peak lock disrupted (R^2=0.03).
  - Global Gardner companion: ||v_BKdV - v_Gardner||_L2 = 1.11, c_BKdV=1.45
    while c_Gardner=1.93. Gardner is NOT the global solution.

Mechanism candidate from traveling-wave analysis. Let u=U(x-ct), v=V(x-ct).
Integrating the u-equation (assuming localization, so U,V -> 0 at infinity, and
ignoring the small linear viscosity nu*u_xx for the algebraic ansatz):
   -cU + (3/2)U^2 + 3V^2 + V_xx = 0                                 (Eu)
Integrating the v-equation:
   -cV + 3V^2 + V_xx + UV = 0                                       (Ev)
From (Ev): V_xx = V(c - 3V - U). Substituting into (Eu):
   -cU + (3/2)U^2 + 3V^2 + V(c - 3V - U) = 0
   -cU + (3/2)U^2 + V c - U V = 0
   c(V - U) + (3/2)U^2 - U V = 0
   c(V - U) + U(3U/2 - V) = 0
   c(V - U) = U(V - 3U/2)
   c(V - U) = U V - (3/2) U^2
   c V - c U = U V - (3/2) U^2
=> (3/2) U^2 - c U - U V + c V = 0       i.e. (3/2)U^2 - U(c + V) + cV = 0
Quadratic in U:
   U = [(c + V) +/- sqrt((c+V)^2 - 6 c V)] / 3
     = [(c + V) +/- sqrt(c^2 - 4 c V + V^2)] / 3

Two branches. The branch passing through U(V=0)=0 is the one with minus sign:
   U_- = [(c + V) - sqrt(c^2 - 4 c V + V^2)] / 3
At V -> 0: sqrt(c^2(1 - 4V/c + (V/c)^2)) ~ c (1 - 2V/c + V^2/(2c^2) - ... )
   U_- ~ [(c + V) - c(1 - 2V/c + V^2/(2c^2))] / 3
       = [c + V - c + 2V - V^2/(2c)] / 3
       = [3V - V^2/(2c)] / 3
       = V - V^2/(6c)
So at small V the leading local relation is U ~ V (linear), NOT U ~ V^2/2.

This explains the E2 finding alpha = du/d(V^2/2) >> 1: locally u ~ V at leading
order, so u/(V^2/2) ~ 2/V which is large when V is small. The "compound" is
**not** the Gardner m=0 algebraic relation u = V^2/2.

E3 design:

E3a — quantitative test of the traveling-wave ansatz:
  Take the snapshot of E1 IC-A at t=10 (already saved in evidence/E1_A_sech2.npz).
  Estimate c by tracking peak centroid late-time. Then check:
    (i) residual_TWeq = U - U_-(V; c) inside peak support; compute RMS and R^2.
    (ii) compare with the m=0 ansatz: residual_m0 = U - V^2/2 inside peak.
    (iii) check the linear-leading ansatz: U ~ V - V^2/(6c) inside peak.
  Best ansatz minimizes RMS residual.

E3b — basin classification by amplitude and shape:
  Sweep v0 = A * sech^2(x+5) for A in {0.3, 0.6, 1.0, 1.5, 2.0} with u0=0
  to find the lowest A at which a compound forms (lock_max >= 0.8 stable late-time).
  Compare with broadband and bore-u controls (already done in E2).
  Result: amplitude-resolved basin map.

E3c — direct comparison of compound vs Gardner soliton at same v_max:
  For each A in the sweep, find the local v-peak (smoothed), fit an effective
  Gardner soliton V_G(x) = A_G sech^2(sqrt(A_G/6)(x-x0)) with A_G = v_max;
  measure ||v_BKdV_local - V_G||_L2 vs the predicted compound profile from
  U_-(V; c) reconstructed from v_BKdV alone (run only the v-equation forward
  from the BKdV v-snap with u replaced by U_-(V; c) -- if this stays stable
  over short times, the compound IS a U_-(V;c)-driven structure).

This E3 is built around analysis of E1/E2 snapshots (cheap) plus one new
amplitude sweep (E3b). We do not re-run a full Gardner companion.
"""
import os
import time
import json
import numpy as np
import numpy.fft as fft

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence")
os.makedirs(OUTDIR, exist_ok=True)


# -------------- domain --------------
Nx = 256
L = 30.0
x = np.linspace(-L/2, L/2, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2 * np.pi * fft.fftfreq(Nx, d=dx)
ik = 1j * k
kcut = Nx // 3
mask = np.ones(Nx)
for j in range(Nx):
    kidx = j if j <= Nx//2 else j - Nx
    if abs(kidx) > kcut:
        mask[j] = 0.0
dealias = mask


def dx_spec(f):
    return np.real(fft.ifft(ik * fft.fft(f)))


def dxx_spec(f):
    return np.real(fft.ifft(-(k**2) * fft.fft(f)))


def dxxx_spec(f):
    return np.real(fft.ifft(-1j * (k**3) * fft.fft(f)))


def dealiased(f):
    F = fft.fft(f); F *= dealias
    return np.real(fft.ifft(F))


NU_U = 5e-2


def rhs_bkdv(u, v):
    ud = dealiased(u); vd = dealiased(v)
    v2 = dealiased(vd*vd); uv = dealiased(ud*vd)
    uu_x = dealiased(ud * dx_spec(ud))
    u_t = -3.0*uu_x - dx_spec(3.0*v2 + dxx_spec(vd)) + NU_U*dxx_spec(ud)
    vv_x = dealiased(vd * dx_spec(vd))
    v_t = -6.0*vv_x - dxxx_spec(vd) - dx_spec(uv)
    return u_t, v_t


def rk4_bkdv(u, v, dt):
    k1u, k1v = rhs_bkdv(u, v)
    k2u, k2v = rhs_bkdv(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs_bkdv(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs_bkdv(u + dt*k3u, v + dt*k3v)
    return u + (dt/6.0)*(k1u + 2*k2u + 2*k3u + k4u), v + (dt/6.0)*(k1v + 2*k2v + 2*k3v + k4v)


def in_peak(v, frac=0.2):
    vmax = np.max(np.abs(v))
    if vmax < 1e-10:
        return np.zeros_like(v, dtype=bool)
    return np.abs(v) > frac * vmax


def lock_corr(u, v):
    msk = in_peak(v, 0.2)
    if msk.sum() < 5: return 0.0
    a = u[msk]; b = 0.5*v[msk]*v[msk]
    a = a - a.mean(); b = b - b.mean()
    den = np.sqrt(np.sum(a*a) * np.sum(b*b))
    return float(np.sum(a*b)/den) if den > 1e-12 else 0.0


def alpha_fit(u, v):
    msk = in_peak(v, 0.2)
    if msk.sum() < 5: return 0.0, 0.0, 0.0
    vv = v[msk]; uu = u[msk]
    X = 0.5*vv*vv
    A = np.vstack([X, np.ones_like(X)]).T
    sol, *_ = np.linalg.lstsq(A, uu, rcond=None)
    return float(sol[0]), float(sol[1]), float(1 - np.mean((uu - sol[0]*X - sol[1])**2)/(np.var(uu)+1e-12))


def peak_centroid(v):
    w = np.abs(v); s = np.sum(w)
    if s < 1e-10: return 0.0
    phi = 2*np.pi*(x + L/2)/L
    cx = np.sum(w*np.cos(phi))/s; sy = np.sum(w*np.sin(phi))/s
    ang = np.arctan2(sy, cx)
    if ang < 0: ang += 2*np.pi
    return ang*L/(2*np.pi) - L/2


# ----- traveling-wave ansatz tests -----

def U_minus_branch(V, c):
    """U_-(V;c) = [(c+V) - sqrt(c^2 - 4cV + V^2)] / 3, real-valued when
    discriminant >= 0. Discriminant: c^2 - 4cV + V^2 = (V - 2c)^2 - 3c^2.
    >= 0 when |V - 2c| >= sqrt(3) c, i.e. V <= (2 - sqrt(3))c ~ 0.268 c
    or V >= (2 + sqrt(3))c ~ 3.732 c. For small V the small-V branch is OK."""
    disc = c*c - 4.0*c*V + V*V
    disc_safe = np.where(disc >= 0, disc, 0.0)
    U_ = ((c + V) - np.sqrt(disc_safe)) / 3.0
    valid = disc >= 0
    return U_, valid


def fit_speed_from_centroid(t_arr, cent, t_start=2.0):
    msk = t_arr >= t_start
    if msk.sum() < 5: return 0.0
    cv = cent[msk].copy()
    for j in range(1, len(cv)):
        d_ = cv[j] - cv[j-1]
        if d_ > 15: cv[j:] -= 30
        elif d_ < -15: cv[j:] += 30
    return float(np.polyfit(t_arr[msk], cv, 1)[0])


def analyze_TW_ansatz(name, snap_path):
    """Load E1 snapshot at t=10 (and Cs), compute the three ansatz residuals,
    and the traveling-wave R^2 in peak support."""
    d = np.load(snap_path)
    t = d['t']; cent = d['centroid']
    # use snapshot at last time
    sn_t = d['snap_t']; sn_u = d['snap_u']; sn_v = d['snap_v']
    idx = int(np.argmin(np.abs(sn_t - 10.0)))
    u_snap = sn_u[idx]; v_snap = sn_v[idx]
    c_est = fit_speed_from_centroid(t, cent)
    res = dict(name=name, t_snap=float(sn_t[idx]), c_est=float(c_est))
    msk = in_peak(v_snap, 0.2)
    if msk.sum() < 5:
        res['note'] = 'insufficient in-peak points'
        return res
    Vp = v_snap[msk]; Up = u_snap[msk]
    # Ansatz 1: m=0 (alpha=1)
    r_m0 = Up - 0.5*Vp*Vp
    res['rms_m0'] = float(np.sqrt(np.mean(r_m0**2)))
    # Ansatz 2: linear-rescaled u = alpha v^2/2 + beta (best fit)
    al, be, r2_lin = alpha_fit(u_snap, v_snap)
    res['alpha'] = al; res['beta'] = be; res['r2_lin'] = r2_lin
    res['rms_lin'] = float(np.sqrt(np.mean((Up - al*(0.5*Vp*Vp) - be)**2)))
    # Ansatz 3: traveling-wave U_-(V; c_est)
    U_pred, valid = U_minus_branch(Vp, c_est)
    res['n_valid'] = int(np.sum(valid))
    res['n_total'] = int(len(Vp))
    if np.sum(valid) > 5:
        r_tw = Up[valid] - U_pred[valid]
        res['rms_tw_validregion'] = float(np.sqrt(np.mean(r_tw**2)))
        # R^2 of TW ansatz
        Uv = Up[valid]
        res['r2_tw'] = float(1 - np.mean((Uv - U_pred[valid])**2)/(np.var(Uv)+1e-12))
    else:
        res['rms_tw_validregion'] = float('nan'); res['r2_tw'] = float('nan')
    # Ansatz 4: linear-leading-order U ~ V - V^2/(6c)
    U_lin = Vp - (Vp*Vp)/(6.0*c_est)
    res['rms_linleading'] = float(np.sqrt(np.mean((Up - U_lin)**2)))
    res['r2_linleading'] = float(1 - np.mean((Up - U_lin)**2)/(np.var(Up)+1e-12))
    # store profile
    res['u_in'] = Up.tolist(); res['v_in'] = Vp.tolist()
    if np.sum(valid) > 0:
        res['U_pred_TW'] = U_pred.tolist()
    res['v_max_snap'] = float(np.max(np.abs(v_snap)))
    res['u_max_snap'] = float(np.max(np.abs(u_snap)))
    return res


# ----- E3b amplitude sweep -----

def run_amp(A, T=10.0, dt=1e-4):
    v0 = A * (1.0/np.cosh(x + 5))**2
    u0 = np.zeros_like(v0)
    u = u0.copy(); v = v0.copy()
    n_steps = int(round(T/dt)); log_every = int(round(0.1/dt))
    log_t = [0.0]; log_lock = [lock_corr(u, v)]
    log_vmax = [float(np.max(np.abs(v)))]; log_umax = [0.0]
    log_alpha = [0.0]; log_r2 = [0.0]; log_centroid = [peak_centroid(v)]
    t0 = time.time()
    blew = False
    for n in range(1, n_steps+1):
        u, v = rk4_bkdv(u, v, dt)
        if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
            blew = True
            print(f"[A={A}] BLOWUP at step {n}, t={n*dt:.4f}")
            break
        t_now = n*dt
        if n % log_every == 0:
            log_t.append(t_now)
            log_lock.append(lock_corr(u, v))
            log_vmax.append(float(np.max(np.abs(v))))
            log_umax.append(float(np.max(np.abs(u))))
            al, be, r2 = alpha_fit(u, v)
            log_alpha.append(al); log_r2.append(r2)
            log_centroid.append(peak_centroid(v))
    elapsed = time.time() - t0
    print(f"[A={A}] done in {elapsed:.1f}s; v_max(T)={log_vmax[-1]:.3f}, lock(T)={log_lock[-1]:.3f}, "
          f"r2(T)={log_r2[-1]:.3f}, alpha(T)={log_alpha[-1]:.2f}, blew={blew}")
    return dict(A=A, t=np.array(log_t), lock=np.array(log_lock), vmax=np.array(log_vmax),
                umax=np.array(log_umax), alpha=np.array(log_alpha), r2=np.array(log_r2),
                centroid=np.array(log_centroid), blew=blew, elapsed=elapsed, u_final=u, v_final=v)


def main():
    # E3a — analyze E1 snapshots
    print("\n--- E3a: traveling-wave ansatz residual analysis ---")
    e3a = {}
    for nm in ["A_sech2", "B_gauss", "D_two"]:
        path = os.path.join(OUTDIR, f"E1_{nm}.npz")
        if os.path.exists(path):
            r = analyze_TW_ansatz(nm, path)
            e3a[nm] = r
            print(f"\n{nm}: c_est={r['c_est']:.3f}, v_max={r['v_max_snap']:.3f}, u_max={r['u_max_snap']:.3f}")
            print(f"  Ansatz residuals (in-peak RMS):")
            print(f"    m=0 ansatz (u=v^2/2):        RMS={r['rms_m0']:.4f}")
            print(f"    linear-rescaled (u=a*v^2/2+b): RMS={r['rms_lin']:.4f}, R^2={r['r2_lin']:.3f}, alpha={r['alpha']:.2f}")
            print(f"    TW small-V leading (u=v-v^2/(6c)): RMS={r['rms_linleading']:.4f}, R^2={r['r2_linleading']:.3f}")
            print(f"    TW full U_-(V;c) ansatz:     RMS={r['rms_tw_validregion']:.4f}, R^2={r['r2_tw']:.3f}, valid={r['n_valid']}/{r['n_total']}")
        else:
            print(f"  Skip {nm}: no snapshot at {path}")

    # save residual results
    e3a_save = {}
    for nm, r in e3a.items():
        e3a_save[nm] = {k: v for k, v in r.items() if k not in ('u_in','v_in','U_pred_TW')}
    with open(os.path.join(OUTDIR, "E3a_TW_residuals.json"), "w") as f:
        json.dump(e3a_save, f, indent=2)

    # E3b — amplitude sweep
    print("\n--- E3b: amplitude sweep ---")
    amps = [0.3, 0.6, 1.0, 1.5, 2.0]
    e3b = {}
    for A in amps:
        r = run_amp(A)
        e3b[f"A_{A}"] = dict(A=A, vmax_T=float(r['vmax'][-1]),
                              umax_T=float(r['umax'][-1]),
                              lock_T=float(r['lock'][-1]),
                              lock_max=float(np.max(r['lock'])),
                              alpha_T=float(r['alpha'][-1]),
                              r2_T=float(r['r2'][-1]),
                              blew=bool(r['blew']))
        # save full data
        np.savez(os.path.join(OUTDIR, f"E3b_A{A}.npz"),
                 A=A, t=r['t'], lock=r['lock'], vmax=r['vmax'], umax=r['umax'],
                 alpha=r['alpha'], r2=r['r2'], centroid=r['centroid'],
                 u_final=r['u_final'], v_final=r['v_final'])
    with open(os.path.join(OUTDIR, "E3b_amp_sweep.json"), "w") as f:
        json.dump(e3b, f, indent=2)

    print("\nE3 summary:")
    print(json.dumps(dict(E3a={k: {k2:v2 for k2,v2 in v.items() if k2 not in ('u_in','v_in','U_pred_TW')} for k,v in e3a.items()},
                          E3b=e3b), indent=2))


if __name__ == "__main__":
    main()
