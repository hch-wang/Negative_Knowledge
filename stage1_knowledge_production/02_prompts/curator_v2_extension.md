You are extending a structured knowledge bank with new Gardner-equation findings. The existing bank has 20 entries; you will produce an EXTENDED bank of approximately 30 entries.

# Inputs

## Existing bank (20 entries, do NOT modify or remove)
Read first to know what's already there:
`${PROJECT_ROOT}/stage1/knowledge_bank.jsonl`

These cover Burgers, KdV (including IMEX-CN positive + integrating-factor RK4 negative), Shallow Water, and three general-purpose entries.

## New Gardner stress tests (4 attempts, just completed)

For each `Gℕ`, read these files:
- `${PROJECT_ROOT}/stage1/sandboxes/Gℕ/meta.json`
- `${PROJECT_ROOT}/stage1/sandboxes/Gℕ/reasoning.md`
- `${PROJECT_ROOT}/stage1/sandboxes/Gℕ/result.json`

Gardner equation: `v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0` (KdV plus an extra cubic nonlinearity). This is the m=0 reduction of the coupled Burgers-swept-KdV system from Holm et al. 2025.

- G1 = Gardner / explicit RK4 only, IC amp 1.5
- G2 = Gardner / IMEX Crank-Nicolson spectral with 2/3 dealiasing, IC amp 1.5
- G3 = Gardner / IMEX-CN spectral, NO dealiasing, IC amp 1.5
- G4 = Gardner / IMEX-CN spectral, IC amp 3.0 (large amplitude, KdV-style sech^2)

Observed diagnostics (from result.json):
- G1: all-finite, peak at x=2.11 amp 1.506, 14 local maxima, mass conserved 3.000 — explicit RK4 with very small dt did NOT blow up, but soliton fragmented
- G2: all-finite, peak at x=-3.52 amp 0.612, 13 local maxima, mass 3.000 — IC was NOT a true Gardner soliton, so the wave radiates and breaks up even with good method
- G3: similar to G1 (peak 1.545, 11 maxima) — aliasing artifacts visible but not catastrophic at amp 1.5
- G4: ALL 256 NaN — IMEX-CN BLEW UP at amplitude 3.0 (with same dt that worked at amp 1.5)

# Your output

Write `${PROJECT_ROOT}/stage1/knowledge_bank.jsonl` containing **all 20 existing entries unchanged** plus **approximately 10 new entries** derived from the Gardner runs. Total target: **~30 entries (29-32 acceptable)**.

## What kinds of new entries to add (rough breakdown)

Aim for ~6 Gardner-specific entries (4 from G1-G4 + 2 syntheses) and ~3-4 cross-cutting entries that newly become possible because Gardner shows variant behavior:

**Gardner direct entries (one or two per stress test):**
- G1: positive or partial — "explicit RK4 on Gardner with small enough dt is finite but soliton fragments" (degree partial)
- G2: positive — "IMEX-CN-spectral is stable for Gardner at amp ~1.5; but IC matters — KdV-style sech^2 is NOT a Gardner soliton and radiates"
- G3: negative — "no dealiasing on Gardner is similar in failure-magnitude to no dealiasing on KdV at small amp; cubic v^2 v_x adds more aliasing channels"
- G4: NEGATIVE strong — "IMEX-CN explicit-on-nonlinear has an amplitude-dependent CFL: blowup at amp 3 with same dt that worked at amp 1.5"

**Cross-cutting / synthesized entries (use evidence from Gardner + existing bank):**
- "Sech^2 ICs are exact only for KdV; for Gardner, you must use the proper Gardner soliton parametrization or accept radiation."
- "The (3/2) v^2 v_x cubic term significantly tightens the nonlinear-explicit CFL constraint — methods that work for KdV may fail on Gardner at the same dt."
- "Gardner is the m=0 reduction of Burgers-swept-KdV. Numerical methods that destabilize Gardner will also destabilize the full coupled system in this reduction regime."
- "Mass conservation alone is not sufficient — G1 and G3 both have mass=3.000 but fragmented soliton structure (∴ verify peak amplitude and count, not just integrals)."

## Entry schemas (same as before)

### Positive
```json
{"id": "kb-XXX", "kind": "positive", "domain": "gardner | general", "claim": "...", "method": "...", "regime": "...", "evidence": [{"file": "absolute path", "summary": "..."}], "applicability": "..."}
```

### Negative
```json
{"id": "kb-XXX", "kind": "negative", "domain": "gardner | general", "attempted_route": "...", "observation": "...", "failure": {"layer": "...", "scope": "...", "degree": "...", "recommended_action": "...", "risk": "..."}, "rationale": "...", "evidence": [{"file": "absolute path", "summary": "..."}], "applicability": "..."}
```

# Requirements

1. Keep all 20 existing entries verbatim. Append your new entries at the end.
2. Each new entry must cite real evidence files (from G1-G4 paths above, or referring back to existing bank where appropriate).
3. Use schema fields consistent with existing entries (layer / scope / degree / recommended_action / risk taxonomy already established).
4. Make sure each new entry has a clear `applicability` field projecting onto the coupled Burgers-swept-KdV sub-tasks (especially the Gardner-reduction regime, soliton stability, and Gaussian decomposition tasks).
5. Total should be ~30 entries (29-32 acceptable).

# Hard agent rules

1. Use Read freely on the existing bank and the 4 Gardner sandboxes.
2. Use Write tool EXACTLY ONCE to overwrite knowledge_bank.jsonl with the FULL extended bank (existing 20 verbatim + new entries).
3. Do NOT use Bash, Edit, Grep, Glob.
4. After the single Write, respond with a brief summary: total entry count, breakdown by domain (gardner / kdv / burgers / shallow_water / general) and by kind (positive / negative).
