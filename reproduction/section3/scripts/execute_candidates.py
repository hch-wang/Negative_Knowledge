#!/usr/bin/env python3
"""Execute solver candidate.py files and run the evaluator.

For each solver sandbox (round1 / solver-nkr / solver-deep / etc.):
  1. cd into the sandbox
  2. run `python3 candidate.py` (180s timeout) via PY_VENV
  3. if it produced the expected output, run the eval script (120s timeout)
  4. parse the eval's last stdout line as a `(score, msg)` tuple
  5. write result.json + exec.log + eval.log

Reviewer CLI:
  python3 execute_candidates.py --cell round1 --tasks 072
  python3 execute_candidates.py --cell solver-deep --tasks all
"""
from __future__ import annotations
import argparse
import ast
import datetime as dt
import json
import pathlib
import shutil
import subprocess

from _paths import RUNS, BENCH, TASKS, PY, NK_TEST_24, HARD_19, all_38_tasks


def run(cmd, cwd, timeout=180):
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


def execute_one(tid: str, cell: str) -> dict:
    sandbox = RUNS / cell / f"task_{tid}"
    if not (sandbox / "candidate.py").exists():
        return {"task": tid, "cell": cell, "error": "no candidate.py"}

    spec = json.load(open(TASKS / f"task_{tid}.json"))
    output_fname = spec["output_fname"]
    eval_script = spec["eval_script_name"]

    # Clean prior outputs
    for p in (sandbox / "exec.log", sandbox / "eval.log",
              sandbox / "result.json", sandbox / "_eval.py"):
        p.unlink(missing_ok=True)
    out_path = sandbox / output_fname
    if out_path.exists() and out_path.is_file():
        out_path.unlink()

    print(f"=== task_{tid} / {cell} ===", flush=True)
    t0 = dt.datetime.now()
    rc, so, se = run([str(PY), "candidate.py"], cwd=sandbox, timeout=180)
    cand_dur = (dt.datetime.now() - t0).total_seconds()
    (sandbox / "exec.log").write_text(
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
            BENCH / "eval_programs" / eval_script, sandbox / "_eval.py"
        )
        t1 = dt.datetime.now()
        e_rc, e_so, e_se = run(
            [str(PY), "_eval.py"], cwd=sandbox, timeout=120
        )
        eval_dur = (dt.datetime.now() - t1).total_seconds()
        (sandbox / "eval.log").write_text(
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
        (sandbox / "_eval.py").unlink(missing_ok=True)

    result = {
        "task": tid, "cell": cell, "exit_code": rc,
        "output_exists": output_exists, "eval_status": eval_status,
        "eval_score": eval_score, "eval_msg": eval_msg,
        "stderr_tail": "\n".join(se.splitlines()[-8:]) if se else "",
        "cand_duration_sec": cand_dur, "eval_duration_sec": eval_dur,
    }
    (sandbox / "result.json").write_text(json.dumps(result, indent=2))
    print(f"  exit={rc} output={output_exists} "
          f"eval={eval_status} score={eval_score}", flush=True)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True)
    ap.add_argument("--tasks", required=True, help="task ids comma-sep, or 'all'")
    args = ap.parse_args()

    if args.tasks == "all":
        if args.cell == "round1":
            tasks = all_38_tasks()
        elif "deep" in args.cell:
            tasks = HARD_19
        else:
            tasks = NK_TEST_24
    else:
        tasks = [t.strip() for t in args.tasks.split(",")]

    results = []
    for tid in tasks:
        results.append(execute_one(tid, args.cell))

    summary = RUNS / f"results_{args.cell}.json"
    summary.write_text(json.dumps(results, indent=2))
    n_pass = sum(1 for r in results if r.get("eval_score") == 1)
    print(f"\n{n_pass}/{len(results)} PASS for {args.cell}")
    print(f"summary: {summary}")


if __name__ == "__main__":
    main()
