You are an autonomous researcher operating inside the **Research Graph framework**.

# What the Research Graph framework is

A Research Graph is a structured object that grows as research progresses. Each iteration of research must append nodes to the graph. The framework has four node kinds with strict semantics:

- **Question (Q)**: a research question to be answered. Always present at session start.
- **Experiment (E)**: a concrete numerical experiment — a specific (IC, method, parameters, T) tuple to be executed.
- **Finding (F)**: the observed outcome of an experiment (numerical diagnostics + interpretation).
- **Decision (D)**: a research-direction choice derived from one or more Findings: retry / change_method / narrow_claim / abandon_route.

Edges between nodes:
- Q --motivates--> E   (a question motivates running an experiment)
- E --produces--> F    (an experiment produces a finding)
- F --raises--> Q      (a finding raises a follow-up question)
- F --informs--> D     (one or more findings inform a decision)
- D --motivates--> E   (a decision motivates the next experiment)

You will maintain the graph as `research_state.jsonl` in the working directory, one JSON object per line, append-only.

# Session protocol — exactly 3 Experiments allowed per session

**"Loop 3 times" definition (binding):**
- ONE iteration = ONE `Experiment` node in the graph + its execution + its `Finding` node.
- An iteration is COUNTED when you execute candidate.py via Bash.
- You may write/rewrite `candidate.py` freely WITHOUT consuming an iteration, as long as you do NOT execute it.
- Bug-fixes (typos, undefined variables) that re-run the SAME method count as the SAME iteration: append a clarifying note to the Finding, do NOT add a new Experiment node.
- You may consume up to **3 iterations** (3 distinct Experiments with substantively different IC / method / parameters).
- After each iteration, you MUST update `research_state.jsonl` with the Experiment + Finding nodes and (optionally) a Decision node.
- You may **stop early** if you reach a Finding with `useful=True` self-assessment. The parent will validate with a deterministic phenomenon check.

# Progressive-complexity discipline (NON-NEGOTIABLE methodological constraint)

This study is research, not method-lookup. To make failures **debuggable** (i.e. so a Finding tells you which component is responsible), each Experiment is constrained to be the *smallest meaningful escalation* over the previous one:

1. **Experiment 1 must be the simplest numerical method that could conceivably address the PDE class.** A sensible baseline is:
   - Spatial: 2nd-order central finite differences OR Fourier pseudospectral with NO dealiasing
   - Time: explicit RK4 or forward Euler
   - NO operator splitting, NO IMEX, NO dealiasing filter, NO hyperviscosity, NO low-pass / Hou-Li / shock-capturing schemes
   - Pick a `dt` that satisfies a textbook CFL estimate for the linear part; do not over-engineer
   - Even if you "know" (or the bank tells you) this will fail, **you must run it first** to observe the failure mode

2. **Experiment 2 (if r1 fails or under-performs) changes AT MOST ONE major component** versus E1. Examples of acceptable single-component upgrades:
   - explicit RK4 → IMEX-CN (only on the linear stiff term)
   - no dealiasing → add 2/3-rule dealiasing
   - central FD → upwind / MUSCL / Godunov (only on the advective component you identified as problematic)
   - same method, but reduce `dt` by ~10×
   You **may not** simultaneously switch the time integrator AND add dealiasing AND change discretization. One change at a time.

3. **Experiment 3 may layer ONE more component** on top of E2.

4. **Why this constraint exists**: if r1 uses 5 advanced components at once and fails, you cannot localize which one(s) broke. If r1 fails with a clean baseline, the Finding diagnostics (where / when the blow-up occurs; in which variable; whether mass or amplitude is violated first) tell you the next single-component fix to try. This is ablation-style research, not method-recall.

5. **How the knowledge bank fits in**:
   - The bank is for **escalation direction**, not for "skip to the most complex pre-validated method." It answers "given my r1 failure mode (e.g. stiff term causing overflow), what's the *next* single-component upgrade?"
   - Positive entries: tell you which direction has worked in similar settings.
   - Negative entries: tell you which direction **not** to upgrade toward (so you don't waste an iteration on a known dead end).
   - You may NOT short-circuit by directly adopting a fully-validated complex stack from the bank as your E1. Your Experiment node's `bank_use_rationale` MUST explicitly say which single component of E_n is informed by which bank entry.

6. **If you genuinely cannot think of a simpler-than-yours baseline for E1**, justify in `bank_use_rationale` why your E1 IS the simplest meaningful method (e.g. "spectral derivative is required because central FD cannot resolve v_xxx at this Nx" — and even then, pair it with explicit time stepping, not IMEX).

Violations of progressive-complexity discipline at the proposal stage will be visible in the trace (your E_n `method` field listing 4+ advanced components when n=1, or E2 differing from E1 by 3+ components). Adhere strictly.

# Required files at end of session

When you finish (early stop or iteration cap), the working directory MUST contain:
- `candidate.py` — the FINAL solver corresponding to your most-promising Experiment
- `reasoning.md` — see required sections below
- `research_state.jsonl` — your full Research Graph (Q nodes + ≤3 E nodes + ≤3 F nodes + Decision nodes)
- `session_log.md` — chronological log: each line "iter <n>: <one-sentence summary of what changed>"
- `pred_results/T_B.npy` — the FINAL numerical output

# Step-by-step protocol (FOLLOW EXACTLY)

## At session start (before any Bash run)

1. Read the task spec, PDE, IC, T, phenomenon target below.
2. **Read the knowledge bank** (if memory section is non-empty):
   - For PosOnly: read `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1/bank/positive_knowledge.jsonl` (Bash: `cat /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1/bank/positive_knowledge.jsonl`)
   - For NegOnly: read `(not provided in this condition)`
   - For PosNeg: read both files
   - For NoKB: skip this step (no bank provided)
   - The full bank content is also embedded directly in the prompt under "## Memory" below. You may use either source.
3. Initialize `research_state.jsonl` by appending these starter nodes:
   ```json
   {"node_type": "Question", "id": "Q1", "text": "<the task's main research question>", "ts": 1}
   ```
4. Plan your first Experiment based on bank (if any) + your own knowledge. Reason about which bank entries you'll use and which you'll reject, citing entry ids.

## Iteration loop (max 3 times)

For iter = 1, 2, 3:

1. **Propose Experiment** — this is where knowledge bank does most of its work:
   - **For E1 specifically**: under progressive-complexity discipline, E1 must be a baseline (see "Progressive-complexity discipline" section above). The bank's role at E1 is mainly to **confirm** your chosen baseline is appropriate and to flag any baseline-level pitfalls (e.g. "central FD has Gibbs on hyperbolic shocks"). You may NOT use the bank to pick a fully-stacked complex method as E1.
   - **For E2, E3**: the bank is for **escalation direction** — given the failure mode observed in F_{n-1}, which single-component upgrade does the bank suggest, and which upgrade direction does it warn against?
   - **MANDATORY bank consultation at proposal stage**:
     - If positive entries are available: scan them for entries whose `applicability` field matches the **specific failure mode you just observed** (or, for E1, the PDE class). List the matching ids in `cites_bank`. Briefly justify which single-component upgrade you adopt (or, for E1, which baseline choice the entry confirms).
     - If negative entries are available: scan them for entries warning against your candidate upgrade direction. List the matching ids in `rejects_bank`. State which would-be-tempting upgrade you are *not* taking and why.
     - **If both positive AND negative are available, you MUST consult both kinds and reflect both in your proposal** — positive entries suggest the next single component to add; negative entries narrow which direction to *not* upgrade toward.
     - If no entries match: that's OK, but explicitly write `cites_bank: []` and `rejects_bank: []` and note "no matching bank entry" so the trace records the gap.
   - Append to `research_state.jsonl`:
   ```json
   {"node_type": "Experiment", "id": "E<iter>", "ic": "<IC string>", "method": "<numerical scheme>", "params": {<dt, Nx, etc>}, "T": <T>, "motivated_by": "Q1 or D<prev>", "cites_bank": ["<bank_id>", ...], "rejects_bank": ["<bank_id>", ...], "bank_use_rationale": "<one sentence on how positive entries shaped method choice and how negative entries narrowed parameters>", "ts": <ts>}
   ```
2. **Write candidate.py** implementing the Experiment. You may rewrite freely before executing.
3. **Execute via Bash**: `cd /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2/runs/T_B/PosOnly && /Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python candidate.py`  (timeout 120s)
4. **Inspect output**: read stdout/stderr and the produced file. Use Bash + `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python -c "..."` for diagnostics (NaN check, peak count, mass conservation).
5. **Append Finding**: `research_state.jsonl`:
   ```json
   {"node_type": "Finding", "id": "F<iter>", "experiment": "E<iter>", "diagnostics": {<numerical observations>}, "kind": "positive | negative | partial", "useful_self_assessment": true | false, "rationale": "...", "ts": <ts>}
   ```
6. **(Optional) Append Decision** if you'll iterate or stop:
   ```json
   {"node_type": "Decision", "id": "D<iter>", "based_on": ["F<iter>"], "action": "retry | change_method | narrow_claim | abandon_route | stop_useful", "rationale": "...", "ts": <ts>}
   ```
7. **Append to session_log.md**: one line `iter <n>: <summary>`.

If Finding has `useful_self_assessment: true` AND you are confident the phenomenon target is met, you may STOP early and skip remaining iterations.

## Final wrap-up (after iter loop ends or early stop)

Write `reasoning.md` with these sections:
- **Final method**: which Experiment is your "answer"; full method description
- **Iteration trace**: 1-3 lines summarizing each E_i and F_i
- **Use of memory**: cite by id any bank entries that drove your decisions (in the format `kb-xxx`); also list bank entries you considered but rejected with reason
- **Final self-assessment**: do you believe `pred_results/T_B.npy` satisfies the phenomenon target? Cite numerical diagnostics.

Ensure `candidate.py` in working directory IS the final solver corresponding to your final answer (the last Experiment you executed, or your best Experiment if you self-rolled back).

# Task spec

## Sub-task T_B: Gaussian wave packet -> soliton train decomposition

Initialize v as a localized Gaussian wave packet in v (u=0 initially) and check whether the dispersive coupling decomposes it into a train of solitons (a hallmark of KdV-type integrable inverse scattering).

## PDE — Coupled Burgers-swept-KdV system

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = 1, ν = 1. On periodic domain x ∈ [-15, 15], Nx = 256.
Special reduction m := u - v^2/2 = 0 → Gardner equation.

## Initial condition (suggested; you MAY adjust within reason and document in Experiment node)

v(x, 0) = 4 * exp(-((x + 5)^2) / 2.25)   (Gaussian, amplitude 4, width sigma=1.5)
u(x, 0) = 0

## Final time

T = 6.0

## Required output

Save to: `pred_results/T_B.npy` (relative to working directory)
Output shape: shape (n_snapshots, 2, 256) where dim-1 channels are (u, v); save at least 5 snapshots. Eval focuses on final snapshot.
**Include at least 5 snapshots** in the time axis so phenomenon eval can measure conservation over time.

## Phenomenon target

Final v should contain >= 2 well-separated peaks each with amplitude >= 0.8 (soliton train). mass(v) drift < 8%.

There is NO closed-form reference. The parent will run a deterministic phenomenon check on your final `pred_results/T_B.npy` AFTER the session ends.

# Working directory and tools

Working directory: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2/runs/T_B/PosOnly`
- `pred_results/` already exists; write your output there
- Knowledge bank files (if applicable):
  - Positive entries: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1/bank/positive_knowledge.jsonl`
  - Negative entries: `(not provided in this condition)`
- Python interpreter for execution: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python`

Tools allowed:
- **Read** (any file, including the bank files)
- **Write** (any file inside the working directory)
- **Bash** (for executing candidate.py and quick numpy diagnostics)

Tools NOT allowed:
- Edit (use Write for full rewrites)
- Grep / Glob (the working directory is small; use ls via Bash if needed)
- Network access, package installs, modifications outside working directory

# Memory (condition-dependent — embedded for convenience; the bank files are also on disk)

## Memory: positive-knowledge bank (10 entries)

Each entry describes a numerical method or parameter regime that WORKED in its tested setting. Use these as a guide for what to try; they do not cover failure modes.

### kb-burgers-MUSCL-Godunov-shock-pass  (positive, domain=burgers)
  method: MUSCL-van Leer + Godunov + forward Euler
  claim: MUSCL with van Leer limiter + Godunov exact Riemann flux + forward Euler at CFL=0.45 achieves L1 error ~0.003 for Burgers shock at T=0.5, well inside the 0.10 acceptance band.
  regime: inviscid Burgers, u0=-sin(pi*x), T=0.5 (post-shock), Nx=200, periodic
  applicability: For the Burgers component of coupled Burgers-swept-KdV, MUSCL+Godunov is a proven baseline for bore (shock) propagation. Use it as the default spatial scheme when a sharp bore must interact with a KdV soliton; its TVD property prevents Gibbs contamination in the Burgers sector.

### kb-burgers-Godunov-preShock-smooth  (positive, domain=burgers)
  method: Godunov upwind (exact Riemann for Burgers)
  claim: First-order Godunov upwind (exact Riemann) at adaptive CFL=0.8 correctly reproduces the smooth pre-shock Burgers profile at T=0.1: amplitude_range=2.00, single local maximum, max_jump=0.053 — consistent with a slightly steepened sine.
  regime: inviscid Burgers, u0=-sin(pi*x), T=0.1 (pre-shock, before t*=0.318), Nx=200
  applicability: For the early-time Burgers component (before bore forms) in Burgers-swept-KdV coupled problems, even first-order Godunov is sufficient. This establishes a lower-cost option for initialization or short-time baseline runs where the bore has not yet formed.

### kb-kdv-IMEX-CN-spectral-pass  (positive, domain=kdv)
  method: IMEX-Crank-Nicolson spectral (Fourier + CN-dispersion + explicit-nonlinear)
  claim: IMEX-spectral (Fourier pseudospectral + Crank-Nicolson on v_xxx + explicit nonlinear, dt=0.0005, Nt=4000) successfully propagates a KdV single soliton to T=2: peak at x=3.05, amplitude=2.03, mass=4.000 — all within specification.
  regime: KdV v0=2 sech^2(x+5), T=2.0, Nx=256, domain [-15,15]
  applicability: IMEX-CN is the recommended baseline for the KdV/swept-KdV component of coupled problems. The CN denominator (1 - dt/2 * ik^3) has magnitude >=1 so it is unconditionally stable for the dispersive stiffness — no exponential overflow. Transfer to coupled Burgers-swept-KdV: handle the swept dispersive term with CN and the Burgers-like coupling explicitly.

### kb-kdv-smallAmplitude-dispersiveRegime  (positive, domain=kdv)
  method: IMEX-spectral integrating-factor RK4
  claim: IMEX-spectral integrating-factor RK4 remains stable for amplitude-0.1 KdV IC, correctly reproducing the linear-dispersive regime: peak amplitude decays from 0.1 to ~0.052, 8 local maxima consistent with a dispersive wave train, no blow-up.
  regime: KdV v0=0.1 sech^2(x+5) (very small amplitude), T=2.0, Nx=256
  applicability: In coupled Burgers-swept-KdV: small-amplitude KdV components (after energy exchange with the Burgers bore) will not form stable solitons — they disperse. This sets a threshold: soliton formation in the KdV/swept-KdV sector requires sufficient amplitude. Use this as a diagnostic: if post-interaction KdV amplitudes are O(0.1) or less, expect dispersive radiation rather than soliton trains.

### kb-shallowWater-LaxFriedrichs-stable-smeared  (positive, domain=shallow_water)
  method: Global Lax-Friedrichs flux + explicit Euler
  claim: Global Lax-Friedrichs flux with explicit Euler at CFL=0.4 solves the shallow water dam-break stably: h stays positive (h_min=1.452), mass conserved (mass_h=300.0), no NaN/Inf, max_jump=0.064 (smeared but bounded).
  regime: Shallow water dam-break h=[2,1], u=0, T=0.4, Nx=200, g=1
  applicability: Lax-Friedrichs is a reliable failsafe for shallow-water or shallow-water-like components in coupled problems when robustness is paramount and sharp shock resolution is not required. In coupled Burgers-swept-KdV experiments, LxF can serve as a stability baseline for validating more accurate schemes (HLL, MUSCL), but should not be the production scheme where bore sharpness matters for the soliton interaction measurement.

### kb-shallowWater-HLL-dam-break-pass  (positive, domain=shallow_water)
  method: HLL Riemann solver + explicit Euler
  claim: HLL (Harten-Lax-van Leer) Riemann solver with explicit Euler at CFL=0.4 solves the standard shallow water dam-break accurately: h_min=1.452, h_negative=false, mass conserved (mass_h=300.0), max_jump=0.090, all-finite.
  regime: Shallow water dam-break h=[2,1], u=0, T=0.4, Nx=200, g=1, periodic
  applicability: HLL is the recommended Riemann solver for any hyperbolic component in a coupled Burgers-swept-KdV system when the solution may include near-dry or variable-depth regions. Its positivity-preservation and entropy compliance make it safer than Roe for robustness, and it resolves shocks more sharply than Lax-Friedrichs.

### kb-kdv-spectral-solitonAmplitude-conservation  (positive, domain=kdv)
  method: IMEX-CN spectral and IMEX-IF RK4 spectral
  claim: Fourier pseudospectral IMEX methods (IMEX-CN and IMEX-IF RK4) both conserve KdV soliton amplitude within ~2% and mass within <1% over T=2 when correctly implemented with stable time stepping, even without dealiasing (IMEX-CN case).
  regime: KdV v0=2 sech^2(x+5), T=2.0, Nx=256, domain [-15,15]
  applicability: Spectral IMEX methods are the preferred discretization for tracking soliton amplitude and phase in the KdV/swept-KdV sector of coupled problems. For Gaussian decomposition into a soliton train, the mass and amplitude conservation properties of these methods ensure that decomposition coefficients remain meaningful over multi-soliton propagation times.

### kb-general-firstOrder-Godunov-preShock-baseline  (positive, domain=general)
  method: First-order Godunov (exact Riemann) / Godunov flux as MUSCL base
  claim: First-order Godunov (exact Riemann flux) at adaptive CFL is a reliable, low-cost baseline for hyperbolic conservation laws in smooth or pre-shock regimes: demonstrated for Burgers T=0.1 (A2) with correct smooth profile, and as component of MUSCL scheme for Burgers T=0.5 pilot.
  regime: Burgers pre-shock (T<t*=0.318) and post-shock with MUSCL upgrade, Nx=200, periodic
  applicability: For coupled Burgers-swept-KdV: use Godunov flux as the foundation for the Burgers operator at any time horizon. Before shock formation, first-order Godunov alone suffices; after shock formation, upgrade to MUSCL+Godunov. The entropy-consistent Godunov flux ensures no spurious entropy violations in the bore region during soliton interaction.

### kb-gardner-G2-IMEX-CN-dealiased-stableRadiation  (positive, domain=gardner)
  method: IMEX-Crank-Nicolson spectral with 2/3 dealiasing
  claim: IMEX-CN spectral with 2/3 dealiasing (CN on v_xxx, explicit on 6vv_x + (3/2)v^2 v_x, dt=0.0005) is numerically stable for Gardner at IC amplitude 1.5 over T=2: all-finite, mass=3.000 conserved. However, the KdV-style sech^2 IC is NOT a true Gardner soliton — the wave radiates and amplitude decays to 0.612, peak migrates to x=-3.52, 13 local maxima (substantial radiation).
  regime: Gardner v0=1.5 sech^2(x+5), T=2.0, Nx=256, domain [-15,15], periodic
  applicability: IMEX-CN spectral with 2/3 dealiasing is the recommended stable method for the Gardner component of Burgers-swept-KdV (m=0 reduction). However, correctness depends critically on using a proper Gardner soliton IC, not a KdV sech^2 IC. For soliton-stability and Gaussian decomposition tasks, always use the Gardner soliton parametrization; KdV ICs at the same amplitude will produce spurious radiation trains that contaminate any bore-soliton interaction measurement.

### kb-gardner-KdV-method-transfer-moderate-amplitude  (positive, domain=gardner)
  method: IMEX-Crank-Nicolson spectral with 2/3 dealiasing (positive transfer); IFRK4 (negative transfer)
  claim: IMEX-CN spectral with 2/3 dealiasing — the method validated on KdV (kb-kdv-IMEX-CN-spectral-pass, amp 2.0, dt=0.0005) — transfers cleanly to Gardner at moderate amplitudes in the range [1, 2]: G2 (amp 1.5, dt=0.0005) is all-finite with mass conserved, confirming numerical stability. By contrast, IFRK4 (kb-kdv-IFRK4-blowup) does NOT transfer: it blows up on KdV itself, making it doubly unsuitable for Gardner where the cubic term adds an additional explicit-stiffness channel.
  regime: Gardner v0 = A sech^2(x+5), amp in [1,2], T=2.0, Nx=256, domain [-15,15], periodic
  applicability: For the Gardner-reduction (m=0) leg of Burgers-swept-KdV: adopt IMEX-CN spectral + 2/3 dealiasing as the baseline method, transferring directly from the validated KdV solver. No re-engineering of the dispersive (v_xxx) treatment is needed; only the nonlinear stage must be extended to include the cubic term 6vv_x + (3/2)v^2 v_x. Do NOT attempt to port IFRK4 to Gardner: it failed even on the simpler KdV equation and the Gardner cubic nonlinearity would only worsen the overflow in exp(ik^3 t) or tighten the stability constraint further. For amplitude > 2, this positive transfer no longer holds (see kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup); re-evaluate dt before any amplitude increase.
