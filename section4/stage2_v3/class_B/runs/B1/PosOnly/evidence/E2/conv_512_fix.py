"""
Bug fix for E2 convergence: Nx=512 needs dt <~ 2.5e-5 because dispersion CFL
scales as 1/k_max^3 and k_max doubles. We DON'T extend T=10; T=2.0 is plenty
to see whether the m-trajectory of Nx=256 vs Nx=512 differs systematically.
"""
import os
import sys
import time
import numpy as np

sys.path.insert(0, "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/PosOnly")
import candidate as C

OUT = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/PosOnly/evidence/E2"

T = 2.0
dt = 2.5e-5
SNAP_TIMES = np.array([0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0])
SNAP_STEPS = np.round(SNAP_TIMES / dt).astype(int)

solver512 = C.Solver(Nx=512, L=30.0)
v0 = 1.5 * (1.0 / np.cosh(solver512.x + 5.0)) ** 2
u0 = 0.5 * v0 ** 2
ts, us, vs, diags = C.run(solver512, u0, v0, T, dt, SNAP_STEPS,
                          nu_u=0.0, label="conv_Nx512_dt2.5e-5_T2")
np.savez(os.path.join(OUT, "conv_A1.5_Nx512_dt2.5e-5.npz"),
         x=solver512.x, t=ts, u=us, v=vs,
         diagnostics=np.array(diags, dtype=object))

# Reload Nx=256 result and compare
d256 = np.load(os.path.join(OUT, "sweep_A1.5_Nx256.npz"),
               allow_pickle=True)["diagnostics"]
d256_by_t = {round(float(d["t"]), 4): d for d in d256}
print(f"{'t':>5s} {'v256':>8s} {'v512':>8s} {'rel':>7s} "
      f"{'u256':>8s} {'u512':>8s} {'mglob256':>9s} {'mglob512':>9s} "
      f"{'R256':>6s} {'R512':>6s} {'min256':>7s} {'min512':>7s}")
for d512 in diags:
    tt = round(float(d512["t"]), 4)
    if tt in d256_by_t:
        a = d256_by_t[tt]
        rel = abs(a["vmax"] - d512["vmax"]) / max(d512["vmax"], 1e-6)
        print(f"{tt:5.2f} {a['vmax']:8.4f} {d512['vmax']:8.4f} {rel:7.2e} "
              f"{a['umax']:8.3f} {d512['umax']:8.3f} "
              f"{a['norm_m_global']:9.4f} {d512['norm_m_global']:9.4f} "
              f"{a['R_locking']:6.3f} {d512['R_locking']:6.3f} "
              f"{a['norm_m_inside']:7.3f} {d512['norm_m_inside']:7.3f}")
