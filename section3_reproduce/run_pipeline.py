#!/usr/bin/env python3
"""run_pipeline.py — end-to-end Stage 1 + Stage 2 driver for paper §3.

Reproduces the negative-knowledge pipeline behind §3 on one or more
ScienceAgentBench tasks. Stage 1 is *autoresearch + knowledge production*:
the agent attempts the task with no memory, then self-debugs across two
covering-memory rounds, then a curator distils the three-round trace
into a structured NK record. Stage 2 is *knowledge consumption*: a fresh
agent receives only that NK record and re-attempts the task.

================================================================
Reviewer usage
================================================================

Required environment:
    export ANTHROPIC_API_KEY=sk-ant-...
    export SAB_BENCH=/abs/path/to/ScienceAgentBench/benchmark
    export PY_VENV=/abs/path/to/your/python    # has the 28-lib stack

(1) Cheapest demonstration --- one task, reuse our saved autoresearch
    trace, just re-run the curator + solver. ~$1, ~3 minutes.

        python run_pipeline.py --task 072 --use-saved-trace

(2) Full single-task end-to-end --- one task, re-run everything from
    scratch (round-1 + 2x Self-Debug + curator + solver). ~$3, ~10 minutes.

        python run_pipeline.py --task 072

(3) Full §3 reproduction --- all 19 hard tasks, full pipeline. ~$60, 2-4 hours.

        python run_pipeline.py --task all

================================================================
What each stage does
================================================================

Stage 1 -- knowledge production (autoresearch + curator)
   1.1  round-1            no memory, single shot  (fails by design on these tasks)
   1.2  round-2 B2         Self-Debug; reads round-1 candidate.py + exec.log
   1.3  round-3 B2         Self-Debug; reads round-2 candidate.py + exec.log
   1.4  depth-1 curator    reads round-1 artifacts -> writes a depth-1 NK
   1.5  depth-3 curator    reads round-1/2/3 artifacts -> writes a depth-3 NK

Stage 2 -- knowledge consumption (NK -> solver)
   2.1  NKR solver         reads depth-1 NK only -> writes candidate.py
   2.2  deepNKR Sonnet     reads depth-3 NK only -> writes candidate.py
   2.3  deepNKR Haiku      cross-model: same depth-3 NK -> Haiku writes candidate.py
   2.4  execute_candidates run each candidate.py + grade via the task's evaluator

All dispatches use scripts/dispatch_subagent.py (Anthropic API; tool-use
loop with Read/Write allowlists).
================================================================
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys

# Make `scripts/` importable so we can reuse the helper modules.
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))

from _paths import (
    REPRO_ROOT, RUNS, BENCH, TASKS, LOGS, PY,
    HARD_19, NK_TEST_24, ensure_bench_exists,
)
import build_sandboxes as bb
from dispatch_subagent import run_subagent, MODEL_ALIASES
from execute_candidates import execute_one

# High-level NK production. nk_curator wraps the curator-prompt
# materialisation, the dispatch, and schema validation so that
# run_pipeline never duplicates curator logic locally.
sys.path.insert(0, str(HERE))  # nk_curator.py lives next to this file
from nk_curator import NKCurator, FailureArtifacts


# --------------------------------------------------------------------
# Path helpers
# --------------------------------------------------------------------

def round1_dir(tid: str) -> pathlib.Path:
    return RUNS / "round1" / f"task_{tid}"


def round_b2_dir(tid: str, k: int) -> pathlib.Path:
    return RUNS / f"round{k}_B2" / f"task_{tid}"


def curator_r1_dir(tid: str) -> pathlib.Path:
    return RUNS / "curator-r1" / f"task_{tid}"


def curator_deep_dir(tid: str) -> pathlib.Path:
    return RUNS / "curator-deep" / f"task_{tid}"


def nk_r1_path(tid: str) -> pathlib.Path:
    return RUNS / "nk_records" / f"task_{tid}.json"


def nk_deep_path(tid: str) -> pathlib.Path:
    return RUNS / "nk_records" / f"task_{tid}_deep.json"


def solver_nkr_dir(tid: str) -> pathlib.Path:
    return RUNS / "solver-nkr" / f"task_{tid}"


def solver_deep_dir(tid: str, model: str) -> pathlib.Path:
    return RUNS / f"solver-deep-{model}" / f"task_{tid}"


# --------------------------------------------------------------------
# Single-dispatch wrapper (records every call)
# --------------------------------------------------------------------

DISPATCH_LOG: list[dict] = []


def dispatch(
    label: str,
    sandbox: pathlib.Path,
    model: str,
    read_allowlist: list,
    output_files: list,
) -> dict:
    """Dispatch one sub-agent and record the call. Returns the record."""
    prompt_path = sandbox / "prompt.md"
    prompt = prompt_path.read_text()
    read_set = {str(prompt_path.resolve())}
    read_set.update(str(pathlib.Path(p).resolve()) for p in read_allowlist)
    write_set = {str(pathlib.Path(p).resolve()) for p in output_files}

    print(f"  → dispatch [{label}] model={model} "
          f"sandbox={sandbox.name}", flush=True)
    rec = run_subagent(prompt, MODEL_ALIASES[model], read_set, write_set)
    rec["label"] = label
    rec["sandbox"] = str(sandbox)
    rec["dispatched_at_utc"] = dt.datetime.now(dt.UTC).isoformat()
    DISPATCH_LOG.append(rec)
    (sandbox / "dispatch_record.json").write_text(json.dumps(rec, indent=2))
    print(f"    tokens={rec['total_tokens']} "
          f"tool_uses={rec['tool_uses']} "
          f"stop={rec['stop_reason']} "
          f"duration={rec['duration_sec']}s", flush=True)
    return rec


# --------------------------------------------------------------------
# Stage 1: autoresearch + knowledge production
# --------------------------------------------------------------------

def stage1_full(tid: str, model: str = "sonnet"):
    """Run round-1, two Self-Debug rounds, then both curators on this task."""
    print(f"\n══ Stage 1 ── task_{tid} (full autoresearch) ══")

    # 1.1 round-1 (no memory)
    sb1 = bb.build_round1(tid)
    dispatch("round1", sb1, model,
             read_allowlist=[],
             output_files=[sb1 / "candidate.py", sb1 / "reasoning.md"])
    execute_one(tid, "round1")

    # 1.2 round-2 B2 Self-Debug
    sb2 = _build_round_b2(tid, k=2, prior_dir=sb1)
    dispatch("round2_B2", sb2, model,
             read_allowlist=[sb1 / "candidate.py",
                             sb1 / "exec.log",
                             sb1 / "eval.log"],
             output_files=[sb2 / "candidate.py", sb2 / "reasoning.md"])
    execute_one(tid, "round2_B2")

    # 1.3 round-3 B2 Self-Debug
    sb3 = _build_round_b2(tid, k=3, prior_dir=sb2)
    dispatch("round3_B2", sb3, model,
             read_allowlist=[sb2 / "candidate.py",
                             sb2 / "exec.log",
                             sb2 / "eval.log"],
             output_files=[sb3 / "candidate.py", sb3 / "reasoning.md"])
    execute_one(tid, "round3_B2")

    # 1.4 + 1.5 — depth-1 and depth-3 curators via the nk_curator module.
    _curate_both(tid, [sb1, sb2, sb3], model)


def stage1_from_saved_trace(tid: str, model: str = "sonnet"):
    """Skip autoresearch; reuse saved trace from logs/ to feed the curators.

    The reviewer-cheapest path: we already shipped the round-1/2/3 + B2
    artifacts (and their full I/O) in logs/dispatches/solver/. We point
    the deep curator at the same on-disk content the original deep
    curator saw, then run the curator + downstream solver fresh.
    """
    print(f"\n══ Stage 1 ── task_{tid} (using saved autoresearch trace) ══")

    # Stage the saved artifacts into RUNS/round*/task_<id>/ so build
    # scripts can find them at predictable paths.
    saved_round_dirs = _stage_saved_rounds(tid)
    sb1, sb2, sb3 = saved_round_dirs

    # depth-1 + depth-3 curators via the nk_curator module
    _curate_both(tid, [sb1, sb2, sb3], model)


def _curate_both(tid: str, round_dirs: list, model: str):
    """Produce both the depth-1 and depth-3 NK records for one task,
    using the nk_curator module. Records both dispatches into the
    pipeline-level DISPATCH_LOG so the cost summary is correct."""
    spec = json.load(open(TASKS / f"task_{tid}.json"))
    task_inst = spec["task_inst"]
    sb1, sb2, sb3 = round_dirs

    def _arts_from(d):
        return FailureArtifacts(
            candidate=str(d / "candidate.py"),
            exec_log=str(d / "exec.log"),
            reasoning=str(d / "reasoning.md"),
            eval_log=str(d / "eval.log") if (d / "eval.log").exists() else None,
        )

    curator = NKCurator(model=model)

    # depth-1
    print(f"  → nk_curator.produce_depth1 task_{tid} model={model}",
          flush=True)
    res1 = curator.produce_depth1(
        task_id=tid, task_inst=task_inst,
        round_artifacts=_arts_from(sb1),
        output_path=nk_r1_path(tid),
        round_dir=sb1,
    )
    _record_curator_call("curator-r1", tid, res1)

    # depth-3
    print(f"  → nk_curator.produce_deep task_{tid} (3 rounds) model={model}",
          flush=True)
    res3 = curator.produce_deep(
        task_id=tid, task_inst=task_inst,
        rounds=[_arts_from(sb1), _arts_from(sb2), _arts_from(sb3)],
        output_path=nk_deep_path(tid),
        round_dirs=[sb1, sb2, sb3],
    )
    _record_curator_call("curator-deep", tid, res3)


def _record_curator_call(label: str, tid: str, res):
    """Roll an NKCurator CurationResult into the pipeline's DISPATCH_LOG."""
    rec = dict(res.dispatch)
    rec["label"] = label
    rec["task_id"] = tid
    rec["depth"] = res.depth
    rec["output_path"] = res.output_path
    rec["schema_issues"] = res.schema_issues
    DISPATCH_LOG.append(rec)
    print(f"    tokens={rec['total_tokens']} "
          f"tool_uses={rec['tool_uses']} "
          f"stop={rec['stop_reason']} "
          f"duration={rec['duration_sec']}s "
          f"schema_valid={'✓' if not res.schema_issues else '✗'}",
          flush=True)


def _build_round_b2(tid: str, k: int, prior_dir: pathlib.Path):
    """Build a round-k B2 Self-Debug sandbox that reads prior_dir as memory."""
    spec = json.load(open(TASKS / f"task_{tid}.json"))
    sandbox = round_b2_dir(tid, k)
    bb._make_solver_sandbox(tid, f"round{k}_B2")
    sandbox = bb.RUNS / f"round{k}_B2" / f"task_{tid}"
    prompt = bb.ROUND1_PROMPT.format(
        sandbox=str(sandbox),
        task_inst=spec["task_inst"],
        domain_knowledge=spec["domain_knowledge"] or "(none)",
        ds=bb.ddir(spec["dataset_folder_tree"]),
        avail=bb.AVAILABLE_LIBS,
        not_avail=bb.NOT_AVAILABLE,
        tree=spec["dataset_folder_tree"],
        preview=spec.get("dataset_preview") or "(no preview)",
        output_fname=spec["output_fname"],
    ).replace(
        "# Memory\n(none — this is a no-memory, single-shot attempt)",
        f"# Memory: prior attempt's full code + stderr\n"
        f"This is attempt {k} on this task. Read the prior attempt's "
        f"artifacts to diagnose its failure and write a better candidate:\n"
        f"  - {prior_dir}/candidate.py\n"
        f"  - {prior_dir}/exec.log\n"
        f"  - {prior_dir}/eval.log",
    )
    (sandbox / "prompt.md").write_text(prompt)
    return sandbox


def _stage_saved_rounds(tid: str):
    """Copy round-1/2/3 artifacts from logs/dispatches/solver/ into
    RUNS/round*/task_<id>/ so curator builds can find them."""
    cell_map = {"round1": 1, "round2_B2": 2, "round3_B2": 3}
    out = []
    for cell, k in cell_map.items():
        src_record = LOGS / "dispatches" / "solver" / f"task_{tid}__{cell}.json"
        if not src_record.exists():
            raise SystemExit(
                f"Missing saved trace: {src_record}\n"
                f"--use-saved-trace requires logs/dispatches/solver/*"
                f"task_{tid}__{cell}.json. Re-run without --use-saved-trace"
                f" or restore the logs/ archive."
            )
        rec = json.load(open(src_record))
        dest = (round1_dir(tid) if cell == "round1"
                else round_b2_dir(tid, k))
        dest.mkdir(parents=True, exist_ok=True)

        (dest / "candidate.py").write_text(
            rec["outputs"]["candidate"]["content"]
            if rec["outputs"].get("candidate", {}).get("content")
            else _read_from_disk(rec["outputs"]["candidate"]["path"])
        )
        # Per-file: rebuild what's on the original cell's disk.
        for kind in ("exec_log", "eval_log"):
            content = rec["execution"].get(kind, {}).get("content")
            fn = "exec.log" if kind == "exec_log" else "eval.log"
            if content is not None:
                (dest / fn).write_text(content)
        # reasoning.md
        if rec["outputs"].get("reasoning", {}).get("content"):
            (dest / "reasoning.md").write_text(
                rec["outputs"]["reasoning"]["content"]
            )
        out.append(dest)
    return out


def _read_from_disk(path):
    try:
        return pathlib.Path(path).read_text()
    except Exception:
        return ""


# --------------------------------------------------------------------
# Stage 2: knowledge consumption
# --------------------------------------------------------------------

def stage2(tid: str, *, do_nkr=True, do_deep_sonnet=True, do_deep_haiku=True):
    """Run NK-consuming solvers and grade them."""
    print(f"\n══ Stage 2 ── task_{tid} (NK consumption) ══")

    if do_nkr and nk_r1_path(tid).exists():
        sb = bb.build_solver_nkr(tid, nk_r1_path(tid))
        dispatch("solver-nkr (depth-1)", sb, "sonnet",
                 read_allowlist=[sb / "nk.json"],
                 output_files=[sb / "candidate.py", sb / "reasoning.md"])
        execute_one(tid, "solver-nkr")

    if do_deep_sonnet and nk_deep_path(tid).exists():
        sb = bb.build_solver_deep(tid, nk_deep_path(tid))
        # build_solver_deep writes to RUNS/solver-deep/; the
        # cross-model variant needs a parallel dir.
        # We rename via copy to solver-deep-sonnet/ for clarity:
        target = solver_deep_dir(tid, "sonnet")
        if sb != target:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(sb), str(target))
        dispatch("solver-deep Sonnet (depth-3)", target, "sonnet",
                 read_allowlist=[target / "deep_nk.json"],
                 output_files=[target / "candidate.py", target / "reasoning.md"])
        # execute_one needs the cell name in RUNS/<cell>/task_<id>/
        execute_one(tid, "solver-deep-sonnet")

    if do_deep_haiku and nk_deep_path(tid).exists():
        sb = bb.build_solver_deep(tid, nk_deep_path(tid))
        target = solver_deep_dir(tid, "haiku")
        if sb != target:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(sb), str(target))
        dispatch("solver-deep Haiku (cross-model)", target, "haiku",
                 read_allowlist=[target / "deep_nk.json"],
                 output_files=[target / "candidate.py", target / "reasoning.md"])
        execute_one(tid, "solver-deep-haiku")


# --------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="End-to-end Stage 1 + Stage 2 driver for §3.")
    ap.add_argument("--task", default="072",
                    help="Task id (e.g. 072), or 'all' for the 19 hard tasks "
                         "(default: 072 — the depth-3 NK breakthrough task).")
    ap.add_argument("--stage", choices=["stage1", "stage2", "both"],
                    default="both",
                    help="Which stage to run (default: both).")
    ap.add_argument("--use-saved-trace", action="store_true",
                    help="Stage 1: reuse the autoresearch trace from logs/ "
                         "instead of re-running round-1 + Self-Debug. Saves "
                         "3 sub-agent dispatches per task.")
    ap.add_argument("--skip-haiku", action="store_true",
                    help="Stage 2: don't run the Haiku cross-model condition.")
    args = ap.parse_args()

    ensure_bench_exists()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not set in environment.")

    tasks = HARD_19 if args.task == "all" else [args.task]
    print(f"running {len(tasks)} task(s): {tasks}")
    print(f"stage={args.stage}, use_saved_trace={args.use_saved_trace}")

    for tid in tasks:
        if args.stage in ("stage1", "both"):
            if args.use_saved_trace:
                stage1_from_saved_trace(tid)
            else:
                stage1_full(tid)
        if args.stage in ("stage2", "both"):
            stage2(tid, do_deep_haiku=not args.skip_haiku)

    # Persist dispatch log for the whole run.
    pipeline_log = RUNS / f"pipeline_log_{dt.datetime.now(dt.UTC).isoformat(timespec='seconds').replace(':', '-')}.json"
    pipeline_log.write_text(json.dumps(DISPATCH_LOG, indent=2))
    print(f"\nfull pipeline log: {pipeline_log}")

    # Summary
    n_dispatches = len(DISPATCH_LOG)
    total_tokens = sum(r["total_tokens"] for r in DISPATCH_LOG)
    print(f"\n{n_dispatches} dispatches; "
          f"total ~{total_tokens} tokens "
          f"(~${total_tokens / 1e6 * 5:.2f} at Sonnet rate)")


if __name__ == "__main__":
    main()
