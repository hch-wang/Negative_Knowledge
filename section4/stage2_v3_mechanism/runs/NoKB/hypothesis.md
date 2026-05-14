# Mechanism inquiry: coupled Burgers-swept-KdV system

System studied:
```
u_t + 3 u u_x = - ∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = - ∂_x (u v)
```
Domain x ∈ [-15, 15] periodic, Nx = 256, γ = ν = 1.
Reduction variable m = u − v²/2; m ≡ 0 ⇒ Gardner.

The phenomenon to be explained: generic ICs develop compound (u, v) coherent
structures that propagate as a unit, often *near* but not *on* the m = 0 manifold.

---

## Best current mechanism hypothesis

**H_FORCED-BURGERS-SINK** (the working hypothesis after E1–E3):

The system is NOT pulled to the Gardner (m = 0) manifold. Instead, the dynamics
is dominated by a **forced Burgers loop coupled to a dispersive radiator**:

1. The v-equation `v_t + 6 v v_x + v_xxx = − ∂_x (u v)` looks like KdV plus a
   coupling source. Its KdV part radiates high-k content away from a sech²-like
   coherent envelope; this is the only piece of the dynamics that *dissipates*
   small-scale v structure into the periodic far field.
2. The u-equation `u_t + 3 u u_x = − ∂_x (3 v² + v_xx)` is a **forced Burgers
   equation** whose source `∂_x(3 v² + v_xx)` is determined entirely by v. The
   Burgers self-advection `3 u u_x` is what *transports and steepens* the
   amplitude that the v² forcing keeps pumping into u; without it, u grows
   without bound under continuous v² forcing (see E2 / M2).
3. The "compound coherent state" is therefore a configuration where (i) v
   organizes into a (near-)KdV-pulse that radiates excess high-k content and
   (ii) u settles into a moving front/shock-like profile whose Burgers
   self-flux balances the v² forcing locally. The two fields lock partially
   (lock_corr ≈ 0.3–0.5 typically), not strictly (u = v²/2).

In particular, the m = 0 manifold is **not** an attractor — it is repelling
(see E1). The attractor structure is a multi-component family of "forced-Burgers
sinks coupled to KdV-radiators", and the asymptotic state depends on more than
just the v-mass (see E3: same v-mass IC_D, IC_E, IC_F give different L²_u, L²_v
at t = 20).

Two important caveats:

- This is **not** an integrability claim. H_FORCED-BURGERS-SINK is compatible
  with, but does not require, the system to be integrable. The mechanism is
  energetic/structural, not based on IST.
- The hyperviscosity sweep in E3 (IC_F at 100× hyperviscosity coefficient
  changes ‖m‖_L2 final by ~17 % and L²_u final by ~15 %) shows that the
  quantitative late-time observables are partially set by the dissipation scale.
  The qualitative picture (formation of locked u-shock + v-pulse coherent
  objects with m ≠ 0) survives this sweep, but the literal numerical value of
  ‖m‖ at any specific time is NOT a clean physical invariant.

---

## Supporting evidence (from the three experiments)

### From E1 / F1 (on-manifold vs off-manifold IC)
- **Strong falsifier of H_A (Gardner-manifold attraction):** with an IC that has
  ‖m₀‖_L2 = 0.063 (≈ on-manifold), ‖m‖_L2 grew monotonically to ≈ 1.20 by
  t = 20. With an IC that has ‖m₀‖_L2 = 0.479 (off-manifold), ‖m‖_L2 also went
  to ≈ 1.19 by t = 20. Both ICs converged to nearly identical late-time states
  in this family, but the common state was at ‖m‖_L2 ≈ 1.2, NOT at zero. The
  m = 0 manifold is therefore **repelling**, not attracting.
- E_high_v dropped to ~10 % of its initial value in BOTH runs (radiative loss
  in the v field), while E_high_u grew several orders of magnitude. So v
  *radiates* in the periodic far field while u *accumulates* high-k content
  (steepening). The two fields are not symmetric.
- Mass conservation was exact for both u and v (both equations are divergence
  form; verified numerically to within float precision), so the diagnostics are
  not contaminated by mass drift.
- lock_corr fell from 0.98 → 0.29 (IC_A) and 0.66 → 0.35 (IC_B): the late-time
  field configurations are NOT well-described by u ≈ v²/2.

### From E2 / F2 (coupling ablation)
- **M0 (full system)** baseline: ‖m‖_L2 = 1.19, lock = 0.35, L²_u = 1.20,
  L²_v = 0.56 at t = 20 (same IC as E1's IC_B).
- **M1 (v_xxx removed from v-equation)**: blew up at t = 0.19. v's own KdV
  dispersion is essential for the system to remain stable. Without it, v's
  Burgers-like 6 v v_x self-steepening is unbalanced and modulationally
  unstable. *Caveat:* this is a strong but partly trivial finding — removing
  KdV's dispersion from KdV always destabilizes; it does not by itself prove
  that radiation is the attractor mechanism, only that dispersion is needed for
  evolution to make sense at all.
- **M2 (Burgers self-flux 3 u u_x removed from u-equation)**: did NOT blow up
  but L²_u grew from 0.61 to 2.69 (4.4×) and L²_v from 0.92 to 1.66 (1.8×),
  with ‖m‖_L2 = 2.61. Without u's Burgers self-advection, the v² forcing
  continuously pumps u amplitude with no transport mechanism to spread it.
  This **shows the Burgers self-flux is essential** for the compound-state
  attractor — supporting H_FORCED-BURGERS-SINK.

### From E3 / F3 (robustness + falsification)
- **IC_D (two v-pulses, u₀ = 0)**: ‖m‖_L2 = 0.77, lock = 0.54, L²_u = 0.80 at
  t = 20. Same v-mass as E1 baseline (1.6) but very different late-time state.
  Compound structure forms but is weaker.
- **IC_E (tall narrow v, u₀ = 0)**: ‖m‖_L2 = 1.85, lock = 0.34, L²_u = 1.88.
  Same v-mass; stronger compound structure than IC_D.
- **IC_C (noisy u, clean v)**: ‖m‖_L2 = 6.92 at t = 20 — runaway growth, did
  NOT converge to any compound state on this timescale. Random multi-scale
  noise in u does not seed a compound attractor in T = 20 (basin of attraction
  appears to NOT include arbitrary noise; or convergence is slower).
- **IC_F (E1 baseline at 100× hyperviscosity)**: ‖m‖_L2 = 0.99 (vs 1.19),
  lock = 0.51 (vs 0.35), L²_u = 1.02 (vs 1.20). Quantitative differences
  ≈ 15–45 % suggest the *exact* late-time numerical values are partly set by
  the regularization scale. **The qualitative picture survives the sweep** —
  compound coherent structures still form with m ≠ 0 and partial u/v² locking.
  This is a non-trivial finding: physics is robust to the regularization choice
  in qualitative terms but not quantitatively. Reports of "the late-time state"
  must be interpreted with care.

### Cross-cutting evidence
- Mass conservation exact in all 9 runs (both u, v stayed at the integer-grid
  exact initial-mass value to float precision); reassures us this is not a
  numerical-drift artifact.
- IC_D and IC_E both have v-mass = 1.6 but end up with very different L²_u and
  L²_v. Therefore, the asymptotic state is NOT parameterized by v-mass alone;
  more than one conserved-or-quasi-conserved quantity governs the basin.
  This is a *weakened* finding for any pure "Hamiltonian-ground-state in
  v-mass sector" version of H_C.

---

## Hypotheses considered and falsified / weakened / shown trivial

| Hypothesis | Tested via | Outcome | Status |
|---|---|---|---|
| **H_A: m = 0 (Gardner) manifold attracts** | E1: ICs with ‖m₀‖ ∈ {0.06, 0.48} | ‖m‖ grew in both cases, converging to ≈ 1.2, NOT to 0. The Gardner manifold is repelling on this timescale. | **Falsified.** |
| **H_B: v's dispersive radiation is THE driver** | E2 / M1: removed v_xxx from v-eq | System blew up — modulational instability without dispersion. Removing dispersion does not *eliminate the attractor cleanly*; it just makes the equation ill-posed. Cannot use this as a clean falsifier of H_B *per se* — but the test does say dispersion is necessary. | **Trivial-finding negative result** (dispersion necessary for evolution to be sensible, doesn't isolate radiation as *the* mechanism). |
| **H_C-strict: compound solitons are Hamiltonian extrema in v-mass sector** | E3 / IC_D, IC_E, IC_F all have same v-mass=1.6 | The asymptotic L²_u, L²_v, ‖m‖ differ substantially across these ICs. Asymptotic state is *not* a unique function of v-mass alone. | **Weakened** (more than one conserved/quasi-conserved quantity determines the asymptotic state). |
| **H_F-original: Burgers self-flux is THE driver** | E2 / M2: removed 3 u u_x | Without it, u amplitude grew unboundedly — Burgers self-flux is essential. But isolated, this only shows it's *necessary*, not that it's THE driver. | **Supports** the broader H_FORCED-BURGERS-SINK; rejects the "only this matters" version. |
| **H_TRIVIAL-1: m = 0 invariant set is invariant** | (not run, recognized as trivial) | The claim "m = 0 ⇒ system reduces to Gardner ⇒ m stays 0" is true *by construction* and would not constrain the basin. Recognized in design phase and skipped. | **Trivially true; provides no mechanism information.** |
| **H_TRIVIAL-2: "we ran the system and saw compound solitons"** | — | This is the premise of the task, not a finding. | **Recognized as not a contribution.** |
| **H_NUMERICAL-ARTIFACT** | E3 / IC_F (100× hyperviscosity sweep) | ‖m‖_L2(T) shifted from 1.19 → 0.99 (~17 %) and lock shifted 0.35 → 0.51. **Quantitative** late-time values are dissipation-scale dependent; **qualitative** mechanism (compound formation with m ≠ 0, partial u/v² locking) is robust. | **Partial concern:** qualitative answer survives but quantitative ‖m‖(t) trajectories should not be quoted as physical to better than ~20 %. |
| **H_BASIN-INCLUDES-NOISE** (sub-claim of strong H_FORCED-BURGERS-SINK) | E3 / IC_C (noisy u) | Did NOT converge — kept growing. The basin of attraction does not appear to include arbitrary u-noise on the timescale tested. | **Falsified or basin-restricted.** Compound solitons need *some* coherent seed; pure noise either doesn't relax in T = 20 or sits in a different attractor. |

---

## Open questions / what 1 more experiment would test

If I had a 4th round, the highest-value experiment would be:

**E4 (proposed):** Long-time evolution (T = 80–100) of two ICs from different
  "asymptotic" states in E3 (IC_D's mild compound and IC_E's strong compound),
  with continuous tracking of (L²_u, L²_v, ‖m‖, lock). The question:

  > Are the t = 20 late-time states truly "asymptotic" (genuine attractor
  > fixed points / closed orbits) or are they slowly drifting toward a common
  > universal state on a longer timescale?

  If both ICs drift to a *common* asymptotic state at T = 80, then there IS a
  universal compound-soliton attractor and the t = 20 differences in E3 were
  transient. If they remain distinct, then the attractor *family* is genuinely
  multi-dimensional and H_FORCED-BURGERS-SINK in its multi-attractor form is
  supported.

Three secondary open questions:
- (a) Is the partial lock_corr ≈ 0.3–0.5 universal, or does it eventually
  approach a specific value that can be predicted from the v-amplitude?
  A scaling sweep with several v-amplitudes at T = 80 would clarify.
- (b) What happens to IC_C-like noisy initial conditions on T = 100? Do they
  *eventually* coalesce into compound solitons, or are they in a permanent
  turbulent state? This tests whether the basin of attraction is universal or
  has obstacles.
- (c) Identify the relevant slow-conserved or near-conserved quantity beyond
  v-mass. Candidates: momentum ∫ u v dx, "energy" ∫ (½ u² + v² + ½ v_x²) dx,
  or some IST-like spectral invariant. The current data show v-mass alone is
  not sufficient (IC_D vs IC_E with same v-mass differ at t = 20).

---

## Methods notes

Numerical stack (from `candidate.py`, identical to the working solver in the
prompt):
- Fourier pseudospectral with Nx = 256 on L = 30 periodic domain.
- 2/3-rule dealiasing on every nonlinear product.
- IF-RK4: integrating factor exp(−i k³ t) absorbs the linear dispersive part
  of v's equation; then RK4 in the rotated frame for the remaining nonlinear
  + cross-coupling terms.
- Mild hyperviscosity on u: −ν_h k^(2p) u_hat with p = 8 and ν_h = 10⁻²².
  Sweep to 10⁻²⁰ in E3 IC_F shifts late-time ‖m‖ by ~17 %, so the *exact*
  numerical late-time values are dissipation-set; the qualitative mechanism is
  robust.
- dt = 5×10⁻⁴, T = 20.
- Mass conservation verified exact to float precision in all runs.

Negative-knowledge inventory (per task definition):
- Trivial-finding negative results explicitly flagged: H_TRIVIAL-1, H_TRIVIAL-2.
- Trivial-near-tautology: M1 blow-up is not a clean falsifier of H_B (dispersion
  is necessary for KdV-style evolution to be well-posed; this is dispersive
  PDE theory, not a mechanism finding).
- Initial-IC-amplitude blowup at dt = 2e-3 in the first E1 attempt was a
  numerical re-tuning (smaller dt + add hyperviscosity), explicitly NOT counted
  as a round per the prompt's "bug-fix re-runs that test the SAME hypothesis
  do NOT count" rule.
