# Section 3 — Reviewer reproduction package

This directory is a **self-contained reproduction kit** for §3 of the
paper. The headline finding it verifies:

> On the 38-task deterministic-eval subset of ScienceAgentBench,
> a depth-3 negative-knowledge memory protocol lifts Claude Sonnet 4.6
> from **12/38 PASS** (no memory) to **18/38 PASS** (+6 tasks; 32 % → 47 %),
> entirely attributable to the memory protocol. A single depth-3 NK record
> is **72 % more compact** than the standard Self-Debug covering-memory
> baseline.

Three reproduction modes are supported, scaled by reviewer effort and
API budget:

| Mode | What you get | API cost | Wall-clock | Verifies |
|---|---|---|---|---|
| **A. Verify-only** | Re-derive every numerical claim in §3 from the bundled `logs/` archive | $0 | 5 s | All 30 claims trace to specific artifacts |
| **B. Single-task end-to-end** | Re-run the depth-3 NK pipeline on one task (e.g. task_072, the depth-3 breakthrough) | ~$1 | 5–10 min | The whole curator → NK → solver → eval pipeline works |
| **C. Full re-run** | Re-run all 285 sub-agent dispatches behind §3 | ~$60 | 2–4 hours | The headline 12 → 18 lift on a fresh execution |

Mode A is the default for review and requires no setup beyond Python.
Mode B is the recommended sanity check if you have an API key. Mode C
is the full reproduction.

---

## Quick start (Mode A — verify on bundled logs, 5 s)

```bash
python scripts/reproduce_claims.py
```

You should see:

```
loaded 220 solver dispatches; 12 baseline PASS tasks
30/30 claims match
```

The report at `results/paper_claims_reproduction.md` lists every paper
claim, the value the script computed, and the file paths that support
it. Exit code is `0` iff every claim matches. This is the fastest way
to confirm that the §3 numbers track the bundled archive.

---

## Requirements

### Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install anthropic        # only needed for Modes B / C
```

For executing candidate.py inside sandboxes (Modes B / C), you also
need the 28-library `.venv_full` from the paper's
`paper/release/environment/setup.sh`, or any Python 3.13 environment
that satisfies the libraries listed in
the package list in `curator_prompt.md`. Set `PY_VENV` to your binary path:

```bash
export PY_VENV=/abs/path/to/your/.venv_full/bin/python
```

### ScienceAgentBench data (Modes B / C only)

```bash
git clone https://github.com/OSU-NLP-Group/ScienceAgentBench
export SAB_BENCH=/abs/path/to/ScienceAgentBench/benchmark
```

The dataset CSV / NetCDF / PDB / etc. files are large (~3.8 GB)
and are licensed CC-BY 4.0; we do not redistribute them.

### Anthropic API key (Modes B / C only)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Mode B — Single-task end-to-end (~$1, 5–10 min)

This reproduces the depth-3 deepNKR breakthrough on **task_072** (EEG
signal mapping, the one task where depth-3 NK PASSes while every other
condition — including B2 covering memory — fails).

### Step 1: Build the three sandboxes needed

```bash
python scripts/build_sandboxes.py round1 --tasks 072
# round1 is your fresh attempt; the prior B2 round-2/3 artifacts ship
# in logs/ if you want to reuse them rather than re-run 3 rounds of
# Self-Debug. For the cleanest single-task end-to-end, supply the
# prior-round artifacts manually:
python scripts/build_sandboxes.py curator-deep --tasks 072 \
    --round1-dir $(pwd)/runs/round1/task_072 \
    --round2-dir $(pwd)/logs/dispatches/solver/round2_B2_task_072 \
    --round3-dir $(pwd)/logs/dispatches/solver/round3_B2_task_072
```

(The simpler path: skip the round1/round2/round3 Self-Debug stage and
use the round-1/2/3 artifacts already in `logs/` — the curator only
needs to *read* those.)

### Step 2: Dispatch the deep curator (1 call, ~$0.20)

```bash
python scripts/dispatch_subagent.py runs/curator-deep/task_072 \
    --model sonnet \
    --read-allowlist \
        logs/dispatches/solver/task_072__round1.json \
        logs/dispatches/solver/task_072__round2_B2.json \
        logs/dispatches/solver/task_072__round3_B2.json \
    --output-files runs/nk_records/task_072_deep.json
```

This invokes Claude Sonnet 4.5 as the depth-3 curator. The dispatcher
captures full I/O in `runs/curator-deep/task_072/dispatch_record.json`.

### Step 3: Build the depth-3 solver sandbox

```bash
python scripts/build_sandboxes.py solver-deep --tasks 072 \
    --nk-file runs/nk_records/task_072_deep.json
```

### Step 4: Dispatch the solver (1 call, ~$0.20)

```bash
python scripts/dispatch_subagent.py runs/solver-deep/task_072 \
    --model sonnet \
    --read-allowlist runs/solver-deep/task_072/deep_nk.json \
    --output-files \
        runs/solver-deep/task_072/candidate.py \
        runs/solver-deep/task_072/reasoning.md
```

### Step 5: Run the candidate and grade it

```bash
python scripts/execute_candidates.py --cell solver-deep --tasks 072
```

Output:
```
=== task_072 / solver-deep ===
  exit=0 output=True eval=ran score=1
1/1 PASS for solver-deep
```

A `score=1` confirms the depth-3 NK pipeline reproduces the §3 task-072
breakthrough.

---

## Mode C — Full re-run (~$60, 2–4 hours)

Reproduces all 285 sub-agent dispatches behind §3. Sub-modes by scope:

### C.1 Baseline round-1 only (38 tasks)

```bash
python scripts/build_sandboxes.py round1 --tasks all
parallel -j 4 'python scripts/dispatch_subagent.py runs/round1/task_{} \
    --model sonnet --output-files \
        runs/round1/task_{}/candidate.py runs/round1/task_{}/reasoning.md' \
    ::: $(python -c "from scripts._paths import all_38_tasks; print(' '.join(all_38_tasks()))")
python scripts/execute_candidates.py --cell round1 --tasks all
```

### C.2 NK-Replay (depth-1 curator + solver, 24 tasks)

```bash
# (after the 24 round-1 sandboxes are built and run)
python scripts/build_sandboxes.py curator-r1 --tasks all
# parallel-dispatch the 24 curators
# parallel-dispatch the 24 solver-nkr
python scripts/execute_candidates.py --cell solver-nkr --tasks all
```

### C.3 deepNKR (depth-3 curator + Sonnet/Haiku solvers, 19 tasks)

```bash
python scripts/build_sandboxes.py curator-deep --tasks all
# parallel-dispatch the 19 deep curators
python scripts/build_sandboxes.py solver-deep --tasks all
# parallel-dispatch the 19 Sonnet + 19 Haiku solvers
python scripts/execute_candidates.py --cell solver-deep --tasks all
```

### C.4 Verify the new run reproduces the paper

```bash
# Consolidate fresh runs into the same archive schema as logs/
# (left as an exercise — the original archive convention is documented
# in scripts/reproduce_claims.py)
python scripts/reproduce_claims.py --logs runs/  # or wherever fresh logs landed
```

---

## What's in this directory

```
section3_reproduce/
├── README.md                          this file
├── prompts/
│   ├── curator_prompt__single_round_simpler_schema.md
│   │                                  variant: 1 round in; base 6-field schema
│   └── curator_prompt__chain_with_prior_nk.md
│                                      variant: 1 round + prior NK; adds
│                                      relationship_to_round1 field
├── curator_prompt.md                  ★ canonical (top level): N rounds in,
│                                        depth-N schema with cross-round fields
├── scripts/
│   ├── _paths.py                      path resolution (uses REPRO_ROOT, no hardcoded paths)
│   ├── build_sandboxes.py             create sandbox dirs for any cell type
│   ├── dispatch_subagent.py           Anthropic-API sub-agent dispatcher (replaces Claude Code Agent tool)
│   ├── execute_candidates.py          run candidate.py + grade via task's evaluator
│   └── reproduce_claims.py            compute every paper claim from logs/ (no API)
├── tasks/                             38 ScienceAgentBench task specs (JSON)
├── logs/                              our original run archive (63 MB)
│   ├── nk_records/                    65 NK files (24 r1 + 22 r2 + 19 deep)
│   ├── curator_audit/                 65 paired audit records (full I/O capture)
│   ├── dispatches/solver/             220 solver dispatch records with full prompt + outputs
│   ├── baseline_results/              38 baseline round-1 result.json files
│   ├── dispatch_log{,_r2,_deep}.jsonl curator dispatch metadata
│   ├── solver_tokens.csv              220 solver dispatch token rows
│   └── b2_covering_bytes.json         per-task B2 covering memory byte size
└── runs/                              fresh runs land here (created by Mode B/C scripts)
```

---

## Reproduction guarantees (and limits)

**What this kit guarantees**:

1. Every numerical claim in §3 is **traceable** to a specific file in
   `logs/`. `scripts/reproduce_claims.py` runs the trace.
2. The **schemas** of NK records, audit records, and dispatch records
   are stable and documented (see `prompts/*.md` for the NK schema and
   `scripts/dispatch_subagent.py` for the dispatch-record schema).
3. The dispatcher is **stateless**: any reviewer with an API key can
   reproduce a single dispatch in isolation by re-running
   `scripts/dispatch_subagent.py` on a freshly-built sandbox.

**Known caveats**:

1. **LLM nondeterminism.** Re-dispatching the same prompt to Claude
   Sonnet 4.5 will not always produce byte-identical outputs.
   Re-running Mode C will reproduce the *direction* of the §3 finding
   (a positive lift from memory, depth-3 > depth-1 on hard tasks) but
   not necessarily the exact task IDs or PASS counts.
2. **Library version drift.** The 28-library `.venv_full` is pinned in
   `paper/release/environment/requirements.txt`. New library releases
   may break candidate scripts that depend on, e.g., NumPy 2.0 API
   changes (NK_011 in our records). Re-running with a freshly-pinned
   venv reproduces the experiment we ran.
3. **Cross-model results.** The Haiku 4.5 cross-model PASS rate (0/19)
   is sensitive to which Haiku snapshot is dispatched. Use
   `claude-haiku-4-5` for the experiment we ran.

---

## Citation

If you use any artifact in this directory, please cite the paper:

```
@inproceedings{NegativeKnowledge2026,
  title  = {Negative Knowledge as Failure-aware shared memory for AutoResearch},
  author = {...},
  booktitle = {ICML 2026 AI4Research Workshop},
  year   = {2026},
}
```

ScienceAgentBench is from Chen et al., 2024
(https://github.com/OSU-NLP-Group/ScienceAgentBench).
