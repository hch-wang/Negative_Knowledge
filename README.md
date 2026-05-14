# Negative Knowledge

Code and reproducibility artifacts for the ICML 2026 AI4Research Workshop
paper *Negative Knowledge as Failure-aware shared memory for AutoResearch*.

A *negative-knowledge record* (NK) is a structured, machine-readable
summary of one or more failed attempts on a task.

---

## The bounded failure schema

The NK record is a JSON object with a fixed shape. Every field draws
from a controlled vocabulary; no field is free text in a way that
would defeat downstream machine consumption. The base form has 6
required fields:

```
task_id, attempted_route, observation,
failure { layer, scope, degree, recommended_action, risk },
rationale, recommended_alternative
```

A **depth-N** extension adds three cross-round fields
(`rounds_summary`, `ruled_out_routes`, `synthesised_diagnosis`)
when the curator reads more than one failed round.

The schema is implemented in
[`section3_reproduce/nk_curator.py`](section3_reproduce/nk_curator.py)
(constants `SCHEMA_BASE_FIELDS`, `SCHEMA_DEEP_EXTRA`, `LAYERS`, …),
with `validate_nk(nk, depth)` returning a list of violations.

---

## Running the §3 experiment

### Verify mode (no API key, ~5 seconds)

```bash
cd section3_reproduce
python analyze_results.py
```

Re-derives every §3 paper claim from the bundled archive in `logs/`.
Expected output: `31/31 claims match`. Full report at
`section3_reproduce/results/claim_report.md`.

### End-to-end mode (Anthropic API, ~$1, ~10 min)

```bash
cd section3_reproduce
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
git clone https://github.com/OSU-NLP-Group/ScienceAgentBench
export SAB_BENCH=$(pwd)/ScienceAgentBench/benchmark

python run_pipeline.py --task 072 --use-saved-trace
```

Re-runs the depth-3 deepNKR pipeline on task_072 (the §3 breakthrough
task): dispatches the canonical curator, builds a fresh Sonnet solver
sandbox, runs `candidate.py` + the task evaluator, prints the result.
A `score=1` reproduces the §3 task_072 PASS.

Full guide:
[`section3_reproduce/README.md`](section3_reproduce/README.md).

---

## Citation

```bibtex
@inproceedings{NegativeKnowledge2026,
  title  = {Negative Knowledge as Failure-aware shared memory for AutoResearch},
  author = {...},
  booktitle = {ICML 2026 AI4Research Workshop},
  year   = {2026},
}
```

ScienceAgentBench: Chen et al., 2024
(https://github.com/OSU-NLP-Group/ScienceAgentBench).
