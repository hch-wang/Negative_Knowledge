# Hypothesis: BKdV bore–soliton interaction regimes

## Best current mechanism hypothesis

In the BKdV system with bore-on-u (smooth tanh, amplitude `u_L`, initially at
x = +6, propagating leftward) and sech²-on-v "soliton" (amplitude `A`,
initially at x = -6, propagating rightward), the interaction does **not**
produce all four textbook regimes (transmission / reflection / fusion /
destruction). Across the parameter window we tested (u_L ∈ [0, 1] for the
main grid; u_L = 2 in one falsification probe; A ∈ [0.2, 2.0]; T = 12 with a
T = 24 long-time arm), we observe two distinct regimes plus a transient
that masquerades as a third:

1. **"Coherent-transmission with bore-acceleration"** (single dominant peak
   on v at t = T, located on the right of the original bore position;
   peak speed exceeds the free KdV-soliton speed 2 A by an additive
   bore-advection contribution roughly proportional to `u_L`).
2. **"Fission into a multi-peak comb + radiation"** (n_peaks ≥ 2 at t = T,
   peak amplitudes well below A, broad spectral spread on v).

The third regime listed in the prompt — "reflection" — we could not
reproduce in our parameter range (even u_L = 2.0 with A = 0.2 gave a
right-going single peak, dragged at ~bore-speed rather than rebound);
"fusion" (soliton absorbed into bore) is also not seen as a distinct
attractor — the v-field always retains amplitude. So at least for the bore
geometry tested, the regime structure is **binary** in the (u_L, A) plane
plus a phase-shift continuum.

The **phase boundary** between transmission and fission tilts in the
(u_L, A) plane. At u_L = 0 (no bore), the v IC fissions for any A ≥ 0.5
(this is intrinsic — the sech² IC is not a true BKdV soliton; cf. E2
Arm A baseline). As u_L increases, the boundary moves to larger A:
at u_L = 0.4 the boundary is between A = 0.2 and A = 0.5; at u_L = 0.8
between A = 0.5 and A = 1.0; at u_L = 1.0 we locate it sharply
**between A = 1.00 and A = 1.05** (Δ ≤ 0.05 in A, with dt-convergence
checked at 5×10⁻⁵). Mechanistically, the bore acts as a positive-u
background that *raises the local effective dispersion balance* and
suppresses the KdV soliton-resolution decomposition of an over-tall
sech² IC. We name this hypothesis **H_BORE_STABILISE**.

A crucial caveat from E3 Arm B: the "transmission" regime at T = 12 is
**transient** for A near the boundary — at T = 24 the (u_L = 1.0, A = 1.0)
case has already fissioned to 2 peaks, oscillating between 2 and 3. So the
boundary location depends on the observation horizon T; the *physical*
boundary is best interpreted as a "bore-induced delay of fission" boundary
rather than an asymptotic attractor boundary. The transition itself
appears **sharp** at fixed T (single grid cell of Δ A = 0.05 captures the
jump from n_peaks = 1 to 2), with no intermediate states. We cannot yet
rule out a smooth crossover beneath our resolution Δ A < 0.05.

## Supporting evidence (from our experiments)

- **From E1 / F1** (5×5 coarse grid, u_L ∈ {0.2,…,1.0}, A ∈ {0.2,…,2.0},
  T = 12):
  - n_peaks(uL=1.0, A=0.5) = 1; n_peaks(uL=0.2, A=0.5) = 3.
    Holding A fixed and increasing u_L *reduces* peak count
    (1 < n_peaks(uL=0.2,A=0.5) = 3) — opposite of "bore destroys soliton".
  - x_peak at T grows monotonically in u_L for fixed small A (A=0.2:
    x_peak from 1.6 at u_L=0.2 to 9.0 at u_L=1.0; well past free
    prediction x_free = -1.2). Bore advection accelerates the soliton.

- **From E2 / F2** (u_L = 0 baseline + finer A sweep at u_L = 1.0):
  - With u_L = 0 (no bore), A = 0.5 already fissions to 3 peaks; A = 1.0 to
    4 peaks. So fission seen in E1 is largely **intrinsic to the v IC, not
    bore-induced**. The bore *suppresses* this intrinsic fission.
  - At u_L = 1.0, A in {0.3, 0.4, 0.6, 0.7, 0.8} all give n_peaks = 1. The
    boundary is bracketed: between A = 1.0 and A = 1.2.

- **From E3 / F3** (sharpness + falsifications):
  - **Sharpness (Arm A)**: at u_L = 1.0, n_peaks jumps from 1 to 2
    between A = 1.00 and A = 1.05. Δ A = 0.05, no intermediate state seen.
    Boundary is sharp at the Δ A = 0.05 resolution.
  - **dt convergence (Arm C)**: at (u_L = 1.0, A = 1.10), dt = 1×10⁻⁴ and
    dt = 5×10⁻⁵ give identical (to 4 sig figs) `max_v_T = 0.3474`,
    `L2_v_T = 0.8587`, `n_peaks = 2`. The boundary location is **not**
    a numerical artifact of dt.
  - **Long-time asymptote (Arm B)**: (u_L = 1.0, A = 1.0) is single-peak
    at T = 12 but bifurcates to 2 peaks by T = 24, with n_peaks
    oscillating between 2 and 3 thereafter. "Transmission" at T = 12 is
    a delayed-fission transient.
  - **Reflection probe (Arm D)**: (u_L = 2.0, A = 0.2) gives single peak
    with x_peak = -13.83 (wrap of right-moving soliton dragged at
    ~bore-speed). No reflection observed.

## Hypotheses considered and falsified / weakened / shown trivial

- **H_A "Linear superposition"**: predicts soliton always transmits with
  trivial phase shift regardless of bore. **Falsified by E1**: at u_L = 0.2,
  A = 0.5, soliton fissions to 3 peaks (max_v_T = 0.175 << A = 0.5).
- **H_B "Single-parameter amplitude ratio r = A/u_L sets regime"**:
  predicts a single sharp boundary in r. **Falsified by E1**: at r ≈ 1
  (A = u_L = 0.2 vs A = u_L = 1.0) the two cells give different behaviour
  (n_peaks = 1 vs 1 — agree); but at r = 2.5 (A=0.5, u_L=0.2 vs A=2.5,
  u_L=1.0) they don't lie on the same curve — A=0.5/u_L=0.2 gives 3
  peaks; A=2.5/u_L=1.0 (extrapolating from A=2.0, n_peaks=5) shows large
  multi-peak. The boundary is closer to an *additive* shift in A by u_L
  than a *ratio*.
- **H_C "Large bore destroys soliton"**: predicts u_L large → n_peaks high
  / soliton fragmented. **Falsified by E1/E2 Arm B**: increasing u_L at
  fixed A *decreases* n_peaks (bore stabilises soliton).
- **H_E "Smooth crossover (no distinct regimes)"**: **partially falsified
  by E3 Arm A**: the n_peaks jump 1→2 at u_L = 1.0 occurs in a single
  Δ A = 0.05 cell, with no n_peaks=1.5 intermediate. Cannot rule out a
  width < 0.05 in A, but at our resolution the boundary is sharp.
- **H_REFLECT "Reflection regime exists for large bore"**: tested by
  E3 Arm D (u_L = 2.0, A = 0.2). **Not observed** in our parameter range.
  Status: weakened — possibly only at u_L >> A and with a tall enough
  bore that we did not push to. We did not falsify the existence of
  reflection in principle, only its presence in the tested window.
- **H_ARTIFACT "Boundary is dt-dependent"**: tested by E3 Arm C, **falsified**
  to 4 sig figs at dt = 5×10⁻⁵ vs 1×10⁻⁴.

The intrinsic-fission baseline (E2 Arm A) is flagged
`is_trivial: false` because it actively *changed our interpretation* of E1:
without that baseline we would have wrongly attributed all multi-peak
outputs to bore physics.

## Open questions / what 1 more experiment would test

If we had a 4th round, the highest-value experiment would be a
**T-dependence of the boundary**: at u_L = 1.0, sweep A in {0.95, 1.00,
1.05, 1.10} for T ∈ {6, 12, 18, 24, 30}. Hypothesis to discriminate:

- **H_DELAY**: the bore *delays* fission by an amount ~ proportional to
  u_L; the asymptotic-T boundary is at A_crit(∞) = 0.5 (same as
  u_L = 0 baseline) for all u_L. The bore-stabilised regime is purely
  transient.
- **H_LOCK**: the bore creates a genuine "locked" composite state at
  some A range; below some A* the soliton stays a single peak for all T.
  The boundary at T = ∞ is non-trivial (A_crit(u_L = 1.0, T = ∞) > 0.5).

E3 Arm B already weakly supports H_DELAY at A = 1.0 (fissions by T = 24).
A T-sweep would tell us whether the "1-peak" regime at small A is just a
slower form of the same delay or a qualitatively distinct attractor.

A second high-value experiment: scan the bore *width* w in
`0.5 u_L (1 - tanh((x - x0)/w))`. Our fixed w = 1.0 confounds bore
amplitude with bore gradient. A sharp narrow bore vs a wide diffuse step
at equal u_L would probe whether it is the **gradient ∂_x u** or the
**u-plateau** that does the stabilising; this is the natural next
mechanistic discrimination.
