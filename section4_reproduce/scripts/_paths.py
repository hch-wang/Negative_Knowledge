"""Centralised path resolution for section4_reproduce.

All paths resolve from this file's location, NOT from any hardcoded
absolute path. Reviewers can override:

  REPRO_RUNS  where to put generated sandboxes (default: REPRO_ROOT/runs)
  PY_VENV     path to Python binary for executing candidate.py
              (default: ../../experiments/pde_pilot_2026-05-11/.venv/bin/python
              relative to REPRO_ROOT)
"""
import os
import pathlib

# REPRO_ROOT = section4_reproduce/  (parent of this scripts/ folder)
REPRO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROMPTS = REPRO_ROOT / "prompts"
CURATOR_PROMPTS = REPRO_ROOT / "curator_prompts"
TASKS = REPRO_ROOT / "tasks"
LOGS = REPRO_ROOT / "logs"
RESULTS = REPRO_ROOT / "results"

# Archive sub-directories
STAGE1_RUNS = LOGS / "stage1"          # BKdV-S1..S7 program runs
STAGE2_RUNS = LOGS / "stage2"          # T_{A,B,C} × {NoKB,PosOnly,NegOnly,PosNeg} cells
NK_RECORDS = LOGS / "nk_records"       # 28 curator output JSONs
BANKS = LOGS / "banks"                  # bank files
VERIFIED_RESULTS = LOGS / "verified_results"

# Per-run outputs (for new sandboxes built by build_*.py scripts)
RUNS = pathlib.Path(os.environ.get("REPRO_RUNS", str(REPRO_ROOT / "runs")))

# Python binary used to execute candidate.py
_DEFAULT_PY = (REPRO_ROOT.parent.parent / "experiments"
               / "pde_pilot_2026-05-11" / ".venv" / "bin" / "python")
PY = pathlib.Path(os.environ.get("PY_VENV", str(_DEFAULT_PY)))


# Canonical task / condition / program lists
BKDV_PROGRAMS = ["BKdV-S1", "BKdV-S2", "BKdV-S3", "BKdV-S4", "BKdV-S5", "BKdV-S6", "BKdV-S7"]
STAGE2_TASKS = ["T_A", "T_B", "T_C"]
STAGE2_CONDS = ["NoKB", "PosOnly", "NegOnly", "PosNeg"]
