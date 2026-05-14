# Curator role: synthesize stage1_bnls findings into a B-NLS knowledge bank

You are the curator for the B-NLS stage 1 knowledge bank. Your job is to read the structured findings from 8 stress tests and produce a unified, deduplicated, well-organized bank file that captures the methodological knowledge produced.

## Inputs

Read these 8 files (each is a structured `knowledge_findings.json`):

- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S1/knowledge_findings.json` (bright soliton Madelung validation, 4 pos / 3 neg)
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S2/knowledge_findings.json` (direct vs Madelung, 5 pos / 5 neg — direct fails structurally)
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S3/knowledge_findings.json` (MI threshold, convergence-dependent)
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S4/knowledge_findings.json` (dark soliton, anti-periodic basis required)
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S5/knowledge_findings.json` (B-NLS on Mcs, Madelung-Psi as structural representation)
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S6/knowledge_findings.json` (Mcs relaxation, hypothesis refuted under standard NLS sign)
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S7/knowledge_findings.json` (bore × soliton — dual fix MUSCL + Madelung required)
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S8/knowledge_findings.json` (low density singularity, direct fails structurally)

## Output schema (one JSON object per line)

Write to:
`/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/bank/nls_knowledge.jsonl`

Each entry must have at minimum:

```json
{
  "id": "kb-nls-<short-descriptor>",
  "kind": "positive | negative",
  "domain": "NLS | B-NLS | B-NLS-Mcs | B-NLS-shock | B-NLS-low-density | B-NLS-dark-soliton",
  "claim": "<one-sentence rule that an agent can act on>",
  "applicability": "<concrete description of when this entry applies — be specific about regime>",
  "depth": "single-experiment | multi-experiment | family-level | structural",
  "source_tests": ["S1", "S2", ...],
  "evidence": "<numbers / diagnostics supporting the claim>",
  "recommended_alternative_or_action": "<if negative: what to use instead; if positive: how to use>"
}
```

Use `depth` to mark how deep the finding is:
- `single-experiment`: standard error message — agent could discover this in 1 run
- `multi-experiment`: needed comparing >=2 method variants in the same test
- `family-level`: confirmed by multiple stress tests independently
- `structural`: mathematical / algebraic identity, not a measurement

## Curation guidelines

1. **Deduplicate**: if the same finding appears in multiple stress tests, merge into one entry with `source_tests` listing all sources. **Mark the merged entry as `family-level` depth**.

2. **Promote depth**: a finding that S2, S4, S6, S7, S8 all independently confirmed is `family-level`. Examples likely include "direct (N, phi) integration fails structurally" — this should be ONE entry, not five.

3. **Keep specific parameter boundaries**: if a finding has concrete numbers (e.g. "Nx >= 1024 for A=3 Gaussian"), keep them in `evidence`.

4. **Add a SIGN-CONVENTION entry**: a critical entry must record the fact that the user's variational form has +sqrt(N)_xx/(2 sqrt(N)) sign in the phi equation (opposite from standard NLS Madelung). Agents working on B-NLS must:
   - Verify the sign before reaching for "standard" Madelung-Psi
   - Be aware that standard NLS results (e.g. from S6) may not directly transfer to the user's sign-convention system
   This entry should be `domain: "B-NLS"`, `kind: "negative"` (warns of confound), `depth: "structural"`.

5. **Mcs as attractor — record both findings**: include BOTH the empirical finding from S6 (||m|| grows under standard NLS sign) AND the caveat that this is sign-convention-dependent. Two entries OR one entry with explicit caveat.

6. **The Madelung-as-structural-coupling finding from S5**: this is one of the most valuable entries. It says u = Im(conj(Psi) * Psi_x) makes m = 0 a structural identity, not a numerical constraint. Mark `depth: "structural"`.

7. **Aim for 15-25 entries** total. Quality over quantity — each entry should be actionable by an agent.

## Output format

After writing the bank file, also print:
- A 1-paragraph summary of the bank composition (counts by kind / depth / domain)
- The 5 most important entries (ids and one-line claims) for downstream agents

Tools available: Read, Write, Bash. Do not modify the source `knowledge_findings.json` files.
