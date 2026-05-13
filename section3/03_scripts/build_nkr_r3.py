#!/usr/bin/env python3
"""Build round-3 NK-Replay sandboxes for the 22 round-2 NKR fails.

Each sandbox is at
  pilot_2026-05-10/runs/task_<id>/sonnet_4.6/v3/round3_NKR/
so the existing run_v3.py picks it up.

Round-3 NKR agent sees:
  - prompt.md           — task spec, no raw round-1/round-2 code/log
  - nk_r1.json          — copy of the round-1 NK
  - nk_r2.json          — copy of the round-2 NK (with relationship_to_round1)
  - benchmark/...       — data + gold symlinks

This isolates whether NK accumulates: r1 NK gave fix A; r2 NK records
that A was correct-but-insufficient and recommends B; can the r3 agent
combine them and PASS?
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

# 22 tasks that failed round-2 NKR
R2_FAIL_TASKS = [
    "002", "005", "012", "018", "021", "022", "026", "029", "034", "035",
    "037", "044", "058", "060", "067", "071", "072", "078", "085", "087",
    "097", "101",
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


PROMPT_TMPL = """You are solving a scientific computing task from ScienceAgentBench. This is the THIRD attempt on this task — two prior attempts have failed.

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

# Memory: accumulating bounded failure records

Two prior attempts have produced two NK records:

  - {run_dir}/nk_r1.json   — bounded failure record from attempt 1
  - {run_dir}/nk_r2.json   — bounded failure record from attempt 2

You are expected to Read both. They form an accumulating diagnosis:

  - `nk_r1.json` describes the round-1 failure and recommended a fix.
  - The round-2 agent implemented that fix and STILL failed.
  - `nk_r2.json` describes the round-2 failure and contains a critical
    field `relationship_to_round1` indicating one of:
      * `round1_recipe_was_correct_but_insufficient` — apply r1 fix AND
        the r2 fix on top
      * `round1_recipe_was_wrong` — discard r1 fix, use r2 fix instead
      * `round1_recipe_was_misapplied` — re-apply r1 fix more carefully
      * `new_failure_mode_unrelated_to_round1` — keep r1 fix, fix r2 mode

You do NOT have access to either prior attempt's source code, raw stderr,
or evaluator output — ONLY the two NK records.

# Constraints
1. Write exactly twice (candidate.py + reasoning.md).
2. You may Read prompt.md, nk_r1.json, and nk_r2.json. Do NOT read any other files.
3. Script self-contained, runnable as `python candidate.py`.
4. After both Writes, return ONE short sentence describing which prior
   recommendation(s) you followed and what new fix (if any) you added.
"""


def main():
    built = []
    for tid in R2_FAIL_TASKS:
        spec = json.load(open(PILOT / f"tasks/task_{tid}.json"))
        ds = ddir(spec["dataset_folder_tree"])

        run_dir = PILOT / f"runs/task_{tid}/sonnet_4.6/v3/round3_NKR"
        if (run_dir / "candidate.py").exists():
            print(f"  skip task_{tid}: candidate already exists")
            continue

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

        # copy both NKs into the sandbox
        r1_nk = SECTION3 / f"04_outputs/nk_records/task_{tid}.json"
        r2_nk = SECTION3 / f"04_outputs/nk_records/task_{tid}_r2.json"
        if not r1_nk.exists() or not r2_nk.exists():
            print(f"  SKIP task_{tid}: NK missing (r1={r1_nk.exists()} r2={r2_nk.exists()})")
            continue
        shutil.copy2(r1_nk, run_dir / "nk_r1.json")
        shutil.copy2(r2_nk, run_dir / "nk_r2.json")

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
        built.append(str(run_dir))

    print(f"\nbuilt {len(built)} round3_NKR sandboxes")
    for d in built:
        rel = d.replace(str(PILOT) + "/", "")
        print(f"  {rel}")


if __name__ == "__main__":
    main()
