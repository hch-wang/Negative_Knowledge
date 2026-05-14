"""Print actual u(x) and v(x) profiles at selected times around the peak."""
import numpy as np
import os

OUT_DIR = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/NoKB/evidence/E1"
data = np.load(os.path.join(OUT_DIR, "E1_snapshots.npz"))
x = data["x"]
t = data["t"]
u_t = data["u"]
v_t = data["v"]
m_t = data["m"]
print(f"snapshots: {len(t)}")

def print_profile(idx, half_window=12):
    ti = t[idx]
    v = v_t[idx]
    u = u_t[idx]
    m = m_t[idx]
    ix = int(np.argmax(np.abs(v)))
    print(f"\n=== t={ti:.2f} === peak at x={x[ix]:.2f} v={v[ix]:.3f} u={u[ix]:.3f}")
    lo = max(0, ix - half_window)
    hi = min(len(x), ix + half_window + 1)
    print(" x        v        u        v^2/2     m       u/(v^2/2)")
    for j in range(lo, hi):
        vv = v[j]
        uu = u[j]
        vh = 0.5 * vv * vv
        rat = uu / vh if abs(vh) > 1e-4 else float("nan")
        print(f"{x[j]:6.2f}  {vv:8.4f}  {uu:8.4f}  {vh:8.4f}  {m[j]:8.4f}  {rat:8.3f}")

# Snapshots at t = 0, 1, 5, 10, 15, 20
for idx in [0, 4, 20, 40, 60, 80]:
    print_profile(idx)

# Look at "mass" of u vs v^2/2 in core:
print("\n\nCore mass comparison (over core50 mask):")
for idx in [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80]:
    v = v_t[idx]
    u = u_t[idx]
    abs_v = np.abs(v)
    vmax = abs_v.max()
    mask = abs_v > 0.5 * vmax
    M_u = np.sum(u[mask]) * (x[1] - x[0])
    M_vh = np.sum(0.5 * v[mask] ** 2) * (x[1] - x[0])
    print(f"  t={t[idx]:5.2f}  M_u(core)={M_u:7.4f}  M_v^2/2(core)={M_vh:7.4f}  ratio={M_u/(M_vh+1e-9):6.3f}")
