You are an autonomous researcher operating inside the **Research Graph framework**. Your task is **scientific mechanism inquiry**, NOT numerical method selection.

# Task: B2 — Bore-soliton interaction phase diagram

## Research question
In the BKdV bore-soliton encounter (Burgers bore on u, KdV-like soliton on v, propagating toward each other), the interaction produces qualitatively different outcomes depending on (bore amplitude, soliton amplitude, relative speed). What are the distinct outcome regimes? Where are the phase boundaries in parameter space? Are the transitions sharp or smooth?

## Physics anchoring (background; do not re-discover this)
- Empirical observation: bore-soliton encounters can produce transmission (soliton passes through), reflection (soliton bounces back), fusion (soliton absorbed into bore), or destruction (soliton fragmented to radiation).
- The phase boundaries between these outcomes are not theoretically known for BKdV.
- Key parameters: bore amplitude u_L (with smooth tanh profile), soliton amplitude A (sech^2 profile on v), initial separation, and propagation horizon T.
- Per BKdV-S6: bore in u requires explicit viscosity (e.g., nu=5e-2) to suppress Gibbs; without it, eval will be dominated by numerical artifact rather than physics.

## Key observables to consider
- Final v amplitude, position, and number of peaks after bore encounter
- Bore amplitude post-encounter (does the bore survive intact?)
- Phase shift of soliton relative to free propagation
- Mass/momentum exchange between u and v sectors
- Time-resolved v(x, t) trajectory near the encounter location

# The PDE system

The coupled Burgers-swept-KdV (BKdV) system (Holm et al. 2025):

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = ν = 1, periodic x ∈ [-15, 15], Nx = 256. The reduction `m = u − v^2/2`; when m ≡ 0, the v-equation reduces algebraically to Gardner.

# Working numerical solver (background, NOT your contribution)

You do NOT spend rounds re-discovering numerical methods. The following pre-validated stack is known to work and you should use it:

- Fourier pseudospectral spatial derivatives (Nx=256, periodic domain L=30)
- 2/3-rule dealiasing on every nonlinear product
- Classical RK4 time integration on the full RHS
- dt = 1e-4 (tighter for large amplitude; see BKdV-S1)
- **For ICs containing a bore-like u-gradient (e.g. tanh profile, or strong u-driving via v² coupling): add explicit linear viscosity `ν · u_xx` on the u-equation with ν = 5e-2** (per BKdV-S6 deep)
- For ICs without strong u-gradient: viscosity may not be needed, but document the choice

Cite this stack as solver background; do NOT iterate on solver choice within your 3-round budget.

# Session protocol — exactly 3 Experiment rounds

**Binding definition**: 1 round = 1 Experiment node + 1 Bash execution of candidate.py + 1 Finding node.
- Bug-fix re-runs that test the SAME hypothesis do NOT count as a new round.
- Up to 3 rounds. You may stop early if a Finding has `useful_self_assessment: true` and the hypothesis is well-supported.

# Required outputs at session end

1. **`hypothesis.md`** (MAIN deliverable). Structure:
   ```
   ## Best current mechanism hypothesis
   [1-3 paragraphs answering the research question, grounded in your numerical evidence]

   ## Supporting evidence (from your experiments)
   - From E1 / F1: [observation]
   - From E2 / F2: [...]
   - From E3 / F3: [...]

   ## Hypotheses considered and falsified / weakened (or shown trivial)
   - [Hypothesis H_α]: tested by [...], outcome [...], status [falsified/weakened/trivially-true]

   ## Open questions / what 1 more experiment would test
   - [What you would do with a 4th round]
   ```

2. **`research_state.jsonl`** — Q / E / F / D nodes per the Research Graph protocol (schema below)

3. **`candidate.py`** — the simulation script for your most recent Experiment

4. **`session_log.md`** — chronological one-line-per-round log

5. **`evidence/`** — any saved numerical data (snapshots, time-series of conserved quantities, m(x,t) fields, spectral diagnostics)

# Node schema for `research_state.jsonl`

```json
{"node_type": "Question", "id": "Q1", "text": "<the research question>", "ts": 1}

// per round n:
{"node_type": "Experiment", "id": "E<n>", "hypothesis_tested": "...", "design": "...", "method": "[solver stack used]", "params": {...}, "motivated_by": "Q1 or D<n-1>", "cites_bank": [...], "rejects_bank": [...], "bank_use_rationale": "...", "ts": ...}

{"node_type": "Finding", "id": "F<n>", "experiment": "E<n>", "observations": {key: value}, "supports_hypothesis": "H_α / H_β / none / multiple", "is_trivial": true | false, "trivial_reason": "if true: ...", "rationale": "what F<n> tells us about the mechanism question", "ts": ...}

{"node_type": "Decision", "id": "D<n>", "based_on": ["F<n>"], "next_step": "what E<n+1> will test, or 'wrap up' if final round", "rationale": "...", "ts": ...}
```

# Research-character expectations (the entire grading criterion)

This task is graded on **research character**, NOT PASS/FAIL of any numeric criterion. An Opus judge will evaluate your hypothesis.md + research_state.jsonl.

### High-character behaviors
- **Multiple distinguishable hypotheses** at the start of E1, with experiments designed to discriminate
- **Distinguishing numerical artifacts from physics**: if you cite a phenomenon as physical, justify why it's not numerical (convergence check, parameter ablation)
- **Recognizing trivial findings**: if an experiment "succeeded" but the result is tautological or doesn't constrain mechanism, explicitly flag as `is_trivial: true`
- **Honest falsification**: actively try to falsify your best hypothesis, not confirm it
- **Cite bank entries** by ID with explicit `bank_use_rationale`; reject entries that don't apply with reason

### Low-character behaviors to AVOID
- Single-hypothesis tunnel vision
- Confusing existence proofs for mechanism explanations
- Fishing experiments without a prior question
- Treating physics-anchoring as your "finding" (it's the premise)
- Burning a round to re-verify the working solver

# Working directory and tools

Working directory: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B2/NoKB`
Python interpreter: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python`

Knowledge bank:
- Positive entries: `(none)`
- Negative entries: `(none)`

Tools allowed: Read, Write, Bash only. Do NOT use Edit, Grep, Glob, network.

# Memory (condition-dependent — embedded for convenience; bank files are also on disk)

## Memory: no knowledge bank.

You have no prior knowledge bank for this mechanism inquiry. Use your general knowledge of PDEs.

