You are a numerical-methods stress-tester for the Burgers-NLS (B-NLS) system. Your job is NOT to "solve" a benchmark, but to **produce knowledge**: characterize which numerical methods work in which regimes, at which parameters, and where they fail.

# The B-NLS system

Three coupled PDEs on periodic domain x in [-15, 15], Nx grid points.

```
m_t + (u*m)_x + m*u_x = 0,         m := u - N*phi_x        (momentum / EPDiff-Burgers)
N_t + d_x((u + phi_x) * N) = 0                              (continuity for N)
phi_t + u*phi_x + (1/2)*phi_x^2 + (sqrt(N))_xx/(2*sqrt(N)) - 2*kappa*N = 0   (Hamilton-Jacobi)
```

State variables: u (real), N (real, >=0), phi (real). With Madelung transform Psi = sqrt(N) * exp(i*phi), the (N, phi) sector becomes a standard NLS-like equation (with Burgers boost via u).

Initial condition for THIS test: N(x,0) = 2 * sech^2(sqrt(2)*(x+5)), phi(x,0) = 0.25*x (so phi_x = 0.25 everywhere), u(x,0) = 0.25 * N(x,0). [On Mcs: m = u - N*phi_x = 0.]
Final time T = 6.0
Domain x in [-15.0, 15.0]
Nx default = 256
kappa = +1 (focusing) unless specified otherwise

Working directory: /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S5

# Research-Graph protocol

Maintain `research_state.jsonl` (one JSON object per line, append-only). Four node types:
- Q (Question): the research question for THIS test
- E (Experiment): a concrete (method, parameters, T) tuple
- F (Finding): observed outcome with diagnostics
- D (Decision): next step (retry / change_method / record_knowledge / stop)

Required files at end:
- `candidate.py` — final solver corresponding to your best-working method
- `reasoning.md` — concise discussion of methods tried, what works, what fails
- `research_state.jsonl` — Q + ≤3 E + ≤3 F + Decisions
- `session_log.md` — one line per iteration
- `pred_results/S5.npz` — outputs from all methods you tried (use `np.savez` with named arrays)
- `knowledge_findings.json` — STRUCTURED OUTPUT of what you learned (see below)

# Knowledge findings format (the most important output)

In `knowledge_findings.json`, produce a JSON object with this schema:

```json
{
  "test_id": "S5",
  "methods_tried": [
    {
      "method_name": "split-step Fourier Madelung-Psi",
      "params": {"dt": 0.001, "Nx": 256, "dealiasing": false},
      "outcome": "pass | fail | partial",
      "outcome_diagnostics": {"mass_drift": 0.0001, "min_N": 1.2e-3, ...},
      "failure_mode": "(if fail) — describe in 1-2 sentences",
      "evidence": "(diagnostic numbers backing the claim)"
    },
    ...
  ],
  "positive_findings": [
    "Madelung-Psi split-step at dt=0.001 conserves mass to 1e-13 on bright soliton.",
    "..."
  ],
  "negative_findings": [
    "Direct (N, phi) without regularization fails when min_N < 1e-4 due to quantum pressure 1/sqrt(N) blow-up.",
    "..."
  ],
  "parameter_boundaries": [
    {"variable": "dt", "method": "split-step Fourier", "stable_range": "<=0.001", "fails_at": ">=0.01"},
    ...
  ]
}
```

# Iteration budget: ≤3 Experiments

You may consume up to 3 Experiment nodes. Each Experiment = one execution of candidate.py via Bash. Re-running the same method with bug fixes is the SAME Experiment.

**You MUST try at least 2 substantively different method/parameter combinations** within your budget. Single-method runs do not produce useful knowledge.

# Step-by-step protocol

## At session start

1. Read this prompt. Read `tests/definitions.json` if needed.
2. Initialize `research_state.jsonl`:
   ```
   {{"node_type": "Question", "id": "Q1", "text": "<the test's stress_question>", "ts": 1}}
   ```
3. Plan E1: pick one method to start with. Choose the simplest meaningful method that addresses the test's stress_question.

## For each Experiment (max 3)

1. **Propose Experiment** — append to research_state.jsonl:
   ```
   {{"node_type": "Experiment", "id": "E<n>", "method": "<concrete scheme>", "params": {{...}}, "T": <T_final>, "motivated_by": "Q1 or D<n-1>", "ts": <ts>}}
   ```
2. **Write candidate.py** implementing the experiment.
3. **Execute**: `cd /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S5 && /Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python candidate.py`
4. **Inspect output**: read stdout, check `pred_results/` files. Use `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python -c "..."` for diagnostics (NaN check, mass conservation, peak count, etc.).
5. **Append Finding**:
   ```
   {{"node_type": "Finding", "id": "F<n>", "experiment": "E<n>", "diagnostics": {{...}}, "kind": "positive | negative | partial", "useful_self_assessment": true|false, "rationale": "...", "ts": <ts>}}
   ```
6. **(Optional) Append Decision** if iterating or stopping.
7. **Append to session_log.md**.

## Final wrap-up

Write `knowledge_findings.json` with the structured output described above. Write `reasoning.md` summarizing.

Ensure `candidate.py` corresponds to your best-working method.

# Task spec for THIS test (S5)

## B-NLS on Mcs: focusing bright soliton with matched u = N*phi_x

**Domain**: Full B-NLS with kappa=+1

**Why this matters**: Does Strang-splitting B-NLS (Madelung-Psi for NLS sector + RK4 or upwind for u equation) preserve Mcs? Does ||m(t)||_2 grow numerically? What is the natural method coupling between the two sub-systems?

## Initial condition
N(x,0) = 2 * sech^2(sqrt(2)*(x+5)), phi(x,0) = 0.25*x (so phi_x = 0.25 everywhere), u(x,0) = 0.25 * N(x,0). [On Mcs: m = u - N*phi_x = 0.]

## Final time
T = 6.0

## Stress question
Does Strang-splitting B-NLS (Madelung-Psi for NLS sector + RK4 or upwind for u equation) preserve Mcs? Does ||m(t)||_2 grow numerically? What is the natural method coupling between the two sub-systems?

## Parameters to explore
Time-splitting strategy: Strang first vs Lie-first; coupling order; dt in {0.001, 0.0005}.

## Required observations to report
mass_drift, m_norm_over_time, peak_position_drift, energy_drift

## Ground truth (if known)
If the compound-soliton hypothesis is right, the soliton structure propagates approximately rigidly with the boost. Mass conserved exactly. m(x,t) should stay close to zero.

# Tools and environment

Python interpreter: /Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python
Tools allowed: Read, Write, Bash
Tools NOT allowed: Edit (use Write for full rewrites), Grep/Glob, network, package installs

Working directory: /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/runs/S5

# Output requirements

After session ends, working directory MUST contain:
- candidate.py (final solver)
- reasoning.md
- research_state.jsonl
- session_log.md
- pred_results/S5.npz (named arrays from all methods)
- **knowledge_findings.json** (the structured knowledge output)
