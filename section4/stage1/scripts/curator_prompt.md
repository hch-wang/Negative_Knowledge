You are a research-knowledge curator. Your task: read a set of PDE numerical experiment artifacts and produce a structured JSONL **knowledge bank** of positive and negative findings that future agents can use when studying coupled Burgers-swept-KdV systems.

# Inputs (13 attempts total)

## Stage 1 stress tests (10 attempts, all on basic methods or edge parameters)

For each `Aℕ`, read these files:
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/stage1/sandboxes/Aℕ/meta.json`  (task spec, predicted outcome)
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/stage1/sandboxes/Aℕ/reasoning.md`  (agent's reasoning)
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/stage1/sandboxes/Aℕ/result.json`  (observed numerical outcome with diagnostics)

The 10 Stage-1 tests, in summary:
- A1 = Burgers / forward Euler + central diff
- A2 = Burgers / T=0.1 (pre-shock)
- A3 = Burgers / T=10 (long-time)
- A4 = KdV / explicit RK4
- A5 = KdV / Fourier spectral, NO dealiasing
- A6 = KdV / very small amplitude IC (0.1)
- A7 = Shallow water / forward Euler + central diff
- A8 = Shallow water / Lax-Friedrichs
- A9 = Shallow water / dry-bed IC
- A10 = Shallow water / HLL Riemann solver

## Prior pilot data (3 attempts)

Also read these to extract knowledge:

1. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/runs/burgers_T05/sonnet_4.6/round1/reasoning.md`
   `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/runs/burgers_T05/sonnet_4.6/round1/result.json` (if present, otherwise check exec.log)
   Context: Burgers T=0.5 with MUSCL+Godunov+Euler → PASS (L1 error ~0.003).

2. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/runs/kdv_T2/sonnet_4.6/round1/failure_record.json`
   `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/runs/kdv_T2/sonnet_4.6/round1/reasoning.md`
   Context: KdV T=2 with Fourier + integrating-factor RK4 → ALL-NaN BLOW-UP.

3. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/runs/kdv_T2/sonnet_4.6/round2_M4/reasoning.md`
   `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/runs/kdv_T2/sonnet_4.6/round2_M4/result.json`
   Context: KdV T=2 with Fourier + IMEX-CN → PASS (peak at x=3.05, amp=2.03, mass=4.000).

# Your output

Write ONE file via the Write tool:
`/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/stage1/knowledge_bank.jsonl`

It contains 18–22 JSONL entries. Each line is one JSON object. Two kinds of entries:

## Positive entry schema
```json
{
  "id": "kb-XXX",
  "kind": "positive",
  "domain": "burgers | kdv | shallow_water | general",
  "claim": "specific factual claim about what worked numerically",
  "method": "name of the numerical scheme",
  "regime": "parameter / IC regime where this was observed",
  "evidence": [
    {"file": "absolute_path_to_source_artifact", "summary": "what it shows in <= 20 words"}
  ],
  "applicability": "where this knowledge would transfer to in future PDE work (especially coupled Burgers-swept-KdV problems)"
}
```

## Negative entry schema
```json
{
  "id": "kb-XXX",
  "kind": "negative",
  "domain": "burgers | kdv | shallow_water | general",
  "attempted_route": "what was tried (method + parameter regime)",
  "observation": "what actually happened (cite specific numerical signature)",
  "failure": {
    "layer": "implementation_failure | method_failure | measurement_failure | hypothesis_failure",
    "scope": "local_failure | regime_bound | general_failure",
    "degree": "contradicted | partial | inconclusive | unstable | artifact_driven | overclaimed",
    "recommended_action": "retry | change_method | narrow_claim | abandon_route",
    "risk": "low_risk_omission | medium_risk_drift | high_risk_false_progress"
  },
  "rationale": "1-2 sentences on why it failed; do not pretend to have proven a theorem",
  "evidence": [
    {"file": "absolute_path_to_source_artifact", "summary": "<= 20 words"}
  ],
  "applicability": "what kinds of future problems should heed this; especially relevance to coupled Burgers-swept-KdV"
}
```

# Requirements / constraints

1. Write **18–22 entries total**, spanning all 3 PDE families. Don't go under 18 (we need richness).
2. Every entry must have at least one `evidence` block citing a real file from the list above. Do NOT cite files you didn't read.
3. Both positive and negative entries should exist; aim for roughly 6–8 positive, 12–14 negative.
4. The 10 Stage-1 tests + 3 prior pilots together = 13 attempts. You can produce more than 13 entries by:
   - splitting a single attempt into multiple distinct knowledge claims (e.g., one entry about "method choice" + one about "parameter regime")
   - writing "synthesized" entries that draw across multiple attempts (e.g., "shock-forming PDEs all need flux limiters" — cites A1 + A7 as evidence)
5. Use the applicability field to project each entry onto the coupled Burgers-swept-KdV target (sub-task hints: soliton stability, Gaussian decomposition into soliton train, Burgers bore × soliton interaction).
6. Negative entries about method failures should map `recommended_action` to one of: retry / change_method / narrow_claim / abandon_route. Be specific.
7. For the prior KdV IFRK4 blow-up (file 2 above), include a NEGATIVE entry; for the IMEX-CN success (file 3), include a POSITIVE entry — these are the "seed" entries.
8. Do NOT include any positive entry that claims success without evidence (e.g., do not claim "ETDRK4 works" if nobody ran ETDRK4 here).
9. Each entry id should be readable, e.g. `kb-burgers-fwdEuler-Gibbs`.

# Hard agent rules

1. Use Read freely on the 13 input files listed.
2. Use Write tool EXACTLY ONCE to produce `knowledge_bank.jsonl` (newline-separated JSON, one entry per line).
3. Do NOT use Bash, Edit, Grep, Glob.
4. After the single Write, respond with a brief summary: how many entries you wrote, breakdown by domain and by kind.
