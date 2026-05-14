#!/usr/bin/env python3
"""Parent-side phenomenon eval for the 16 Stage-3 cells (B-NLS appendix).

Reads each cell's pred_results/<task>.npy and applies the task-specific
phenomenon check from eval/phenomenon_checks_bnls.py. Writes per-cell
verified_eval.json and an aggregate verified_results.json.
"""
import importlib.util
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _paths import (
    PHENOM_CHECKS, STAGE3_LOGS, VERIFIED_RESULTS,
    CONDITIONS, TASKS, cell_dir,
)

spec = importlib.util.spec_from_file_location("pc", PHENOM_CHECKS)
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
            o = json.loads(line)
        except Exception:
            continue
        if o.get("node_type") == "Experiment":
            n += 1
    return n


def count_bank_citations(state_path):
    """Tally cites_bank / rejects_bank entries; classify by NLS vs BKdV id prefix."""
    if not state_path.exists():
        return dict(cites=0, rejects=0, cite_nls=0, cite_bkdv=0,
                    reject_nls=0, reject_bkdv=0, cite_ids=[], reject_ids=[])
    cites = rejects = cite_nls = cite_bkdv = reject_nls = reject_bkdv = 0
    cite_ids = []
    reject_ids = []
    for line in state_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        for k in ("cites_bank", "cites"):
            v = o.get(k)
            if isinstance(v, list):
                cites += len(v)
                cite_ids.extend(v)
                for eid in v:
                    if isinstance(eid, str):
                        if eid.startswith("kb-nls"):
                            cite_nls += 1
                        else:
                            cite_bkdv += 1
        for k in ("rejects_bank", "rejects"):
            v = o.get(k)
            if isinstance(v, list):
                rejects += len(v)
                reject_ids.extend(v)
                for eid in v:
                    if isinstance(eid, str):
                        if eid.startswith("kb-nls"):
                            reject_nls += 1
                        else:
                            reject_bkdv += 1
    return dict(cites=cites, rejects=rejects,
                cite_nls=cite_nls, cite_bkdv=cite_bkdv,
                reject_nls=reject_nls, reject_bkdv=reject_bkdv,
                cite_ids=cite_ids, reject_ids=reject_ids)


def main():
    rows = []
    for task in TASKS:
        for cond in CONDITIONS:
            cell = cell_dir(task, cond)
            out_npy = cell / "pred_results" / f"{task}.npy"
            state = cell / "research_state.jsonl"

            iters = count_iterations(state)
            bank = count_bank_citations(state)

            row = dict(task=task, condition=cond, iterations=iters,
                       bank_cites=bank["cites"], bank_rejects=bank["rejects"],
                       cite_nls=bank["cite_nls"], cite_bkdv=bank["cite_bkdv"],
                       reject_nls=bank["reject_nls"], reject_bkdv=bank["reject_bkdv"],
                       cite_ids=bank["cite_ids"], reject_ids=bank["reject_ids"],
                       output_exists=out_npy.exists())

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
            rows.append(row)

            mark = "PASS" if row["useful"] else "FAIL"
            d = row["diag"]
            ex = []
            if "mass_drift_rel" in d: ex.append(f"mass={d['mass_drift_rel']:.2%}")
            if "NT_max" in d: ex.append(f"NT_max={d['NT_max']:.2f}")
            if "uT_max" in d: ex.append(f"uT_max={d['uT_max']:.2f}")
            if "n_peaks_T" in d: ex.append(f"peaks={d['n_peaks_T']}")
            if "m_qualitative" in d: ex.append(f"m={d['m_qualitative']}")
            if "n_padding_steps" in d and d["n_padding_steps"] > 0:
                ex.append(f"pad={d['n_padding_steps']}")
            line = (f"  {task}/{cond:8s}  iter={iters}  NLS({bank['cite_nls']:2d}c+{bank['reject_nls']:2d}r) "
                    f"BKdV({bank['cite_bkdv']:2d}c+{bank['reject_bkdv']:2d}r) {mark}  {'; '.join(ex)}")
            print(line)
            if not row["useful"] and "reason" in d:
                print(f"      reason: {d['reason']}")

    VERIFIED_RESULTS.write_text(json.dumps(rows, indent=2, default=float))
    print(f"\nwrote {VERIFIED_RESULTS}")

    print("\n=== Useful rate by condition ===")
    for cond in CONDITIONS:
        n = sum(1 for r in rows if r["condition"] == cond and r["useful"])
        print(f"  {cond:8s}: {n}/{len(TASKS)}")

    print("\n=== Per-task verdict ===")
    print(f"  {'task':6s}  " + "  ".join(f"{c:8s}" for c in CONDITIONS))
    for task in TASKS:
        cells = [next(x for x in rows if x["task"] == task and x["condition"] == c) for c in CONDITIONS]
        print(f"  {task:6s}  " + "  ".join(f"{'PASS' if r['useful'] else 'FAIL':8s}" for r in cells))


if __name__ == "__main__":
    main()
