# Parent Decision Log

> Parent = the human + LLM orchestrator that runs **outside** the sub-agents.
> This file records the *why* behind the experimental design choices, in chronological order.
> All decisions originally lived in chat transcripts; they are fixed here for auditability.

---

## A. Pre-PDE-pilot phase (early BKdV cases)

### A1. Why PDE numerical methods as case studies at all?
We were writing a workshop short paper on a *negative-knowledge memory layer* for autoresearch. Earlier evidence on ScienceAgentBench tasks showed structured memory had moderate effects on toy benchmark failures (schema mismatch, missing-library substitution). The reviewer-style critique was: "this is all software/library failures, not real research failures." We chose PDE numerical method selection because (a) real research-style decisions, (b) clear failure modes (NaN / oscillation / mass drift / wrong soliton speed), (c) maps cleanly to schema fields like `layer = method_failure` and `scope = regime_bound`.

### A2. Why the Burgers-swept-KdV system specifically?
We followed Holm et al. 2025 (arXiv:2505.17026). Reasons: (1) coupled system with two scientifically distinct components (Burgers shock + KdV dispersion), forcing the agent to handle *multi-component* numerical decisions; (2) compound soliton solutions are documented, so we have *qualitative* targets; (3) the m=0 reduction gives Gardner — a useful intermediate.

### A3. Why two pilots (BKdV-T1 Burgers + BKdV-T2 KdV) before Stage 1?
We needed (a) one positive control (Burgers shock; should be tractable) to validate the pipeline, and (b) one stiffness test (KdV with v_xxx) to confirm we could detect interesting failure modes. T2 round-1 NaN → round-2 IMEX PASS became Case G — a clean repair narrative.

---

## B. Stage 1 design phase

### B1. Why 14 stress tests, not 5 or 30?
Initial plan was ~5 (one per component PDE). User pushed for "until we have ~20 entries." We expanded to 10 (3 Burgers + 3 KdV + 4 SW) then added 4 Gardner to reach the target. Resulting bank of 30 entries comes from 14 sub-agent runs + curator synthesis (mostly 1 entry per run, plus 3 cross-cutting synthesis entries).

### B2. Why force agents to use **basic** methods even when they know better?
Sub-agents asked to "solve a PDE" naturally choose IMEX spectral. That produces almost no `negative` knowledge. To populate the negative-knowledge side of the bank, we explicitly forbid advanced methods in prompts ("you MUST use forward Euler + central FD; NO TVD; NO limiter"). Without these forced-method constraints, Stage 1 would produce ~10 positive entries and zero negatives.

### B3. Why parameter-regime tests (A2, A3, A6, etc.) and not only method tests?
Stage 2 sub-tasks all involve IC/parameter choices that themselves can yield negative outcomes (Gaussian too narrow → aliasing; T too short → no phenomenon). The bank needs entries about *parameters* not just *methods*, so we added A2 (short T), A3 (long T), A6 (small amplitude).

### B4. Why a separate Curator agent?
We could have parent-side rule-based extraction, but: (a) parent-side rules are brittle (each PDE has its own diagnostic), (b) agent-side curation is itself a research artifact — the bank reflects what a researcher would naturally write. We accept the trade-off that curator has some hallucination risk and mitigate with parent audit (every cited evidence file must actually exist).

### B5. Why three curator passes (v1 → +4 Gardner → +2 top-up) instead of one?
v1 ran on the original 10 stress tests + 3 BKdV pilots. After we added Gardner (G1-G4), we needed to extend. The third pass was administrative: we wanted exactly ~30 entries and the second pass produced 28.

### B6. Bank format (JSONL with positive/negative kinds) instead of e.g. RDF / graph DB?
JSONL is human-readable, line-addressable, diff-friendly, and the only inter-agent communication format we need. Each entry is self-contained with `evidence[]` pointing to source files. Schema is flat (no nested relations) which matches what an agent can produce and a downstream agent can consume.

---

## C. Stage 2 design phase

### C1. Why three conditions (NoKB / PosOnly / PosNeg)?
Two-condition (NoKB vs PosNeg) would let us measure "any bank vs no bank." Three-condition lets us isolate the *negative* contribution. The PosOnly vs PosNeg gap measures specifically what negative entries add. This turned out to be crucial — the most striking result is *PosOnly ≈ NoKB ≈ 0%* while *PosNeg = 67%*.

### C2. Why allow 3 rounds of internal iteration per cell?
A single attempt would conflate "good method on first try" with "lucky guess." Multi-round lets us measure *attempts to useful result*, which is the right capacity-aware metric. We chose 3 rounds as compromise between budget and depth — empirically, after r2 the agent's space of new methods to try contracts.

### C3. Why phenomenon-based eval and not L2 error to reference?
No closed-form reference exists for the full coupled BKdV system (paper has only compound-soliton solutions in special cases). Phenomenon checks (peak count, mass conservation, amplitude bounds) are deterministic but allow multiple "correct" numerical paths. This is also closer to how a working scientist would judge "did the simulation give a meaningful result."

### C4. Why the specific edge-case ICs (non-pure m=0 in T_A, narrow Gaussian in T_B, sharp bore in T_C)?
Calibrated *for differentiation*. If the IC is too easy, all three conditions PASS at round 1 and we have no signal. If too hard, all fail in all rounds. Edge cases are designed (using parent's domain knowledge of which Stage 1 entries are relevant) so a knowledgeable agent (PosNeg) can succeed by combining the right method choices, while a naive agent (NoKB) cannot.

### C5. Why no re-calibration after round 1?
After r1 we observed PosNeg 2/3 vs NoKB+PosOnly 0/3 — sufficient differentiation. Re-tuning IC mid-experiment would invalidate the comparison.

### C6. Why no condition × model crossover (e.g., NoKB Sonnet vs PosNeg Sonnet)?
Single subject model (Sonnet 4.6) across all 9 cells. Mixing models would conflate condition effect with capability. Future work could add Opus 4.7 or Haiku 4.5 as a separate experiment.

### C7. Why r2/r3 receive both bank AND internal r1/r2 finding?
The point of memory comparison is the *external* bank. Internal memory (this agent's own previous failure) is allowed in all three conditions equally — otherwise NoKB would be stuck without any feedback signal at all. Differential effect we measure is exclusively from Stage 1 bank.

---

## D. Termination decisions

### D1. Why stop at r3?
Pre-registered upper bound. Even if some cells were "close" (T_A NoKB r2 had amp_ratio 0.48 vs 0.50 threshold), continuing iteration would not have changed the qualitative finding (PosNeg dominates).

### D2. Why not retry T_B with revised IC after Stage 2?
T_B failed in all conditions including PosNeg. This is an honest *negative* finding: the bank's coverage of nonlinear-CFL for large-amplitude Gaussian was qualitative, not quantitative. We chose to report this honestly rather than re-tune the IC to make PosNeg succeed. It strengthens the paper because it shows the limits of bank-driven autoresearch.

### D3. Why three-curator-pass for exactly 30 entries instead of accepting 28?
User-requested round number. Marginally more bank content, no harm.

---

## E. Anti-patterns avoided

1. **Did not let curator agent see Stage 2 task descriptions.** The curator only saw Stage 1 stress-test artifacts. Otherwise it could write entries specifically tuned to Stage 2 ICs, leaking the answer.
2. **Did not include candidate.py from successful Stage 1 runs as part of Stage 2 prompts.** Only bank entries (text-form claims with evidence). Otherwise PosNeg would essentially be receiving working code.
3. **Did not extract any "what would have worked" hindsight into Stage 1 negative entries.** All `recommended_action` fields come from agent reasoning + curator's reading of what failed, not from later success knowledge.
4. **Did not bank-aware build Stage 2 r2/r3 prompts.** R2 and R3 build scripts are condition-agnostic; the bank content used is exactly the same as r1, modulo whatever round-N internal failure traces appear.

---

## F. Resource discipline

- Total **43 sub-agent calls** (3 early pilot + 17 Stage 1 + 23 Stage 2). All single-model (Sonnet 4.6). Tokens ~940k. Wall ~80 min.
- No parallel batches exceeded 14 calls (Stage 1 stress tests). No serialized cell ran more than 3 rounds.
- Every candidate.py was actually executed and its output evaluated.
