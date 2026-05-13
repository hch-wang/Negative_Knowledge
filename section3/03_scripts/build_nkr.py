#!/usr/bin/env python3
"""Build round-2 NK-Replay sandboxes for the 24 v3 tasks.

Each sandbox is dropped under
  pilot_2026-05-10/runs/task_<id>/sonnet_4.6/v3/round2_NKR/
so that the existing run_v3.py runner picks it up as a regular v3 cell.

The agent in each sandbox sees:
  - prompt.md            (task spec; NO raw round-1 code/log/eval)
  - nk.json              (the curator-produced NK file, copied in)
  - benchmark/datasets/<ds_name>   (symlink to real data)
  - benchmark/eval_programs/gold_results  (symlink, for the evaluator only)

The agent must Write:
  - candidate.py
  - reasoning.md
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

TASKS = ['002', '003', '005', '012', '015', '018', '021', '022', '026', '029',
         '034', '035', '037', '044', '058', '060', '067', '071', '072', '078',
         '085', '087', '097', '101']


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


PROMPT_TMPL = """You are solving a scientific computing task from ScienceAgentBench. Produce a Python script + reasoning note via Write.

You will make EXACTLY TWO Write calls:
1) {run_dir}/candidate.py
2) {run_dir}/reasoning.md (under 500 words, with sections Approach / Library choices / Risks / Use of memory)

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

# Memory: bounded failure record from a prior attempt

You (or a peer agent) attempted this exact task once and failed. A structured
bounded-failure record summarising that attempt is mounted at:

  - {run_dir}/nk.json

You may Read it. It contains:
  - `attempted_route`         — exactly what was tried (library + parameters)
  - `observation`             — what went wrong, with a specific signature
  - `failure.{{layer, scope, degree, recommended_action, risk}}` — taxonomy
  - `rationale`               — 1–2 sentence mechanism explanation
  - `recommended_alternative` — ONE specific concrete fix to try instead

You do NOT have access to the prior attempt's source code, raw stderr,
or evaluator output — ONLY this record. Read it; use it.

# Constraints
1. Write exactly twice (candidate.py + reasoning.md).
2. You may Read prompt.md and nk.json. Do NOT read any other files.
3. Script self-contained, runnable as `python candidate.py`.
4. After both Writes, return ONE short sentence.
"""


def main():
    built = []
    for tid in TASKS:
        spec = json.load(open(PILOT / f"tasks/task_{tid}.json"))
        ds = ddir(spec["dataset_folder_tree"])

        run_dir = PILOT / f"runs/task_{tid}/sonnet_4.6/v3/round2_NKR"
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

        # copy the curator-produced NK file into the sandbox
        nk_src = SECTION3 / f"04_outputs/nk_records/task_{tid}.json"
        if not nk_src.exists():
            print(f"  SKIP task_{tid}: NK file missing at {nk_src}")
            continue
        shutil.copy2(nk_src, run_dir / "nk.json")

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

    print(f"\nbuilt {len(built)} round2_NKR sandboxes")
    for d in built:
        rel = d.replace(str(PILOT) + "/", "")
        print(f"  {rel}")


if __name__ == "__main__":
    main()
