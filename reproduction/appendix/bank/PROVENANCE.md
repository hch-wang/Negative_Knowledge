# Bank provenance

This appendix re-uses two pre-existing knowledge banks. Both were produced **in earlier sections of the paper** and are bundled here verbatim for reproducibility — they are **not** new contributions of this appendix.

## 1. NLS bank (`nls_knowledge.jsonl`, 21 entries)

- **Source**: Section §B-NLS (this paper), curator pass over the 8 stage-1 stress tests bundled here under `appendix_reproduce/logs/stage1_bnls/`.
- **Original artifacts** (also bundled at `logs/stage1_bnls/S{1..8}/`):
  - 8 stress tests: S1 (bright soliton, Madelung validation), S2 (direct vs Madelung), S3 (Gaussian MI threshold), S4 (dark soliton), S5 (B-NLS on Mcs), S6 (off-Mcs relaxation), S7 (bore × soliton), S8 (low-density quantum-pressure singularity).
  - Each stress test produced a structured `knowledge_findings.json` with methods_tried / positive_findings / negative_findings / parameter_boundaries fields.
  - Curator agent (prompt at `prompts/curator_prompt.md`) synthesised these 8 files into the 21-entry bank.
- **Composition**: 11 negative / 10 positive; 2 structural / 4 family-level / 3 multi-experiment / 12 single-experiment.
- **Most-cited entries during Stage 3**:
  - `kb-nls-sign-convention` (structural) — warns user's +sqrt(N)_xx sign is opposite standard NLS Madelung
  - `kb-nls-madelung-psi-structural-coupling` (structural) — Mcs constraint becomes algebraic identity via Madelung-Ψ
  - `kb-nls-direct-n-phi-structural-failure` (family-level, 5 stress tests) — direct (N,φ) RK4 fails on any sech-tail problem

## 2. BKdV bank (`bkdv_positive.jsonl` 10 entries + `bkdv_negative.jsonl` 20 entries)

- **Source**: Section §3 (this paper), now bundled here as `appendix_reproduce/bank/bkdv_positive.jsonl` and `appendix_reproduce/bank/bkdv_negative.jsonl`.
- The BKdV bank was constructed from a different physical system (Burgers-swept-KdV, Holm 2025) on 14 stress tests of Burgers / KdV / Gardner / shallow-water schemes.
- **It is used here as a cross-domain bank**: the appendix's central question is whether knowledge constructed on one PDE family (BKdV) transfers to a related-but-different family (B-NLS). The bundled `logs/verified_results.json` and `analyze_results.py` reproduce the answer: **partial transfer with active negative-transfer risk** on the new failure modes (NLS quantum pressure, sign-convention).
- **Composition**: 10 positive (recommended methods) + 20 negative (warned routes). Schema is the bounded-failure-record 6-field schema from §3.

## How the appendix uses the two banks

The 4 conditions in this appendix are defined by which bank(s) the sub-agent gets to read:

| Condition | NLS bank? | BKdV bank? | What it tests |
|---|---|---|---|
| `NoKB` | ✗ | ✗ | What's achievable with general PDE knowledge only |
| `BKdV` | ✗ | ✓ | Cross-domain bank ALONE (the negative-transfer probe) |
| `NLS` | ✓ | ✗ | Domain-matched bank ALONE (the baseline-with-help) |
| `NLSBKdV` | ✓ | ✓ | Composition (does cross-domain add anything when domain-matched is present?) |

No new bank entries are produced by this appendix; the 51-entry combined bank is held fixed across all 4 conditions on all 4 tasks (T_A, T_B, T_C, T_D).
