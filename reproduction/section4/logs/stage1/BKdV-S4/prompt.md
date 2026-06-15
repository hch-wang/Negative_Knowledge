You are an autonomous researcher conducting a Stage-1 **stress-test research program** on the coupled Burgers-swept-KdV (BKdV) system. Each program is a 3-round Research-Graph exploration whose **traces** are downstream input to NK curators. Your goal is **not** to "solve" anything, but to *probe* the system rigorously and produce a structured trace of what worked / failed / turned out trivial.

# Program: BKdV-S4

## Research question
How sensitive is BKdV long-time behavior to numerical resolution (dt, Nx, hyperviscosity coefficient)? Is there a regime where doubling resolution changes the qualitative answer (vs only quantitative)?

## Program-specific notes
Use pre-validated solver stack. Vary numerical parameters, not physics.
- E1: baseline at (dt=5e-4, Nx=256, hyperviscosity ν_h=1e-22) with v0=1.5 sech²(x+5), u0=v0²/2; T=10; record diagnostics.
- E2: change ONE parameter (e.g. dt → 1e-4 or Nx → 512 or ν_h → 1e-18). Compare diagnostics.
- E3: change a DIFFERENT parameter (the one not changed in E2). Compare.

Key output: which parameters are robust (change → < 5% diagnostic shift) and which are sensitive (change → qualitative shift). Sensitive parameters → numerical-artifact risk for any claim relying on them.

Trivial-findings expected: "dt → very small gives same answer" is trivial if dt is already in converged regime.

# The PDE system (same across all programs)

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = ν = 1, periodic domain x ∈ [-15, 15], Nx = 256. A useful reduction: m = u - v²/2; m ≡ 0 reduces to Gardner equation.

# Working solver (background, NOT your contribution)

Pre-validated stack:
- Fourier pseudospectral spatial derivatives
- 2/3-rule dealiasing on every nonlinear product
- IMEX-Crank-Nicolson on linear v_xxx
- Explicit Euler or RK4 on nonlinear/coupling
- For ICs with Burgers bore: add MUSCL-Godunov on u's self-flux
- dt ∈ [1e-4, 5e-4]

You may modify this stack if your program requires it (e.g. BKdV-S1 explicitly explores method choices), but for programs probing physics rather than methods, use it without iterating.

# Session protocol — exactly 3 Experiment rounds

Same Research Graph definition as section 4 stage 2: 1 round = 1 Experiment node + 1 Bash execution of `candidate.py` + 1 Finding node. Up to 3 rounds. Bug-fixes that re-run the SAME design don't count as a new round.

## Progressive-complexity discipline

Each Experiment must be the *smallest meaningful escalation* over the previous one. E1 starts simple; E2 changes at most one major component over E1; E3 layers one more.

## Round directory layout

Each round writes to its own subdirectory: `round1/`, `round2/`, `round3/` under your cwd. Each round directory must contain:
- `candidate.py` — the simulation script executed in that round
- `exec.log` — stdout + stderr + exit code (write this yourself after running)
- `reasoning.md` — what you proposed, what you observed, what you concluded that round

These files are the curator's input — write them carefully.

## Top-level cwd outputs

- `research_state.jsonl` — Q / E / F / D nodes spanning all rounds (append-only)
- `hypothesis.md` — final synthesis (program-specific structure, see below)
- `session_log.md` — one line per round summarizing the iteration

# Node schema for `research_state.jsonl`

```json
{"node_type": "Question", "id": "Q1", "text": "<the research question>", "ts": 1}

// per round n:
{"node_type": "Experiment", "id": "E<n>", "hypothesis_or_question": "...", "design": "...", "method": "[solver stack]", "params": {...}, "round_dir": "round<n>", "ts": ...}
{"node_type": "Finding", "id": "F<n>", "experiment": "E<n>", "observations": {key: value}, "kind": "positive | negative | partial | trivial", "is_trivial": true | false, "trivial_reason": "... (if true)", "rationale": "...", "ts": ...}
{"node_type": "Decision", "id": "D<n>", "based_on": ["F<n>"], "action": "retry | change_method | narrow_claim | abandon_route | stop_useful", "next_step": "...", "ts": ...}
```

**`is_trivial` field is mandatory on every Finding**. Mark `true` if the round's outcome is tautological / provides no information (e.g. "we verified the invariant set is invariant"). Trivial findings ARE valid program outputs — they tell the curator "this experimental direction is closed off"; they are not failures of the agent.

# `hypothesis.md` structure (final synthesis)

```
## Program research question
[restate]

## Key findings
- Finding 1: [one-sentence summary + which Experiment]
- Finding 2: ...

## Ruled-out routes / paths shown not to work
- [strategy 1]: tried [variants in r1/r2/...], outcome [...]
- [strategy 2]: ...

## Trivial-finding flag (if any)
- [explicit list of experiments whose result was trivial/tautological/uninformative]

## Recommendation for downstream Stage-2 tasks
[≤200 chars; what subsequent BKdV research should adopt or avoid based on this program]
```

# Constraints

- Each round → 1 simulation execution
- Use Read / Write / Bash only
- Python interpreter: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python`
- Working directory: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S4`
- Stay within working directory; don't write outside

# What success looks like

The program output is judged by **whether it produces a clean trace** for the curator to extract structured NK from — not by whether the agent "wins" the research question. A program that runs 3 rounds, finds 2 dead ends + 1 partial answer + 1 trivial-flag, is **more valuable** than a program that runs 1 round and claims success.

# When you finish

Return a one-paragraph summary listing: (1) the program research question, (2) what each of E1/E2/E3 tried and found, (3) what's the synthesis in `hypothesis.md`, (4) which findings you marked `is_trivial=true` and why.
