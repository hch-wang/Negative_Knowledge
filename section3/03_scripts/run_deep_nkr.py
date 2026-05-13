#!/usr/bin/env python3
"""Run all deepNKR candidates (Sonnet + Haiku cells) and write results.

Same execution / eval / classify protocol as pilot's run_v3.py, but globs
two model paths and writes a separate CSV at:
  experiments/pilot_2026-05-10/results_deep_nkr.csv

Each cell sandbox has: candidate.py, deep_nk.json, prompt.md,
benchmark/datasets/<ds>, benchmark/eval_programs/gold_results.

For each candidate:
  1. cd into the sandbox
  2. run `python candidate.py` (180s timeout) via the .venv_full Python
  3. if it produced the expected output, copy in _eval.py and run it (120s timeout)
  4. parse the eval's last stdout line as a `(score, msg)` tuple if possible
  5. write result.json + exec.log + eval.log
  6. write failure_record.json for non-PASS via classify_failure()

Skip cells whose result.json already shows PASS (idempotent).
"""
from __future__ import annotations
import ast, csv, datetime as dt, glob, json, pathlib, shutil, subprocess

PILOT = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/experiments/pilot_2026-05-10"
)
BENCH = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/benchmark"
)
PY = str(PILOT / ".venv_full" / "bin" / "python")


def load_tasks():
    tasks = {}
    for p in sorted(glob.glob(str(PILOT / "tasks" / "task_*.json"))):
        spec = json.load(open(p))
        tid = f"{spec['instance_id']:03d}"
        tasks[tid] = {
            "output": spec["output_fname"],
            "eval": spec["eval_script_name"],
            "task_inst": spec["task_inst"],
        }
    return tasks


def run_cmd(cmd, cwd, timeout=180):
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        return -9, (e.stdout or ""), f"TIMEOUT after {timeout}s\n{e.stderr or ''}"


def parse_eval(stdout):
    last = stdout.strip().splitlines()[-1] if stdout.strip() else ""
    try:
        val = ast.literal_eval(last)
        if isinstance(val, tuple) and len(val) >= 1:
            return val[0], (val[1] if len(val) > 1 else "")
    except Exception:
        pass
    return None, last[:300]


def classify_failure(rc, output_exists, eval_status, eval_score,
                     stderr_tail, eval_msg):
    s = (stderr_tail or "").lower()
    e = (eval_msg or "").lower()
    fr = {
        "layer": "implementation_failure", "scope": "local_failure",
        "degree": "contradicted", "reproducibility": "observed_once",
        "recommended_action": "retry", "risk": "low_risk_omission",
    }
    rationale = ""
    if rc != 0:
        rationale = "Unclassified exec error."
    elif not output_exists:
        fr.update(layer="communication_failure")
        rationale = "Exec OK but output missing."
    elif eval_status == "crashed":
        fr.update(layer="communication_failure", degree="partial")
        rationale = "Eval crashed: output schema mismatch."
    elif eval_score == 0 or eval_score == "0":
        fr.update(layer="method_failure", scope="regime_bound_failure",
                  recommended_action="narrow_claim")
        rationale = "Generic eval=0."
    elif eval_score == 1 or eval_score == "1":
        return None
    return {"failure": fr, "rationale": rationale}


def main():
    tasks = load_tasks()
    patterns = [
        "runs/task_*/sonnet_4.6/v3/deepNKR_sonnet/candidate.py",
        "runs/task_*/haiku_4.5/v3/deepNKR_haiku/candidate.py",
    ]
    cands = []
    for p in patterns:
        cands.extend(sorted(glob.glob(str(PILOT / p))))
    print(f"discovered {len(cands)} deepNKR candidates\n", flush=True)

    all_results = []
    for cand_path in cands:
        run_dir = pathlib.Path(cand_path).parent
        parts = run_dir.parts
        cell = parts[-1]            # deepNKR_sonnet or deepNKR_haiku
        model = parts[-3]            # sonnet_4.6 or haiku_4.5
        task = parts[-4].replace("task_", "")
        if task not in tasks:
            continue

        # idempotent: skip PASS
        if (run_dir / "result.json").exists():
            try:
                existing = json.load(open(run_dir / "result.json"))
                if existing.get("eval_status") == "ran" and existing.get("eval_score") == 1:
                    all_results.append(existing)
                    continue
            except Exception:
                pass

        info = tasks[task]
        for p in [run_dir / "exec.log", run_dir / "eval.log",
                  run_dir / "result.json", run_dir / "_eval.py",
                  run_dir / "failure_record.json"]:
            p.unlink(missing_ok=True)
        out_path = run_dir / info["output"]
        if out_path.exists() and out_path.is_file():
            out_path.unlink()

        print(f"=== {task} / {model} / {cell} ===", flush=True)
        t0 = dt.datetime.now()
        rc, so, se = run_cmd([PY, "candidate.py"], cwd=run_dir, timeout=180)
        cand_dur = (dt.datetime.now() - t0).total_seconds()
        (run_dir / "exec.log").write_text(
            f"exit_code={rc}\nduration_sec={cand_dur:.1f}\n"
            f"--- stdout ---\n{so}\n--- stderr ---\n{se}\n"
        )
        output_exists = out_path.exists()

        eval_status = "not_run"
        eval_score = None
        eval_msg = ""
        eval_dur = 0.0
        if output_exists:
            shutil.copy2(
                BENCH / "eval_programs" / info["eval"],
                run_dir / "_eval.py"
            )
            t1 = dt.datetime.now()
            e_rc, e_so, e_se = run_cmd(
                [PY, "_eval.py"], cwd=run_dir, timeout=120
            )
            eval_dur = (dt.datetime.now() - t1).total_seconds()
            (run_dir / "eval.log").write_text(
                f"exit_code={e_rc}\nduration_sec={eval_dur:.1f}\n"
                f"--- stdout ---\n{e_so}\n--- stderr ---\n{e_se}\n"
            )
            if e_rc == 0:
                score, msg = parse_eval(e_so)
                eval_status = "ran"
                eval_score = score
                eval_msg = msg or ""
            else:
                eval_status = "crashed"
                eval_msg = "\n".join((e_se or "").splitlines()[-3:])[:400]
            (run_dir / "_eval.py").unlink(missing_ok=True)

        stderr_tail = "\n".join(se.splitlines()[-8:]) if se else ""
        result = {
            "task": task, "model": model, "cell": cell, "exit_code": rc,
            "output_exists": output_exists, "eval_status": eval_status,
            "eval_score": eval_score, "eval_msg": eval_msg,
            "stderr_tail": stderr_tail,
            "cand_duration_sec": cand_dur, "eval_duration_sec": eval_dur,
        }
        (run_dir / "result.json").write_text(json.dumps(result, indent=2))

        fr = classify_failure(
            rc, output_exists, eval_status, eval_score, stderr_tail, eval_msg
        )
        if fr is not None:
            record = {
                "run_ref": {"task_id": task, "model": model, "cell": cell},
                "target": info["task_inst"][:200],
                "observation": (
                    f"exec_error: {stderr_tail.splitlines()[-1] if stderr_tail else ''}"
                    if rc != 0
                    else f"eval_crashed: {eval_msg[:200]}"
                    if eval_status == "crashed"
                    else f"eval_failed: {eval_msg[:200]}"
                ),
                "evidence": [{
                    "kind": "exec_log", "ref": "exec.log",
                    "summary": stderr_tail.splitlines()[-1] if stderr_tail else "(no stderr)"
                }],
                "failure": fr["failure"],
                "rationale": fr["rationale"],
            }
            (run_dir / "failure_record.json").write_text(json.dumps(record, indent=2))

        all_results.append(result)
        print(
            f"  exit={rc} output={output_exists} eval={eval_status} score={eval_score}",
            flush=True,
        )

    # CSV summary
    fields = [
        "task", "model", "cell", "exit_code", "output_exists",
        "eval_status", "eval_score", "eval_msg",
        "cand_duration_sec", "eval_duration_sec",
    ]
    out_csv = PILOT / "results_deep_nkr.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in all_results:
            w.writerow(r)
    print(f"\nwrote {out_csv} with {len(all_results)} rows")


if __name__ == "__main__":
    main()
