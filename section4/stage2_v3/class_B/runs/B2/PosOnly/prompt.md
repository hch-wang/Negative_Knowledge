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

Working directory: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/B2/PosOnly`
Python interpreter: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python`

Knowledge bank:
- Positive entries: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/bank/bank_v3A_positive.jsonl`
- Negative entries: `(not provided in this condition)`

Tools allowed: Read, Write, Bash only. Do NOT use Edit, Grep, Glob, network.

# Memory (condition-dependent — embedded for convenience; bank files are also on disk)

## Memory: positive-knowledge bank (15 entries, v3.A — includes BKdV stress-test entries S1-S7)

Positive entries describe methods, regimes, or observations VALIDATED in related settings. Deep synthesis entries (depth≥2) span multiple stage-1 stress-test rounds.

### kb-burgers-MUSCL-Godunov-shock-pass  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: For the Burgers component of coupled Burgers-swept-KdV, MUSCL+Godunov is a proven baseline for bore (shock) propagation. Use it as the default spatial scheme when a sharp bore must interact with a KdV soliton; its TVD property prevents Gibbs contamination in the Burgers sector.

### kb-burgers-Godunov-preShock-smooth  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: For the early-time Burgers component (before bore forms) in Burgers-swept-KdV coupled problems, even first-order Godunov is sufficient. This establishes a lower-cost option for initialization or short-time baseline runs where the bore has not yet formed.

### kb-kdv-IMEX-CN-spectral-pass  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: IMEX-CN is the recommended baseline for the KdV/swept-KdV component of coupled problems. The CN denominator (1 - dt/2 * ik^3) has magnitude >=1 so it is unconditionally stable for the dispersive stiffness — no exponential overflow. Transfer to coupled Burgers-swept-KdV: handle the swept dispersive term with CN and the Burgers-like coupling explicitly.

### kb-kdv-smallAmplitude-dispersiveRegime  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: In coupled Burgers-swept-KdV: small-amplitude KdV components (after energy exchange with the Burgers bore) will not form stable solitons — they disperse. This sets a threshold: soliton formation in the KdV/swept-KdV sector requires sufficient amplitude. Use this as a diagnostic: if post-interaction KdV amplitudes are O(0.1) or less, expect dispersive radiation rather than soliton trains.

### kb-shallowWater-LaxFriedrichs-stable-smeared  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: Lax-Friedrichs is a reliable failsafe for shallow-water or shallow-water-like components in coupled problems when robustness is paramount and sharp shock resolution is not required. In coupled Burgers-swept-KdV experiments, LxF can serve as a stability baseline for validating more accurate schemes (HLL, MUSCL), but should not be the production scheme where bore sharpness matters for the soliton interaction measurement.

### kb-shallowWater-HLL-dam-break-pass  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: HLL is the recommended Riemann solver for any hyperbolic component in a coupled Burgers-swept-KdV system when the solution may include near-dry or variable-depth regions. Its positivity-preservation and entropy compliance make it safer than Roe for robustness, and it resolves shocks more sharply than Lax-Friedrichs.

### kb-kdv-spectral-solitonAmplitude-conservation  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: Spectral IMEX methods are the preferred discretization for tracking soliton amplitude and phase in the KdV/swept-KdV sector of coupled problems. For Gaussian decomposition into a soliton train, the mass and amplitude conservation properties of these methods ensure that decomposition coefficients remain meaningful over multi-soliton propagation times.

### kb-general-firstOrder-Godunov-preShock-baseline  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: For coupled Burgers-swept-KdV: use Godunov flux as the foundation for the Burgers operator at any time horizon. Before shock formation, first-order Godunov alone suffices; after shock formation, upgrade to MUSCL+Godunov. The entropy-consistent Godunov flux ensures no spurious entropy violations in the bore region during soliton interaction.

### kb-gardner-G2-IMEX-CN-dealiased-stableRadiation  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: IMEX-CN spectral with 2/3 dealiasing is the recommended stable method for the Gardner component of Burgers-swept-KdV (m=0 reduction). However, correctness depends critically on using a proper Gardner soliton IC, not a KdV sech^2 IC. For soliton-stability and Gaussian decomposition tasks, always use the Gardner soliton parametrization; KdV ICs at the same amplitude will produce spurious radiation trains that contaminate any bore-soliton interaction measurement.

### kb-gardner-KdV-method-transfer-moderate-amplitude  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: For the Gardner-reduction (m=0) leg of Burgers-swept-KdV: adopt IMEX-CN spectral + 2/3 dealiasing as the baseline method, transferring directly from the validated KdV solver. No re-engineering of the dispersive (v_xxx) treatment is needed; only the nonlinear stage must be extended to include the cubic term 6vv_x + (3/2)v^2 v_x. Do NOT attempt to port IFRK4 to Gardner: it failed even on the simpler KdV equation and the Gardner cubic nonlinearity would only worsen the overflow in exp(ik^3 t) or tighten the stability constraint further. For amplitude > 2, this positive transfer no longer holds (see kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup); re-evaluate dt before any amplitude increase.

### BKdV-S1  (positive)
  attempted_route: Fourier pseudospectral + 2/3-rule dealiasing (zero |k_idx|>Nx/3=85, 171/256 modes) on every nonlinear product (v^2, u*v, v*v_x, u*u_x) + classical explicit RK4 over full RHS incl. v_xxx; Nx=256, L=30, dt=2e-4, IC v0=1.5 sech^2(x+5), u0=v0^2/2, T=10.
  observation: Reached T=10 cleanly: mass_v conserved <1e-12 (3.000000e+00), sup bounded 3.5-4.0 (final 3.97), tail_frac above 2/3 band ~2e-18 (machine zero), energy grew 2.08->3.69 (physical, not artifact), elapsed 22.66s, no NaN/warnings.
  rationale: Positive finding: 2/3-rule cutoff blocks alias-folded modes from quadratic products feeding resolved band, isolating aliasing (not v_xxx stiffness) as R1's dominant failure. Cutoff also lowers effective k_max from pi/dx to (2/3)pi/dx, raising RK4 dispersion CFL bound from ~1.47e-4 to ~4.94e-4, so dt=2e-4 is now safely below.
  recommended_alternative: Extend by raising amp from 1.5 to 3.0 (top of requested [1,3] range) with identical stack (Nx=256, dt=2e-4, 2/3-dealias, RK4) to probe second failure mode (shock-front aliasing in u from u*u_x or v gradient-steepening exceeding 2/3 band); diagnose via separate sup_u/sup_v and edge_frac in top 10% of resolved band.
  failure: layer=method_failure, scope=regime_bound_failure, action=change_method, risk=low_risk_omission

### BKdV-S1  (positive)
  attempted_route: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (dt=2e-4, Nx=256, L=30); IC v0=amp*sech^2(x+5) with amp=3.0 (top of [1,3]), u0=v0^2/2; T=10; track sup_u, sup_v, mass_v, edge_frac.
  observation: Reached T=10 cleanly: mass_v=6.0 conserved to <1e-12, sup_u rose 4.49->~10.5 with oscillations, sup_v decayed 3.0->1.16, edge_frac peaked ~3e-6 (well below 1e-4 alert), no NaN/overflow, elapsed 22.4s.
  rationale: Positive finding: the predicted second failure mode (high-amp gradient steepening of u or Burgers-side under-resolution at the 2/3 band) did not materialize at amp=3, T=10. The 2/3 cutoff raises dispersion-CFL above dt=2e-4 and u-steepening stayed band-resolved.
  recommended_alternative: To experimentally hit a second failure mode, stress an orthogonal axis: either raise dt above the post-dealias CFL bound ~4.94e-4 (e.g. dt=8e-4 with same RK4) to trigger v_xxx dispersion stiffness, or extend T to 50-100 / use Burgers-dominant IC to force shock formation requiring MUSCL-Godunov on u*u_x.
  failure: layer=hypothesis_failure, scope=regime_bound_failure, action=narrow_claim, risk=low_risk_omission

### BKdV-S7  (positive)
  attempted_route: Gardner-only baseline (m=0 reduction): v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0; IC v_0 = 1.5 sech^2(x+5); Fourier pseudospectral + 2/3 dealias + RK4, Nx=256, L=30, T=10, dt=2e-4. Diagnostics: mass_v, L2v, Gardner H, v_max, n_peaks.
  observation: Clean single-peak propagation over T=10: mass_v and L2v conserved to 0.000000%, H drift +0.188%, v_max in [1.4957, 1.5067] (drift -0.137%), n_peaks=1 throughout, phase speed c~3.564 (peak wraps domain twice). No blowup; positive baseline confirmed.
  rationale: Positive baseline, not a failure. sech^2 is an exact KdV soliton and the cubic (3/2)v^2 v_x is a mild perturbation at A=1.5 (cubic/quadratic flux ratio ~A/4=0.375), so radiative shedding stays sub-percent. Establishes that any E2 BKdV breakdown cannot be blamed on Gardner-side instability or numerics.
  recommended_alternative: Proceed to E2: rerun identical stack under full BKdV (u_t + 3 u u_x = -d_x(3 v^2 + v_xx), v_t + 6 v v_x + v_xxx = -d_x(uv)) with u_0 = v_0^2/2 so m_0=0 to machine precision; track ||m||_L2(t), v_max(t), u_max(t), ||v_BKdV(t)-v_Gardner(t)||_L2 against round1/snapshots.npz.
  failure: layer=hypothesis_failure, scope=local_failure, action=retry, risk=low_risk_omission

### BKdV-S7  (positive)
  attempted_route: Full BKdV (coupled u,v) with IC v0=1.5*sech^2(x+5), u0=v0^2/2 so m0=0; Fourier pseudospectral Nx=256 L=30, 2/3 dealiasing, RK4 dt=2e-4, T=10. Measured ||m||_L2, v_max, u_max, ||v_BKdV-v_Gardner||_L2 vs round1.
  observation: m=0 manifold destroyed on O(1) time: ||m||_L2 reaches 0.74 by t=0.5, 1.22 by t=1, saturates ~2.55. v_max drops 1.498->0.558 (-62.8%), u_max climbs 1.12->3.97, n_peaks 1->8. ||v_BKdV-v_Gardner||_L2 grows to 1.81 (> ||v_BKdV||=0.84). Mass conserved, no blowup.
  rationale: Positive finding: confirms program hypothesis. The m=0 manifold is a kinematic substitution, not a dynamical invariant set of coupled BKdV; the -∂_x(u v) coupling immediately forces m_t off zero, fragmenting the Gardner-stable soliton into a dispersive train while v itself remains bounded (purely physical breakdown).
  recommended_alternative: Proceed to E3: evaluate the BKdV-S5 algebraic identity m_t|_{m=0}=(v-1)(6 v v_x + v_xxx) on v0(x); compute its L2 norm and FFT spectrum to predict the dominant unstable modes, then compare against early-time m_hat(k,t) from this round's snapshots.npz.
  failure: layer=hypothesis_failure, scope=regime_bound_failure, action=retry, risk=low_risk_omission

### BKdV-S7  (positive)
  attempted_route: Evaluate BKdV-S5 algebraic source S(x)=(v0-1)(6 v0 v0_x + v0_xxx) for v0=1.5 sech^2(x+5) via Fourier pseudospectral (Nx=256, L=30, 2/3 dealias); compare ||S||_L2, |S_hat(k)|, and A-sweep against round2 m-trajectory.
  observation: Predicted growth rate ||S||_L2=1.77/t matches observed ||m||_L2(0.5)/0.5=1.47 within 17%; top-5 amplifying modes (n=4,3,5,2,6) coincide with predicted (n=4,5,3,6,2); spectral cos-sim 0.940; A-sweep loglog slope 0.22 for A in [0.25,0.75], 2.49 for A in [1,2.5], pinpointing the (v-1) sign-flip at A=1.
  rationale: Positive finding: the m_t|_{m=0}=(v-1)(6 v v_x + v_xxx) identity is quantitatively predictive at t<=0.5 because at t=0 it is exact by construction and linear extrapolation t*S is the leading Taylor term; saturation to 0.53 by t=2 reflects nonlinear feedback from accumulated m.
  recommended_alternative: Extend to A<1 (e.g. A in {0.3, 0.6, 0.9}) where (v-1)<0 over the soliton core and the dispersive piece dominates: rerun the round2 BKdV stack with v0=A sech^2(x+5), u0=v0^2/2, and check whether m-growth scales as predicted slope 0.22 vs the 2.49 regime above A=1.
  failure: layer=hypothesis_failure, scope=local_failure, action=narrow_claim, risk=low_risk_omission

