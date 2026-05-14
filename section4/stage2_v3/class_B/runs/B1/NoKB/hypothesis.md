# B1 / NoKB — Compound-soliton formation mechanism in BKdV

## Best current mechanism hypothesis

The BKdV system does NOT relax to a "u ≈ v²/2 inside support" compound, contrary
to the working physics anchoring in the prompt. Across three rounds of numerical
experiments with Gaussian, sech², asymmetric multipulse, and high- vs
low-amplitude initial conditions — all started exactly on m = 0 (u = v²/2) —
the local m = u − v²/2 inside the v-peak grows from 0 and **stabilises at a
strictly positive value** with u/(v²/2)|_peak between 2 and 9. The peak of u is
**spatially offset to the right of the v-peak** by Δx ≈ 0.5–1.0 (one pulse
width), and this offset grows monotonically. What forms is therefore best
described as a **(v-pulse + trailing u-shock-wake) bound pair**: v carries the
KdV-like dispersive bump on the leading edge, while u accumulates as a slower,
shock-like wake driven by the conservative source `−∂_x(3v² + v_xx)` in the
u-equation. This is the compound structure, but it is *not* a Gardner soliton.

The driving mechanism is **conservative source-mismatch + group-velocity
separation**: the v-equation's nonlinear group velocity at peak amplitude A
predicts c_Gardner = 6A + (3/2)A² ≈ 3 for our late-time A ≈ 0.5; but the
*measured* compound speed is c ≈ 1.0–1.8 across all four runs (E3 LO_nu5e2,
LO_nu0, HI_nu5e2, MULTIPULSE), i.e. only 30–53% of the Gardner prediction. The
dressing −∂_x(u v) in the v-equation slows v substantially; meanwhile the u
field, driven by 3 u u_x (Burgers) and the v²/v_xx source, has its own dynamics
and forms a slow shock that *cannot keep up with* a Gardner-speed v-pulse, so a
quasi-steady wake offset develops. The structure is bound — both v and u stay
co-localised at distance Δx of order one pulse width — but it is dynamically
**stationary in an asymmetric (advecting) frame**, not in a single soliton
co-moving frame.

The Gardner equivalence in the m = 0 reduction is therefore a **kinematic
algebraic identity** (substitute u = v²/2 into the v-equation, get Gardner
formally), not a dynamical attractor. The m = 0 surface in (u, v) phase space
is invariant *as a surface in algebraic equation space*, but **not invariant
under the BKdV flow**: starting on it (m ≡ 0 at t = 0), the dynamics
immediately and ubiquitously moves the state off it inside the pulse support.
The local equivalence is *transient* (holds for t ≲ 0.25 in our runs) and
breaks down by the BKdV's natural separation of u and v dynamics. The basin of
attraction for compound formation is broad — Gaussian, sech², asymmetric
multipulse all produce a compound — but the compound that forms is not Gardner-
like.

## Supporting evidence (from your experiments)

- **From E1 / F1** (single Gaussian, A = 1.5, T = 20, ν = 5 × 10⁻², saved in
  `evidence/E1/`): Starting from u = v²/2 (so m ≡ 0 at t = 0), m_peak rises to
  +1.0 by t = 2 then settles to +0.1 to +0.5 for t > 5. The u-peak is shifted
  Δx ≈ 0.2 → 1.0 to the right of the v-peak over the run. The ratio
  u/(v²/2)|_peak hovers between 1.8 and 9.0 indefinitely; it does NOT approach
  1. Late-time peak speed c ≈ 1.0 vs Gardner prediction ≈ 3 for v_peak ≈ 0.4.

- **From E2 / F2** (three side-by-side ICs, T = 10, saved in `evidence/E2/`):
  Both the low-amplitude case (LO: Gaussian A = 0.6, v_max < 1 throughout) and
  the sech² case (GARDNER_LO: A = 0.6) produce the SAME compound state with
  m_peak ≈ +0.5 at t = 10 and ratio u/(v²/2)|_peak ≈ 8. The pretty-symmetric
  initial conditions DO NOT keep m near 0, even when the linearised analysis
  `m_t|_{m=0} = (v − 1)(6 v v_x + v_xxx)` would suggest the m = 0 manifold is
  "attractive" because (v − 1) < 0. The shape universality across Gaussian vs
  sech² IC means H_F (u-wake structure) is the canonical compound state, not
  IC-specific.

- **From E3 / F3** (viscosity ablation + speed + basin, T = 8, saved in
  `evidence/E3/`): Viscosity ablation: LO_nu5e2 (ν = 0.05) and LO_nu0 (ν = 0)
  both show the same qualitative compound with m_peak = +0.49 and +0.29
  respectively. ν = 0 actually keeps u_max GROWING (1.59 vs 0.78), so the u-
  wake is REAL physics, not a viscosity artifact (H_E falsified). Speeds:
  c_meas/c_Gardner ratios are LO_nu5e2 = 0.47, LO_nu0 = 0.40, HI_nu5e2 = 0.53,
  MULTIPULSE = 0.30. The compound is uniformly sub-Gardner. Basin: the
  asymmetric sign-mixed multipulse IC also forms a compound (positive lobe
  forms v-peak; negative lobe partially disperses), confirming a broad basin
  of attraction; but the compound that forms is the same (v + u-wake) pair,
  not a Gardner soliton.

## Hypotheses considered and falsified / weakened (or shown trivial)

- **H_A (Gardner-template attractor)**: tested in E1 and E3 by comparing
  measured phase speed to c = 6A + (3/2)A² and inspecting u(x) vs v²(x)/2 in
  the peak window. Outcome: c_meas / c_Gardner < 0.55 in every run; u ≠ v²/2
  pointwise. Status: **FALSIFIED**.

- **H_B (Burgers shock fixed-point at u = v²/2)**: implicit in F1 / F2; if
  Burgers self-steepening drove u to a fixed value v²/2, we should observe u
  collapsing toward v²/2 from above. Instead u grows ABOVE v²/2 and develops a
  trailing wake. Status: **FALSIFIED**.

- **H_C (dispersive cleanup)**: not separately experiment-tested, but subsumed
  by the failure of m → 0 globally and locally. Status: **WEAKENED** (the m
  field never decays).

- **H_D ((v − 1) sign-flip mechanism)**: tested in E2 by running A = 0.6 ICs
  (v_max ≤ 0.6 < 1 throughout the run). The (v − 1) factor is everywhere
  negative for these runs, but m still grows monotonically positive to +0.5;
  the diagnostic m_dot_lin = (v − 1)(6 v v_x + v_xxx) is observed POSITIVE at
  the peak in low-amplitude runs (because (6 v v_x + v_xxx) is negative there
  too: trailing edge has v_x < 0 and the dispersive term has its own sign).
  The (v − 1) factor alone does not predict the m = 0 manifold's attractivity.
  Status: **FALSIFIED as a quantitative mechanism**; it is a partial
  contributor but not the dominant story.

- **H_E (viscosity artifact)**: tested by ν ablation in E3 (ν = 0 vs ν = 5 ×
  10⁻²). The (v-pulse + u-wake) compound forms in both cases. Status:
  **FALSIFIED**.

- **H_F (u-wake / asymmetric compound)**: emerged from F1 and was systematically
  tested in E2 and E3. The compound is observed across all IC families and ν
  choices. Status: **SUPPORTED — the working best hypothesis.**

- **H_G (sub-Gardner speed due to u-wake drag)**: directly measured in E3:
  c_meas / c_Gardner = 0.30–0.53. Status: **SUPPORTED**, complements H_F.

## Open questions / what 1 more experiment would test

A fourth round would do exactly one thing: **co-moving-frame analysis of the
compound**. Subtract the empirical phase speed c_meas from x and check whether
(u(ξ, t), v(ξ, t)) becomes time-independent in the moving frame ξ = x − c_meas
t. If yes, the compound is a true 2-field travelling-wave solution of BKdV
(not Gardner!) and one could derive its profile ODE system; the answer to
"what is the compound" would then be a non-Gardner travelling wave with a
fixed Δx between u and v peaks.

A second 4th-round option would be a **longer-time (T = 100) low-amplitude run**
to see whether the u-wake eventually detaches and the v-peak relaxes to a
clean Gardner soliton — i.e. whether the BKdV → Gardner asymptotic limit
exists at all (it might not: H_F suggests the wake is permanent). A third
option would be a **compound–compound collision test** to determine whether
two BKdV compounds interact elastically (like Gardner solitons) or inelastically
(like generic two-field bound states) — this would also discriminate whether
the compound is integrable-like or not.

Finally, the **negative findings about the prompt's anchoring claim** (the
"u ≈ v²/2 inside support" picture) should be reported back to the project as
a candidate correction: at the IC families and amplitudes tested here, the
local compound is NOT u = v²/2 but rather a (v-pulse + u-shock-wake) bound
state with positive m inside the support and sub-Gardner phase speed.
