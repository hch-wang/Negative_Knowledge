#!/usr/bin/env python3
"""Quickstart: turn one failed attempt into a negative-knowledge record.

    # offline: shows the inputs and validates a bundled example record
    python examples/quickstart.py

    # live: actually curates the failure into an NK record
    export ANTHROPIC_API_KEY=sk-ant-...
    python examples/quickstart.py

Run from the repository root so that ``negative_knowledge`` is importable
(or ``pip install -e .`` first).
"""
import json
import os
import pathlib
import sys
import tempfile

# Make the package importable when run from a checkout without installing.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from negative_knowledge import NKCurator, FailureArtifacts, validate_nk

HERE = pathlib.Path(__file__).resolve().parent
ROUND1 = HERE / "sample_round1"

# 1. A failed attempt leaves behind a few artifacts. Bundle them.
artifacts = FailureArtifacts(
    candidate=str(ROUND1 / "candidate.py"),
    exec_log=str(ROUND1 / "exec.log"),
    reasoning=str(ROUND1 / "reasoning.md"),
)

print("A failed attempt left these artifacts:")
for f in artifacts.files():
    print(f"  - {pathlib.Path(f).relative_to(HERE.parent)}")

TASK_INSTRUCTION = (
    "Compute per-feature importances for the regression target and save "
    "them to pred_results/importances.csv."
)

# 2. Without an API key we can still demonstrate the schema offline.
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("\n[no ANTHROPIC_API_KEY set] skipping the live curation call.\n")
    print("With a key, NKCurator(...).produce_depth1(...) dispatches a curator")
    print("agent that reads the artifacts above and writes one NK record like:\n")
    example = json.loads((HERE / "sample_nk_record.json").read_text())
    print(json.dumps(example, indent=2))
    issues = validate_nk(example, depth=1)
    print("\nschema check:", "VALID" if not issues else issues)
    raise SystemExit(0)

# 3. Live: the curator turns the failure into a structured record.
curator = NKCurator(model="sonnet")
out_path = pathlib.Path(tempfile.mkdtemp()) / "nk_demo.json"
result = curator.produce_depth1(
    task_id="demo",
    task_inst=TASK_INSTRUCTION,
    round_artifacts=artifacts,
    output_path=out_path,
)

print("\nNegative-knowledge record the curator wrote:")
print(json.dumps(result.nk, indent=2))
print("\nschema valid:", not result.schema_issues)
print("curation tokens:", result.dispatch["total_tokens"])

# 4. The downstream research agent reads this record before its next
#    attempt: it sees the 'shap' route is ruled out and adopts
#    recommended_alternative instead of repeating the failing import.
print("\nNext step the research agent should take:")
print(" ", result.nk.get("recommended_alternative", "<missing>"))
