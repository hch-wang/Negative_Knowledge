"""
E3: Final round.  Tests three things in a single run set:

A) Speed test (H_A: Gardner-template).  Compare v-peak phase speed against the
   KdV/Gardner prediction c = 6A (in the standard 'v_t + 6 v v_x + v_xxx = 0'
   convention; for A=0.6 sech^2: c=6*A=3.6 — but our small-amplitude pulses
   were never proper Gardner solitons, so we instead measure the empirical
   c(t) and compare against 6 v_peak(t) AND 6 v_peak + (3/2) v_peak^2 to test
   whether the v-equation is dominated by Gardner or by BKdV's full -d_x(uv).

B) Viscosity ablation (H_E).  Run the SAME low-amplitude sech^2 IC with
   ν_u = 0 (no Burgers viscosity) and ν_u = 5e-2.  If 'compound m≈0' is a
   viscosity artifact, ν=0 should give a very different behaviour.  If the
   persistent positive m and the u-wake are the same regardless of ν, H_E
   is falsified.

C) Pulse-shape characterisation.  At the final time, extract the (u, v, m)
   profiles and the u-peak vs v-peak offset Δx.  This characterises the
   ACTUAL compound structure, which we have now seen is NOT u=v^2/2 but
   rather a (v-pulse + u-wake-with-shock) structure.

We additionally include the FIRST asymmetric IC (a sign-mixed multipulse)
to extend basin-of-attraction observation.

Output: time series and final snapshots per case in evidence/E3/.
"""
import numpy as np
import json
import os

OUT_DIR = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/NoKB/evidence/E3"
os.makedirs(OUT_DIR, exist_ok=True)

Nx = 256
L = 30.0
dx = L / Nx
x = -L / 2 + dx * np.arange(Nx)
k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k * k
kmax = (2.0 / 3.0) * (np.pi / dx)
dealias = (np.abs(k) <= kmax).astype(float)


def to_phys(uh):
    return np.real(np.fft.ifft(uh))


def rhs(u, v, nu_u):
    uhat = np.fft.fft(u) * dealias
    vhat = np.fft.fft(v) * dealias
    u_d = to_phys(uhat)
    v_d = to_phys(vhat)
    ux = to_phys(ik * uhat)
    uux = u_d * ux
    v2 = v_d * v_d
    v2_x = to_phys(ik * np.fft.fft(v2) * dealias)
    vvx = v_d * to_phys(ik * vhat)
    uv = u_d * v_d
    uv_x = to_phys(ik * np.fft.fft(uv) * dealias)
    vxx = to_phys(-k2 * vhat)
    vxx_x = to_phys(ik * np.fft.fft(vxx) * dealias)
    rhs_u = -3.0 * uux - 3.0 * v2_x - vxx_x + nu_u * to_phys(-k2 * uhat)
    rhs_v = -6.0 * vvx - vxx_x - uv_x
    return rhs_u, rhs_v


def step(u, v, dt, nu):
    k1u, k1v = rhs(u, v, nu)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v, nu)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v, nu)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v, nu)
    return (
        u + (dt / 6) * (k1u + 2 * k2u + 2 * k3u + k4u),
        v + (dt / 6) * (k1v + 2 * k2v + 2 * k3v + k4v),
    )


def unwrap_periodic(xs, L):
    xs = np.asarray(xs).copy()
    for i in range(1, len(xs)):
        while xs[i] - xs[i - 1] > L / 2:
            xs[i] -= L
        while xs[i] - xs[i - 1] < -L / 2:
            xs[i] += L
    return xs


def run_case(name, v0, u0, T=8.0, dt=1e-4, nu=5e-2, snap_interval=0.2):
    print(f"\n--- {name}  nu={nu} ---")
    print(f"v0_max={v0.max():.3f}  v0_min={v0.min():.3f}  L2_v0={np.sqrt(dx*np.sum(v0*v0)):.3f}")
    u, v = u0.copy(), v0.copy()
    N_steps = int(T / dt)
    snap_every = int(snap_interval / dt)
    times = []
    v_peaks = []
    u_peaks = []
    m_peaks = []
    x_vpk = []
    x_upk = []
    L2m_full = []
    L2m_core = []
    full_snaps = []  # save sparse snapshots for shape analysis
    snap_times = []

    def core_mask(v):
        a = np.abs(v)
        m = a > 0.5 * a.max()
        ix = int(np.argmax(a))
        N = len(v)
        out = np.zeros(N, bool)
        out[ix] = True
        i = (ix + 1) % N
        while m[i] and i != ix:
            out[i] = True
            i = (i + 1) % N
        i = (ix - 1) % N
        while m[i] and i != ix:
            out[i] = True
            i = (i - 1) % N
        return out

    def diagnose(t):
        m = u - 0.5 * v * v
        ix_v = int(np.argmax(np.abs(v)))
        ix_u = int(np.argmax(u))
        cm = core_mask(v)
        times.append(float(t))
        v_peaks.append(float(v[ix_v]))
        u_peaks.append(float(u[ix_u]))
        m_peaks.append(float(m[ix_v]))
        x_vpk.append(float(x[ix_v]))
        x_upk.append(float(x[ix_u]))
        L2m_full.append(float(np.sqrt(dx * np.sum(m * m))))
        L2m_core.append(float(np.sqrt(dx * np.sum((m * cm) ** 2))))

    diagnose(0.0)
    snap_times.append(0.0)
    full_snaps.append((u.copy(), v.copy(), (u - 0.5 * v * v).copy()))

    for n in range(1, N_steps + 1):
        u, v = step(u, v, dt, nu)
        if n % snap_every == 0:
            t = n * dt
            diagnose(t)
            if n % (snap_every * 4) == 0:  # save shape every 0.8 t
                full_snaps.append((u.copy(), v.copy(), (u - 0.5 * v * v).copy()))
                snap_times.append(float(t))

    # save
    np.savez(
        os.path.join(OUT_DIR, f"E3_{name}_summary.npz"),
        x=x,
        t=np.array(times),
        v_peak=np.array(v_peaks),
        u_peak=np.array(u_peaks),
        m_peak=np.array(m_peaks),
        x_vpk=np.array(x_vpk),
        x_upk=np.array(x_upk),
        L2m_full=np.array(L2m_full),
        L2m_core=np.array(L2m_core),
        snap_t=np.array(snap_times),
        snaps=np.array(full_snaps),
    )

    # estimate speed in later half
    tarr = np.array(times)
    xpk_u = unwrap_periodic(x_vpk, L)
    half = len(tarr) // 2
    if half + 4 < len(tarr):
        c_est = (xpk_u[-1] - xpk_u[half]) / (tarr[-1] - tarr[half])
    else:
        c_est = float("nan")
    print(f"  estimated v-peak phase speed (late half) = {c_est:.3f}")
    return dict(
        name=name, nu=nu,
        t=tarr, v_peak=np.array(v_peaks), u_peak=np.array(u_peaks),
        m_peak=np.array(m_peaks), c_est=float(c_est), x_vpk_unwrapped=xpk_u,
    )


# ===================== CASE A: LO with nu=5e-2 (baseline LO from E2 but T=8) =====================
A_lo, sig_lo = 0.6, 1.5
v_lo = A_lo * np.exp(-(x ** 2) / (2 * sig_lo ** 2))
u_lo = 0.5 * v_lo * v_lo
res_A = run_case("LO_nu5e2", v_lo, u_lo, T=8.0, nu=5e-2)

# ===================== CASE B: LO with nu=0 (ablation) =====================
res_B = run_case("LO_nu0", v_lo, u_lo, T=8.0, nu=0.0)

# ===================== CASE C: HI with nu=5e-2 (Gardner-speed test, baseline) =====================
A_hi, sig_hi = 1.5, 1.2
v_hi = A_hi * np.exp(-(x ** 2) / (2 * sig_hi ** 2))
u_hi = 0.5 * v_hi * v_hi
res_C = run_case("HI_nu5e2", v_hi, u_hi, T=8.0, nu=5e-2)

# ===================== CASE D: sign-mixed multipulse (basin test) =====================
# v_0 = 0.6 sech^2(x/W) - 0.4 sech^2((x-4)/W) ; u_0 = v_0^2/2
W = 1.5
v_mp = 0.6 * (1 / np.cosh((x + 2) / W)) ** 2 - 0.4 * (1 / np.cosh((x - 3) / W)) ** 2
u_mp = 0.5 * v_mp * v_mp
res_D = run_case("MULTIPULSE", v_mp, u_mp, T=8.0, nu=5e-2)


print("\n\n===== Speed comparison =====")
for r in [res_A, res_B, res_C, res_D]:
    # Gardner prediction: c = 6 A + (3/2) A^2 for soliton in
    # v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0 ; but our IC isn't a Gardner soliton.
    # We compare measured c against (a) 6*<v_peak> and (b) 6*<v>+1.5*<v>^2.
    v_mean_late = float(np.mean(r["v_peak"][len(r["v_peak"]) // 2:]))
    c_kdv = 6.0 * v_mean_late
    c_gardner = 6.0 * v_mean_late + 1.5 * v_mean_late ** 2
    print(f"  {r['name']:>14s}  c_meas={r['c_est']:+6.3f}  <v_peak>_late={v_mean_late:+6.3f}  "
          f"c_KdV={c_kdv:+6.3f}  c_Gardner={c_gardner:+6.3f}  ratio_meas/Gardner={r['c_est']/(c_gardner+1e-9):.2f}")

print("\n===== Viscosity ablation =====")
print(f"  LO nu=5e-2:  final v_peak={res_A['v_peak'][-1]:.3f}  m_peak={res_A['m_peak'][-1]:.3f}  L2m_core ~ from summary npz")
print(f"  LO nu=0   :  final v_peak={res_B['v_peak'][-1]:.3f}  m_peak={res_B['m_peak'][-1]:.3f}")
print(f"  HI nu=5e-2:  final v_peak={res_C['v_peak'][-1]:.3f}  m_peak={res_C['m_peak'][-1]:.3f}")

print("done.")
