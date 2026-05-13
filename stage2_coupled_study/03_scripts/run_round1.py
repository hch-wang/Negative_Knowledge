#!/usr/bin/env python3
"""Run all Stage 2 candidates that exist, evaluate phenomenon checks."""
import json, pathlib, subprocess, datetime as dt, sys, importlib.util

ROOT = pathlib.Path("")
STAGE2 = ROOT / "stage2"
PY = str(ROOT / ".venv" / "bin" / "python")

# load phenomenon checks
spec = importlib.util.spec_from_file_location("pc", STAGE2 / "eval" / "phenomenon_checks.py")
pc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)

def run(cmd, cwd, timeout=240):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        return -9, (e.stdout or ""), f"TIMEOUT after {timeout}s\n{e.stderr or ''}"

CONDITIONS = ["NoKB", "PosOnly", "PosNeg"]
TASKS = ["T_A", "T_B", "T_C"]
all_results = []

for task_id in TASKS:
    for cond in CONDITIONS:
        cwd = STAGE2 / "runs" / task_id / cond / "round1"
        if not (cwd / "candidate.py").exists():
            print(f"SKIP {task_id}/{cond}: no candidate.py"); continue

        for p in [cwd / "exec.log", cwd / "result.json", cwd / "eval_result.json"]:
            p.unlink(missing_ok=True)
        out_path = cwd / "pred_results" / f"{task_id}.npy"
        out_path.unlink(missing_ok=True)

        print(f"=== {task_id} / {cond} ===", flush=True)
        t0 = dt.datetime.now()
        rc, so, se = run([PY, "candidate.py"], cwd=cwd, timeout=240)
        dur = (dt.datetime.now() - t0).total_seconds()
        (cwd / "exec.log").write_text(f"exit_code={rc}\nduration_sec={dur:.1f}\n--- stdout ---\n{so[-2000:]}\n--- stderr ---\n{se[-2000:]}\n")

        output_exists = out_path.exists()
        useful = False; diag = None
        if output_exists:
            try:
                useful, diag = pc.EVALS[task_id](str(out_path))
            except Exception as e:
                diag = {"eval_error": str(e)}

        result = {"task": task_id, "condition": cond, "round": 1,
                  "exit_code": rc, "duration_sec": dur,
                  "output_exists": output_exists, "useful": bool(useful),
                  "diag": diag, "stderr_tail": "\n".join(se.splitlines()[-5:]) if se else ""}
        (cwd / "result.json").write_text(json.dumps(result, indent=2, default=float))
        (cwd / "eval_result.json").write_text(json.dumps({"useful": bool(useful), "diag": diag}, indent=2, default=float))
        all_results.append(result)

        if not output_exists:
            line = f"  NO OUTPUT (exit={rc})"
        elif diag is None:
            line = f"  output exists but eval failed"
        elif not diag.get("all_finite", True):
            line = f"  NaN/Inf in output"
        elif diag.get("error"):
            line = f"  shape error: {diag['error']}"
        else:
            useful_mark = "✓" if useful else "✗"
            extras = []
            if "mass_drift_rel" in diag: extras.append(f"mass_drift={diag['mass_drift_rel']:.2%}")
            if "vT_max" in diag: extras.append(f"vT_max={diag['vT_max']:.2f}")
            if "n_dominant_peaks_vT" in diag: extras.append(f"peaks={diag['n_dominant_peaks_vT']}")
            line = f"  {useful_mark} useful={useful}  ({'; '.join(extras)})"
            if not useful and "reason" in diag:
                line += f"\n      reason: {diag['reason']}"
        print(line, flush=True)

(STAGE2 / "results_round1.json").write_text(json.dumps(all_results, indent=2, default=float))
print(f"\nwrote results_round1.json ({len(all_results)} runs)")
