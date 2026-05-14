"""
Analyse E1 sweep output:
* classify each (uL, A) into a regime by inspecting v(x,T)
* check whether soliton survives at large amplitude / small bore
* identify candidate phase boundaries

Regime classification rules (heuristic, refined from inspection):
  - "transmission" : exactly 1 peak with height > 0.5 * A AND located beyond bore initial pos (x>0 for the original soliton or wraparound at x>0)
  - "destruction"  : peak height < 0.3 * A OR n_peaks > 3
  - "fission"      : 2-3 peaks, each with non-trivial amplitude
  - "trapped"      : peak still on left side (x<0) and height moderate
"""
import numpy as np
import json, os

with open("evidence/E1_summary.json") as f:
    summary = json.load(f)

rows = summary["rows"]
uL_grid = summary["uL_grid"]
A_grid  = summary["A_grid"]

# Build matrices indexed by (i_uL, j_A)
def grid_field(key):
    M = np.zeros((len(uL_grid), len(A_grid)))
    for i, uL in enumerate(uL_grid):
        for j, A in enumerate(A_grid):
            for r in rows:
                if abs(r["uL"]-uL)<1e-9 and abs(r["A"]-A)<1e-9:
                    M[i,j] = r[key]
    return M

max_v_T  = grid_field("max_v_T")
L2_v_T   = grid_field("L2_v_T")
n_peaks  = grid_field("n_peaks_T")
x_peak_T = grid_field("x_peak_T")
bore_step_T = grid_field("bore_step_T")

print("\n== max_v(T) / A_initial  ==  (1.0 = perfect transmission of amplitude)")
print(f"{'A\\uL':>8}", *[f"{u:>8.2f}" for u in uL_grid])
for j, A in enumerate(A_grid):
    print(f"{A:>8.2f}", *[f"{max_v_T[i,j]/A:>8.3f}" for i,u in enumerate(uL_grid)])

print("\n== L2_v(T) / L2_v(0)  ==  (1.0 = perfect transmission of mass)")
print(f"{'A\\uL':>8}", *[f"{u:>8.2f}" for u in uL_grid])
for j, A in enumerate(A_grid):
    # KdV soliton's L2 norm = A * sqrt(4/3) * sqrt(2/A) ... wait, more carefully
    # int sech^4(b*x) dx = 4/(3*b).  So int v^2 dx = A^2 * 4/(3b), with b=sqrt(A/2).
    # L2 = A * sqrt(4*sqrt(2/A)/3) = A * sqrt(4/(3*sqrt(A/2))) = sqrt(4 A^2 / (3 sqrt(A/2)))
    b = np.sqrt(A/2.0)
    L2_init = np.sqrt(A**2 * 4.0/(3.0*b))
    print(f"{A:>8.2f}", *[f"{L2_v_T[i,j]/L2_init:>8.3f}" for i,u in enumerate(uL_grid)])

print("\n== n_peaks at t=T ==")
print(f"{'A\\uL':>8}", *[f"{u:>8.2f}" for u in uL_grid])
for j, A in enumerate(A_grid):
    print(f"{A:>8.2f}", *[f"{int(n_peaks[i,j]):>8d}" for i,u in enumerate(uL_grid)])

print("\n== x_peak at t=T ==  (initially soliton at x=-6, bore at x=+6)")
print(f"{'A\\uL':>8}", *[f"{u:>8.2f}" for u in uL_grid])
for j, A in enumerate(A_grid):
    print(f"{A:>8.2f}", *[f"{x_peak_T[i,j]:>8.2f}" for i,u in enumerate(uL_grid)])

# Compute free-propagation prediction: x_peak_free = -6 + 2*A*T
# But soliton hits periodic boundary at x=15, wraps to -15.
print("\n== expected free x_peak (mod periodic) ==  (no bore, just 2A*T)")
print(f"{'A\\uL':>8}", *[f"{u:>8.2f}" for u in uL_grid])
T = summary["T"]
for j, A in enumerate(A_grid):
    x_free = -6.0 + 2.0*A*T
    # wrap to [-15, 15)
    while x_free >= 15: x_free -= 30
    while x_free <  -15: x_free += 30
    print(f"{A:>8.2f}", *[f"{x_free:>8.2f}" for _ in uL_grid])

# Inspect snapshots to refine regime classification: load one snap per cell
print("\n== loading snapshots and checking peaks more carefully ==")

# For each cell, also compute v_T evaluated and report peak structure
def reanalyse(uL, A):
    tag = f"uL{uL:.2f}_A{A:.2f}"
    d = np.load(f"pred_results/E1_{tag}.npz")
    x = d["x"]; snaps_v = d["snaps_v"]; snaps_u = d["snaps_u"]; snap_t = d["snap_t"]
    v_T = snaps_v[-1]; u_T = snaps_u[-1]
    # find all peaks with height > 0.05 (low threshold)
    peaks = []
    N = len(v_T)
    for i in range(N):
        ip = (i+1)%N; im = (i-1)%N
        if v_T[i] > v_T[ip] and v_T[i] > v_T[im] and v_T[i] > 0.05:
            peaks.append((float(x[i]), float(v_T[i])))
    peaks.sort(key=lambda p: -p[1])  # tallest first
    return peaks, u_T, v_T

print("\n== detailed peak list per (uL,A), sorted by height ==")
for uL in uL_grid:
    for A in A_grid:
        peaks, u_T, v_T = reanalyse(uL, A)
        # show top 4 peaks
        top = peaks[:4]
        s = ", ".join(f"({p[0]:+.2f},h={p[1]:.3f})" for p in top)
        print(f"  uL={uL:.2f} A={A:.2f} npks={len(peaks)} top4: [{s}]  max_u={float(np.max(u_T)):.2f} min_u={float(np.min(u_T)):.2f}")

# Now classify regimes based on the peak structure.
# Convention: the soliton initially at x=-6 moving right with speed 2A.
# Bore step centered at +6, drifting left because Burgers bore moves at u_L average ~ uL/2.
# Encounter happens somewhere between x=-6 and x=+6 for slow soliton, or soliton reaches
# the right boundary first for fast soliton.

def classify(uL, A, peaks, u_T):
    if not peaks:
        return "destruction"
    h_top = peaks[0][1]
    A_thresh_hi = 0.5 * A   # >= 50% of A: amplitude preserved
    A_thresh_lo = 0.2 * A   # < 20% of A: largely destroyed
    n_signif = sum(1 for p in peaks if p[1] > 0.2 * A)
    if h_top < A_thresh_lo:
        return "destruction"
    if n_signif == 1:
        x_p = peaks[0][0]
        # transmission: soliton emerged on the right of original bore position
        # given periodic wrap & 2A*T distance, transmitted soliton is in:
        # x_free = (-6 + 2*A*T) mod 30 - 15
        x_free = -6.0 + 2.0*A*12.0
        while x_free >= 15: x_free -= 30
        while x_free <  -15: x_free += 30
        if abs(x_p - x_free) < 3.0:
            return "transmit"
        elif x_p < 0:
            return "reflect"
        else:
            return "transmit?"
    if n_signif >= 2:
        return "fission"
    return "weakened"

print("\n== regime classification ==")
print(f"{'A\\uL':>8}", *[f"{u:>10.2f}" for u in uL_grid])
class_grid = [["" for _ in uL_grid] for _ in A_grid]
for j, A in enumerate(A_grid):
    row = []
    for i, uL in enumerate(uL_grid):
        peaks, u_T, v_T = reanalyse(uL, A)
        c = classify(uL, A, peaks, u_T)
        class_grid[j][i] = c
        row.append(c)
    print(f"{A:>8.2f}", *[f"{c:>10s}" for c in row])

# Save analysis
out = {
    "regime_classification": class_grid,
    "uL_grid": uL_grid, "A_grid": A_grid,
    "max_v_T_over_A": (max_v_T / np.array(A_grid)[None,:]).tolist(),
    "n_peaks": n_peaks.tolist(),
    "x_peak_T": x_peak_T.tolist(),
}
with open("evidence/E1_analysis.json", "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved evidence/E1_analysis.json")
