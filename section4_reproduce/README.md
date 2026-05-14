# Section 4 reproduction kit

Reviewer-facing package for §4 of the paper. The headline finding:

> On the BKdV (Burgers-swept-KdV) coupled-system case study, with three
> open phenomenology sub-tasks and four memory conditions, a
> **negative-only knowledge bank** containing 7 multi-round path-closure
> records (depth-3 deep synthesis) reaches **3/3 PASS**, matching the
> full positive-plus-negative bank. The no-bank baseline reaches 0/3
> and the positive-only bank reaches 1/3. **A negative bank can be
> prescriptive**, not merely a veto list, when its records contain
> ruled-out routes plus a replacement direction.

Two reproduction modes:

| Mode | Cost | Time | What you verify |
|---|---|---|---|
| **A. Verify-only** | $0 | <5 s | Every paper §4 claim traces to bundled `logs/` |
| **B. End-to-end** | several $ | tens of min | Stage 1 stress-test programs + Stage 2 cells re-run |

---

## A. Verify-only (no API key)

```bash
python analyze_results.py
```

Expected output: `20/20 claims match`. Report at
`results/claim_report.md` lists every paper §4 claim, the value the
script computed, and the file paths supporting it.

What gets verified:
- Stage~1 bank composition (7 BKdV-S programs, 28 NK records, 58-entry final bank)
- Stage~2 PASS rates per condition (NoKB 0/3, PosOnly 1/3, **NegOnly 3/3**, PosNeg 3/3)
- Phenomenon-check threshold (T-A amp_ratio $\geq 0.25$ + single-dominant-peak)
- BKdV-S6 specifics ($\nu=5\times 10^{-2}$ prescription; BKdV-S4 envelope 13 orders too weak)
- BKdV-S7 specifics ($-62.8\%$ $v_{\max}$ decay; cosine-similarity $0.94$ mode prediction)

## B. End-to-end (Anthropic API)

```bash
pip install -r ../requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export PY_VENV=/path/to/your/.venv/bin/python  # for the sub-agent's Bash

# Replay one cell end-to-end on bundled saved trace (no API):
python run_pipeline.py --task T_C --cond NegOnly --use-saved-trace

# Replay with a fresh sub-agent dispatch (uses anthropic SDK + API key):
python run_pipeline.py --task T_C --cond NegOnly
```

``run_pipeline.py`` reuses the saved Stage~2 prompt for the (task, cond)
cell (which already embeds the canonical 58-entry bank), dispatches a
fresh sub-agent with Read / Write / Bash tools (Stage~2 cells execute
``candidate.py`` inline), then runs the parent-side phenomenon-aware
eval on the produced ``pred_results/<task>.npy``. The default cell is
``T_C/NegOnly`` because it is the cleanest single-cell demonstration of
prescriptive negative knowledge: the cell passes in two iterations by
adopting the BKdV-S6 deep record's
``nu_linear = 5\times 10^{-2}`` prescription.

For curator dispatch alone (Stage~1 NK production), use
``nk_curator.py``:

```python
from nk_curator import NKCurator
curator = NKCurator(model="sonnet")

# depth-1: distill one round of failure into a single NK record
rec = curator.produce_per_round(
    program_id="BKdV-S6", round_num=1,
    program_dir="logs/stage1/BKdV-S6",
    output_path="logs/nk_records/BKdV-S6_r1.json",
)

# depth-3: synthesise across all 3 rounds
rec = curator.produce_deep(
    program_id="BKdV-S6",
    program_dir="logs/stage1/BKdV-S6",
    output_path="logs/nk_records/BKdV-S6_deep.json",
)
print(rec.schema_issues)   # empty list iff valid
```

The full multi-stage pipeline writes new generated artifacts under
`runs/` by default (`REPRO_RUNS` can override this): build sandboxes →
dispatch 7 stage-1 programs → dispatch 28 curators → aggregate bank →
build 12 stage-2 cells → dispatch 12 stage-2 agents → run eval.
It uses the scripts in ``scripts/``:

```bash
python scripts/build_stage1_programs.py        # 7 BKdV-S program prompts
# ...dispatch each via Claude Code or python -c "from nk_curator ..."
python scripts/build_curator_prompts.py        # 28 curator prompts
# ...dispatch curators
python scripts/aggregate_bank.py               # merge 30 legacy + 28 new -> 58
python scripts/build_stage2.py                 # 12 stage-2 sandboxes
# ...dispatch stage-2 agents
python scripts/run_eval.py                     # parent-side phenomenon eval
```

---

## Directory layout

```
section4_reproduce/
├── README.md                       this file
├── analyze_results.py              ★ Mode A: derive paper §4 claims from logs/
├── nk_curator.py                   ★ NK production class (NKCurator)
├── run_pipeline.py                 ★ Mode B: end-to-end one-cell re-run
├── prompts/                        ★ canonical agent prompts (first-class artifacts)
│   ├── stage1_program_template.md  Stage 1 BKdV-S program template
│   └── stage2_template.md          Stage 2 cell template (incl. progressive-complexity)
├── curator_prompts/                ★ canonical curator prompts
│   ├── per_round_template.md       per-round (depth-1) curator
│   └── deep_template.md            multi-round (deep, depth-3) curator
├── scripts/
│   ├── _paths.py                   path resolution from REPRO_ROOT
│   ├── dispatch_subagent.py        low-level Anthropic-API sub-agent loop
│   ├── build_stage1_programs.py    generate 7 BKdV-S program prompts
│   ├── build_curator_prompts.py    generate 28 curator prompts (4/program)
│   ├── aggregate_bank.py           merge 30 legacy + 28 new → 58-entry bank
│   ├── build_stage2.py             generate 12 Stage 2 sandboxes
│   ├── phenomenon_checks.py        physics-aware eval module
│   └── run_eval.py                 parent-side eval driver
├── tasks/
│   └── stage2_definitions.json     T_A, T_B, T_C task specs
└── logs/                           archive of original run
    ├── stage1/                     7 BKdV-S program runs with full per-round artifacts
    │   └── BKdV-S{1..7}/
    │       ├── prompt.md
    │       ├── hypothesis.md
    │       ├── research_state.jsonl
    │       └── round{1,2,3}/
    │           ├── candidate.py
    │           ├── exec.log
    │           ├── reasoning.md
    │           └── *.npz
    ├── stage2/                     12 Stage 2 cells
    │   └── T_{A,B,C}/{NoKB,PosOnly,NegOnly,PosNeg}/
    │       ├── prompt.md
    │       ├── memory.md
    │       ├── candidate.py
    │       ├── reasoning.md
    │       ├── research_state.jsonl
    │       ├── session_log.md
    │       └── pred_results/<task>.npy
    ├── nk_records/                 28 JSON NK records (21 per-round + 7 deep)
    ├── banks/
    │   ├── pilot_legacy_{positive,negative,all}.jsonl   30-entry pilot bank (input)
    │   ├── bank_{positive,negative,all}.jsonl            58-entry final bank (output)
    │   └── bank_index.json                               aggregation metadata
    ├── verified_results/
    │   └── verified_results.json   parent-eval output
    ├── curator_prompts_generated/  28 instantiated curator prompts (audit trail)
    └── stage2_log.md               experiment log
```

## How NK gets produced (curators)

Stage 1 NK records are written by curator sub-agents that read the
complete 3-round trace of a BKdV-S program. There are two passes:

- **Per-round curator** reads ONE round's `candidate.py + exec.log +
  reasoning.md`, writes one **depth-1** NK record (single-round schema).
- **Deep curator** reads ALL 3 rounds plus `research_state.jsonl` and
  `hypothesis.md`, writes one **depth-3** synthesis record with extra
  fields: `depth`, `rounds_summary`, `ruled_out_routes`,
  `synthesised_diagnosis`. The `recommended_alternative` field must NOT
  duplicate anything in `ruled_out_routes`.

```jsonc
// Single-round NK record schema (depth-1)
{
  "task_id": "BKdV-S6",
  "round": 1,
  "attempted_route": "...",           // ≤ 200 chars
  "observation": "...",               // ≤ 200 chars
  "failure": {"layer": "...", "scope": "...", "degree": "...",
              "recommended_action": "...", "risk": "..."},
  "rationale": "...",                 // ≤ 300 chars
  "recommended_alternative": "...",   // ≤ 300 chars; specific API + params
  "is_trivial": false,
  "trivial_degree": 0
}

// Deep synthesis NK record (depth ≥ 2)
{
  "task_id": "BKdV-S6", "depth": 3,
  "rounds_summary": [{"round": 1, "attempted_route": "...", "observation": "..."}, ...],
  "ruled_out_routes": ["...", ...],
  "synthesised_diagnosis": "...",     // the load-bearing claim
  "failure": {...},
  "rationale": "...",
  "recommended_alternative": "..."    // must not duplicate ruled_out_routes
}
```

Canonical curator prompts are in `curator_prompts/`. They are
first-class artifacts: the operational definition of the NK schema.

## Caveats

- **LLM nondeterminism**: re-running Mode B does not produce
  byte-identical NK records, but reproduces the qualitative result
  (prescriptive depth-3 negatives let NegOnly match PosNeg).
- **Per-round storage**: Stage 2 sub-agents save only the FINAL solver
  per cell on disk. The `research_state.jsonl` records the method
  description for each Experiment node but not byte-exact intermediate
  code. Stage 1 sub-agents DO save per-round artifacts.
- **Schema split heuristic**: the positive/negative classification of
  curated entries is heuristic (based on `failure.recommended_action`).
  One entry (BKdV-S7 round-2) is misclassified as positive due to its
  `action=retry` field — discussed in `appendix:ic-trap`.
- **Phenomenon-check threshold**: the original T-A threshold ($\geq 0.5$)
  was physically unattainable per BKdV-S7's quantitative prediction;
  the bundled `phenomenon_checks.py` uses the corrected $\geq 0.25$ +
  single-dominant-peak threshold.

## Citation

```
@inproceedings{NegativeKnowledge2026,
  title  = {Negative Knowledge as Failure-aware shared memory for AutoResearch},
  author = {...},
  booktitle = {ICML 2026 AI4Research Workshop},
  year   = {2026},
}
```

BKdV system: Holm et al., 2025.
