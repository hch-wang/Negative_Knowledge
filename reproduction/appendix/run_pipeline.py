#!/usr/bin/env python3
"""Mode B — re-run a single Stage-3 cell end-to-end.

Two sub-modes:
  --use-saved-trace : re-run the parent-side phenomenon eval on the
                      bundled pred_results/<task>.npy. No API calls. Cost $0.
  (default)         : rebuild the cell's sandbox, dispatch a fresh sub-agent
                      through NK_AGENT_COMMAND, then re-run eval. Requires an
                      external Python venv with numpy / scipy.

Usage:
  python3 run_pipeline.py --task T_C --cond NLS --use-saved-trace
  python3 run_pipeline.py --task T_C --cond NLS
"""
import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "scripts"))
from _paths import (
    REPRO_ROOT, PHENOM_CHECKS, CONDITIONS, TASKS, cell_dir, PY_VENV,
)


def eval_one(task, cond):
    spec = importlib.util.spec_from_file_location("pc", PHENOM_CHECKS)
    pc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pc)
    cell = cell_dir(task, cond)
    npy = cell / "pred_results" / f"{task}.npy"
    if not npy.exists():
        print(f"ERROR: {npy} not found")
        sys.exit(1)
    useful, diag = pc.EVALS[task](str(npy))
    print(f"\n=== {task}/{cond} ===")
    print(f"  useful: {'PASS' if useful else 'FAIL'}")
    print(f"  diagnostics: {json.dumps(diag, indent=2, default=float)}")
    out = {"useful": bool(useful), "diag": diag}
    (cell / "verified_eval.json").write_text(json.dumps(out, indent=2, default=float))
    return out


def rebuild_sandbox(task, cond):
    """Run build_sandboxes.py for the single (task, cond) cell."""
    print(f"Rebuilding sandbox for {task}/{cond}...")
    subprocess.check_call([sys.executable, str(REPRO_ROOT / "scripts" / "build_sandboxes.py"),
                           "--task", task, "--cond", cond])


def dispatch_subagent(task, cond):
    print(f"Dispatching sub-agent for {task}/{cond}...")
    subprocess.check_call([sys.executable, str(REPRO_ROOT / "scripts" / "dispatch_subagent.py"),
                           "--task", task, "--cond", cond])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=TASKS, required=True)
    p.add_argument("--cond", choices=CONDITIONS, required=True)
    p.add_argument("--use-saved-trace", action="store_true",
                   help="Re-run eval on bundled .npy without dispatching a sub-agent ($0)")
    args = p.parse_args()

    if args.use_saved_trace:
        out = eval_one(args.task, args.cond)
        sys.exit(0 if out["useful"] else 1)

    rebuild_sandbox(args.task, args.cond)
    dispatch_subagent(args.task, args.cond)
    out = eval_one(args.task, args.cond)
    sys.exit(0 if out["useful"] else 1)


if __name__ == "__main__":
    main()
