"""Centralised path resolution for section3_reproduce.

All paths resolve from this file's location, NOT from any hardcoded
absolute path. The reviewer needs to set only ONE environment variable:

  SAB_BENCH   absolute path to a clone of ScienceAgentBench's benchmark/
              directory (containing datasets/ and eval_programs/). Get
              it from https://github.com/OSU-NLP-Group/ScienceAgentBench

Optional environment variables:

  REPRO_RUNS  where to put generated sandboxes (default: REPRO_ROOT/runs)
  PY_VENV     path to the Python binary to use for executing candidates
              (default: REPRO_ROOT/.venv_full/bin/python). Set this to
              your own venv path if you installed dependencies elsewhere.
"""
import os
import pathlib

# REPRO_ROOT = section3_reproduce/  (the parent of this scripts/ folder)
REPRO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROMPTS = REPRO_ROOT / "prompts"
TASKS = REPRO_ROOT / "tasks"
LOGS = REPRO_ROOT / "logs"

# Per-run outputs go here. Reviewer can override.
RUNS = pathlib.Path(os.environ.get("REPRO_RUNS", str(REPRO_ROOT / "runs")))

# Upstream benchmark (datasets + eval programs). NOT bundled here; the
# reviewer downloads it separately. We default to ../../benchmark/
# (section3_reproduce → Negative_Knowledge → paper → benchmark), which
# is where it lives in our own working tree; reviewers set SAB_BENCH
# to point at their own clone.
_DEFAULT_BENCH = REPRO_ROOT.parent.parent / "benchmark"
BENCH = pathlib.Path(os.environ.get("SAB_BENCH", str(_DEFAULT_BENCH)))

# Python binary used to execute candidate.py and the evaluator.
_DEFAULT_PY = REPRO_ROOT / ".venv_full" / "bin" / "python"
PY = pathlib.Path(os.environ.get("PY_VENV", str(_DEFAULT_PY)))


def ensure_bench_exists():
    """Raise a clear error if BENCH is unset or missing."""
    if not BENCH.exists():
        raise SystemExit(
            f"BENCH directory missing at {BENCH}.\n"
            f"Set the SAB_BENCH env var to your local clone of\n"
            f"https://github.com/OSU-NLP-Group/ScienceAgentBench, e.g.:\n"
            f"  export SAB_BENCH=/path/to/ScienceAgentBench/benchmark"
        )
    for sub in ("datasets", "eval_programs"):
        if not (BENCH / sub).exists():
            raise SystemExit(
                f"BENCH is missing {sub}/ subdir at {BENCH / sub}"
            )


# Canonical task sets (encoded once here, used everywhere).
# 38 pilot tasks: derived from tasks/ JSON files at runtime.
# 24 NK-test: Primary-4.6 round-1 failures (hand-curated by the original
#             v3 builder; see section3_journal_2026-05-13.md §1).
# 19 hard: 24 minus B2 round-1/2/3 PASS (003, 005, 015, 071, 097).
NK_TEST_24 = [
    "002", "003", "005", "012", "015", "018", "021", "022", "026", "029",
    "034", "035", "037", "044", "058", "060", "067", "071", "072", "078",
    "085", "087", "097", "101",
]
HARD_19 = [t for t in NK_TEST_24
           if t not in {"003", "005", "015", "071", "097"}]


def all_38_tasks():
    """Read 38 task ids from tasks/task_*.json."""
    out = []
    for p in sorted(TASKS.glob("task_*.json")):
        import json
        spec = json.load(open(p))
        out.append(f"{spec['instance_id']:03d}")
    return out
