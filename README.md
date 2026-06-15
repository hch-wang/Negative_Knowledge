# Negative Knowledge

A failure-aware shared memory layer for AutoResearch. Instead of
discarding failed attempts as transient debugging noise, a **curator**
agent turns each failure into a bounded, typed *negative-knowledge (NK)
record* in a shared bank, and a downstream **research agent** reads the
bank — adopting or rejecting records — before proposing its next
experiment. Failures become reusable constraints that steer exploration
away from dead ends.

This is the reference implementation for the ICML 2026 AI4Research
Workshop paper *Negative Knowledge as Failure-aware Shared Memory for
AutoResearch*.

```
                failed attempt artifacts
        (candidate.py, exec.log, reasoning.md, …)
                          │
                          ▼
                   ┌─────────────┐      bounded, typed
                   │   curator   │  ──▶  NK record  ──▶  shared bank
                   └─────────────┘                          │
                                                            ▼
   next experiment  ◀──  research agent  ◀── adopt / reject records
```

## Install

```bash
pip install -e .          # from a checkout
# or just run from the repo root without installing
```

The only runtime dependency is the `anthropic` SDK (used by the
curator). Validating records needs nothing beyond the standard library.

## Quickstart

```python
from negative_knowledge import NKCurator, FailureArtifacts

curator = NKCurator(model="sonnet")           # needs ANTHROPIC_API_KEY
result = curator.produce_depth1(
    task_id="072",
    task_inst="Map Sub01 EEG signals to Sub03 ...",
    round_artifacts=FailureArtifacts(
        candidate="round1/candidate.py",
        exec_log="round1/exec.log",
        reasoning="round1/reasoning.md",
    ),
    output_path="nk_records/task_072.json",
)
print(result.nk["recommended_alternative"])   # what to try instead
```

A runnable end-to-end demo (works offline without an API key):

```bash
python examples/quickstart.py
```

## The NK record schema

Every record is a JSON object with a fixed shape; each typed field draws
from a closed vocabulary, so no field is free text in a way that defeats
machine consumption. The base (depth-1) record has six fields:

```
task_id, attempted_route, observation,
failure { layer, scope, degree, recommended_action, risk },
rationale, recommended_alternative
```

A **depth-N** record (one curator pass over N failed rounds) adds three
cross-round fields: `rounds_summary`, `ruled_out_routes`,
`synthesised_diagnosis`.

Validation is pure Python and needs no API key:

```python
from negative_knowledge import validate_nk
issues = validate_nk(record, depth=1)         # [] == valid
```

The controlled vocabularies live in `negative_knowledge/curator.py`
(`LAYERS`, `SCOPES`, `DEGREES`, `RECOMMENDED_ACTIONS`, `RISKS`).

## API

| Object | Purpose |
|---|---|
| `NKCurator(model, base_dir=None)` | curator agent; `produce_depth1(...)`, `produce_deep(...)` |
| `FailureArtifacts(candidate, exec_log, reasoning, eval_log=None)` | the file bundle one curator pass reads |
| `CurationResult` | `.nk`, `.schema_issues`, `.dispatch` (token usage) |
| `validate_nk(record, depth)` | list of schema violations (empty = valid) |
| `CuratorPrompt` | load / override the curator prompt templates |

CLI:

```bash
python -m negative_knowledge depth1 --task-id 072 \
    --task-inst-file inst.txt --round-dir runs/round1/task_072 \
    --output nk_records/task_072.json
```

## Repository layout

```
negative_knowledge/     the reusable module (curator, schema, runtime, prompts)
examples/               quickstart.py + a self-contained sample failure
reproduction/           everything behind the paper's numbers (see below)
```

## Reproducing the paper

All experiments, logs, banks, and verification scripts live under
[`reproduction/`](reproduction/) — one subdirectory per study
(`section3/`, `section4/`, `appendix/`). Every number in the paper can
be re-derived from bundled artifacts with no API key:

```bash
cd reproduction/section3 && python analyze_results.py   # 31/31 claims match
python count_tokens.py                                   # Table 1 token figures
```

See [`reproduction/README.md`](reproduction/README.md) for the full
guide, including the optional end-to-end (Anthropic API) re-runs.
