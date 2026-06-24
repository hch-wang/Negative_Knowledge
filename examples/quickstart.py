#!/usr/bin/env python3
"""Offline example; replace ``backend`` with your own agent call."""
import json
import pathlib
import sys
import tempfile


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from negative_knowledge import append, curate, load


HERE = pathlib.Path(__file__).resolve().parent
SAMPLE = json.loads((HERE / "sample_nk_record.json").read_text())


def backend(prompt: str) -> dict:
    assert "ModuleNotFoundError" in prompt
    return SAMPLE


record = curate(
    backend,
    task_id="demo",
    task="Compute per-feature importances.",
    evidence={
        "code": (HERE / "sample_round1/candidate.py").read_text(),
        "error": (HERE / "sample_round1/exec.log").read_text(),
        "reasoning": (HERE / "sample_round1/reasoning.md").read_text(),
    },
)

with tempfile.TemporaryDirectory() as directory:
    path = pathlib.Path(directory) / "memory.jsonl"
    append(path, record)
    print(json.dumps(load(path), indent=2))
