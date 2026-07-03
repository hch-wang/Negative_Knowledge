#!/usr/bin/env python3
"""Offline consumer-side demo: the paper's adopt/reject loop in miniature.

A downstream research agent must read the shared bank and explicitly
adopt or reject the relevant records BEFORE proposing its next
experiment. This example mocks the model call so it runs offline; the
full Research-Graph protocol (with applicability checks and positive
banks) lives under ``reproduction/``.
"""
import json
import pathlib
import sys
import tempfile


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from negative_knowledge import append, load


HERE = pathlib.Path(__file__).resolve().parent
RECORD = json.loads((HERE / "sample_nk_record.json").read_text(encoding="utf-8"))


def researcher(prompt: str) -> dict:
    """Mock backend — replace with your own model call.

    The contract: the agent sees the rendered bank and must return its
    adopt/reject decisions alongside the route it proposes next.
    """
    assert "dead ends" in prompt
    return {
        "adopt": [RECORD["task_id"]],
        "reject": [],
        "next_route": "sklearn.inspection.permutation_importance on the fitted model",
        "rationale": (
            "Adopting the bank record: shap is unavailable in this "
            "environment, so switch to an importance method that needs "
            "no extra installs instead of retrying the import."
        ),
    }


with tempfile.TemporaryDirectory() as directory:
    bank_path = pathlib.Path(directory) / "bank.jsonl"
    append(bank_path, RECORD)

    bank = load(bank_path)
    bullets = "\n".join(
        f"- [{r['task_id']}] tried: {r['attempted_route']}\n"
        f"  observed: {r['observation']}\n"
        f"  instead: {r['recommended_alternative']}"
        for r in bank
    )
    prompt = (
        "Known dead ends from the shared bank:\n" + bullets +
        "\n\nAdopt or reject each record, then propose the next route."
    )

    decision = researcher(prompt)
    print(f"bank records read: {len(bank)}")
    print(json.dumps(decision, indent=2))
