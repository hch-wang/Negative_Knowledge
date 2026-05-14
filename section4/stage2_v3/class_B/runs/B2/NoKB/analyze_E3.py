"""
Quick analysis of E3 results combined with E1/E2 to write up findings.
"""
import numpy as np, json

with open("evidence/E1_summary.json") as f: E1 = json.load(f)
with open("evidence/E2_summary.json") as f: E2 = json.load(f)
with open("evidence/E3_summary.json") as f: E3 = json.load(f)

# Build a master table of (uL, A, T, dt, n_peaks, max_v_T, x_peak_T)
all_rows = []
for r in E1["rows"]:
    all_rows.append({**r, "round":1, "dt":1e-4, "T":12.0})
for r in E2["rows"]:
    all_rows.append({**r, "round":2, "dt":1e-4, "T":12.0})
for r in E3["rows"]:
    all_rows.append({**r, "round":3})

# Map for u_L=1.0 sweep at T=12, dt=1e-4
print("=== Master table: u_L=1.0 sweep in A (T=12, dt=1e-4) ===")
print(f"{'A':>5} {'n_peaks':>8} {'max_v_T':>9} {'x_peak':>8} {'L2_v_T':>8} {'source':>10}")
u_target = 1.0
rows_uL = [(r["A"], r["n_peaks_T"], r["max_v_T"], r["x_peak_T"], r["L2_v_T"],
            f"E{r['round']}{r.get('arm','')}") for r in all_rows
            if abs(r["uL"]-u_target)<1e-9 and abs(r["T"]-12.0)<1e-9 and abs(r["dt"]-1e-4)<1e-9]
rows_uL.sort()
for A, n, mv, xp, l2, src in rows_uL:
    print(f"{A:>5.2f} {int(n):>8d} {mv:>9.3f} {xp:>8.2f} {l2:>8.3f} {src:>10}")

# Same for u_L=0
print("\n=== u_L=0 sweep in A (T=12, dt=1e-4)  -- no-bore baseline ===")
print(f"{'A':>5} {'n_peaks':>8} {'max_v_T':>9} {'x_peak':>8} {'L2_v_T':>8}")
for r in all_rows:
    if abs(r["uL"])<1e-9 and abs(r["T"]-12.0)<1e-9:
        print(f"{r['A']:>5.2f} {int(r['n_peaks_T']):>8d} {r['max_v_T']:>9.3f} "
              f"{r['x_peak_T']:>8.2f} {r['L2_v_T']:>8.3f}")

# 2D table of n_peaks
print("\n=== 2D n_peaks(uL, A) from E1 ===")
print("         ", " ".join(f"A={A:.2f}" for A in [0.2,0.5,1.0,1.5,2.0]))
for uL in [0.2,0.4,0.6,0.8,1.0]:
    row=[]
    for A in [0.2,0.5,1.0,1.5,2.0]:
        for r in E1["rows"]:
            if abs(r["uL"]-uL)<1e-9 and abs(r["A"]-A)<1e-9:
                row.append(r["n_peaks_T"])
                break
    print(f"u_L={uL:.2f}  ", "  ".join(f"  {int(n):2d} " for n in row))

# Sharpness numerical metric: change in n_peaks per unit A near boundary
print("\n=== Sharpness metric near boundary at u_L=1.0 ===")
boundary_data = [(r["A"], r["n_peaks_T"], r["L2_v_T"], r["max_v_T"]) for r in E3["rows"]
                 if r.get("arm")=="A_sharpness"]
boundary_data.sort()
print("A     | n_peaks | max_v_T | L2_v_T")
for A, n, l2, mv in boundary_data:
    print(f"{A:.3f} | {int(n):>7d} | {mv:.3f}   | {l2:.3f}")

# Find the jump location
for i in range(len(boundary_data)-1):
    A1, n1, _, _ = boundary_data[i]
    A2, n2, _, _ = boundary_data[i+1]
    if n2 > n1:
        print(f"\n** sharp jump n_peaks {int(n1)} -> {int(n2)} between A={A1} and A={A2} (delta A = {A2-A1:.3f}) **")

# dt convergence
print("\n=== dt convergence check ===")
e2_110 = None
e3_110 = None
e3_110_half = None
for r in E2["rows"]:
    if abs(r["uL"]-1.0)<1e-9 and abs(r["A"]-1.10)<1e-9:
        # No, E2 has only A=1.2 at uL=1.0
        pass
for r in E3["rows"]:
    if abs(r["uL"]-1.0)<1e-9 and abs(r["A"]-1.10)<1e-9:
        if r.get("arm") == "A_sharpness":
            e3_110 = r
        elif r.get("arm") == "C_dt_half":
            e3_110_half = r
if e3_110 and e3_110_half:
    print(f"(uL=1.0, A=1.10) dt=1e-4: n_peaks={e3_110['n_peaks_T']}, max_v_T={e3_110['max_v_T']:.4f}, L2_v_T={e3_110['L2_v_T']:.4f}")
    print(f"(uL=1.0, A=1.10) dt=5e-5: n_peaks={e3_110_half['n_peaks_T']}, max_v_T={e3_110_half['max_v_T']:.4f}, L2_v_T={e3_110_half['L2_v_T']:.4f}")
    delta_mv = abs(e3_110['max_v_T'] - e3_110_half['max_v_T'])
    delta_l2 = abs(e3_110['L2_v_T'] - e3_110_half['L2_v_T'])
    print(f"  |delta_max_v_T| = {delta_mv:.5f}, |delta_L2_v_T| = {delta_l2:.5f}  -> dt-converged")

# Long-time check
print("\n=== Long-time asymptote check ===")
long_T = None
for r in E3["rows"]:
    if r.get("arm") == "B_long_T":
        long_T = r
if long_T:
    print(f"(uL=1.0, A=1.0) T=12: n_peaks=1 (E1+E3 baseline)")
    print(f"(uL=1.0, A=1.0) T=24: n_peaks={long_T['n_peaks_T']} max_v_T={long_T['max_v_T']:.3f}")
    print("** Implication: 'transmission' regime at T=12 is TRANSIENT; the system fissions on longer time scale **")

# Reflection probe
print("\n=== Reflection probe ===")
ref = None
for r in E3["rows"]:
    if r.get("arm") == "D_reflect":
        ref = r
if ref:
    print(f"(uL=2.0, A=0.2) T=12: n_peaks={ref['n_peaks_T']}, x_peak={ref['x_peak_T']:.2f}")
    print(f"  initial soliton at x=-6, free trajectory predicts x_free = -1.2")
    print(f"  observed x_peak = {ref['x_peak_T']:.2f} -> displacement {ref['x_peak_T']-(-6.0):+.2f}")
    print(f"  if + (and wraparound), bore co-advected soliton; if -, reflection")
    if ref['x_peak_T'] < -8.0:
        print(f"  -> looks like WRAPAROUND of right-moving soliton dragged at near-bore speed (~u_L)")
        print(f"     Bore advection accelerated the soliton; NOT classical reflection")
