#!/usr/bin/env python3
"""Build deepNKR sandboxes for the 19 hard tasks.

Two cells per task — same prompt, different solver model:
  - pilot_2026-05-10/runs/task_<id>/sonnet_4.6/v3/deepNKR_sonnet/  ← Sonnet solver
  - pilot_2026-05-10/runs/task_<id>/haiku_4.5/v3/deepNKR_haiku/    ← Haiku solver

Each sandbox sees:
  - prompt.md     (task spec; explicitly says this is a deep NK with 3 rounds of prior failures)
  - deep_nk.json  (copy of section3/04_outputs/nk_records/task_<id>_deep.json)
  - benchmark/datasets/<ds_name>  (symlink to real data)
  - benchmark/eval_programs/gold_results  (symlink, for the evaluator only)

The agent must Write candidate.py + reasoning.md.

This is the §3 Option-A+B experiment:
  A — NK derived from 3-round Self-Debug exploration, not a single failure
  B — same NK tested on the same model (Sonnet) and a cheaper model (Haiku)
"""
from __future__ import annotations
import json
import os
import pathlib
import shutil

PILOT = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/experiments/pilot_2026-05-10"
)
BENCH = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/benchmark"
)
SECTION3 = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/Negative_Knowledge/section3"
)

# 19 hard tasks (B2 failed all 3 rounds)
DEEP_TASKS = [
    "002", "012", "018", "021", "022", "026", "029", "034", "035",
    "037", "044", "058", "060", "067", "072", "078", "085", "087", "101",
]


def ddir(tree: str) -> str:
    for line in tree.splitlines():
        s = line.strip().lstrip("|").lstrip("-").strip().rstrip("/")
        if s:
            return s
    return ""


AVAILABLE_LIBS = (
    "numpy, pandas, scikit-learn, scipy, matplotlib, xarray, netCDF4, "
    "rasterio, geopandas, shapely, pyproj, torch, tensorflow, keras, rdkit, "
    "deepchem, chemprop, modnet, matminer, neurokit2, biopsykit, MDAnalysis, "
    "prolif, scikit-image, PIL, openpyxl, statsmodels, ccobra, papyrus_scripts, json"
)
NOT_AVAILABLE = "pymatgen, DeepPurpose, iris"


PROMPT_TMPL = """You are solving a scientific computing task from ScienceAgentBench. This is a FOURTH attempt — three prior Self-Debug rounds (Sonnet-4.6 with full covering memory: prior code + raw stderr) all failed.

EXACTLY TWO Write calls:
1) {run_dir}/candidate.py
2) {run_dir}/reasoning.md (under 500 words, sections: Approach / Library choices / Risks / Use of memory)

# Task
{task_inst}

# Domain knowledge
{domain_knowledge}

# Environment
Working dir: {run_dir}
Data paths MUST start with `benchmark/datasets/{ds}/`. Output paths MUST start with `pred_results/`.
Available packages (Python 3.13): {avail}.
NOT available (do not import): {not_avail}. If the task seems to require one of these, substitute with the closest available analogue.

# Dataset folder tree
{tree}

# Data preview
{preview}

# Required output
{output_fname}

# Memory: deep negative-knowledge record (3-round distillation)

A previous Sonnet-4.6 agent ran 3 rounds of Self-Debug on this task with
covering memory (each round saw the prior round's full code and stderr).
All 3 rounds failed. A curator then read all 3 rounds' artifacts and
distilled a single deep NK record at:

  - {run_dir}/deep_nk.json

You MUST Read deep_nk.json before writing your candidate. Its fields:

  - `rounds_summary` — what each of the 3 prior rounds tried and how it failed
  - `ruled_out_routes` — 2-4 concrete (library + parameter) combinations
    that have been empirically shown not to work on this task. DO NOT
    propose any of these routes; they will fail again.
  - `synthesised_diagnosis` — one coherent mechanism-level explanation
    that ties all three failures together. This is the curator's best
    understanding of why this task is genuinely hard.
  - `recommended_alternative` — ONE specific concrete fix the curator
    recommends, which avoids everything in `ruled_out_routes`. This is
    your default starting point; you may deviate if you can articulate a
    clear reason in reasoning.md.

You do NOT have access to the 3 prior attempts' source code, raw stderr,
or evaluator output — ONLY this deep NK record.

# Constraints
1. Write exactly twice (candidate.py + reasoning.md).
2. You may Read prompt.md and deep_nk.json. Do NOT read any other files.
3. Script self-contained, runnable as `python candidate.py`.
4. After both Writes, return ONE short sentence describing which part of
   the deep NK (recommended_alternative or your own variant) you implemented.
"""


def _build(tid: str, model_dir: str, cell_name: str) -> str | None:
    spec = json.load(open(PILOT / f"tasks/task_{tid}.json"))
    ds = ddir(spec["dataset_folder_tree"])

    run_dir = PILOT / f"runs/task_{tid}/{model_dir}/v3/{cell_name}"
    if (run_dir / "candidate.py").exists():
        print(f"  skip task_{tid}/{cell_name}: candidate exists")
        return None

    # sandbox layout
    (run_dir / "benchmark" / "datasets").mkdir(parents=True, exist_ok=True)
    (run_dir / "pred_results").mkdir(exist_ok=True)

    ds_link = run_dir / "benchmark" / "datasets" / ds
    if not ds_link.exists():
        os.symlink(BENCH / "datasets" / ds, ds_link)

    gold_link = run_dir / "benchmark" / "eval_programs" / "gold_results"
    gold_link.parent.mkdir(exist_ok=True)
    if not gold_link.exists():
        os.symlink(BENCH / "eval_programs" / "gold_results", gold_link)

    # copy deep NK into sandbox
    deep_nk = SECTION3 / f"04_outputs/nk_records/task_{tid}_deep.json"
    if not deep_nk.exists():
        print(f"  SKIP task_{tid}/{cell_name}: deep NK missing")
        return None
    shutil.copy2(deep_nk, run_dir / "deep_nk.json")

    prompt = PROMPT_TMPL.format(
        run_dir=str(run_dir),
        task_inst=spec["task_inst"],
        domain_knowledge=spec["domain_knowledge"] or "(none)",
        ds=ds,
        avail=AVAILABLE_LIBS,
        not_avail=NOT_AVAILABLE,
        tree=spec["dataset_folder_tree"],
        preview=spec.get("dataset_preview") or "(no preview)",
        output_fname=spec["output_fname"],
    )
    (run_dir / "prompt.md").write_text(prompt)
    return str(run_dir)


def main():
    built_sonnet, built_haiku = [], []
    for tid in DEEP_TASKS:
        s = _build(tid, "sonnet_4.6", "deepNKR_sonnet")
        if s:
            built_sonnet.append(s)
        h = _build(tid, "haiku_4.5", "deepNKR_haiku")
        if h:
            built_haiku.append(h)

    print(f"\nbuilt {len(built_sonnet)} Sonnet deepNKR sandboxes")
    print(f"built {len(built_haiku)} Haiku deepNKR sandboxes")


if __name__ == "__main__":
    main()
