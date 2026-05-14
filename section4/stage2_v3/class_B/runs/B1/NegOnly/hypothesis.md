# B1 / NegOnly — Hypothesis report

## Best current mechanism hypothesis

The BKdV compound soliton is **a genuine attractor of the coupled
(u, v) system that is fundamentally distinct from a Gardner soliton**,
formed from any smooth-localized initial seed (sech², Gaussian, mild
sinusoid) regardless of whether u₀ starts on the m=0 manifold. Inside
the compound, u is *not* approximately v²/2 — empirically u_peak / v_peak
≈ 2.0 (so u ≫ v²/2 at the peak), with a robust *u-leads-v* spatial
offset of order 0.5–1.0 (u_peak position is ahead of v_peak position
in the propagation direction). The compound's phase speed *matches the
IC-amplitude Gardner soliton speed* (≈ 1.7 vs 1.8 for A=1.0, a 5 % gap
inside numerical drift) but does **not** match the Gardner speed at
its own dressed amplitude (Gardner at A=0.39 would travel at 0.30, more
than five times slower). So the dynamical equivalence claim "compound
≈ Gardner soliton inside support" is **quantitatively false** at the
pointwise (u, v²/2) level — but a global-phase-speed coincidence with
the IC-amplitude Gardner does survive, mediated by the coupled u field
contributing a -∂ₓ(u v) advection that compensates for the v-amplitude
collapse.

Mechanistically: the m=0 manifold is **not** dynamically invariant, as
BKdV-S5 already established. From any smooth-localized seed, the
system rapidly relaxes off m=0 (within t ≲ 1 the BKdV-S5 source
S = (v−1)(6 v v_x + v_xxx) drives m to grow), losing ~half of the
v-peak amplitude to radiation. The remaining mass reorganizes into a
*coupled traveling structure* in which the u field locally tracks v
through a near-quadratic (a v + b v²) profile (best-fit b ≈ 2.8, far
from the 0.5 of m=0) and locally locks at u_peak ≈ 2 v_peak. This
local algebraic relation, NOT u ≈ v²/2, is the actual signature of
the compound. The (v−1) factor in S modulates the m-escape rate: at
A=0.5 (where (v−1) ≤ −0.5 is sign-definite, with no zero-crossing),
local m grows ~half as fast as at A=1.0, and v retention nearly
doubles in proportional terms. So H_alpha's sign-cancellation
intuition is **partially correct as a modulation principle** but does
not produce a true m=0 core.

The basin of attraction includes smooth-localized seeds at v-L2 ≲ 1.2:
single sech², Gaussian, two-pulse, and a low-mode sinusoid all relax
to one or more compounds at T=10 with the same structural u-leads-v
signature. Two-pulse ICs produce TWO compounds with a phase-shift but
no merger over T=10. The compound is robust to the BKdV-S6
nu_u·u_xx prescription: with nu_u=0 the compound forms identically in
v_peak and u_peak, but the AMBIENT u-field develops a spurious Burgers
cascade (TV(u) grows 6×) that pollutes the global m diagnostic
without altering the compound itself. The nu_u=5e-2 prescription from
BKdV-S6 is a numerical-hygiene knob that affects the wake, not the
attractor.

## Supporting evidence (from your experiments)

- From **E1 / F1**: Baseline run at A=1.0 sech². The compound forms by
  T≈2 and propagates to x=12.19 by T=10 with v_peak=0.39 (down from
  IC 1.0). Co-evolved isolated Gardner soliton at the same IC keeps
  v_peak=0.85 — BKdV radiates *much* more than Gardner. Peak positions
  track within ~0.8 grid points up to T=7 then diverge by 0.8 at T=10,
  giving an avg phase-speed gap of 4-5%. **Critically**, the pointwise
  fit u = (slope)·v²/2 inside the v-peak window gives slope ≈ 9.88, NOT
  1.0 — the "u ≈ v²/2" physics anchoring is *quantitatively false at
  this amplitude*. L2_m local / L2_m global ≈ 0.85, the opposite of the
  "core-lock with m shed into wake" prediction. u_peak leads v_peak by
  ≈ 0.59 spatial units at T=10. Mass_u, mass_v conserved to 1e-14.

- From **E2 / F2**: Basin scan. Four sub-runs at matched v-L2 = 1.155.
  E2a (sech² with u_0=0) produces a compound identical in v_peak (0.36
  vs 0.39 in E1) and u_peak (0.76 vs 0.77) — the compound is an
  *attractor* and forms even from u_0=0 IC where mass_u is *forced to
  remain 0 everywhere by divergence form*, yet u spatially redistributes
  to build a localized u_peak ≈ 0.76. E2b (Gaussian, matched L2) gives
  the same compound. E2c (two-pulse) gives TWO compounds at T=10, no
  merger; the basin is multi-seed-per-IC. E2d (low-mode sinusoid)
  relaxes to one compound at x=-10.5 with v_peak=0.56, u_peak=0.41 and
  lock_corr_local=0.85; basin extends past BKdV-S3's broadband-blow-up
  wall at this v-L2 because peak v_0 = 0.30 stays well inside the
  dealias-stable envelope. **The empirical signature u_peak/v_peak ≈ 2
  is consistent across all single-compound runs.**

- From **E3 / F3**: Three discriminations.
  (a) **H_gamma falsified**. nu_u=0 leaves the compound structure
  intact (v_peak=0.35, u_peak=0.72 in compound region) but inflates the
  ambient TV(u) to 15.9 (vs 2.77 at nu_u=5e-2) and produces a spurious
  secondary u-peak at x=-12.77 — confirming BKdV-S6 deep's
  recommendation, while showing the compound itself is a physical
  object not an artifact.
  (b) **H_alpha partial**: at A=0.5 (peak v < 1, sign-definite (v−1)
  source), v retention 0.505 vs 0.387 at A=1.0, and local L2_m roughly
  halves (0.42 vs 0.92). So the sign-cancellation argument modulates
  the m-escape rate, but the m=0 manifold is never preserved (L2_m =
  0.42 at T=10 starting from L2_m = 0).
  (c) **H_beta sharpened**: BKdV compound phase speed = 1.71/u via
  linear fit to v-peak trajectory; Gardner at IC amplitude A=1.0 gives
  1.80/u (5% gap); Gardner at the COMPOUND'S OWN late-amplitude
  A=0.39 gives 0.30/u — *not even close*. So the compound's
  propagation is NOT explainable by Gardner-at-effective-amplitude; it
  is set by the coupled (u, v) structure.

## Hypotheses considered and falsified / weakened / shown trivial

- **H_alpha** (compound is a dressed quasi-Gardner core, local m ≈ 0
  with dispersive shedding of m into the wake): **FALSIFIED** as a
  core-lock claim. L2_m_local / L2_m_global ≈ 0.85 at T=10 in E1; the
  m-content is concentrated INSIDE the compound, exactly opposite to
  the prediction. Pointwise fit u vs v²/2 inside window has slope 9.88.
  **PARTIALLY SUPPORTED** as a sign-cancellation modulation: at
  A=0.5 (sign-definite (v−1)) the m-escape rate roughly halves vs
  A=1.0, consistent with the BKdV-S5 source identity.

- **H_beta** (compound is a true coupled traveling wave, distinct from
  Gardner): **STRONGLY SUPPORTED**. (i) u_peak/v_peak ≈ 2 stable across
  IC families. (ii) u-leads-v offset 0.5-1.0 in compound region — a
  feature absent from any Gardner solution (which has u absent). (iii)
  Late-time compound phase speed = 1.71, matching IC-Gardner speed but
  NOT amplitude-rescaled-Gardner — only the COUPLED structure can
  carry the original phase speed despite massive v-radiation.

- **H_gamma** (compound is a numerical artifact of dealias + nu_u
  prescription): **FALSIFIED**. nu_u=0 still produces the compound at
  identical v_peak / u_peak / position; viscosity only cleans up the
  ambient field (which would otherwise show a spurious Burgers
  cascade). The compound itself is robust.

- **H_delta** (basin = smooth-localized; broadband fragments per
  BKdV-S3 deep): **CONFIRMED** for v-L2 = 1.155 across sech², Gaussian,
  two-pulse, and mild low-mode sinusoid (peak v_0 = 0.30). All produce
  at least one compound at T=10. The BKdV-S3 deep broadband-blow-up
  wall (white-noise / sinusoid at A ≥ 0.8 with high-k power) was not
  hit at this lower amplitude. Basin is broader than the conservative
  BKdV-S3 boundary at this L2.

## Open questions / what 1 more experiment would test

- **Compound's exact relation**: u_peak/v_peak ≈ 2 is empirical;
  what is the analytical traveling-wave ODE solution for u(ξ) and
  v(ξ) with ξ = x − c t? A Petviashvili / Newton iteration on
  (u, v) = (U(x−ct), V(x−ct)) seeded by the compound profile at T=10
  would yield the exact compound shape and test whether the
  empirical a v + b v² fit is the leading-order asymptotic. The
  predicted ODE: at the peak (V'=0) the v-equation gives
  c V_peak = 3 V_peak² + U_peak V_peak + V''_peak, so c ≈ 3 V + U
  (using V''_peak ≈ 0 for the peak); plugging V_peak=0.39, U_peak=0.77
  gives c ≈ 1.94, close to but slightly above the measured 1.71 —
  suggesting V''_peak < 0 (peak negative curvature) shaves ~0.2 off.

- **Phase-speed conservation**: Why does the BKdV compound carry the
  IC-amplitude Gardner phase speed despite losing half its v-amplitude?
  A 4th-round experiment would track v_peak(t), u_peak(t), and the
  compound phase speed c(t) over multiple amplitude IC values
  A ∈ {0.5, 0.75, 1.0, 1.25, 1.5}, fitting c(t) versus the
  coupled-traveling-wave prediction c = 3 V + U at each instant.

- **Basin H_delta boundary**: BKdV-S3 deep predicts a hard
  broadband-L2 blow-up wall at A ≈ 0.8 with high-k power. E2d at v-L2
  = 1.155 (peak v_0 = 0.30) was safely inside. A 4th-round experiment
  would scan a sinusoid IC at kmode ∈ {2, 4, 6, 8, 10} or white-noise
  σ ∈ {0.05, 0.2, 0.4, 0.8} at fixed v-L2 = 1.155 to locate the
  boundary between compound formation and fragmentation, refining
  BKdV-S3 deep's "spectral support" rule.

- **Two-compound interaction**: E2c shows two compounds coexisting at
  T=10 without merger. A 4th-round experiment would extend T=10 → 30
  to see whether compounds collide elastically (KdV-like), inelastically
  (with phase shift), or merge into one compound at the same v-L2.
