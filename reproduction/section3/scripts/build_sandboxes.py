#!/usr/bin/env python3
"""Build sandboxes for the §3 NK-depth experiment.

Supports four cell types:

  round1        the round-1 baseline (no memory, single shot)
  curator-r1    depth-1 curator (reads 1 round of failure)
  curator-deep  depth-3 curator (reads 3 rounds of Self-Debug failure)
  solver-nkr    round-2 NK-Replay solver (reads one depth-1 NK)
  solver-deep   deepNKR solver (reads one depth-3 NK)

Reviewer CLI:
  python build_sandboxes.py round1 --tasks all
  python build_sandboxes.py round1 --tasks 072
  python build_sandboxes.py curator-deep --tasks 072
  python build_sandboxes.py solver-deep --tasks 072 --model sonnet

By default all sandboxes go to {REPRO_RUNS}/<cell>/task_<id>/.
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib

from _paths import (
    REPRO_ROOT, RUNS, BENCH, TASKS, NK_TEST_24, HARD_19,
    all_38_tasks, ensure_bench_exists,
)


AVAILABLE_LIBS = (
    "numpy, pandas, scikit-learn, scipy, matplotlib, xarray, netCDF4, "
    "rasterio, geopandas, shapely, pyproj, torch, tensorflow, keras, rdkit, "
    "deepchem, chemprop, modnet, matminer, neurokit2, biopsykit, MDAnalysis, "
    "prolif, scikit-image, PIL, openpyxl, statsmodels, ccobra, papyrus_scripts, json"
)
NOT_AVAILABLE = "pymatgen, DeepPurpose, iris"


def ddir(tree: str) -> str:
    for line in tree.splitlines():
        s = line.strip().lstrip("|").lstrip("-").strip().rstrip("/")
        if s:
            return s
    return ""


def _load_task(tid: str) -> dict:
    return json.load(open(TASKS / f"task_{tid}.json"))


def _make_solver_sandbox(tid: str, cell: str) -> pathlib.Path:
    """Create benchmark/datasets, benchmark/eval_programs/gold_results, and
    pred_results/ directories for a solver sandbox."""
    spec = _load_task(tid)
    ds = ddir(spec["dataset_folder_tree"])
    sandbox = RUNS / cell / f"task_{tid}"
    (sandbox / "benchmark" / "datasets").mkdir(parents=True, exist_ok=True)
    (sandbox / "pred_results").mkdir(exist_ok=True)
    ds_link = sandbox / "benchmark" / "datasets" / ds
    if not ds_link.exists():
        os.symlink(BENCH / "datasets" / ds, ds_link)
    gold = sandbox / "benchmark" / "eval_programs" / "gold_results"
    gold.parent.mkdir(exist_ok=True)
    if not gold.exists():
        os.symlink(BENCH / "eval_programs" / "gold_results", gold)
    return sandbox


# ---------- round 1 (no memory) ----------

ROUND1_PROMPT = """You are solving a scientific computing task from ScienceAgentBench.

You will make EXACTLY TWO Write calls:
1) {sandbox}/candidate.py
2) {sandbox}/reasoning.md (under 500 words, sections: Approach / Library choices / Risks / Use of memory)

# Task
{task_inst}

# Domain knowledge
{domain_knowledge}

# Environment
Working dir: {sandbox}
Data paths MUST start with `benchmark/datasets/{ds}/`. Output paths MUST start with `pred_results/`.
Available packages (Python 3.13): {avail}.
NOT available (do not import): {not_avail}. If the task seems to require one of these, substitute with the closest available analogue.

# Dataset folder tree
{tree}

# Data preview
{preview}

# Required output
{output_fname}

# Memory
(none — this is a no-memory, single-shot attempt)

# Constraints
1. Write exactly twice (candidate.py + reasoning.md).
2. You may Read prompt.md. Do NOT read any other files.
3. Script self-contained, runnable as `python candidate.py`.
4. After both Writes, return ONE short sentence.
"""


def build_round1(tid: str) -> pathlib.Path:
    spec = _load_task(tid)
    sandbox = _make_solver_sandbox(tid, "round1")
    prompt = ROUND1_PROMPT.format(
        sandbox=str(sandbox),
        task_inst=spec["task_inst"],
        domain_knowledge=spec["domain_knowledge"] or "(none)",
        ds=ddir(spec["dataset_folder_tree"]),
        avail=AVAILABLE_LIBS,
        not_avail=NOT_AVAILABLE,
        tree=spec["dataset_folder_tree"],
        preview=spec.get("dataset_preview") or "(no preview)",
        output_fname=spec["output_fname"],
    )
    (sandbox / "prompt.md").write_text(prompt)
    return sandbox


# ---------- curator (r1 depth-1) ----------

CURATOR_R1_TMPL = """You are a research-failure curator. Read ONE round-1 attempt's artifacts on a ScienceAgentBench task that failed, and write a single bounded **negative-knowledge (NK) record**.

# Task
Task id: `{task_id}`

Task instruction:
> {task_inst}

# Inputs you may read (and only these)

1. `{round1_dir}/candidate.py`
2. `{round1_dir}/exec.log`
3. `{round1_dir}/eval.log`  {eval_note}
4. `{round1_dir}/reasoning.md`

# Output

Write ONE JSON file via the Write tool to:

`{output_nk_path}`

Schema (no extra fields, no markdown fences, JSON-parseable):

{{
  "task_id": "{task_id}",
  "attempted_route": "<=200 chars; specific method/library/parameters tried",
  "observation": "<=200 chars; specific failure signature",
  "failure": {{
    "layer": "implementation_failure | communication_failure | method_failure",
    "scope": "local_failure | regime_bound_failure | general_failure",
    "degree": "contradicted | partial | inconclusive | unstable | artifact_driven | overclaimed",
    "recommended_action": "retry | change_method | narrow_claim | abandon_route",
    "risk": "low_risk_omission | medium_risk_drift | high_risk_false_progress"
  }},
  "rationale": "<=300 chars; mechanism-level explanation",
  "recommended_alternative": "<=300 chars; ONE specific concrete fix, named with library + parameters"
}}

# Hard rules
1. Read up to four input files above. Do NOT read anything else.
2. Write tool EXACTLY ONCE.
3. Do NOT use Bash, Edit, Grep, Glob.
4. After Write, respond with ONE short sentence on the root cause.
"""


def build_curator_r1(tid: str, round1_dir: pathlib.Path) -> pathlib.Path:
    spec = _load_task(tid)
    sandbox = RUNS / "curator-r1" / f"task_{tid}"
    sandbox.mkdir(parents=True, exist_ok=True)
    nk_out = RUNS / "nk_records" / f"task_{tid}.json"
    nk_out.parent.mkdir(parents=True, exist_ok=True)
    eval_present = (round1_dir / "eval.log").exists()
    eval_note = ("(present)" if eval_present
                 else "(ABSENT — exec crashed before producing output)")
    prompt = CURATOR_R1_TMPL.format(
        task_id=tid, task_inst=spec["task_inst"],
        round1_dir=str(round1_dir),
        output_nk_path=str(nk_out),
        eval_note=eval_note,
    )
    (sandbox / "prompt.md").write_text(prompt)
    return sandbox


# ---------- curator (deep depth-3) ----------

CURATOR_DEEP_TMPL = """You are a deep research-failure curator. Read THREE rounds of Self-Debug failure on one ScienceAgentBench task (each round saw the prior round's code + raw stderr; all three failed) and write ONE distilled depth-3 NK record.

# Task
Task id: `{task_id}`

Task instruction:
> {task_inst}

# Inputs you may read

Round 1 (no memory, free attempt):
  - {round1_dir}/candidate.py
  - {round1_dir}/exec.log
  - {round1_dir}/eval.log {r1_eval_note}
  - {round1_dir}/reasoning.md

Round 2 (Self-Debug covering round 1):
  - {round2_dir}/candidate.py
  - {round2_dir}/exec.log
  - {round2_dir}/eval.log {r2_eval_note}
  - {round2_dir}/reasoning.md

Round 3 (Self-Debug covering round 2):
  - {round3_dir}/candidate.py
  - {round3_dir}/exec.log
  - {round3_dir}/eval.log {r3_eval_note}
  - {round3_dir}/reasoning.md

# Output

Write ONE JSON file to `{output_nk_path}` with this schema:

{{
  "task_id": "{task_id}",
  "depth": 3,
  "rounds_summary": [
    {{"round": 1, "attempted_route": "...", "observation": "..."}},
    {{"round": 2, "attempted_route": "...", "observation": "..."}},
    {{"round": 3, "attempted_route": "...", "observation": "..."}}
  ],
  "ruled_out_routes": ["...", "...", "..."],
  "synthesised_diagnosis": "<=400 chars; ONE coherent mechanism explaining all 3 failures",
  "failure": {{"layer", "scope", "degree", "recommended_action", "risk"}},
  "rationale": "<=300 chars",
  "recommended_alternative": "<=400 chars; ONE specific fix NOT in ruled_out_routes"
}}

# Hard rules
1. Read only the 12 listed input files.
2. Write tool EXACTLY ONCE.
3. The recommended_alternative MUST avoid everything in ruled_out_routes.
"""


def build_curator_deep(tid: str, round1_dir, round2_dir, round3_dir) -> pathlib.Path:
    spec = _load_task(tid)
    sandbox = RUNS / "curator-deep" / f"task_{tid}"
    sandbox.mkdir(parents=True, exist_ok=True)
    nk_out = RUNS / "nk_records" / f"task_{tid}_deep.json"
    nk_out.parent.mkdir(parents=True, exist_ok=True)
    def _en(p):
        return ("(present)" if (p / "eval.log").exists()
                else "(ABSENT)")
    prompt = CURATOR_DEEP_TMPL.format(
        task_id=tid, task_inst=spec["task_inst"],
        round1_dir=str(round1_dir),
        round2_dir=str(round2_dir),
        round3_dir=str(round3_dir),
        r1_eval_note=_en(round1_dir),
        r2_eval_note=_en(round2_dir),
        r3_eval_note=_en(round3_dir),
        output_nk_path=str(nk_out),
    )
    (sandbox / "prompt.md").write_text(prompt)
    return sandbox


# ---------- solver: NK-Replay (depth-1) ----------

SOLVER_NK_TMPL = """You are solving a scientific computing task. A prior agent failed; a structured NK record summarises that failure.

EXACTLY TWO Write calls:
1) {sandbox}/candidate.py
2) {sandbox}/reasoning.md

# Task
{task_inst}

# Domain knowledge
{domain_knowledge}

# Environment
Working dir: {sandbox}
Data paths start with `benchmark/datasets/{ds}/`. Output paths start with `pred_results/`.
Available packages: {avail}.
NOT available: {not_avail}.

# Dataset folder tree
{tree}

# Data preview
{preview}

# Required output
{output_fname}

# Memory: {memory_label}

{memory_block}

# Constraints
1. Write exactly twice (candidate.py + reasoning.md).
2. Read prompt.md and {nk_files_clause}. Do NOT read other files.
3. Script self-contained, runnable as `python candidate.py`.
4. After both Writes, return ONE short sentence on which NK recommendation you followed.
"""


def build_solver_nkr(tid: str, nk_file: pathlib.Path) -> pathlib.Path:
    """Build a depth-1 NK-Replay solver sandbox (cell = 'solver-nkr')."""
    spec = _load_task(tid)
    sandbox = _make_solver_sandbox(tid, "solver-nkr")
    import shutil
    shutil.copy2(nk_file, sandbox / "nk.json")
    memory_block = (
        f"A bounded NK record summarising the prior failure is at:\n"
        f"  - {sandbox}/nk.json\n\n"
        f"Read it. Use the `recommended_alternative` field."
    )
    prompt = SOLVER_NK_TMPL.format(
        sandbox=str(sandbox),
        task_inst=spec["task_inst"],
        domain_knowledge=spec["domain_knowledge"] or "(none)",
        ds=ddir(spec["dataset_folder_tree"]),
        avail=AVAILABLE_LIBS,
        not_avail=NOT_AVAILABLE,
        tree=spec["dataset_folder_tree"],
        preview=spec.get("dataset_preview") or "(no preview)",
        output_fname=spec["output_fname"],
        memory_label="depth-1 NK from prior failed attempt",
        memory_block=memory_block,
        nk_files_clause="nk.json",
    )
    (sandbox / "prompt.md").write_text(prompt)
    return sandbox


def build_solver_deep(tid: str, deep_nk_file: pathlib.Path) -> pathlib.Path:
    """Build a depth-3 deepNKR solver sandbox (cell = 'solver-deep')."""
    spec = _load_task(tid)
    sandbox = _make_solver_sandbox(tid, "solver-deep")
    import shutil
    shutil.copy2(deep_nk_file, sandbox / "deep_nk.json")
    memory_block = (
        f"A depth-3 NK distilled from 3 rounds of Self-Debug failure is at:\n"
        f"  - {sandbox}/deep_nk.json\n\n"
        f"Fields you must consult: `synthesised_diagnosis`, "
        f"`ruled_out_routes` (do NOT propose any of these), "
        f"`recommended_alternative`."
    )
    prompt = SOLVER_NK_TMPL.format(
        sandbox=str(sandbox),
        task_inst=spec["task_inst"],
        domain_knowledge=spec["domain_knowledge"] or "(none)",
        ds=ddir(spec["dataset_folder_tree"]),
        avail=AVAILABLE_LIBS,
        not_avail=NOT_AVAILABLE,
        tree=spec["dataset_folder_tree"],
        preview=spec.get("dataset_preview") or "(no preview)",
        output_fname=spec["output_fname"],
        memory_label="depth-3 NK distilled from 3 rounds of failure",
        memory_block=memory_block,
        nk_files_clause="deep_nk.json",
    )
    (sandbox / "prompt.md").write_text(prompt)
    return sandbox


# ---------- CLI ----------

def _resolve_tasks(arg: str, all_set: list[str]) -> list[str]:
    if arg == "all":
        return all_set
    return [t.strip() for t in arg.split(",")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cell", choices=["round1", "curator-r1", "curator-deep",
                                     "solver-nkr", "solver-deep"])
    ap.add_argument("--tasks", required=True,
                    help="Comma-separated task ids, or 'all' (round1: all 38;"
                         " others: NK_TEST_24 or HARD_19).")
    ap.add_argument("--round1-dir", type=pathlib.Path,
                    help="For curator-r1: dir containing round-1 artifacts.")
    ap.add_argument("--round2-dir", type=pathlib.Path,
                    help="For curator-deep: dir with round-2 (B2) artifacts.")
    ap.add_argument("--round3-dir", type=pathlib.Path,
                    help="For curator-deep: dir with round-3 (B2) artifacts.")
    ap.add_argument("--nk-file", type=pathlib.Path,
                    help="For solver-nkr / solver-deep: NK file path.")
    args = ap.parse_args()

    ensure_bench_exists()

    if args.cell == "round1":
        tasks = _resolve_tasks(args.tasks, all_38_tasks())
        for tid in tasks:
            sb = build_round1(tid)
            print(f"  built {sb}")

    elif args.cell == "curator-r1":
        tasks = _resolve_tasks(args.tasks, NK_TEST_24)
        for tid in tasks:
            r1 = args.round1_dir or (RUNS / "round1" / f"task_{tid}")
            sb = build_curator_r1(tid, r1)
            print(f"  built {sb}  (reads {r1})")

    elif args.cell == "curator-deep":
        tasks = _resolve_tasks(args.tasks, HARD_19)
        for tid in tasks:
            r1 = args.round1_dir or (RUNS / "round1" / f"task_{tid}")
            r2 = args.round2_dir or (RUNS / "solver-b2-r2" / f"task_{tid}")
            r3 = args.round3_dir or (RUNS / "solver-b2-r3" / f"task_{tid}")
            sb = build_curator_deep(tid, r1, r2, r3)
            print(f"  built {sb}")

    elif args.cell == "solver-nkr":
        tasks = _resolve_tasks(args.tasks, NK_TEST_24)
        for tid in tasks:
            nk = args.nk_file or (RUNS / "nk_records" / f"task_{tid}.json")
            sb = build_solver_nkr(tid, nk)
            print(f"  built {sb}  (reads {nk.name})")

    elif args.cell == "solver-deep":
        tasks = _resolve_tasks(args.tasks, HARD_19)
        for tid in tasks:
            nk = args.nk_file or (RUNS / "nk_records" / f"task_{tid}_deep.json")
            sb = build_solver_deep(tid, nk)
            print(f"  built {sb}  (reads {nk.name})")


if __name__ == "__main__":
    main()
