# Appendix reproduction kit — Burgers-NLS 4-condition study

Reviewer-facing package for the **Burgers-NLS appendix** of the paper. The headline finding:

> On the Burgers-NLS coupled-system case study, with **four open phenomenology sub-tasks** and **four memory conditions** (NoKB / BKdV-only / NLS-only / NLS+BKdV), a **domain-matched 21-entry NLS bank** lifts the agent from **0/4 PASS** (no bank) to **3/4 PASS**. Adding the 30-entry cross-domain BKdV bank to NLS yields **0 marginal task-success advantage**. **Cross-domain bank ALONE can actively mislead**: on T_B the BKdV-only condition reached 0.005 % of requested simulation time vs the NoKB baseline's 0.7 % — a 140× degradation — because BKdV's positive entries validate a method that is anti-diffusive under the user's variational +Q sign.

> A research-grade meta-finding: an NLS-bank-aware agent on T_D **corrected** the bank's `kb-nls-sign-convention` entry, identifying the consistent Madelung-Ψ formulation as standard kinetic + non-trivial real potential V[N] = (√N)_xx/√N − 2κN. The bank can be improved by careful agents that use it.

This appendix **does not produce new bank entries**. Both banks were constructed in earlier sections of the paper (see `bank/PROVENANCE.md`); the appendix's experiment is a controlled 4×4 comparison of how those banks transfer to a new PDE system.

Two reproduction modes:

| Mode | Cost | Time | What you verify |
|---|---|---|---|
| **A. Verify-only** | $0 | < 5 s | Every appendix claim traces to bundled `logs/` |
| **B. End-to-end on one cell** | ~$1 | 5 – 15 min | Re-runs one (task, cond) cell with fresh sub-agent dispatch |

---

## A. Verify-only (no API key)

```bash
python analyze_results.py
```

Expected output: `54/54 claims match`. Detailed report at
`results/claim_report.md` lists every claim, the value the script
computed, and the file paths supporting it.

What gets verified:
- Bank composition: 21 NLS entries (2 structural + 4 family-level + 3 multi-experiment + 12 single-experiment), 10 BKdV positive + 20 BKdV negative
- Aggregate pass rates: NoKB 0/4, BKdV 2/4, NLS 3/4, NLSBKdV 3/4
- Per-cell verdicts for all 16 cells (T_A/T_B/T_C/T_D × NoKB/BKdV/NLS/NLSBKdV)
- Negative-transfer signature: T_B/BKdV is more truncated than T_B/NoKB
- T_D BKdV "PASS" via conservative truncation: mass drift 3.74 % < 5 % gate; T_D/NLS mass drift 98.92 % > gate
- Presence of all 16 Stage-3 cell artifacts (candidate.py, reasoning.md, pred_results) and 8 Stage-1 stress test outputs

### BKdV → B-NLS knowledge chain

For an entry-by-entry audit of **which specific BKdV bank entries** enabled which B-NLS task to succeed (and the one entry that *actively misled* T_B BKdV), see:

```
results/BKdV_KNOWLEDGE_CHAIN.md
```

That document traces every cite_bank / reject_bank record in the 4 BKdV-only cells plus the bank-usage sections of the 4 NLSBKdV cells, and lays out the explicit causal chain: **BKdV entry → decision in Experiment E_n → observed outcome in Finding F_n**. Key findings:

1. **`kb-general-firstOrder-Godunov-preShock-baseline` + `kb-burgers-Godunov-preShock-smooth`** → directly enabled T_C's bore-sector stability (the 8× improvement over NoKB).
2. **`kb-general-finiteness-not-accuracy` + `kb-general-massConservation-insufficient-diagnostic`** → motivated T_D's pre-blowup truncation, the ONLY way T_D BKdV passed.
3. **`kb-kdv-IMEX-CN-spectral-pass`** is dual-faced: positive on T_A (motivated Madelung-Ψ split structure) but **NEGATIVE-TRANSFER on T_B** (140× worse than NoKB) because B-NLS's +Q sign makes the spectrally-endorsed method anti-diffusive.

## B. End-to-end (Anthropic API)

```bash
pip install -r ../requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export PY_VENV=/path/to/your/python   # interpreter the sub-agent uses to run candidate.py

# Replay one cell against the bundled saved trace (no API call):
python run_pipeline.py --task T_C --cond NLS --use-saved-trace

# Fresh dispatch (uses Anthropic API):
python run_pipeline.py --task T_C --cond NLS
```

`run_pipeline.py`:
1. (fresh mode) rebuilds the cell's sandbox via `scripts/build_sandboxes.py`, embedding the appropriate bank (or no bank) in the prompt
2. (fresh mode) dispatches a single Claude sub-agent via `scripts/dispatch_subagent.py` — the agent gets Read / Write / Bash tools, follows the Research-Graph protocol in `prompts/stage3_template.md`, runs `candidate.py` inline, and writes the final `pred_results/<task>.npy`
3. runs the parent-side phenomenon check from `eval/phenomenon_checks_bnls.py`
4. prints PASS/FAIL with diagnostics; updates `logs/stage3/<task>/<cond>/verified_eval.json`

Recommended cells for first-time reviewers:
- **`T_C/NLS`** (clean PASS in 3 iterations via MUSCL + Madelung-Ψ Strang) — demonstrates domain-matched bank's effect
- **`T_C/BKdV`** (FAIL — reaches t ≈ 0.65 of T = 8) — demonstrates that cross-domain Godunov entries handle the bore sector but BKdV bank cannot guide the NLS sector
- **`T_B/BKdV`** (FAIL — reaches t ≈ 0.0003 of T = 6, worse than NoKB's 0.043) — the **negative-transfer headline**

---

## Directory layout

```
appendix_reproduce/
├── README.md                       this file
├── analyze_results.py              Mode A: verify saved logs reproduce all claims
├── run_pipeline.py                 Mode B: re-run one cell end-to-end
├── tasks/
│   ├── stage3_tasks.json           4 B-NLS task specs (T_A / T_B / T_C / T_D)
│   └── stage1_bnls_tests.json      8 stage-1 stress test specs (for reference)
├── bank/                           ← *both banks come from earlier sections*
│   ├── PROVENANCE.md               ★ which section produced which bank
│   ├── nls_knowledge.jsonl         21 entries — from §B-NLS stage-1 curator
│   ├── bkdv_positive.jsonl         10 entries — from §3 stage-1 (Burgers-swept-KdV)
│   └── bkdv_negative.jsonl         20 entries — from §3 stage-1
├── prompts/
│   ├── stage3_template.md          Research-Graph + progressive-complexity cell prompt
│   ├── stage1_bnls_template.md     stress-test prompt (reference; stage-1 already run)
│   └── curator_prompt.md           bank curator prompt (reference; bank already curated)
├── eval/
│   └── phenomenon_checks_bnls.py   deterministic phenomenon checks for T_A/T_B/T_C/T_D
├── scripts/
│   ├── _paths.py                   path resolution
│   ├── build_sandboxes.py          build prompts for any subset of 16 cells
│   ├── dispatch_subagent.py        Anthropic-API tool-use loop (Read/Write/Bash)
│   └── run_eval.py                 parent-side eval on all 16 cells
├── logs/                           ★ bundled outputs from our original run
│   ├── verified_results.json       16-row aggregate eval result
│   ├── stage3/<task>/<cond>/       per-cell: prompt.md, candidate.py, reasoning.md,
│   │                               research_state.jsonl, session_log.md,
│   │                               verified_eval.json, pred_results/<task>.npy
│   └── stage1_bnls/S{1..8}/        per-stress-test: candidate.py,
│                                   reasoning.md, research_state.jsonl,
│                                   knowledge_findings.json
└── results/                        populated by analyze_results.py
    └── claim_report.md
```

---

## How the bank was produced (reference)

This appendix uses the bank **as-is**. The bank-production pipeline lived in §B-NLS stage 1; we summarise it here so reviewers can trace any bank entry back to its raw evidence:

```
8 stress-test sub-agents (stage1_bnls/runs/S{1..8})
  → each produces knowledge_findings.json with
     methods_tried / positive_findings / negative_findings / parameter_boundaries
  → curator sub-agent (prompts/curator_prompt.md) reads all 8
     knowledge_findings.json + deduplicates + assigns depth tags
  → bank/nls_knowledge.jsonl (21 entries; bundled here verbatim)
```

The BKdV bank (`bkdv_positive.jsonl` + `bkdv_negative.jsonl`) was produced earlier, in §3 of the paper. It is reused unchanged.

If reviewers wish to re-curate the NLS bank from the bundled stage-1 outputs:

```bash
# (Not part of the standard reproduce flow — bank is bundled verbatim)
# Curator agent dispatch uses the same dispatch_subagent.py with the
# curator prompt. See prompts/curator_prompt.md for the inputs/outputs spec.
```

---

## Caveats

- **LLM non-determinism**: re-running Mode B does not produce byte-identical
  candidate.py or research_state.jsonl. It reproduces the *direction* of the
  finding (e.g. T_C/NLS converges on MUSCL + Madelung-Ψ; T_B/BKdV blows up at
  short time).
- **Audit-trail gap**: research_state.jsonl files for the NoKB / NLS / NLSBKdV
  cells of the original run were overwritten during a sandbox rebuild; only
  the BKdV-only cells (added in a later batch) have intact research_state.jsonl.
  The PASS/FAIL evidence is unaffected because it is read from pred_results/.
- **Sandbox tool fidelity**: the original sub-agents ran inside Claude Code with
  full Read / Write / Bash semantics. `scripts/dispatch_subagent.py` is a
  clean-room reimplementation using the public Anthropic SDK tool-use loop;
  near-identical session behaviour, not bit-identical.
- **Python environment**: candidate.py files use only numpy + scipy. Set
  `PY_VENV` to a virtualenv containing those packages.
- **Sign convention**: the B-NLS equations bundled here use the user's
  variational +sqrt(N)_xx / (2 sqrt N) sign in the phi-equation, which is
  *opposite* the standard NLS Madelung convention. The NLS bank flags this in
  `kb-nls-sign-convention`; the T_D NLS agent's correction of this entry
  (Section §5.2 of the appendix) is the deepest single result.

---

## Citation

```
@inproceedings{NegativeKnowledge2026appendix,
  title  = {Negative Knowledge as Failure-aware shared memory for AutoResearch -- Burgers-NLS appendix},
  author = {...},
  booktitle = {ICML 2026 AI4Research Workshop},
  year   = {2026},
}
```
