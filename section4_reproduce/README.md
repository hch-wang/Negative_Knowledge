# Section 4 Reproduction Bundle (v3 / v3.A')

> Frozen snapshot of Stage 1 + Stage 2 Class A artifacts for Section 4 of the
> Negative Knowledge paper. Includes all code, prompts, banks, sub-agent
> outputs, eval scripts, and analysis logs.
>
> Snapshot date: 2026-05-13
> Source: `paper/Negative_Knowledge/section4/`
> Total size: ~8.7 MB

---

## What's in this bundle

```
section4_reproduce/
├── README.md                         ← this file
├── PLAN_v3.md                        ← experimental design doc (decisions § 8)
├── stage1_legacy_v2era/              ← 30-entry v2-era bank (predecessor of v3.A)
│   └── bank/{positive,negative,knowledge_bank}.jsonl
├── stage1_v3/                        ← Stage 1: BKdV stress-test research programs
│   ├── prompts/program_template.md         ← master agent prompt template
│   ├── curator_prompts/                    ← curator agent prompts (per-round + deep)
│   │   ├── per_round_template.md
│   │   ├── deep_template.md
│   │   └── generated/                      ← 28 instantiated curator prompts
│   ├── scripts/                            ← builders + bank aggregator
│   │   ├── build_programs.py               ← generates 5 BKdV-S{1..5} program prompts
│   │   ├── build_curator_prompts.py        ← generates 20 curator prompts for S1-S5
│   │   ├── build_curator_prompts_s6s7.py   ← generates 8 curator prompts for S6, S7
│   │   └── aggregate_bank.py               ← merges existing 30 + new 28 → bank_v3.A
│   ├── runs/                               ← 7 stress-test programs
│   │   └── BKdV-S{1..7}/
│   │       ├── prompt.md                   ← full agent prompt as run
│   │       ├── hypothesis.md               ← agent's final synthesis
│   │       ├── research_state.jsonl        ← Q / E / F / D node trace
│   │       ├── session_log.md
│   │       └── round{1,2,3}/               ← PER-ROUND artifacts (full)
│   │           ├── candidate.py            ← exact code run that round
│   │           ├── exec.log                ← stdout / stderr / exit code
│   │           ├── reasoning.md            ← agent's reasoning that round
│   │           └── *.npz                   ← saved snapshots / diagnostics
│   ├── nk_records/                         ← 28 JSON NK records (output of curators)
│   │   ├── BKdV-S{1..7}_r{1,2,3}.json      ← single-round (depth-1) records
│   │   └── BKdV-S{1..7}_deep.json          ← multi-round synthesis (depth-3) records
│   └── bank/
│       ├── bank_v3A_positive.jsonl         ← 15 positive entries
│       ├── bank_v3A_negative.jsonl         ← 43 negative entries
│       ├── bank_v3A_all.jsonl              ← 58 total
│       └── bank_v3A_index.json
└── stage2_v3/class_A/                  ← Stage 2 Class A (warm-up sub-tasks)
    ├── CLASS_A_LOG.md                      ← FULL EXPERIMENT LOG (7 sections)
    ├── tasks/definitions.json              ← T_A / T_B / T_C task specs
    ├── prompts/research_graph_template.md  ← v2 template w/ progressive-complexity
    ├── eval/
    │   ├── phenomenon_checks.py            ← v1 eval (legacy)
    │   └── phenomenon_checks_v2.py         ← v2 physics-aware eval
    ├── scripts/
    │   ├── build.py                        ← sandbox builder (includes T_B IC trap)
    │   ├── run_eval.py                     ← runs v1 eval on a runs dir
    │   └── run_eval_v2.py                  ← runs v2 eval across both runs dirs
    ├── runs/                               ← v3.A' EXPANDED (58-entry bank, T_B trap)
    │   └── T_{A,B,C}/{NoKB,PosOnly,NegOnly,PosNeg}/
    │       ├── prompt.md                   ← agent's prompt (input)
    │       ├── memory.md                   ← bank entries embedded (input)
    │       ├── meta.json                   ← task spec (input)
    │       ├── candidate.py                ← FINAL solver only (per-round NOT saved)
    │       ├── reasoning.md                ← agent's final reasoning
    │       ├── research_state.jsonl        ← Q/E/F/D nodes with per-round method
    │       ├── session_log.md
    │       ├── pred_results/T_X.npy        ← numerical output
    │       └── verified_eval.json          ← parent-side eval result
    ├── runs_initial_5programs_bank/    ← v3.A INITIAL (50-entry bank, no S6/S7)
    │   └── T_{A,B,C}/{NoKB,PosOnly,NegOnly,PosNeg}/...
    ├── verified_results.json               ← v1 eval on v3.A'
    ├── verified_results_v2_v3A_initial.json
    └── verified_results_v2_v3Aprime.json
└── historical_reports/                 ← prior Section 4 attempts (for paper diff)
    ├── STAGE2_REPORT_v1.md             ← Class A v1 (no discipline)
    └── STAGE2_REPORT_v2.md             ← Class A v2 (with discipline, before S6/S7)
```

---

## How to re-run (clean reproduction)

### Stage 1 (bank generation)

```bash
PY=/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python

# 1. Generate 7 BKdV-S program prompts
$PY stage1_v3/scripts/build_programs.py

# 2. Dispatch 7 sub-agents (3 rounds each) → see PLAN_v3.md §2
#    Each agent reads runs/BKdV-S<n>/prompt.md and writes its outputs to that dir

# 3. Generate 28 curator prompts (4 per program: per-round × 3 + deep × 1)
$PY stage1_v3/scripts/build_curator_prompts.py
$PY stage1_v3/scripts/build_curator_prompts_s6s7.py

# 4. Dispatch 28 curator sub-agents (each reads one curator prompt
#    and writes a JSON NK record to nk_records/)

# 5. Aggregate 30 v2-era entries + 28 new entries → bank_v3.A
$PY stage1_v3/scripts/aggregate_bank.py
# Outputs bank/bank_v3A_{positive,negative,all}.jsonl + index
```

### Stage 2 Class A (12 cells)

```bash
# 1. Build 12 sandboxes with bank_v3.A embedded
$PY stage2_v3/class_A/scripts/build.py
# Writes runs/T_{A,B,C}/{NoKB,PosOnly,NegOnly,PosNeg}/{prompt.md, memory.md, meta.json}
# T_B gets the IC-adaptation trap addendum automatically

# 2. Dispatch 12 sub-agents (each follows v2 Research Graph + progressive-complexity)
#    Each agent reads runs/<task>/<cond>/prompt.md and writes:
#    - candidate.py (final solver)
#    - reasoning.md, research_state.jsonl, session_log.md
#    - pred_results/<task>.npy

# 3. Parent-side eval — both v1 and v2 (physics-aware)
$PY stage2_v3/class_A/scripts/run_eval.py    # v1 (legacy)
$PY stage2_v3/class_A/scripts/run_eval_v2.py # v2 + compares v3.A vs v3.A'
```

---

## Headline results (from CLASS_A_LOG.md)

### v3.A INITIAL (50-entry bank, no BKdV-S6/S7), physics-aware eval

| | NoKB | PosOnly | NegOnly | PosNeg |
|---|---|---|---|---|
| **PASS / 3** | 0/3 | 1/3 | 1/3 | **3/3** |

### v3.A' EXPANDED (58-entry bank, +BKdV-S6 ν-prescription, +BKdV-S7 Gardner-vs-BKdV)

| | NoKB | PosOnly | NegOnly | PosNeg |
|---|---|---|---|---|
| **PASS / 3** | 0/3 | 1/3 | **3/3** | **3/3** |

### Key paper findings (see CLASS_A_LOG.md §5 for details)

1. **NegOnly 1/3 → 3/3 after adding S6 prescription** — single bank entry with
   prescriptive `recommended_alternative` field (ν=5e-2 on u) lifts negative-
   only bank from "veto-only" to "actionable" → biggest bank-size-vs-content
   demonstration in the experiment.
2. **PosNeg 3/3 robust** across both bank versions — double-source actionable
   signal (positive prescription + negative warning) is most stable.
3. **NoKB 0/3 stable** — no bank → no improvement at any size; validates bank
   actually provides knowledge agents can't derive themselves in ≤ 3 rounds.
4. **T_A eval v1 → v2** — v1's `amp_ratio ≥ 0.5` threshold was physically
   unattainable (BKdV-S7 deep quantifies sech² off-manifold → −62.8% decay);
   v1 rewarded chaotic fragmentation (NoKB 14-peak), punished honest physics
   (NegOnly/PosNeg 1-peak coherent soliton). v2 fixes this with
   `amp_ratio ≥ 0.25` + single-dominant-peak check.

---

## Known storage gaps (transparent disclosure)

| Artifact | Stage 1 has? | Stage 2 Class A has? | Mitigation |
|---|---|---|---|
| Per-round `candidate.py` (E1, E2, E3 each) | ✓ (round1/, round2/, round3/) | ✗ only final | `research_state.jsonl` has method/params per E-node, but not byte-exact code |
| Per-round `exec.log` (stdout/stderr) | ✓ | ✗ | F-node has diagnostics summary |
| Per-round intermediate `.npz` snapshots | ✓ partial | ✗ | only final `pred_results/T_X.npy` |
| Sub-agent verbatim return paragraph | quoted in `reasoning.md` | quoted in `reasoning.md` | full transcript not preserved on disk |

The gap exists because Stage 1 prompts mandated per-round subdirectories, while
Stage 2 v2 templates inherited from earlier work did not. For Class B (B1, B2),
templates should be updated to require per-round saves to close this gap.

---

## File counts

```
stage1_v3/runs/                            7 programs × ~5 files top-level + 3 rounds × ~4 files = ~95 files
stage1_v3/nk_records/                      28 JSON NK records
stage1_v3/bank/                            3 .jsonl + 1 .json = 4 files
stage1_v3/curator_prompts/generated/       28 .md curator prompts
stage1_v3/scripts/                         4 Python scripts
stage1_v3/prompts/                         1 master template
stage2_v3/class_A/runs/                    12 cells × 9 files = 108 files (v3.A')
stage2_v3/class_A/runs_initial_*/          12 cells × 9 files = 108 files (v3.A)
stage2_v3/class_A/eval/                    2 Python eval modules
stage2_v3/class_A/scripts/                 3 Python build/eval drivers
stage2_v3/class_A/tasks/                   1 JSON task spec
stage1_legacy_v2era/bank/                  3 .jsonl entries
historical_reports/                        2 prior Section 4 markdown reports
```

Total: ~390 files, ~8.7 MB.
