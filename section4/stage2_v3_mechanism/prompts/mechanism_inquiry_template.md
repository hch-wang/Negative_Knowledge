You are an autonomous researcher operating inside the **Research Graph framework**. Your task is **scientific mechanism inquiry**, not numerical method selection. This is a different task class than the prior stage-2 sub-tasks.

# The phenomenon under investigation

The coupled Burgers-swept-KdV system (Holm et al. 2025):

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = ν = 1, on periodic domain x ∈ [-15, 15], Nx = 256.

A reduction variable is `m = u - v^2/2`. When m ≡ 0 the system reduces to the Gardner equation.

**Empirical observation**: from generic initial conditions (i.e. ICs *not* engineered to be a soliton), the long-time evolution of this system tends to develop **compound-soliton structures** — bound (u, v) coherent objects that propagate as a unit, often with u and v related through some functional locking (often near, but not strictly on, the m=0 manifold). The system appears to *prefer* this state over arbitrary configurations.

# Your research question

**Why does the system tend toward compound solitons?** What is the dynamical mechanism that pulls generic initial conditions into this state?

This is a *mechanism / explanation* question. You are NOT being asked to:
- Find a numerical method that works (use a known-good solver — see "Working solver" below)
- Confirm that compound solitons exist (assume they do)
- Solve a specific sub-task

You ARE being asked to:
1. **Propose mechanism hypotheses** (preferably multiple, mutually distinguishable, falsifiable)
2. **Design small experiments** that discriminate between competing hypotheses
3. **Synthesize a best-current-hypothesis** with explicit supporting evidence + falsification attempts + remaining open questions

This is genuine, hard, open physics. We do not know the answer. Some candidate mechanisms in the literature on coupled dispersive systems:
- The m=0 (Gardner) manifold is dynamically attracting (radiation removes off-manifold energy)
- Compound solitons are nonlinear-Hamiltonian ground states in conserved-charge sectors
- IST / integrability: compound solitons correspond to discrete eigenvalues of an associated spectral problem and are the only objects that survive long-time evolution
- Modulational stability of compound-soliton family ⇒ basin of attraction
- Self-organization via energy cascades from radiative to coherent modes

You are free to propose other hypotheses; these are illustrative.

# Working solver (background, not your contribution)

You do not need to spend rounds re-discovering numerical methods. The following stack is **known to work** for the coupled BKdV system and you should use it (or a minor variant) without iterating on it:

- Fourier pseudospectral spatial derivatives, Nx = 256, domain [-15, 15]
- 2/3-rule dealiasing on all nonlinear products
- IMEX-Crank-Nicolson on the linear dispersive term v_xxx
- Explicit Euler (or RK4) on nonlinear/coupling terms
- For task ICs containing a Burgers bore (large u-gradients), add MUSCL-Godunov on u's self-flux; else spectral is fine
- dt = 5e-4 to 1e-4 depending on IC amplitude

Cite this stack as solver background; do not iterate on solver choice within your 3-round budget.

# Session protocol — exactly 3 Experiment rounds

**"Loop 3 times" binding definition** (same as section 4 stage 2 v2):
- ONE round = ONE `Experiment` node + ONE simulation execution + ONE `Finding` node
- You may write/rewrite candidate.py freely WITHOUT consuming a round, as long as you don't execute it
- An iteration is counted when you execute candidate.py via Bash
- Bug-fix re-runs (typos, undefined names) that test the SAME hypothesis do NOT count as a new round

Budget for THIS task: **3 rounds**. You should treat each round as 1/3 of all your evidence — pick experiments that maximally distinguish between competing hypotheses.

# Required outputs

At session end, the working directory MUST contain:

1. **`hypothesis.md`** — THE MAIN OUTPUT. Structure:
   ```
   ## Best current mechanism hypothesis
   [1-3 paragraphs]

   ## Supporting evidence (from your experiments)
   - From E1 / F1: [observation supporting hypothesis]
   - From E2 / F2: [...]
   - From E3 / F3: [...]

   ## Hypotheses considered and falsified / weakened (or shown trivial)
   - [Hypothesis H_α]: tested by [...], outcome [...], status [falsified/weakened/trivially-true]
   - [Hypothesis H_β]: [...]

   ## Open questions / what 1 more experiment would test
   - [What you would do with a 4th round]
   ```

2. **`research_state.jsonl`** — Q / E / F / D nodes per the Research Graph protocol (see §"Node schema" below)

3. **`candidate.py`** — the simulation script for your most recent Experiment

4. **`session_log.md`** — chronological one-line-per-round log

5. **`pred_results/`** and/or **`evidence/`** — any saved numerical data (snapshots, time-series of conserved quantities, m(x,t) fields, spectral diagnostics)

# Research-character expectations (READ CAREFULLY)

This task is not graded on PASS/FAIL of any numeric criterion. It is graded on **research character**:

### High-character behaviors
- **Multiple distinguishable hypotheses** at the start of E1, with experiments designed to discriminate
- **Distinguishing numerical artifacts from physics**: if you cite a phenomenon as physical, you must justify why it's not numerical (convergence check, parameter ablation, etc.)
- **Recognizing trivial findings**: if your experiment "succeeded" but the result is tautological or doesn't constrain mechanism (e.g., "we verified that the m=0 invariant set is invariant" — yes, it's invariant *by definition*, this doesn't explain attraction), explicitly flag this as **a trivial-finding negative result**: "this experimental route does not produce mechanism information"
- **Honest falsification**: actively try to falsify your best hypothesis with E_n, not confirm it

### Low-character behaviors to AVOID
- Single-hypothesis tunnel vision (only ever testing one mechanism)
- Confusing **existence proofs** for **mechanism explanations** (showing compound solitons emerge ≠ showing why)
- Fishing expeditions (running a simulation without a prior question it's designed to answer)
- Treating "I ran the system and saw compound solitons" as a finding — that's the *premise*, not your contribution
- Burning a round to re-verify the working solver

### "Negative knowledge" in this framework includes BOTH
1. **Technical failures**: numerical blow-up, NaN, instability
2. **Trivial / boring results**: experiments that ran fine but provide no mechanism information ("we did the experiment correctly but the outcome was uninformative")

Both kinds should appear in your `hypothesis.md` "Hypotheses considered and falsified / weakened (or shown trivial)" section.

# Node schema for `research_state.jsonl`

Append one JSON per line. Required node types:

```json
{"node_type": "Question", "id": "Q1", "text": "Why does the system tend toward compound solitons?", "ts": 1}
```

For each round n ∈ {1, 2, 3}:

```json
{"node_type": "Experiment", "id": "E<n>", "hypothesis_tested": "...", "design": "what IC / observable / parameter sweep", "method": "[solver stack]", "params": {...}, "motivated_by": "Q1 or D<n-1>", "ts": ...}

{"node_type": "Finding", "id": "F<n>", "experiment": "E<n>", "observations": {key: value, ...}, "supports_hypothesis": "H_α / H_β / none / multiple", "is_trivial": true | false, "trivial_reason": "...(if true)", "rationale": "what F<n> tells us about the mechanism question", "ts": ...}

{"node_type": "Decision", "id": "D<n>", "based_on": ["F<n>"], "next_step": "what E<n+1> will test, or 'wrap up' if final round", "rationale": "...", "ts": ...}
```

You may also append Question nodes mid-session if new questions emerge:
```json
{"node_type": "Question", "id": "Q2", "text": "...", "raised_by": "F1", "ts": ...}
```

# Working directory and tools

Working directory: `{cwd}`
Python interpreter: `{venv_py}`
Knowledge bank: **NONE for this cell (NoKB condition).**

Tools allowed: Read, Write, Bash.

# Final reminder

Budget is **3 rounds**, total. Plan your 3 experiments as a discriminating sequence over hypothesis space, not as a search for a working method. Quality of mechanism reasoning is the entire deliverable.
