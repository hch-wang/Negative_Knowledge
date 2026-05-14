#!/usr/bin/env python3
"""Parent-side phenomenon eval for all 12 Section 4 stage-2 cells.

Walks runs/{T_A,T_B,T_C}/{NoKB,PosOnly,NegOnly,PosNeg}/pred_results/T_X.npy,
applies the task-specific eval from eval/phenomenon_checks.py, and writes
verified_results.json next to runs/. This is the independent, deterministic
check that the agent's self-reported PASS/FAIL is correct.
"""
import json, pathlib, importlib.util, sys

SECTION4 = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4")
STAGE2 = SECTION4 / "stage2"
RUNS = STAGE2 / "runs"
EVAL_PY = STAGE2 / "eval" / "phenomenon_checks.py"

TASKS = ["T_A", "T_B", "T_C"]
CONDS = ["NoKB", "PosOnly", "NegOnly", "PosNeg"]

spec = importlib.util.spec_from_file_location("pc", EVAL_PY)
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)


def count_iterations(state_path):
    if not state_path.exists():
        return 0
    n = 0
    for line in state_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("node_type") == "Experiment":
            n += 1
    return n


def count_bank_citations(state_path):
    """Tally cites_bank / rejects_bank entries on any node (agents put them
    on Experiment nodes per the prompt template)."""
    if not state_path.exists():
        return {"cites": 0, "rejects": 0, "cite_ids": [], "reject_ids": []}
    cites, rejects, cite_ids, reject_ids = 0, 0, [], []
    for line in state_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        for k in ("cites_bank", "cites"):
            v = obj.get(k)
            if isinstance(v, list):
                cites += len(v)
                cite_ids.extend(v)
        for k in ("rejects_bank", "rejects"):
            v = obj.get(k)
            if isinstance(v, list):
                rejects += len(v)
                reject_ids.extend(v)
    return {"cites": cites, "rejects": rejects, "cite_ids": cite_ids, "reject_ids": reject_ids}


def main():
    all_rows = []
    for task in TASKS:
        for cond in CONDS:
            cell = RUNS / task / cond
            out_npy = cell / "pred_results" / f"{task}.npy"
            state = cell / "research_state.jsonl"

            iters = count_iterations(state)
            bank_use = count_bank_citations(state)

            row = {
                "task": task,
                "condition": cond,
                "iterations": iters,
                "bank_cites": bank_use["cites"],
                "bank_rejects": bank_use["rejects"],
                "cite_ids": bank_use["cite_ids"],
                "reject_ids": bank_use["reject_ids"],
                "output_exists": out_npy.exists(),
            }

            if not out_npy.exists():
                row["useful"] = False
                row["diag"] = {"error": "no output file"}
            else:
                try:
                    useful, diag = pc.EVALS[task](str(out_npy))
                    row["useful"] = bool(useful)
                    row["diag"] = diag
                except Exception as e:
                    row["useful"] = False
                    row["diag"] = {"eval_error": str(e)}

            (cell / "verified_eval.json").write_text(
                json.dumps({"useful": row["useful"], "diag": row["diag"]}, indent=2, default=float)
            )
            all_rows.append(row)

            mark = "PASS" if row["useful"] else "FAIL"
            extras = []
            d = row["diag"]
            if "mass_drift_rel" in d:
                extras.append(f"mass={d['mass_drift_rel']:.2%}")
            if "vT_max" in d:
                extras.append(f"vT_max={d['vT_max']:.2f}")
            if "u_max" in d:
                extras.append(f"u_max={d['u_max']:.2f}")
            if "n_dominant_peaks_vT" in d:
                extras.append(f"peaks={d['n_dominant_peaks_vT']}")
            reason = d.get("reason", "")
            extra_str = "; ".join(extras)
            print(f"  {task}/{cond:8s}  iter={iters}  cites={bank_use['cites']:2d}  rejects={bank_use['rejects']:2d}  {mark}  {extra_str}")
            if reason and not row["useful"]:
                print(f"      reason: {reason}")

    out = STAGE2 / "verified_results.json"
    out.write_text(json.dumps(all_rows, indent=2, default=float))
    print(f"\nwrote {out}")

    # Top-line summary
    print("\n=== Useful rate by condition ===")
    for cond in CONDS:
        passes = sum(1 for r in all_rows if r["condition"] == cond and r["useful"])
        print(f"  {cond:8s}: {passes}/3")

    print("\n=== Per-task verdict ===")
    print(f"  {'task':6s}  " + "  ".join(f"{c:8s}" for c in CONDS))
    for task in TASKS:
        cells = []
        for cond in CONDS:
            r = next(x for x in all_rows if x["task"] == task and x["condition"] == cond)
            cells.append("PASS" if r["useful"] else "FAIL")
        print(f"  {task:6s}  " + "  ".join(f"{c:8s}" for c in cells))


if __name__ == "__main__":
    main()
