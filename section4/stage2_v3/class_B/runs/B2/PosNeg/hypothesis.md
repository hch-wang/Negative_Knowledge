# B2 / PosNeg — Hypothesis report

## Best current mechanism hypothesis

In the BKdV bore-soliton encounter, **the empirical "four-regime"
classification (transmission / reflection / fusion / destruction) does
NOT manifest cleanly in the (u_L, A) plane within the safe envelope
(u_L<=2, A<=2.5) on a periodic L=30 / Nx=256 / T<=3 stack**. Instead the
encounter has **one continuous control variable -- the soliton amplitude
A -- that governs a SMOOTH transition in the soliton's kinematic response
to the bore**, while u_L only modulates the magnitude and the bore is
effectively re-shaped on a sub-encounter timescale by the required
explicit viscosity (BKdV-S6).

Concretely, define the centroid phase shift
    Delta x(uL, A) := x_centroid(uL, A; T) - x_centroid(uL=0, A; T)
between an interaction run and its A-matched free-propagation reference.
The 8-point fine A-sweep (E3 part A, uL in {0.5, 1.5}, T=2) yields a
**monotone and continuous** trajectory:
  - For A < A_c ~ 1.30 : Delta x > 0  (soliton ACCELERATED through bore)
  - For A > A_c        : Delta x < 0  (soliton DECELERATED by bore)
The zero crossing at A_c ~ 1.30 is the same boundary identified
algebraically in BKdV-S5 deep: the source
    m_t|_{m=0} = (v-1)(6 v v_x + v_xxx)
changes sign of its leading factor (v-1) when v exceeds 1 over the
soliton core. Above A=1 the cubic Burgers piece dominates the m-drift
(loglog slope 2.49 in ||S||_L2(A)); below it the dispersive piece
dominates (slope 0.22). E3 part A bumps the practical threshold from
A=1 to A~1.3 because **the soliton peak drops by ~30% during the early
free-propagation transient** before encountering the bore (BKdV-S7
deep: sech^2 is not a coherent BKdV state).

Crucially, two negative controls falsify alternative mechanisms:
  - **Bore-width invariance** (E3 part B): varying bore_w in {0.25, 0.5,
    1.0} at uL in {0.5, 1.5}, A=1.5, T=3 produces *bitwise identical*
    diagnostics (vp, npk, xc, dx differ by < 1e-3). The required
    explicit viscosity nu=5e-2 (BKdV-S6) re-equilibrates the bore on
    timescale ~ 1/(nu*k_bore^2), faster than the encounter, so initial
    bore sharpness does NOT set the regime boundary.
  - **Initial-separation invariance** (E3 part C): varying sep in
    {6, 9, 12} at A=1.5, uL=0.5, T=2 yields dx_centroid in
    {-0.34, -0.38, -0.38} -- variation < 12%. Outcome is set by the
    *integrated* soliton-bore overlap during the run, not by collision
    kinematics, falsifying a "relative-speed gate" picture (H_alpha).

In this safe envelope we therefore observe **two regimes**, not four:
  - REGIME I  (A <~ 1.3, dx > 0): "acceleration-and-retention" --
    soliton emerges leading its free reference, retention ~ 0.8-1.0.
  - REGIME II (A >~ 1.3, dx < 0): "deceleration-and-damping" -- soliton
    lags free reference, retention saturates at ~0.6.
The transition is **SMOOTH** (continuous in A), not sharp. We saw NO
soliton destruction (n_peaks=1 across the whole grid for A>=0.85) and
NO reflection (centroid never moves backward of the soliton's starting
position). Fusion-like absorption is approached at large A but never
crystallizes within T=3.

## Supporting evidence (from your experiments)

- **E1 / F1**: 4x4 coarse (u_L, A) grid over [0.5, 2.0]^2 at T=4 showed
  the classification GRID IS CONSTANT DOWN EACH u_L COLUMN -- outcome
  depends overwhelmingly on A, not u_L. This already weakened
  amplitude-ratio gating (H_beta) and suggested an A-driven mechanism.
  Free-propagation references at T=4 also revealed periodic wrap-around
  contamination at A>=1.5 (kb-burgers-LaxFriedrichs-periodic-longTime),
  motivating the redesigned geometry in E2.
- **E2 / F2**: Redesigned geometry with bore on the right (x=+7), Gardner-
  seeded soliton on the left (x=-5, u0=v0^2/2 + bore), T=2 produced
  clean coherent encounters. The phase-shift Delta x(A) flipped sign
  near A in [1.2, 1.5], suggesting a transition coincident with the
  BKdV-S5 (v-1) threshold. Retention was non-monotonic (drops to 0.58
  at A~1.8, rises to 0.79 at A=2.5), foreshadowing a cubic-self-focusing
  reassertion at very large A.
- **E3 / F3, Part A**: Fine A-sweep (8 points in [0.7, 1.75]) at
  uL in {0.5, 1.5}, T=2 nails down the transition: dx_centroid is
  MONOTONE in A, with zero-crossing at A_c ~ 1.30 for both u_L levels.
  The transition is SMOOTH (no kink). Retention saturates near 0.6 for
  A > 1.4. This pins down the soft-boundary regime structure.
- **E3 / F3, Part B**: bore_w invariance at A=1.5 falsifies any
  "bore sharpness controls outcome" hypothesis -- the viscosity floor
  required for the bore to be physical (BKdV-S6) erases bore-front
  detail on the encounter timescale.
- **E3 / F3, Part C**: separation invariance at A=1.5 falsifies a
  kinematic-collision gate -- the encounter is not characterized by
  the (uL, A, separation, speed) tuple but by the integrated overlap
  evolution.

## Hypotheses considered and falsified / weakened (or shown trivial)

- **H_alpha (kinematic gate: outcome set by relative speed)**:
  FALSIFIED by E3 part C. dx_centroid varies by < 12% across initial
  separations spanning 6 to 12 units (factor 2 in encounter delay).
  The soliton speed in BKdV is approximately the KdV speed c=2A (the
  bore is stationary at uL=0.5 modulo its slow viscous drift), so a
  pure-kinematics theory would predict outcome to be parametrized by
  d/c=d/(2A). Separation-invariance at fixed A rules this out.

- **H_beta (amplitude-ratio gate: outcome set by u_L/A)**:
  FALSIFIED by E1 row-invariance and E3 part A. The classification
  grid in E1 is identical for u_L in {0.5, 1.0, 1.5, 2.0} (each column
  reads the same regime). In E3 part A both u_L=0.5 and u_L=1.5 produce
  the same zero-crossing A_c~1.30 in dx_centroid(A). u_L re-scales the
  magnitude of the phase shift but not its sign-change location.

- **H_gamma (sharp boundary: nonlinear focusing creates a kink)**:
  WEAKENED. Within the safe envelope we resolved the transition at
  resolution Delta A = 0.15 (E3 part A); the dx_centroid trajectory
  is monotone and continuous, with no detectable kink. A_c ~ 1.30
  matches the BKdV-S5 analytic (v-1) sign-flip, and the (v-1) is itself
  a smooth function of v. We cannot rule out a sharp boundary at
  parameters outside our safe envelope (A>2.5 or near the BKdV-S6
  hyperviscous-stability ceiling), but the available evidence supports
  smoothness.

- **H_delta (smooth boundary: gradual coherence loss)**:
  SUPPORTED. dx_centroid(A) varies continuously by ~1.5 units across
  A in [0.7, 1.75]; retention(A) declines smoothly from 1.0 to 0.6
  and saturates. Best-supported hypothesis among the four.

- **Bore-sharpness controls outcome**:
  FALSIFIED (E3 part B). bore_w in {0.25, 0.5, 1.0} gives indistinguishable
  diagnostics because the BKdV-S6-required viscosity floor (nu=5e-2)
  smooths the bore faster than the encounter unfolds.

- **Four-regime classification (transmission/reflection/fusion/destruction)**:
  WEAKENED for this envelope. Within (u_L<=2, A<=2.5, T<=3, periodic
  L=30) we only resolve two smooth subregimes. The remaining "regimes"
  may exist outside the explored envelope (eg destruction at A>3 where
  BKdV-S1 finds dispersive contamination near the dealias edge, or
  reflection if the bore drift were retrograde).

- **TRIVIAL FINDINGS flagged**:
  - E2 mass_v conservation to 1e-10 across all cells is divergence-form
    trivial (BKdV-S2 deep: int v dx is exactly conserved). We do NOT
    cite mass conservation as a mechanism finding.
  - E3 part B identical-to-1e-4 across bore_w levels is **non-trivial
    in this context** because it falsifies the bore-sharpness
    hypothesis; without that hypothesis on the table it would be trivial.

## Open questions / what 1 more experiment would test

- **Map the (extreme-A) failure of the smooth picture.** Push A to
  [2.5, 3.5] with the same Nx=256 stack (BKdV-S1 positive: A=3.0 is
  safe at dt=2e-4). Specifically run an A in {2.7, 3.0, 3.3} sweep at
  uL=0.5, T=2 to test whether dx_centroid continues to drop linearly
  or saturates (saturation = bore becomes opaque). This would
  distinguish the "smooth deceleration" picture from a hidden
  destruction threshold at very large A.
- **Test against the BKdV-S5 deep alternative geometry**: construct a
  Petviashvili-relaxed traveling-wave seed for the soliton instead of
  bare sech^2. If the smooth two-regime picture survives a properly
  coherent IC, that materially strengthens the claim that the
  transition is intrinsic to BKdV (not an artifact of sech^2's drift
  off the m=0 manifold).
- **Resolve A_c more finely.** Our resolution Delta A=0.15 estimates
  A_c=1.30 +/- 0.075; an A in {1.20, 1.25, 1.30, 1.35, 1.40} run
  would localize the zero-crossing to +/- 0.025 and let us test
  whether A_c depends on u_L (we currently see A_c~1.30 for both
  uL=0.5 and uL=1.5, but with only 8 points and uL=1.5 shift slightly
  larger we cannot yet exclude a weak u_L dependence).
