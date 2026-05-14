#!/usr/bin/env python3
"""Re-eval all Class A cells (both v3.A initial and v3.A') with physics-aware eval v2."""
import json, pathlib, importlib.util, sys

SEC4 = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4")
CLASS_A = SEC4 / "stage2_v3" / "class_A"
EVAL_PY = CLASS_A / "eval" / "phenomenon_checks_v2.py"
TASKS = ["T_A", "T_B", "T_C"]
CONDS = ["NoKB", "PosOnly", "NegOnly", "PosNeg"]

spec = importlib.util.spec_from_file_location("pc2", EVAL_PY)
pc2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc2)


def run_eval_set(label, runs_root):
    print(f"\n========= {label} (runs at {runs_root.name}) =========")
    rows = []
    for t in TASKS:
        for c in CONDS:
            cell = runs_root / t / c
            out = cell / "pred_results" / f"{t}.npy"
            if not out.exists():
                useful, diag = False, {"error": "no output"}
            else:
                try:
                    useful, diag = pc2.EVALS[t](str(out))
                except Exception as e:
                    useful, diag = False, {"eval_error": str(e)}
            rows.append({"task": t, "cond": c, "useful": bool(useful), "diag": diag})
            mark = "PASS" if useful else "FAIL"
            d = diag
            extras = []
            for k in ("vT_max", "amp_ratio", "u_max", "n_peaks_above_0.4", "dominance_ratio", "n_dominant_peaks_vT"):
                if k in d:
                    v = d[k]
                    extras.append(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}")
            reason = d.get("reason", "")
            print(f"  {t}/{c:8s}  {mark}  {' '.join(extras)}")
            if reason and not useful:
                print(f"      reason: {reason}")
    # Tally
    print()
    for c in CONDS:
        n = sum(1 for r in rows if r["cond"] == c and r["useful"])
        print(f"  {c:8s}: {n}/3 PASS")
    return rows


# Run both
v3A_rows = run_eval_set("v3.A INITIAL (50-entry bank)", CLASS_A / "runs_initial_5programs_bank")
v3Aprime_rows = run_eval_set("v3.A' EXPANDED (58-entry bank with S6+S7)", CLASS_A / "runs")

# Comparison
print("\n========= COMPARISON v3.A vs v3.A' (physics-aware eval v2) =========")
print(f"  {'task':6s} {'cond':10s} {'v3.A':10s} {'v3.A''':10s}")
for t in TASKS:
    for c in CONDS:
        r1 = next(x for x in v3A_rows if x["task"]==t and x["cond"]==c)
        r2 = next(x for x in v3Aprime_rows if x["task"]==t and x["cond"]==c)
        m1 = "PASS" if r1["useful"] else "FAIL"
        m2 = "PASS" if r2["useful"] else "FAIL"
        marker = ""
        if r1["useful"] != r2["useful"]:
            marker = "  ← FLIPPED"
        print(f"  {t:6s} {c:10s} {m1:10s} {m2:10s}{marker}")
