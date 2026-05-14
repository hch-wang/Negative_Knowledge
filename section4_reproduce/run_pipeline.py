#!/usr/bin/env python3
"""run_pipeline.py — Mode B end-to-end demonstration on one Stage~2 cell.

Reproduces the headline NegOnly $1/3 \\to 3/3$ result by re-running ONE
cell (default: T_C/NegOnly) end-to-end:

  1. Read the saved Stage-2 prompt for the (task, condition) cell from
     ``logs/stage2/<task>/<cond>/prompt.md``. The prompt already embeds
     the canonical 58-entry bank (positive + negative as appropriate to
     the condition) and the Research Graph + progressive-complexity
     instructions.
  2. Dispatch a fresh sub-agent via the Anthropic API with Read / Write /
     Bash tools (Stage~2 cells execute candidate.py inline to observe
     stdout and iterate).
  3. Run the parent-side phenomenon-aware eval on the cell's saved
     pred_results/<task>.npy.
  4. Print PASS/FAIL + iteration count + cited bank entries.

Run:

    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    export PY_VENV=$(pwd)/.venv/bin/python   # used by the sub-agent's Bash
    python run_pipeline.py --task T_C --cond NegOnly

Or with the bundled saved trace (no API; just runs eval on existing
pred_results):

    python run_pipeline.py --task T_C --cond NegOnly --use-saved-trace

================================================================
Why T_C/NegOnly is the default demonstration
================================================================

The NegOnly cell on T_C is the cleanest single-cell demonstration of
prescriptive negative knowledge: under the 50-entry initial bank
(without BKdV-S6) NegOnly failed T_C; adding the single BKdV-S6
deep-synthesis record (which contains the
``recommended_alternative = "adopt nu_linear=5e-2 ..."`` field) is what
lifts NegOnly to PASS in two iterations.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import pathlib
import shutil
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))
from _paths import (STAGE2_RUNS, STAGE2_TASKS, STAGE2_CONDS, BANKS, PY)


def load_eval_module():
    spec = importlib.util.spec_from_file_location(
        "pc", HERE / "scripts" / "phenomenon_checks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def count_iterations(state_path: pathlib.Path) -> int:
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


def collect_bank_citations(state_path: pathlib.Path) -> dict:
    """Tally cites_bank / rejects_bank across all Experiment nodes."""
    cites, rejects = [], []
    if not state_path.exists():
        return {"cites": cites, "rejects": rejects}
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
                cites.extend(v)
        for k in ("rejects_bank", "rejects"):
            v = o.get(k)
            if isinstance(v, list):
                rejects.extend(v)
    return {"cites": sorted(set(cites)), "rejects": sorted(set(rejects))}


def dispatch_fresh_subagent(cell_dir: pathlib.Path,
                            replay_dir: pathlib.Path,
                            model: str,
                            task: str) -> dict:
    """Re-run a fresh sub-agent on the saved prompt. Requires anthropic SDK."""
    try:
        from dispatch_subagent import run_subagent, MODEL_ALIASES
    except ImportError as e:
        raise RuntimeError(
            "anthropic SDK not installed. Install with `pip install anthropic` "
            "and set ANTHROPIC_API_KEY, or pass --use-saved-trace."
        ) from e

    replay_dir.mkdir(parents=True, exist_ok=True)
    (replay_dir / "pred_results").mkdir(exist_ok=True)
    prompt = (cell_dir / "prompt.md").read_text()
    # Allow the agent to read prompt.md + memory.md (bank) + its own outputs.
    read_allow = {
        str(cell_dir / "prompt.md"),
        str(cell_dir / "memory.md"),
        str(replay_dir / "candidate.py"),
        str(replay_dir / "exec.log"),
        str(replay_dir / "research_state.jsonl"),
        # Bank files referenced by prompt
        str(BANKS / "bank_positive.jsonl"),
        str(BANKS / "bank_negative.jsonl"),
    }
    write_allow = {
        str(replay_dir / "candidate.py"),
        str(replay_dir / "reasoning.md"),
        str(replay_dir / "research_state.jsonl"),
        str(replay_dir / "session_log.md"),
        str(replay_dir / "pred_results" / f"{task}.npy"),
    }
    full_model = MODEL_ALIASES.get(model, model)
    print(f"Dispatching fresh sub-agent (model={full_model})...")
    t0 = time.time()
    rec = run_subagent(
        prompt=prompt, model=full_model,
        read_allowlist=read_allow, write_allowlist=write_allow,
        max_iterations=60,
        enable_bash=True, bash_workdir=str(replay_dir),
    )
    print(f"  done in {time.time()-t0:.1f}s, tokens={rec['total_tokens']}, "
          f"tool_uses={rec['tool_uses']}")
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--task", default="T_C", choices=STAGE2_TASKS)
    ap.add_argument("--cond", default="NegOnly", choices=STAGE2_CONDS)
    ap.add_argument("--use-saved-trace", action="store_true",
                    help="Skip sub-agent dispatch; run eval on the bundled "
                         "candidate.py output.")
    ap.add_argument("--model", default="sonnet",
                    help="Model alias for fresh dispatch (sonnet/haiku/opus).")
    ap.add_argument("--replay-out", type=pathlib.Path, default=None,
                    help="Where to put the fresh dispatch outputs "
                         "(default: replay/<task>_<cond>/).")
    args = ap.parse_args()

    cell_dir = STAGE2_RUNS / args.task / args.cond
    if not cell_dir.exists():
        sys.exit(f"cell not found: {cell_dir}")

    if args.use_saved_trace:
        eval_dir = cell_dir
        print(f"Using bundled saved trace at {eval_dir}")
    else:
        replay_dir = args.replay_out or (
            HERE / "replay" / f"{args.task}_{args.cond}")
        if replay_dir.exists():
            shutil.rmtree(replay_dir)
        dispatch_fresh_subagent(cell_dir, replay_dir, args.model, args.task)
        eval_dir = replay_dir

    # Phenomenon-aware eval on the cell's pred_results/<task>.npy
    pc = load_eval_module()
    out = eval_dir / "pred_results" / f"{args.task}.npy"
    if not out.exists():
        sys.exit(f"no output at {out}")
    useful, diag = pc.EVALS[args.task](str(out))

    iters = count_iterations(eval_dir / "research_state.jsonl")
    bank_use = collect_bank_citations(eval_dir / "research_state.jsonl")

    print()
    print("=" * 70)
    print(f"Cell: {args.task} / {args.cond}    {'PASS' if useful else 'FAIL'}")
    print("=" * 70)
    print(f"  iterations: {iters}")
    print(f"  cites:   {bank_use['cites'][:6]}{'...' if len(bank_use['cites'])>6 else ''}")
    print(f"  rejects: {bank_use['rejects'][:6]}{'...' if len(bank_use['rejects'])>6 else ''}")
    for k in ("vT_max", "amp_ratio", "u_max", "n_dominant_peaks_vT",
              "n_peaks_above_0.4", "dominance_ratio"):
        if k in diag:
            v = diag[k]
            print(f"  {k}: {v}")
    if not useful and "reason" in diag:
        print(f"  reason: {diag['reason']}")


if __name__ == "__main__":
    main()
