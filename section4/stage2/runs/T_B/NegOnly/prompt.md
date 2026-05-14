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
   - For PosOnly: read `(not provided in this condition)` (Bash: `cat (not provided in this condition)`)
   - For NegOnly: read `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1/bank/negative_knowledge.jsonl`
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
3. **Execute via Bash**: `cd /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2/runs/T_B/NegOnly && /Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python candidate.py`  (timeout 120s)
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

Working directory: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2/runs/T_B/NegOnly`
- `pred_results/` already exists; write your output there
- Knowledge bank files (if applicable):
  - Positive entries: `(not provided in this condition)`
  - Negative entries: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1/bank/negative_knowledge.jsonl`
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

## Memory: negative-knowledge bank (20 entries)

Each entry describes a numerical method or parameter regime that FAILED in its tested setting, structured by the 6-field bounded failure schema (layer / scope / degree / recommended_action / risk). Use these to avoid known pitfalls; they do not directly tell you what to do, only what to avoid.

### kb-burgers-fwdEuler-centralFD-Gibbs  (negative, domain=burgers)
  attempted_route: Forward Euler + 2nd-order central FD (no upwinding, no limiter), CFL=0.4, Burgers u0=-sin(pi*x), T=0.5
  observation: Solution is all-finite but exhibits 21 local maxima (vs 1 expected), amplitude_range=7.21 (~3.6× true amplitude), max_jump=3.61 — massive Gibbs-like oscillations, effectively blow-up in accuracy if not in finiteness.
  failure: layer=method_failure, scope=general_failure, degree=contradicted, action=change_method, risk=high_risk_false_progress
  rationale: Central differencing on a nonlinear hyperbolic equation has no upwind dissipation; post-shock oscillations grow without bound in amplitude. The scheme appears to 'run' (exit 0, no NaN) but the output is physically meaningless: amplitude tripled and 20 spurious peaks appeared.
  applicability: In a coupled Burgers-swept-KdV solver, any naive central-difference treatment of the Burgers advection term will corrupt both the Burgers bore and the adjacent KdV soliton region via spurious oscillation cross-contamination. Always use an upwind or flux-limited scheme for the Burgers component.

### kb-burgers-LaxFriedrichs-longTime-dissipation  (negative, domain=burgers)
  attempted_route: Global Lax-Friedrichs FD scheme, CFL=0.5, Burgers u0=-sin(pi*x), T=10.0
  observation: Solution is all-finite but amplitude decayed to max=0.090 (vs expected O(1)), mean_jump=0.0018, single local maximum — severe over-diffusion from Lax-Friedrichs at 10× the shock timescale.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=medium_risk_drift
  rationale: Lax-Friedrichs is unconditionally stable and produces no NaN, but its O(dx) numerical diffusivity acts at every interface continuously. Over T=10 (>>1/pi), the integrated dissipation washes out the shock amplitude by ~10×; the result is a smooth, decayed N-wave not representative of the true inviscid solution.
  applicability: In long-time coupled Burgers-KdV simulations, Lax-Friedrichs is unsuitable for the Burgers component: it will artificially damp the bore amplitude and cause the bore-soliton interaction energy to be misrepresented. Prefer MUSCL or upwind-limited schemes for T >> shock timescale.

### kb-burgers-LaxFriedrichs-periodic-longTime-contamination  (negative, domain=burgers)
  attempted_route: Any stable scheme on periodic domain for Burgers, T=10 (multiple domain-traversal times)
  observation: Result shows smooth, nearly zero-mean profile (amplitude 0.181) with periodic recirculation contaminating any shock/rarefaction structure. Genuine physics vs numerical artifact is indistinguishable at T=10 on this periodic domain.
  failure: layer=measurement_failure, scope=regime_bound, degree=artifact_driven, action=narrow_claim, risk=medium_risk_drift
  rationale: Even a perfect numerical scheme will show periodic wrapping at T=10: the shock and rarefaction recirculate multiple times and overlap. This contamination is a property of the periodic boundary condition, not of the scheme, and should not be interpreted as a scheme failure or as a meaningful physical solution.
  applicability: In coupled Burgers-swept-KdV experiments on periodic domains, long-time runs beyond a few domain-traversal times produce spurious bore-soliton interaction histories. Restrict comparison windows to T where neither wave has wrapped around, or use absorbing/outflow boundaries.

### kb-kdv-IFRK4-blowup  (negative, domain=kdv)
  attempted_route: Fourier pseudospectral + integrating-factor RK4 (IFRK4), dt unspecified, no dealiasing, KdV v0=2 sech^2(x+5), T=2.0, Nx=256
  observation: Output array shape (256,) is all-NaN (256 NaN/Inf). Eval score=0. Blow-up despite agent claiming correct IF-RK4 formulation.
  failure: layer=implementation_failure, scope=local_failure, degree=unstable, action=change_method, risk=medium_risk_drift
  rationale: The IFRK4 concept is mathematically sound, but in practice the integrating factor exp(i*k^3*t) overflows for high wavenumbers (k~100 gives k^3~10^6), or a sign/reshape error in the implementation caused phase errors cascading to NaN. Correct IFRK4 requires dealiasing plus careful handling of the complex exponential at high k.
  applicability: For coupled Burgers-swept-KdV: do not use IFRK4 without (a) 2/3 dealiasing on the nonlinear term, (b) verification that |k^3 * dt| stays below the RK4 stability boundary, and (c) no sign errors in the integrating-factor back-transform. IMEX-CN is a safer default; use IFRK4 only if 4th-order time accuracy is required and the implementation is carefully validated.

### kb-kdv-explicit-RK4-stiffness-blowup  (negative, domain=kdv)
  attempted_route: Explicit RK4 + central FD for v_xxx, dt=1e-5, KdV v0=2 sech^2(x+5), T=2.0, Nx=256
  observation: Unexpectedly, output is all-finite (no NaN) with amplitude_range=1.63 and 10 local maxima — but amplitude is wrong (expected ~2.0) and 10 spurious peaks indicate the soliton has fragmented or dispersed into artifacts. Prediction of NaN blow-up was not confirmed, but the result is physically wrong.
  failure: layer=hypothesis_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=medium_risk_drift
  rationale: The agent chose dt=1e-5 which may be small enough to barely avoid NaN for RK4 (requiring dt~dx^3 for explicit stability of v_xxx at Nx=256), but the soliton amplitude decayed from 2.0 to ~0.87 and spawned 10 peaks — the scheme is marginally stable but deeply inaccurate. The prediction of NaN was not met; the actual failure mode is accuracy collapse, not finiteness blow-up.
  applicability: For coupled Burgers-swept-KdV: explicit-only treatment of the KdV dispersive term (v_xxx or swept equivalent) produces soliton fragmentation even if NaN is avoided. Any agent solving this system must use an implicit or IMEX treatment of the dispersive term; explicit RK4 alone is not sufficient even with very small dt.

### kb-kdv-noDealiasing-aliasing-artifacts  (negative, domain=kdv)
  attempted_route: Fourier pseudospectral + IMEX Euler, dt=0.005, NO 2/3 dealiasing on nonlinear term, KdV v0=2 sech^2(x+5), T=2.0, Nx=256
  observation: Output is all-finite with amplitude 2.87 (>2.0 expected) and 4 local maxima (vs 1 expected soliton) — aliasing energy has created spurious soliton-like peaks and inflated the apparent amplitude.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=medium_risk_drift
  rationale: Without dealiasing, the pseudo-spectral evaluation of v*v_x wraps energy from modes |k|+|k'|>N/2 back into low wavenumbers, acting as a phantom forcing on the soliton. Over 400 steps this aliased energy visibly distorts the soliton: peak amplitude is 43% too high and three spurious peaks appear.
  applicability: For coupled Burgers-swept-KdV spectral implementations: always apply the 2/3 dealiasing rule (or at minimum a smooth spectral filter) to the nonlinear term. Without it, the soliton amplitude and count are unreliable, which would corrupt any soliton-bore interaction measurement. This is especially critical for Gaussian decomposition into soliton trains where individual soliton amplitudes must be accurately tracked.

### kb-kdv-amplitude-threshold-soliton  (negative, domain=kdv)
  attempted_route: KdV with amplitude 0.1 IC, expecting soliton propagation similar to amplitude-2 case
  observation: Peak amplitude at T=2 is 0.052 (nearly halved from IC), 8 local maxima (dispersive wave train), zero_crossings=12 — clearly not a soliton. The soliton-propagation expectation fails at this amplitude.
  failure: layer=hypothesis_failure, scope=regime_bound, degree=contradicted, action=narrow_claim, risk=low_risk_omission
  rationale: KdV soliton formation requires the nonlinear term (O(A^2)) to balance the dispersive term (O(A)); at A=0.1 dispersion dominates and the pulse spreads linearly. Any model predicting soliton-like behavior at this amplitude is incorrect for these parameters.
  applicability: For Gaussian decomposition into KdV soliton trains in coupled Burgers-swept-KdV: only Gaussian components with amplitude above a system-dependent threshold (empirically >> 0.1 for standard KdV scaling) contribute solitons; sub-threshold components produce dispersive radiation. This shapes which Gaussian decomposition modes matter for the soliton-bore interaction measurement.

### kb-shallowWater-centralFD-fwdEuler-hNegative  (negative, domain=shallow_water)
  attempted_route: Forward Euler + central FD (no limiter, no upwinding, no Riemann solver), shallow water dam-break h=[2,1], T=0.4, Nx=200
  observation: h goes negative (h_min=-0.139, h_negative=true), momentum reaches |value|=5.27e10 — explosive blow-up in the momentum field while h is only marginally negative. All-finite in floating point but physically degenerate.
  failure: layer=method_failure, scope=general_failure, degree=contradicted, action=change_method, risk=high_risk_false_progress
  rationale: Central differencing on the shallow water system produces Gibbs oscillations near the dam-break discontinuity; h dips below zero making wave speed imaginary and hu/h singular; forward Euler amplifies these into exponentially growing modes. The scheme is provably inadequate for discontinuous hyperbolic systems.
  applicability: Directly relevant to the Burgers-swept-KdV coupled system if the swept-KdV has a shallow-water-like structure: central FD without upwinding or Riemann fluxes is catastrophic for any hyperbolic system with discontinuous ICs. Never use central FD alone for the advective terms in any wave-breaking or bore-like regime.

### kb-shallowWater-LaxFriedrichs-overdiffusion  (negative, domain=shallow_water)
  attempted_route: Global Lax-Friedrichs flux, CFL=0.4, shallow water dam-break h=[2,1], T=0.4
  observation: max_jump=0.064 vs HLL's max_jump=0.090 at same resolution — shock is ~28% more smeared than HLL. The shock-rarefaction structure is excessively broadened for physical analysis.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=low_risk_omission
  rationale: Global LxF applies the maximum wave speed alpha everywhere as viscosity, not just near discontinuities. This globally adds O(alpha*dx) diffusion per step, smearing both shock and rarefaction more than Riemann-solver methods. The result is quantitatively incorrect for cases where shock width matters.
  applicability: For coupled Burgers-swept-KdV where bore sharpness affects the soliton interaction timescale, prefer HLL over Lax-Friedrichs for the hyperbolic component. Smeared bores may delay or distort the interaction region, leading to incorrect soliton phase shifts in measurement.

### kb-shallowWater-dryBed-naiveClip-hu-singular  (negative, domain=shallow_water)
  attempted_route: HLL + Godunov finite volume + adaptive CFL, with positivity clip (h=max(h,0)) at dry interface h_R=0, shallow water, T=0.3
  observation: h stays non-negative (h_min=0.00153, clipped) and mass is conserved (100.0), but the momentum (hu) field has values reaching -0.295 while h is near zero — u = hu/h is ill-defined at dry cells (effective |u| > 100 near dry front).
  failure: layer=implementation_failure, scope=local_failure, degree=partial, action=change_method, risk=medium_risk_drift
  rationale: Post-hoc positivity clipping prevents h<0 but breaks conservation locally; the momentum equation then computes hu/h ratios at near-zero h that are numerically huge even if not NaN. A correct dry-bed solver needs a consistent wet/dry treatment (HLLE with dry Riemann solution, or a well-balanced scheme) rather than clipping.
  applicability: In coupled Burgers-swept-KdV if any region can develop near-zero depth or near-zero amplitude (e.g., swept-KdV in a region where the Burgers bore evacuates material), use a wet/dry front tracking scheme rather than simple positivity clips. Otherwise velocity blow-up near the front will corrupt the bore-soliton interaction.

### kb-general-centralFD-hyperbolic-shockFormation  (negative, domain=general)
  attempted_route: Central finite differences (no upwinding, no limiter) applied to any nonlinear hyperbolic conservation law with discontinuous or shock-forming initial conditions — observed in A1 (Burgers) and A7 (shallow water)
  observation: A1: 21 local maxima, amplitude 7.2×; A7: h goes negative (h_min=-0.139), momentum 5.3e10. Both cases produce physically degenerate output that is technically finite but numerically useless.
  failure: layer=method_failure, scope=general_failure, degree=contradicted, action=change_method, risk=high_risk_false_progress
  rationale: Central FD lacks the upwind dissipation necessary for Godunov-type stability in hyperbolic systems; spurious oscillations at discontinuities grow without bound under either forward Euler or similar non-dissipative time steppers. This is a universal failure across PDE families, not scheme-specific.
  applicability: Universal rule for coupled Burgers-swept-KdV: the Burgers and any hyperbolic component must use upwind, Riemann-solver, or flux-limited spatial discretization. Central FD is acceptable only for smooth dispersive terms (like v_xxx in KdV when treated implicitly) — never for the advective nonlinear flux in a shock-forming equation.

### kb-general-finiteness-not-accuracy  (negative, domain=general)
  attempted_route: Various schemes (A1, A4, A7) that produced all-finite output arrays but with physically wrong solutions
  observation: A1: all_finite=true but 21 local maxima; A4: all_finite=true but soliton fragmented into 10 peaks with amplitude 1.63 vs 2.0; A7: all_finite=true but momentum 5.3e10. Exit code 0 in all cases.
  failure: layer=measurement_failure, scope=general_failure, degree=overclaimed, action=narrow_claim, risk=high_risk_false_progress
  rationale: A scheme that produces finite (non-NaN/Inf) output can still be completely wrong. Diagnostics based only on finiteness or exit code will produce false positives; amplitude, local-maxima count, and jump statistics are necessary secondary checks.
  applicability: For future coupled Burgers-swept-KdV evaluation pipelines: do not use NaN/Inf presence as the sole correctness criterion. Also check: local maxima count vs expected soliton count, peak amplitude vs reference, mass conservation, and maximum jump vs reference max-jump. These diagnostics distinguish catastrophic accuracy failures from true stability.

### kb-gardner-G1-explicitRK4-finiteFrag  (negative, domain=gardner)
  attempted_route: Explicit RK4 + 2nd-order central FD for all spatial derivatives (v_xxx and nonlinear), dt=1e-5, Gardner v0=1.5 sech^2(x+5), T=2.0, Nx=256, periodic
  observation: Output is all-finite (no NaN), mass=3.000, but soliton has fragmented: 14 local maxima (vs 1 expected), peak amplitude only 1.506 (down from IC amplitude 1.5 — near-stationary peak but heavily fragmented structure), peak migrated to x=2.11 (expected ~x=3-5 for KdV-speed soliton). The scheme survived only because dt=1e-5 is near the stability boundary dt~O(dx^3)~1.6e-4.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=medium_risk_drift
  rationale: Explicit RK4 on the Gardner v_xxx term requires dt~O(dx^3) for stability. At dt=1e-5 the run narrowly avoids NaN blow-up, but the cubic nonlinearity (3/2)v^2 v_x adds extra high-frequency forcing beyond KdV, causing soliton fragmentation into 14 pieces rather than clean propagation. The method is impractical (200,000 steps for T=2) and inaccurate at this dt.
  applicability: For the Gardner-reduction regime of coupled Burgers-swept-KdV (m=0): pure explicit RK4 on Gardner is impractical — it requires ~200,000 steps for T=2 and still produces fragmented soliton structure. Any production solver for this regime must use IMEX or spectral-ETD methods for the dispersive term. Do not use explicit-only methods even with very small dt to 'be safe'; they do not produce accurate soliton propagation on Gardner.

### kb-gardner-G3-noDealiasing-cubicAliasing  (negative, domain=gardner)
  attempted_route: IMEX-CN spectral, NO 2/3 dealiasing, dt=0.001, Gardner v0=1.5 sech^2(x+5), T=2.0, Nx=256
  observation: Output is all-finite with peak amplitude 1.545 (slightly above IC amplitude 1.5, vs 2.87 inflation in KdV no-dealiasing case A5), 11 local maxima, mass=3.000. Aliasing artifacts are present (11 spurious peaks) but amplitude inflation is more modest than KdV case at this amplitude; no catastrophic blow-up at amp 1.5.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=medium_risk_drift
  rationale: The cubic v^2 v_x term aliases at up to 3x the Nyquist wavenumber (vs 2x for quadratic KdV term), so Gardner without dealiasing has more aliasing channels. Yet at amplitude 1.5 the absolute aliasing energy is not dramatically worse than KdV (A5 had 43% amplitude inflation; G3 has only ~3% inflation). The extra cubic aliasing channel creates more spurious peaks (11 vs 4 in KdV) but the amplitude inflation is masked by the radiation from the wrong IC. Dealiasing remains essential for accurate multi-soliton counting.
  applicability: For Gardner and the full coupled Burgers-swept-KdV system: the cubic nonlinearity adds a third aliasing channel that, even at moderate amplitude, creates more spurious peak count than the KdV quadratic term alone. Always apply 2/3 dealiasing (or higher-order filtering) when the PDE contains cubic or higher polynomial nonlinearities. For Gaussian decomposition tasks, spurious peak count from aliasing would directly corrupt soliton-train identification.

### kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup  (negative, domain=gardner)
  attempted_route: IMEX-CN spectral (CN on v_xxx, explicit on nonlinear), dt=1e-4, Gardner v0=3.0 sech^2(x+5), T=2.0, Nx=256 — same method as G2 but at 2× the IC amplitude
  observation: All 256 outputs are NaN (n_nan=256, all_finite=false). Runtime overflow encountered in the nonlinear term: 'overflow encountered in multiply' (6.0*v*vx + 1.5*v^2*vx) and 'invalid value encountered in fft' — the IMEX-CN explicit nonlinear step blew up at amplitude 3.0 even though the same method (similar dt) was stable at amplitude 1.5.
  failure: layer=method_failure, scope=regime_bound, degree=unstable, action=change_method, risk=high_risk_false_progress
  rationale: IMEX-CN treats the dispersive term v_xxx implicitly (unconditionally stable) but the nonlinear terms 6vv_x + (3/2)v^2 v_x explicitly. The explicit nonlinear CFL constraint is amplitude-dependent: the combined nonlinearity at A=3 is O(6A + 1.5A^2) ~ O(18 + 13.5) = O(31.5) vs O(9 + 3.375) = O(12.4) at A=1.5. The CFL restriction tightens by approximately 2.5×, making dt=1e-4 insufficient at A=3 even though a comparable dt worked at A=1.5.
  applicability: Critical for the Gardner-reduction regime and full coupled Burgers-swept-KdV: IMEX-CN with explicit nonlinear has an amplitude-dependent CFL limit driven by the combined 6vv_x + (3/2)v^2 v_x term. When amplitude doubles, the effective CFL limit tightens by more than 2×. Always re-evaluate dt when changing IC amplitude; do not assume a dt validated at lower amplitude is safe at higher amplitude. For large-amplitude Gardner or swept-KdV regimes, consider fully implicit nonlinear solvers or ETD-RK methods with accurate stability analysis.

### kb-gardner-sech2IC-not-exact-soliton  (negative, domain=gardner)
  attempted_route: Using KdV sech^2 IC (v0 = A sech^2(x+x0)) as initial condition for Gardner equation at any amplitude
  observation: G2 (amp 1.5): amplitude decayed from 1.5 to 0.612, 13 local maxima, peak migrated to x=-3.52 — substantial radiation from wrong IC. G4 (amp 3.0): complete NaN blow-up (amplitude-CFL failure exacerbated by wrong IC shape causing rapid nonlinear transient).
  failure: layer=hypothesis_failure, scope=general_failure, degree=contradicted, action=change_method, risk=high_risk_false_progress
  rationale: The Gardner equation v_t + 6vv_x + (3/2)v^2 v_x + v_xxx = 0 has soliton solutions with a different amplitude-width-velocity relationship than KdV. The KdV soliton A sech^2(sqrt(A/6)(x-ct)) satisfies 6vv_x + v_xxx = 0 but NOT the Gardner equation. Inserting a KdV sech^2 IC into Gardner creates an immediate nonlinear mismatch that radiates energy continuously. The correct Gardner soliton is parametrized differently (involving the cubic coefficient).
  applicability: Essential for all Gardner-reduction sub-tasks in Burgers-swept-KdV: use the proper Gardner soliton IC (parametrized with the cubic coefficient epsilon) for soliton stability tests, not a KdV sech^2 IC. Using KdV ICs will (a) generate spurious radiation trains that corrupt bore-soliton interaction measurements, (b) potentially trigger amplitude-CFL blow-up at amplitudes where the nonlinear transient is large. For the Gaussian decomposition task, fit Gardner soliton profiles to the data, not KdV soliton shapes.

### kb-gardner-cubicTerm-tightens-nonlinearCFL  (negative, domain=gardner)
  attempted_route: Any IMEX or semi-implicit method with explicit treatment of the nonlinear terms in Gardner, re-using a dt validated on KdV at the same grid resolution
  observation: G4 (IMEX-CN, dt=1e-4, amp 3.0): complete NaN blow-up. G1 (explicit RK4, dt=1e-5, amp 1.5): survived but fragmented. KdV IMEX-CN at dt=0.0005 (amp 2.0, kb-kdv-IMEX-CN-spectral-pass): stable. The cubic term (3/2)v^2 v_x at amplitude A contributes O(1.5A^2) to the nonlinear CFL, tightening it by a factor ~(1 + 0.25A) compared to pure KdV at the same A.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=high_risk_false_progress
  rationale: In Gardner's combined nonlinearity 6vv_x + (3/2)v^2 v_x, the effective advection speed for the explicit CFL is proportional to max|6v + (3/2)v^2| = max|6A + 1.5A^2|. For A=2 (KdV pilot): 12+6=18; for A=1.5: 9+3.375=12.4; for A=3: 18+13.5=31.5. The ratio 31.5/12.4 ~2.5 means the same dt that was marginally safe at A=1.5 is 2.5× too large at A=3. Agents transferring KdV dt choices to Gardner without amplitude-adjustment will encounter blow-up.
  applicability: For the Gardner-reduction regime of Burgers-swept-KdV and the full coupled system: when increasing IC amplitude from KdV baseline to Gardner or swept-KdV regimes, rescale dt by max(6A + 1.5A^2)^{-1} relative to the KdV-validated dt. The cubic coefficient makes Gardner significantly more restrictive than KdV at A > 2. Document the amplitude used when recording a 'stable dt' in the knowledge bank — it is not transferable across amplitudes.

### kb-general-massConservation-insufficient-diagnostic  (negative, domain=general)
  attempted_route: Using mass conservation alone as the correctness diagnostic for dispersive or fragmented wave solutions
  observation: G1 (Gardner explicit RK4): mass=3.000 but 14 local maxima, soliton fragmented. G3 (Gardner no dealiasing): mass=3.000 but 11 local maxima, aliasing artifacts. Earlier: A4 (KdV explicit RK4): soliton fragmented into 10 peaks with mass still conserved. A5 (KdV no dealiasing): 4 spurious solitons but mass approximately conserved.
  failure: layer=measurement_failure, scope=general_failure, degree=overclaimed, action=narrow_claim, risk=high_risk_false_progress
  rationale: Mass (integral of v) is conserved by many numerical methods even when the solution is physically wrong: fragmentation, aliasing-driven spurious peaks, and soliton amplitude errors all leave the L1 mass integral unchanged. A run reporting mass=3.000 with 14 local maxima is not a correct solution. Peak count, peak amplitude, and peak location are orthogonal diagnostics that must also be checked.
  applicability: Universal rule for coupled Burgers-swept-KdV evaluation pipelines: mass conservation is a necessary but not sufficient correctness criterion. The primary correctness check for soliton problems must include: (1) peak local maxima count matching expected soliton count, (2) peak amplitude within tolerance of reference, (3) peak x-position consistent with theoretical phase speed. This is especially important for Gaussian decomposition tasks where spurious peaks from aliasing or fragmentation would produce incorrect soliton-train amplitudes.

### kb-gardner-GardnerIsM0-coupledSystemInstability  (negative, domain=gardner)
  attempted_route: Assuming that a numerical method validated on the isolated Gardner equation will be equally stable when embedded in the full coupled Burgers-swept-KdV system at the same parameters
  observation: G4 demonstrates that IMEX-CN with explicit nonlinear blows up on Gardner at amplitude 3.0 (the m=0 reduction). The full coupled system at m=0 has additional coupling terms that add further explicit stiffness beyond the isolated Gardner equation.
  failure: layer=hypothesis_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=high_risk_false_progress
  rationale: Gardner is the m=0 reduction of the coupled Burgers-swept-KdV system from Holm et al. 2025. If IMEX-CN with explicit nonlinear blows up on the isolated Gardner equation at a given (dt, amplitude), it will certainly blow up on the full coupled system in the Gardner-reduction regime — the coupling terms add O(m) correction to the nonlinear explicit stiffness. Conversely, a dt that is stable for the coupled system at small m will not automatically be stable as m -> 0 if the Gardner nonlinear CFL becomes the binding constraint.
  applicability: Directly applicable to Burgers-swept-KdV coupled system design: validate numerical methods first on the isolated Gardner equation (m=0 reduction) before testing the full coupled system. Gardner blow-up at a given (dt, amplitude) is a necessary failure condition for the full coupled system in that regime. Treat Gardner stress tests as a prerequisite gate for coupled-system parameter sweeps.

### kb-gardner-nonlinearCFL-amplitude-boundary  (negative, domain=gardner)
  attempted_route: IMEX-CN spectral with explicit nonlinear (6vv_x + (3/2)v^2 v_x) at dt=5e-4 for Gardner amplitude escalating from 1.5 to 3.0
  observation: Empirically: dt=5e-4 is STABLE at amp 1.5 (G2, all_finite=true, mass conserved). The same scheme with dt=1e-4 BLOWS UP (all 256 NaN) at amp 3.0 (G4). Interpolating the effective nonlinear wave-speed: at amp 1.5, max|6v + 1.5v^2| ~ 9 + 3.375 = 12.4; at amp 3.0, max|6v + 1.5v^2| ~ 18 + 13.5 = 31.5. The empirical stability boundary therefore scales as dt * (6A + 1.5A^2) * k_max / (2*pi/L) < C for some O(1) constant C, where k_max is set by the steepest resolved mode.
  failure: layer=method_failure, scope=regime_bound, degree=unstable, action=narrow_claim, risk=high_risk_false_progress
  rationale: For the explicit nonlinear part of IMEX schemes applied to Gardner, the nonlinear CFL condition is dt <= C / (max_v * k_max) where max_v = max|6v + 1.5v^2| and k_max is determined by the steepest active spectral mode. The key distinction from linear CFL: max_v scales as O(6A + 1.5A^2) with amplitude A, so the constraint is NOT linear in A. Doubling A from 1.5 to 3 increases the nonlinear speed by a factor 31.5/12.4 ~ 2.54, requiring dt to shrink by the same factor. At A=1.5 the empirically safe dt=5e-4 implies C ~ 5e-4 * 12.4 * k_max; at A=3 this budget requires dt <= 5e-4 / 2.54 ~ 2e-4. Using dt=1e-4 at A=3 is borderline (consistent with overflow seen in G4). The nonlinear-CFL rule can be stated as: amp * (6 + 1.5*amp) * dt * k_eff < O(1), where k_eff is the effective peak wavenumber of the soliton (of order sqrt(A/6) for the KdV sech^2 IC).
  applicability: Critical design rule for any IMEX solver applied to the Gardner or swept-KdV component of the coupled Burgers-swept-KdV system: before each amplitude sweep, compute the nonlinear CFL number NL-CFL = dt * max(6*A + 1.5*A^2) * k_soliton and confirm NL-CFL < threshold (~O(0.5-1) based on G2/G4 bracket). The empirical evidence is: dt=5e-4 passes at A=1.5 (NL-CFL ~ 0.31 for k_soliton ~ 0.5), dt=1e-4 fails at A=3.0 (NL-CFL ~ 0.16 — yet blow-up still occurs, suggesting the relevant k_max is the grid Nyquist, not the soliton wavenumber). This implies agents must use dt <= C/(max_nonlinear_speed * k_Nyquist) rather than the soliton-scale wavenumber. For Burgers-swept-KdV production runs at A in [1,3], target dt in [1e-4, 3e-4] and monitor the first few steps for overflow.
