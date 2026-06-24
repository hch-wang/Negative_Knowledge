# Section 3 Reproduction: Negative-Knowledge Retry on ScienceAgentBench

This directory reproduces and evaluates the Section 3 ScienceAgentBench
performance results from the paper. It provides two workflows:

| Mode | Cost | Time | What you verify |
|---|---:|---:|---|
| **A. Verify-only** | $0 | 5 s | Recompute the paper-format pass-rate and memory table from bundled `logs/` |
| **B. End-to-end on one task** | ~$1 | 5–10 min | Run the curator → NK → solver → evaluator pipeline on `task_072` |

The main evaluation table reproduced by Mode A is:

| Method | Pass rate (%) | Memory (B) |
|---|---:|---:|
| Base | 31.6 | -- |
| Retry | 31.6 | -- |
| Negative knowledge retry (d=1) | 36.8 | 1,187 (-72.2%) |
| Self-debug (round=3) | 44.7 | 4,272 (baseline) |
| Deep negative knowledge retry (d=3) | **47.4** | 3,354 (-21.5%) |

Depth-1 negative knowledge is the most compact memory object. Depth-3
negative knowledge gives the highest pass rate while remaining smaller than
the Self-debug memory baseline.

---

## A. Verify-only (no API key)

```bash
python3 analyze_results.py
```

Expected output: all provenance checks pass. The generated report starts with
the paper-format evaluation table and then lists the count-based provenance
checks behind each value.

Generated files:

```text
results/claim_report.md
results/claim_report.json
```

### Verify the Table 1 token figures

Table 1 of the paper reports memory-object size in **`cl100k_base`
tokens** (296 / 1,109 / 795, with savings 73.3% and 28.3%). The
per-task token counts are precomputed and shipped as
`logs/memory_tokens.json` (the token-side analogue of the existing
`logs/b2_covering_bytes.json` byte file). To verify the medians match
the paper:

```bash
python3 count_tokens.py
```

Stdlib only, no install, no LLM API. The script prints per-task token
counts and the three medians, and exits 0 when all three match the
paper.

The raw self-debug inputs are also bundled under
`logs/self_debug_inputs/task_<id>/` (`candidate.py` + `exec.log` +
`eval.log`, the artifacts the self-debug condition shows to the next
attempt). To re-derive `memory_tokens.json` from these primary inputs:

```bash
pip install tiktoken
python3 count_tokens.py --regenerate
```

## B. End-to-end (your agent stack)

```bash
export NK_AGENT_COMMAND="python3 /absolute/path/to/agent_adapter.py"
git clone https://github.com/OSU-NLP-Group/ScienceAgentBench
export SAB_BENCH=/absolute/path/to/ScienceAgentBench/benchmark
export PY_VENV=/absolute/path/to/python

python3 run_pipeline.py --task 072 --use-saved-trace --skip-secondary
```

This command:

1. reuses the saved three-round Self-debug trace from `logs/`;
2. dispatches the depth-3 curator to produce a negative-knowledge record;
3. builds a fresh Primary solver sandbox using only that record;
4. runs `candidate.py` and the task evaluator;
5. writes the result under `runs/solver-deep-primary/task_072/result.json`.

A successful reproduction has `eval_score=1`. For `task_072`, the evaluator
message should report a task-specific metric of approximately `0.763`.

Drop `--use-saved-trace` to re-run the three Self-debug rounds from scratch
before producing the depth-3 negative-knowledge record.

---

## Directory layout

```text
section3_reproduce/
├── README.md                this file
├── nk_curator.py            NK production module
├── curator_prompt.md        canonical curator prompt
├── analyze_results.py       Mode A: recompute the paper-format table from logs
├── count_tokens.py          recompute Table 1 token figures (296/1,109/795)
├── run_pipeline.py          Mode B: curator + solver + evaluator pipeline
├── prompts/                 curator prompt variants
├── scripts/                 sandbox, dispatch, and execution utilities
├── tasks/                   ScienceAgentBench task specs
└── logs/                    archived run data used by Mode A
```

## How NK gets produced by the curator

```python
from nk_curator import NKCurator, FailureArtifacts

curator = NKCurator(model="default")

nk = curator.produce_depth1(
    task_id="072",
    task_inst="Map Sub01 EEG to Sub03 …",
    round_artifacts=FailureArtifacts(
        candidate="round1/candidate.py",
        exec_log="round1/exec.log",
        reasoning="round1/reasoning.md",
        eval_log="round1/eval.log",
    ),
    output_path="nk_072.json",
)

nk = curator.produce_deep(
    task_id="072",
    task_inst="…",
    rounds=[round1_arts, round2_arts, round3_arts],
    output_path="nk_072_deep.json",
)
```

The prompts in `curator_prompt.md` and `prompts/` define the operational NK
schema used by the reproduction scripts. The audit trail for a reproduced
value is: prompt → audit record → NK record → solver/evaluator logs.
