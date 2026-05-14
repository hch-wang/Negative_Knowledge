"""Analyze E3 results: shape, m structure, and wake offset across nu and IC."""
import numpy as np
import os

OUT = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B1/NoKB/evidence/E3"

L = 30.0
for name in ["LO_nu5e2", "LO_nu0", "HI_nu5e2", "MULTIPULSE"]:
    f = np.load(os.path.join(OUT, f"E3_{name}_summary.npz"))
    x = f["x"]
    t = f["t"]
    v_peak = f["v_peak"]
    u_peak = f["u_peak"]
    m_peak = f["m_peak"]
    x_vpk = f["x_vpk"]
    x_upk = f["x_upk"]
    L2m_core = f["L2m_core"]
    L2m_full = f["L2m_full"]
    snap_t = f["snap_t"]
    snaps = f["snaps"]  # shape: (n_snap, 3, Nx) with (u, v, m)

    print(f"\n========== {name} ==========")
    print(f"  T_final = {t[-1]:.2f}, snapshots = {len(snap_t)}")
    print(f"  v_peak: init={v_peak[0]:.3f}  half={v_peak[len(t)//2]:.3f}  final={v_peak[-1]:.3f}")
    print(f"  m_peak: init={m_peak[0]:+.3f}  half={m_peak[len(t)//2]:+.3f}  final={m_peak[-1]:+.3f}")
    print(f"  L2m_core: init={L2m_core[0]:.3f}  half={L2m_core[len(t)//2]:.3f}  final={L2m_core[-1]:.3f}")
    print(f"  L2m_full: init={L2m_full[0]:.3f}  half={L2m_full[len(t)//2]:.3f}  final={L2m_full[-1]:.3f}")
    # u-peak to v-peak periodic offset
    print("\n  t,    v_pk,   u_pk(max),  m_at_v_pk,   x_v_pk,   x_u_pk(max),  Δx (periodic)")
    for i in range(0, len(t), max(1, len(t) // 8)):
        dx_off = x_upk[i] - x_vpk[i]
        if dx_off > L / 2: dx_off -= L
        if dx_off < -L / 2: dx_off += L
        print(f"   {t[i]:5.2f}  {v_peak[i]:+6.3f}  {u_peak[i]:+6.3f}     "
              f"{m_peak[i]:+6.3f}     {x_vpk[i]:+6.2f}    {x_upk[i]:+6.2f}      {dx_off:+6.3f}")

    # final snapshot shape (use the last snap)
    u_f, v_f, m_f = snaps[-1]
    ix_v = int(np.argmax(np.abs(v_f)))
    # report around peak
    print(f"\n  Final shape near v-peak (last snap t={snap_t[-1]:.2f}):")
    print("    x      v       u      v^2/2     m      u-v^2/2")
    N = len(x)
    for j in range(ix_v - 10, ix_v + 11):
        jj = j % N
        vh = 0.5 * v_f[jj] ** 2
        print(f"    {x[jj]:+6.2f}  {v_f[jj]:+7.4f}  {u_f[jj]:+7.4f}  {vh:7.4f}  {m_f[jj]:+7.4f}  {u_f[jj]-vh:+7.4f}")
print("\ndone")
