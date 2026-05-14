"""
Walk through diagnostics(t) for each IC to see when (if ever) the locking R was
near 1 and the m_inside small, and when fragmentation happened. We want the
TIME EVOLUTION of locking — not just final.
"""
import os
import numpy as np

D = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/PosOnly/evidence/E1"

names = [
    "sech2_A1.5_m0", "gauss_A1.5_m0", "sech2_A1.5_u0zero",
    "sech2_A0.4_m0", "bimodal_m0", "bore_plus_v",
]
print(f"{'IC':22s} {'t':>5s} {'vmax':>6s} {'umax':>6s} {'m_glo':>6s} {'m_in':>6s} "
      f"{'m_out':>6s} {'R':>7s} {'R2':>7s} {'np':>3s}")
print("-" * 90)
for n in names:
    p = os.path.join(D, n + ".npz")
    data = np.load(p, allow_pickle=True)
    diags = data["diagnostics"]
    for d in diags:
        if d["t"] in (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0):
            print(f"{n:22s} {d['t']:5.2f} {d['vmax']:6.3f} {d['umax']:6.3f} "
                  f"{d['norm_m_global']:6.3f} {d['norm_m_inside']:6.3f} "
                  f"{d['norm_m_outside']:6.3f} {d['R_locking']:7.3f} "
                  f"{d['R2_locking']:7.3f} {d['n_peaks']:3d}")
    print()
