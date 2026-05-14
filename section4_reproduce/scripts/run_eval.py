#!/usr/bin/env python3
"""run_eval.py — parent-side phenomenon eval driver.

Reads cell outputs from logs/stage2/, applies phenomenon_checks.py
to each cell's pred_results/<task>.npy, writes per-cell verdicts to
logs/verified_results/verified_results.json, prints a summary table.
"""
import json
import pathlib
import importlib.util
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _paths import (STAGE2_RUNS, VERIFIED_RESULTS, STAGE2_TASKS, STAGE2_CONDS)

EVAL_PY = HERE / "phenomenon_checks.py"
spec = importlib.util.spec_from_file_location("pc", EVAL_PY)
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)


def main():
    rows = []
    print(f"\n========= Stage 2: phenomenon-aware eval =========")
    for t in STAGE2_TASKS:
        for c in STAGE2_CONDS:
            cell = STAGE2_RUNS / t / c
            out = cell / "pred_results" / f"{t}.npy"
            if not out.exists():
                useful, diag = False, {"error": "no output"}
            else:
                try:
                    useful, diag = pc.EVALS[t](str(out))
                except Exception as e:
                    useful, diag = False, {"eval_error": str(e)}
            rows.append({"task": t, "cond": c, "useful": bool(useful), "diag": diag})
            mark = "PASS" if useful else "FAIL"
            extras = []
            for k in ("vT_max", "amp_ratio", "u_max", "n_peaks_above_0.4",
                      "dominance_ratio", "n_dominant_peaks_vT"):
                if k in diag:
                    v = diag[k]
                    extras.append(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}")
            reason = diag.get("reason", "")
            print(f"  {t}/{c:8s}  {mark}  {' '.join(extras)}")
            if reason and not useful:
                print(f"      reason: {reason}")

    print("\n========= PASS rate per condition =========")
    for c in STAGE2_CONDS:
        n = sum(1 for r in rows if r["cond"] == c and r["useful"])
        print(f"  {c:8s}: {n}/3 PASS")

    VERIFIED_RESULTS.mkdir(exist_ok=True)
    out_path = VERIFIED_RESULTS / "verified_results.json"
    out_path.write_text(json.dumps(rows, indent=2, default=float))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
