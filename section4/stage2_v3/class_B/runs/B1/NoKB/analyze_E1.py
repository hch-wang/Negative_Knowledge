"""Analyze E1 snapshots: compound formation diagnostics."""
import numpy as np
import json
import os

OUT_DIR = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/NoKB/evidence/E1"
data = np.load(os.path.join(OUT_DIR, "E1_snapshots.npz"))
x = data["x"]
t = data["t"]
u_t = data["u"]
v_t = data["v"]
m_t = data["m"]
dx = x[1] - x[0]
L = x[-1] - x[0] + dx
print(f"snapshots: {len(t)}, x range {x[0]:.2f}..{x[-1]:.2f}, dx={dx:.4f}")


def find_peak_window(v, frac=0.5):
    """Periodic-aware peak window: x where |v| > frac * vmax (contiguous around the peak)."""
    abs_v = np.abs(v)
    vmax = abs_v.max()
    if vmax < 1e-6:
        return np.zeros_like(v, dtype=bool)
    ix_max = int(np.argmax(abs_v))
    mask = abs_v > frac * vmax
    # use the contiguous-region containing ix_max with periodic wrap
    # find left and right edges scanning out from ix_max
    N = len(v)
    out = np.zeros(N, dtype=bool)
    out[ix_max] = True
    # scan right
    i = (ix_max + 1) % N
    while mask[i] and i != ix_max:
        out[i] = True
        i = (i + 1) % N
    # scan left
    i = (ix_max - 1) % N
    while mask[i] and i != ix_max:
        out[i] = True
        i = (i - 1) % N
    return out


# Per-snapshot diagnostics
records = []
for i, ti in enumerate(t):
    u = u_t[i]
    v = v_t[i]
    m = m_t[i]
    mask50 = find_peak_window(v, frac=0.5)  # "core" 50% of peak
    mask30 = find_peak_window(v, frac=0.3)
    mask15 = find_peak_window(v, frac=0.15)
    abs_v = np.abs(v)
    vmax = abs_v.max()
    ix_max = int(np.argmax(abs_v))
    v_peak = float(v[ix_max])
    u_peak = float(u[ix_max])
    m_peak = float(m[ix_max])

    # in-core peak metric: |m| / (v^2/2 scale) at peak
    rel_m_peak = m_peak / max(0.5 * v_peak * v_peak, 1e-6)

    # L2 of m over core 50%
    L2_m_core50 = float(np.sqrt(dx * np.sum((m * mask50) ** 2)))
    L2_m_core30 = float(np.sqrt(dx * np.sum((m * mask30) ** 2)))
    L2_v_core50 = float(np.sqrt(dx * np.sum((v * mask50) ** 2)))
    L2_v_core30 = float(np.sqrt(dx * np.sum((v * mask30) ** 2)))
    L2_v_full = float(np.sqrt(dx * np.sum(v * v)))
    L2_u_full = float(np.sqrt(dx * np.sum(u * u)))
    L2_m_full = float(np.sqrt(dx * np.sum(m * m)))

    # Width of peak
    width50 = float(np.count_nonzero(mask50)) * dx
    width30 = float(np.count_nonzero(mask30)) * dx
    width15 = float(np.count_nonzero(mask15)) * dx

    # Mass / first moment in the peak window 30%
    if mask30.any():
        xc = float(np.sum(x[mask30] * v[mask30]) / max(np.sum(v[mask30]), 1e-12))
    else:
        xc = float(x[ix_max])

    # Functional locking: r = corr(u, v^2/2) over core50
    if mask50.sum() > 3:
        uu = u[mask50]
        vv = 0.5 * (v[mask50] ** 2)
        # ratio at peak and slope through origin
        slope, _ = np.polyfit(vv, uu, 1)
        # raw correlation
        if np.std(uu) > 1e-12 and np.std(vv) > 1e-12:
            r = float(np.corrcoef(uu, vv)[0, 1])
        else:
            r = float("nan")
    else:
        slope = float("nan")
        r = float("nan")

    # Spectral high-k fraction
    vhat = np.fft.fft(v)
    Pk = np.abs(vhat) ** 2
    k = 2 * np.pi * np.fft.fftfreq(len(v), d=dx)
    high = np.abs(k) > 0.5 * np.abs(k).max()
    hi_frac = float(Pk[high].sum() / max(Pk.sum(), 1e-30))

    records.append(
        dict(
            t=float(ti),
            v_peak=v_peak,
            u_peak=u_peak,
            m_peak=m_peak,
            rel_m_peak=rel_m_peak,
            L2_m_full=L2_m_full,
            L2_m_core50=L2_m_core50,
            L2_m_core30=L2_m_core30,
            L2_v_core50=L2_v_core50,
            L2_v_core30=L2_v_core30,
            L2_v_full=L2_v_full,
            L2_u_full=L2_u_full,
            width15=width15,
            width30=width30,
            width50=width50,
            xc_30=xc,
            x_peak=float(x[ix_max]),
            uv_locking_slope=float(slope),
            uv_locking_r=r,
            spec_hi_frac=hi_frac,
        )
    )

with open(os.path.join(OUT_DIR, "E1_analysis.json"), "w") as f:
    json.dump(records, f)

# Print summary
print("t      v_peak  m_peak rel_m  L2m_core50  width50  slope  corr  hi_frac")
for r in records[::4]:  # every 4th (every 1.0 in t)
    print(
        f"{r['t']:5.2f}  {r['v_peak']:6.3f}  {r['m_peak']:7.3f}  {r['rel_m_peak']:7.3f}  "
        f"{r['L2_m_core50']:9.4f}  {r['width50']:6.3f}  {r['uv_locking_slope']:6.3f}  "
        f"{r['uv_locking_r']:6.3f}  {r['spec_hi_frac']:.2e}"
    )

# Speed: dx_peak/dt over windows where peak is well-defined and not wrapping
xpeaks = np.array([r["xc_30"] for r in records])
ts = np.array([r["t"] for r in records])
# unwrap periodically
xp_u = np.copy(xpeaks)
for i in range(1, len(xp_u)):
    while xp_u[i] - xp_u[i - 1] > L / 2:
        xp_u[i] -= L
    while xp_u[i] - xp_u[i - 1] < -L / 2:
        xp_u[i] += L
# Estimate speeds from 4-snapshot windows
window = 8
speeds = []
times_s = []
for i in range(window, len(ts) - window):
    dx_s = xp_u[i + window] - xp_u[i - window]
    dt_s = ts[i + window] - ts[i - window]
    speeds.append(dx_s / dt_s)
    times_s.append(ts[i])
speeds = np.array(speeds)
times_s = np.array(times_s)
print("\nspeed of compound (windowed):")
for ts_i, s in zip(times_s[::4], speeds[::4]):
    print(f"  t={ts_i:5.2f}  c={s:6.3f}")

# Gardner soliton speed comparison
# Gardner equation: v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0
# Sech^2 soliton (single-bump): v = A sech^2((x - c t)/W) ?  Actually Gardner equation
# has more complex soliton structure (sech with rational denominator).
# For small amplitude, c ~ 3 A + (small correction).
# Let's just report mean amplitude.
print(f"\nmean v_peak after t>=5 (steady-ish): {np.mean([r['v_peak'] for r in records if r['t']>=5]):.3f}")
print(f"std v_peak after t>=5: {np.std([r['v_peak'] for r in records if r['t']>=5]):.3f}")

# Check the m/v^2 ratio at the peak point
print("\nm_peak vs 0.5*v_peak^2 (at v-peak point):")
for r in records[::8]:
    print(
        f"  t={r['t']:5.2f}  v={r['v_peak']:6.3f}  u={r['u_peak']:6.3f}  "
        f"0.5v^2={0.5*r['v_peak']**2:6.3f}  m={r['m_peak']:7.3f}  ratio u/(v^2/2)={r['u_peak']/(0.5*r['v_peak']**2+1e-9):.3f}"
    )

print("done")
