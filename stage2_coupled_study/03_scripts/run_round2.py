#!/usr/bin/env python3
"""Run all Stage 2 round-2 candidates and evaluate."""
import json, pathlib, subprocess, datetime as dt, importlib.util

ROOT = pathlib.Path("")
STAGE2 = ROOT / "stage2"
PY = str(ROOT / ".venv" / "bin" / "python")

spec = importlib.util.spec_from_file_location("pc", STAGE2 / "eval" / "phenomenon_checks.py")
pc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)

def run(cmd, cwd, timeout=300):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        return -9, (e.stdout or ""), f"TIMEOUT after {timeout}s\n{e.stderr or ''}"

import glob
sandboxes = sorted(glob.glob(str(STAGE2 / "runs/T_*/*/round2/candidate.py")))
print(f"discovered {len(sandboxes)} round-2 candidates\n")

all_results = []
for cand in sandboxes:
    cwd = pathlib.Path(cand).parent
    parts = cwd.parts
    # ...runs/T_X/<cond>/round2
    cond = parts[-2]
    task = parts[-3]
    meta = json.load(open(cwd / "meta.json"))

    for p in [cwd / "exec.log", cwd / "result.json", cwd / "eval_result.json"]:
        p.unlink(missing_ok=True)
    out_path = cwd / "pred_results" / f"{task}.npy"
    out_path.unlink(missing_ok=True)

    print(f"=== {task} / {cond} / round2 ===", flush=True)
    t0 = dt.datetime.now()
    rc, so, se = run([PY, "candidate.py"], cwd=cwd, timeout=300)
    dur = (dt.datetime.now() - t0).total_seconds()
    (cwd / "exec.log").write_text(f"exit_code={rc}\nduration_sec={dur:.1f}\n--- stdout ---\n{so[-2000:]}\n--- stderr ---\n{se[-2000:]}\n")

    output_exists = out_path.exists()
    useful = False; diag = None
    if output_exists:
        try:
            useful, diag = pc.EVALS[task](str(out_path))
        except Exception as e:
            diag = {"eval_error": str(e)}

    result = {"task": task, "condition": cond, "round": 2,
              "exit_code": rc, "duration_sec": dur,
              "output_exists": output_exists, "useful": bool(useful),
              "diag": diag,
              "stderr_tail": "\n".join(se.splitlines()[-5:]) if se else ""}
    (cwd / "result.json").write_text(json.dumps(result, indent=2, default=float))
    (cwd / "eval_result.json").write_text(json.dumps({"useful": bool(useful), "diag": diag}, indent=2, default=float))
    all_results.append(result)

    if not output_exists:
        line = f"  NO OUTPUT (exit={rc})"
    elif diag is None or not diag.get("all_finite", True):
        line = f"  NaN/Inf or eval failure"
    elif diag.get("error"):
        line = f"  shape: {diag['error']}"
    else:
        m = "✓" if useful else "✗"
        extras = []
        if "mass_drift_rel" in diag: extras.append(f"mass_drift={diag['mass_drift_rel']:.2%}")
        if "vT_max" in diag: extras.append(f"vT_max={diag['vT_max']:.2f}")
        if "n_dominant_peaks_vT" in diag: extras.append(f"peaks={diag['n_dominant_peaks_vT']}")
        line = f"  {m} useful={useful} ({'; '.join(extras)})"
        if not useful and "reason" in diag:
            line += f"\n      reason: {diag['reason']}"
    print(line, flush=True)

(STAGE2 / "results_round2.json").write_text(json.dumps(all_results, indent=2, default=float))
print(f"\nwrote results_round2.json ({len(all_results)} runs)")
