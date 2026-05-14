#!/usr/bin/env python3
import json, pathlib, importlib.util

SEC4 = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4")
CLASS_A = SEC4 / "stage2_v3" / "class_A"
RUNS = CLASS_A / "runs"
EVAL_PY = SEC4 / "stage2" / "eval" / "phenomenon_checks.py"

TASKS = ["T_A", "T_B", "T_C"]
CONDS = ["NoKB", "PosOnly", "NegOnly", "PosNeg"]

spec = importlib.util.spec_from_file_location("pc", EVAL_PY)
pc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)


def count_iters(state_path):
    if not state_path.exists(): return 0
    n = 0
    for line in state_path.read_text().splitlines():
        line = line.strip()
        if not line: continue
        try: o = json.loads(line)
        except: continue
        if o.get("node_type") == "Experiment": n += 1
    return n


def bank_use(state_path):
    if not state_path.exists(): return 0, 0
    c, r = 0, 0
    for line in state_path.read_text().splitlines():
        line = line.strip()
        if not line: continue
        try: o = json.loads(line)
        except: continue
        for k in ("cites_bank", "cites"):
            v = o.get(k)
            if isinstance(v, list): c += len(v)
        for k in ("rejects_bank", "rejects"):
            v = o.get(k)
            if isinstance(v, list): r += len(v)
    return c, r


rows = []
for t in TASKS:
    for c in CONDS:
        cell = RUNS / t / c
        out = cell / "pred_results" / f"{t}.npy"
        state = cell / "research_state.jsonl"
        iters = count_iters(state)
        cites, rejects = bank_use(state)
        if not out.exists():
            useful, diag = False, {"error": "no output"}
        else:
            try: useful, diag = pc.EVALS[t](str(out))
            except Exception as e: useful, diag = False, {"eval_error": str(e)}
        rows.append({"task": t, "condition": c, "iterations": iters, "cites": cites, "rejects": rejects, "useful": bool(useful), "diag": diag})
        (cell / "verified_eval.json").write_text(json.dumps({"useful": bool(useful), "diag": diag}, indent=2, default=float))
        mark = "PASS" if useful else "FAIL"
        d = diag
        extras = []
        for k in ("vT_max", "u_max", "amp_ratio", "n_dominant_peaks_vT"):
            if k in d:
                extras.append(f"{k}={d[k]:.2f}" if isinstance(d[k], float) else f"{k}={d[k]}")
        reason = d.get("reason", "")
        print(f"  {t}/{c:8s}  iter={iters} cites={cites:2d} rejects={rejects:2d}  {mark}  {'; '.join(extras)}")
        if reason and not useful: print(f"      reason: {reason}")

OUT = CLASS_A / "verified_results.json"
OUT.write_text(json.dumps(rows, indent=2, default=float))

print(f"\nwrote {OUT}")
print("\n=== PASS rate by condition ===")
for c in CONDS:
    n = sum(1 for r in rows if r["condition"] == c and r["useful"])
    print(f"  {c:8s}: {n}/3")

print("\n=== Per-task verdict ===")
print(f"  {'task':4s}  " + "  ".join(f"{c:8s}" for c in CONDS))
for t in TASKS:
    cells = []
    for c in CONDS:
        r = next(x for x in rows if x["task"]==t and x["condition"]==c)
        cells.append("PASS" if r["useful"] else "FAIL")
    print(f"  {t:4s}  " + "  ".join(f"{c:8s}" for c in cells))

print("\n=== Iterations to success (success cells only) ===")
for c in CONDS:
    success_iters = [r["iterations"] for r in rows if r["condition"]==c and r["useful"]]
    avg = sum(success_iters)/len(success_iters) if success_iters else 0
    print(f"  {c:8s}: {success_iters} (avg={avg:.1f})")
