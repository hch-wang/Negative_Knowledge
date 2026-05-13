# Section 3 reproduction kit

Reviewer-facing package for §3 of the paper. The headline finding:

> On the 38-task deterministic-eval subset of ScienceAgentBench, a
> depth-3 negative-knowledge memory protocol lifts Claude Sonnet 4.6
> from **12/38 PASS** (no memory) to **18/38 PASS** (+6 tasks; 32 % → 47 %),
> entirely attributable to the memory protocol. A depth-3 NK record is
> **72 % more compact** than the standard Self-Debug covering-memory
> baseline (depth-1 NK is the simpler variant).

Two reproduction modes:

| Mode | Cost | Time | What you verify |
|---|---|---|---|
| **A. Verify-only** | $0 | 5 s | Every paper claim traces to bundled `logs/` |
| **B. End-to-end on one task** | ~$1 | 5–10 min | The full curator → NK → solver pipeline works on `task_072` |

---

## A. Verify-only (no API key)

```bash
python analyze_results.py
```

Expected output: `31/31 claims match`. Report at
`results/claim_report.md` lists every paper claim, the value the script
computed, and the file paths supporting it.

## B. End-to-end (Anthropic API)

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
git clone https://github.com/OSU-NLP-Group/ScienceAgentBench
export SAB_BENCH=$(pwd)/ScienceAgentBench/benchmark

python run_pipeline.py --task 072 --use-saved-trace
```

This:
1. reuses our saved 3-round Self-Debug trace from `logs/` (saves API$);
2. dispatches the canonical curator (3 rounds → 1 depth-3 NK);
3. builds a `solver-deep` sandbox and dispatches a fresh Sonnet solver;
4. runs `candidate.py` + the task's evaluator;
5. prints the result. A `score=1` reproduces the §3 task_072 breakthrough.

Drop `--use-saved-trace` to re-run all 3 Self-Debug rounds from scratch
(~$3 instead of ~$1).

---

## Directory layout

```
section3_reproduce/
├── README.md                this file
├── nk_curator.py            ★ NK production module (NKCurator class + schema)
├── curator_prompt.md        ★ canonical curator prompt (multi-round distillation)
├── analyze_results.py       Mode A: derive paper claims from logs/
├── run_pipeline.py          Mode B: end-to-end curator + solver + eval
├── prompts/                 modifications of the canonical prompt
│   ├── README.md
│   ├── curator_prompt__single_round_simpler_schema.md
│   └── curator_prompt__chain_with_prior_nk.md
├── scripts/                 low-level building blocks
│   ├── _paths.py            path resolution from REPRO_ROOT + env vars
│   ├── build_sandboxes.py   create sandboxes for any cell type
│   ├── dispatch_subagent.py Anthropic-API sub-agent (Read/Write tools)
│   └── execute_candidates.py run candidate.py + task evaluator
├── tasks/                   38 ScienceAgentBench task specs
└── logs/                    our original run archive (~63 MB)
    ├── nk_records/          65 NK files
    ├── curator_audit/       65 paired audit records
    ├── dispatches/solver/   220 solver dispatch records
    ├── baseline_results/    38 baseline round-1 results
    └── b2_covering_bytes.json
```

## How NK gets produced (the curator)

```python
from nk_curator import NKCurator, FailureArtifacts

curator = NKCurator(model="sonnet")

# Depth-1: read one failed round, write a base 6-field NK
nk = curator.produce_depth1(
    task_id="072",
    task_inst="Map Sub01 EEG to Sub03 …",
    round_artifacts=FailureArtifacts(
        candidate="round1/candidate.py",
        exec_log="round1/exec.log",
        reasoning="round1/reasoning.md",
        eval_log="round1/eval.log",  # or None if exec crashed
    ),
    output_path="nk_072.json",
)

# Depth-N: read N >= 2 rounds, write a depth-N NK with rounds_summary,
# ruled_out_routes, synthesised_diagnosis. This is the canonical form.
nk = curator.produce_deep(
    task_id="072",
    task_inst="…",
    rounds=[round1_arts, round2_arts, round3_arts],
    output_path="nk_072_deep.json",
)
```

The prompts in `curator_prompt.md` and `prompts/` are first-class
artifacts: they are the operational definition of the NK schema. The
audit trail for any paper claim is prompt → audit record → NK record.

## Caveats

- **LLM nondeterminism**: re-running Mode B does not produce
  byte-identical NK records, but reproduces the direction of the finding
  (depth-3 NK > depth-1 NK on hard tasks).
- **No standalone dispatcher** in the original run: the original §3
  experiment was issued through Claude Code's Agent tool. Mode B's
  `scripts/dispatch_subagent.py` is a clean-room reimplementation
  against the public Anthropic API; the curator/solver behavior matches
  but is not bit-identical to the original session.
- **Library version drift**: `candidate.py` files depend on the 28
  pre-installed libraries in our `.venv_full`. Use
  `paper/release/environment/requirements.txt` for the pinned set.
- **Cross-model results** (Haiku 4.5 0/19 on hard subset) depend on
  the specific Haiku snapshot.

## Citation

```
@inproceedings{NegativeKnowledge2026,
  title  = {Negative Knowledge as Failure-aware shared memory for AutoResearch},
  author = {...},
  booktitle = {ICML 2026 AI4Research Workshop},
  year   = {2026},
}
```

ScienceAgentBench: Chen et al., 2024
(https://github.com/OSU-NLP-Group/ScienceAgentBench).
