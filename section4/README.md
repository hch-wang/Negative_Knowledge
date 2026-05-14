# Section 4 — Negative Knowledge for AutoResearch (Research Graph framework)

> This directory implements the two-stage PDE pilot used in **paper §4**.
> Stage 1 generates a structured knowledge bank from component-PDE stress tests.
> Stage 2 runs an AutoResearch loop (Research Graph framework) on a coupled Burgers-swept-KdV study, comparing 4 memory conditions × 3 sub-tasks × ≤3 iterations.

---

## Two-stage layout

```
section4/
├── stage1/   ← Knowledge production (already done)
│   ├── bank/{knowledge_bank.jsonl, positive_knowledge.jsonl, negative_knowledge.jsonl}
│   ├── sandboxes/{A1..A10, G1..G4}/  (14 stress-test runs)
│   ├── scripts/{build_stage1.py, build_gardner.py, run_stage1.py, curator_prompt.md}
│   └── README.md
└── stage2/   ← AutoResearch (Research Graph framework, READY but not yet executed)
    ├── prompts/research_graph_template.md
    ├── tasks/definitions.json
    ├── bank → ../stage1/bank  (symlink)
    ├── scripts/{split_bank.py, build_v2.py}
    └── runs/{T_A,T_B,T_C}/{NoKB, PosOnly, NegOnly, PosNeg}/
        ├── prompt.md
        ├── memory.md
        ├── meta.json
        ├── research_state.jsonl  (empty; agent appends)
        ├── session_log.md
        └── pred_results/
```

---

## Stage 1 (done) — Knowledge production summary

- **14 component-PDE stress tests** (Burgers shock / KdV soliton / Shallow water / Gardner, each tested under specific forced methods or parameter regimes that surface common failures)
- **Curator agents** synthesized stress-test outcomes into **30 bounded knowledge entries** (10 positive + 20 negative), each with `applicability` field projecting onto the coupled Burgers-swept-KdV target
- Split into two files:
  - `stage1/bank/positive_knowledge.jsonl` — 10 entries (methods that worked)
  - `stage1/bank/negative_knowledge.jsonl` — 20 entries (methods that failed, structured by §7 6-field failure schema)
- Full schema audit: 30/30 entries cite real evidence files

See `stage1/README.md` (= original STAGE1_INDEX.md) for full per-test breakdown.

---

## Stage 2 (ready, NOT executed) — AutoResearch framework

### Framework: Research Graph

Each sub-agent operates inside an explicit Research Graph protocol — graph nodes are append-only entries in `research_state.jsonl`:

| Node | Purpose | Fields |
|---|---|---|
| **Q** Question | research question being attacked | `text`, optionally `relevant_bank_domains` |
| **E** Experiment | a concrete (IC, method, params, T) proposal | `ic`, `method`, `params`, **`cites_bank`** (positive entries adopted), **`rejects_bank`** (negative entries avoided), **`bank_use_rationale`** |
| **F** Finding | observed outcome of an Experiment | `diagnostics`, `kind` (positive/negative/partial), `useful_self_assessment` |
| **D** Decision | choice of next action | `action` (retry / change_method / narrow_claim / abandon_route / stop_useful), `rationale` |

Edges (implicit through `produces`, `motivated_by`, `based_on` fields):
- Q → motivates → E
- E → produces → F
- F → informs → D
- D → motivates → E (next iteration)

### Where NK is consulted (binding)

**Primary use: proposal stage (E node creation).**

The Research Graph prompt **mandates** at each E node:
- If positive entries available → scan `applicability` field, list matching ids in `cites_bank`
- If negative entries available → scan `applicability` field for warned-against approaches, list matching ids in `rejects_bank`
- **If both positive AND negative available (PosNeg condition) → MUST consult both kinds**
- If nothing matches → explicitly record `cites_bank: []` with `"no matching bank entry"` note

### "Loop 3 times" — binding definition

> **One iteration = one Bash execution of `candidate.py`, paired with one new Experiment + one new Finding node.**

- Bash execution counts; rewriting code without execution does not
- Trivial typo bug-fixes that re-run the SAME method → SAME iteration (clarifying note on Finding)
- Substantively different IC / method / params → NEW Experiment node → consumes one iteration
- Hard cap: **3 iterations**. Agent may stop early on `useful_self_assessment: true`

### 4 memory conditions

| Condition | Sees `positive_knowledge.jsonl` (10) | Sees `negative_knowledge.jsonl` (20) |
|---|---|---|
| NoKB    | ✗ | ✗ |
| PosOnly | ✓ | ✗ |
| NegOnly | ✗ | ✓ |
| PosNeg  | ✓ | ✓ |

→ **Files are physically disjoint**: PosOnly is given a path to positive_knowledge.jsonl only; NegOnly is given a path to negative_knowledge.jsonl only. There is no way for PosOnly to accidentally see negative entries.

### 3 sub-tasks (Burgers-swept-KdV phenomena)

| Sub-task | Phenomenon under study |
|---|---|
| **T_A** | Soliton stability under non-zero `m := u - v²/2` perturbation, long-time propagation |
| **T_B** | Gaussian wave packet → soliton train decomposition (inverse-scattering-like) |
| **T_C** | Burgers bore × KdV soliton interaction (refraction / reflection / fusion) |

ICs and phenomenon targets in `tasks/definitions.json`. **No closed-form reference solutions** — eval uses deterministic phenomenon checks (mass drift, peak count, amplitude survival, boundedness).

### Agent tool access

- Read (any file, including bank files)
- Write (any file inside working directory)
- **Bash** (executes `candidate.py` via venv Python and runs quick numpy diagnostics)
- ❌ Edit / Grep / Glob / network / install

This is the **AutoResearch** layer that v1 (the previous Stage 2) didn't have — agent autonomously executes, observes, and decides within session.

---

## Comparison to v1 (the earlier Stage 2 under `../../stage2/`)

| Dimension | v1 | v2 (this section4/stage2/) |
|---|---|---|
| Framework | Single-shot code writer, parent orchestrates rounds | **Research Graph** with explicit Q/E/F/D nodes |
| Conditions | 3 (NoKB / PosOnly / PosNeg) | **4** (adds **NegOnly**) |
| Agent tools | Read + Write | Read + Write + **Bash** |
| Iteration | Parent invokes sub-agent 3 times in sequence | One sub-agent session with **3 internal iterations** |
| NK usage | Implicit (bank dumped into prompt) | **Explicit at proposal stage** (mandatory `cites_bank` + `rejects_bank` fields, with `bank_use_rationale` justifying use of both kinds when both available) |
| Output graph | None (just `failure_record.json` per round) | `research_state.jsonl` append-only Research Graph |

---

## Status

✅ Stage 1 complete (30 entries, audit pass)
✅ Stage 2 sandboxes built (12 cells, prompts regenerated with section4 paths)
✅ Research Graph prompt template emphasizes proposal-stage NK use (both pos+neg)
⏸ **Stage 2 sub-agent dispatch NOT yet executed — awaiting go-ahead**

---

## How to run Stage 2 (when go-ahead is given)

```bash
# 1. (Already done) Split bank into pos + neg
.venv/bin/python Negative_Knowledge/section4/stage2/scripts/split_bank.py

# 2. (Already done) Build 12 sandboxes
.venv/bin/python Negative_Knowledge/section4/stage2/scripts/build_v2.py

# 3. (TBD) Dispatch 12 long-running Research Graph sessions in parallel
#    Each uses Read+Write+Bash tools, ≤3 internal iterations
#    Estimated: ~600k tokens, ~30-45 min wall time

# 4. (TBD) Parent runs deterministic phenomenon eval on each cell's pred_results/
.venv/bin/python Negative_Knowledge/section4/stage2/scripts/run_eval.py   # not yet written

# 5. (TBD) Cross-condition aggregator
.venv/bin/python Negative_Knowledge/section4/stage2/scripts/aggregate.py  # not yet written
```

---

## Resource budget (Stage 2, not yet spent)

| Item | Estimate |
|---|---|
| Sub-agent sessions | 12 (3 tasks × 4 conditions) |
| Tokens / session (Sonnet, up to 3 iters with PDE runs) | ~50k |
| Total tokens | ~600k |
| Wall time | ~30-45 min |
| Disk | ~5 MB additional artifacts (research_state.jsonl, candidate.py, etc.) |

---

## Stage 1 was already finished using the older folder layout

For provenance, the original Stage 1 was conducted under `paper/experiments/pde_pilot_2026-05-11/stage1/`. We **moved a copy** of code + bank files into `section4/stage1/`, and **symlinked** large data dirs (sandboxes/, ref_results/, gold/) to preserve disk + provenance. Both locations are valid; the canonical paper-§4 reference is the section4 path.
