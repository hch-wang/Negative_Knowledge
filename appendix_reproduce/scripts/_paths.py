"""Path resolution for the appendix reproduce package.

REPRO_ROOT is the appendix_reproduce/ directory itself.
PY_VENV is an external Python interpreter used by sub-agents to execute
candidate.py. Default falls back to `python3` on PATH.
"""
import os
import pathlib

REPRO_ROOT = pathlib.Path(__file__).resolve().parent.parent

BANK_DIR = REPRO_ROOT / "bank"
TASKS_DIR = REPRO_ROOT / "tasks"
PROMPTS_DIR = REPRO_ROOT / "prompts"
EVAL_DIR = REPRO_ROOT / "eval"
LOGS_DIR = REPRO_ROOT / "logs"
RESULTS_DIR = REPRO_ROOT / "results"

BANK_NLS = BANK_DIR / "nls_knowledge.jsonl"
BANK_BKDV_POS = BANK_DIR / "bkdv_positive.jsonl"
BANK_BKDV_NEG = BANK_DIR / "bkdv_negative.jsonl"

STAGE3_TASKS = TASKS_DIR / "stage3_tasks.json"
STAGE1_BNLS_TASKS = TASKS_DIR / "stage1_bnls_tests.json"

STAGE3_TEMPLATE = PROMPTS_DIR / "stage3_template.md"
STAGE1_BNLS_TEMPLATE = PROMPTS_DIR / "stage1_bnls_template.md"
CURATOR_PROMPT = PROMPTS_DIR / "curator_prompt.md"

PHENOM_CHECKS = EVAL_DIR / "phenomenon_checks_bnls.py"

STAGE3_LOGS = LOGS_DIR / "stage3"
STAGE1_BNLS_LOGS = LOGS_DIR / "stage1_bnls"
VERIFIED_RESULTS = LOGS_DIR / "verified_results.json"

# Conditions/tasks
CONDITIONS = ["NoKB", "BKdV", "NLS", "NLSBKdV"]
TASKS = ["T_A", "T_B", "T_C", "T_D"]

# External Python interpreter for candidate.py execution.
# Reviewers should set PY_VENV to a venv with numpy / scipy installed.
PY_VENV = os.environ.get("PY_VENV", "python3")


def cell_dir(task: str, cond: str) -> pathlib.Path:
    """Return the logs/stage3/<task>/<cond>/ directory."""
    return STAGE3_LOGS / task / cond


def stress_test_dir(test_id: str) -> pathlib.Path:
    """Return the logs/stage1_bnls/<test_id>/ directory."""
    return STAGE1_BNLS_LOGS / test_id
