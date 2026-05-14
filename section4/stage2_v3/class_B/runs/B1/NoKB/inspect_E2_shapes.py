"""Inspect E2 final-time shapes to understand the (u, v) bound structure."""
import numpy as np
import os

OUT_DIR = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/NoKB/evidence/E2"
for case in ["LO", "HI", "GARDNER_LO"]:
    d = np.load(os.path.join(OUT_DIR, f"E2_{case}_snapshots.npz"))
    x = d["x"]
    t = d["t"]
    u = d["u"]
    v = d["v"]
    m = d["m"]
    # take a few times
    times = [0.0, 2.0, 5.0, 10.0]
    print(f"\n\n========== {case} ==========")
    for ti in times:
        idx = int(np.argmin(np.abs(t - ti)))
        print(f"\n--- t={t[idx]:.2f} ---  v_pk_idx={int(np.argmax(np.abs(v[idx])))}")
        vmax = np.abs(v[idx]).max()
        ix_pk = int(np.argmax(np.abs(v[idx])))
        # Print around the peak
        for j in range(max(0, ix_pk - 8), min(len(x), ix_pk + 9)):
            print(f"  x={x[j]:6.2f}  v={v[idx][j]:+7.4f}  u={u[idx][j]:+7.4f}  "
                  f"v^2/2={0.5*v[idx][j]**2:7.4f}  m={m[idx][j]:+7.4f}  ")

    # also: look at u-peak offset relative to v-peak
    print("\n  Peak offset (x_u_pk - x_v_pk) over time:")
    for ti in [0.5, 1.0, 2.0, 5.0, 10.0]:
        idx = int(np.argmin(np.abs(t - ti)))
        ix_v = int(np.argmax(np.abs(v[idx])))
        ix_u = int(np.argmax(u[idx]))
        # account for periodicity
        dx_off = x[ix_u] - x[ix_v]
        L = x[-1] - x[0] + (x[1] - x[0])
        if dx_off > L/2: dx_off -= L
        if dx_off < -L/2: dx_off += L
        print(f"    t={ti:.2f}  x_v_pk={x[ix_v]:+6.2f}  x_u_pk={x[ix_u]:+6.2f}  "
              f"Δx={dx_off:+6.3f}  v_pk={v[idx][ix_v]:.3f}  u_max={u[idx][ix_u]:.3f}")
