# B2 — Bore-soliton interaction phase diagram (NegOnly)

## Best current mechanism hypothesis

**The bore-soliton outcome in BKdV is governed primarily by the v-soliton amplitude A, not by the bore amplitude u_L.** Across an order-of-magnitude sweep u_L ∈ {0.3, 0.6, 1.0, 1.5} the late-time v-peak retention varies by less than 10% at fixed A, while across A ∈ {0.5, 0.7, 0.9, 1.1, 1.3, 1.5} the retention drops monotonically from ~0.79 to ~0.24. The phase diagram in (u_L, A) has nearly-horizontal contours: regime boundaries are set by A.

Three distinguishable regimes emerge:
- **Transmission (A ≲ 0.9)**: a single coherent peak survives the encounter with retention v_peak_end/A ≳ 0.5 (single dominant local maximum, no fragmentation).
- **Ambiguous / marginal (A ≈ 1.0–1.1)**: retention ≈ 0.4–0.5, still a single peak, but the soliton is heavily eroded and clearly off-equilibrium.
- **Destruction (A ≳ 1.3)**: retention drops below 0.35, the v-field fragments into 4–7 peaks of comparable height (dispersive radiation), and the u-field develops strong negative excursions (u_min < −0.5).

The transition is **smooth, not sharp**: it spans roughly Δ_A ≈ 0.4 around A ≈ 1.0. The locus A ≈ 1 corresponds exactly to the sign flip of the (v − 1) factor in the m=0 instability source S = (v − 1)(6 v v_x + v_xxx) documented in BKdV-S7. When peak v > 1 the source is nonzero and drives m = u − v²/2 off zero, which the −∂_x(uv) coupling feeds back into v as fragmentation. The bore u_L is a secondary perturbation: it accelerates the decay slightly (E3 zero-bore vs u_L=0.6 at A=1.5: retention 0.35 → 0.24) and biases u away from the m=0 manifold from the start, but it does not change the regime.

This means the "bore-soliton interaction" as posed in the research question is partly a misnomer for the parameters tested: at A ≥ 1.5 the sech² soliton fragments via intrinsic BKdV m=0 instability even when u≡0, so what looks like "bore destroys soliton" is mostly "BKdV destroys sech² ansatz". The bore's distinguishable contribution is small relative to this intrinsic effect.

## Supporting evidence (from your experiments)

- **From E1 / F1** (u_L=0.5, A=1.5, T=8, anchor): v_peak drops 1.50 → 0.36 (ratio 0.24), n_peaks grows 1 → 4, u_max reaches 2.20 (>4× u_L), u_min dips to −0.52. Both ∫u dx and ∫v dx are conserved to 6 decimal places throughout — solver passes the BKdV-S6 viscosity-required test (ν=5e-2) and the BKdV-S1 dealias-required test. L2_v decays monotonically 1.86 → 0.75 (energy bleeds from coherent core into dispersive wash). The soliton wraps around the periodic domain by t≈3 (consistent with KdV speed c_s≈2A=3.0) and meets the bore in the right half thereafter.

- **From E2 / F2** (4×4 grid u_L ∈ {0.3, 0.6, 1.0, 1.5} × A ∈ {0.5, 1.0, 1.5, 2.0}, T=6): the v_peak_ratio is a function of A almost independent of u_L. At A=0.5 ratio≈0.78 ± 0.01 across all u_L; at A=1.0 ratio≈0.46 ± 0.02 across all u_L (except u_L=1.5 where the bore is amplitude-comparable, giving 0.43); at A=1.5 ratio≈0.26 ± 0.03; at A=2.0 ratio≈0.21 ± 0.02. n_peaks similarly clusters: 1 at A ≤ 1.0, 5–7 at A ≥ 1.5. This **falsifies the kinematic-threshold hypothesis** (H_A: outcome controlled by c_b vs c_s ratio).

- **From E3 / F3a** (A-refinement at fixed u_L=0.6): the A-axis transition is smooth and monotone. v_peak_ratio: 0.87 (A=0.3) → 0.79 (A=0.5) → 0.63 (A=0.7) → 0.52 (A=0.9) → 0.42 (A=1.1) → 0.31 (A=1.3) → 0.24 (A=1.5). n_peaks remains 1 up through A=1.1, then jumps to 4 at A=1.3 and 5 at A=1.5. The transition centre A_c ≈ 1.0 ± 0.2 (where n_peaks first exceeds 1 and ratio crosses 0.5).

- **From E3 / F3b** (zero-bore control u_L=0, A ∈ {0.5, 1.0, 1.5}): even with u(x, 0) ≡ 0, the soliton **still fragments at A=1.5** (3 peaks, ratio 0.35) and u spontaneously develops O(1) amplitude (u_max=1.15). At A=0.5 and A=1.0 the zero-bore case is statistically indistinguishable from the u_L=0.6 case. This **discriminates the mechanism**: bore presence is not necessary for destruction at A ≥ 1.5. The destruction is the BKdV-S5/S7 m=0 instability, not a bore-driven effect.

## Hypotheses considered and falsified / weakened (or shown trivial)

- **H_A — Kinematic threshold (c_b > c_s ⇒ bore overruns soliton ⇒ destruction; c_s > c_b ⇒ transmission)**: Falsified by E2/F2. At fixed A=1.5, varying u_L by 5× (0.3 → 1.5) changes c_b = (3/2)u_L by the same factor, yet retention varies by <12% and the regime label stays "destruction" throughout. The kinematic prediction would have given a sharp threshold at c_b ≈ c_s, i.e. u_L ≈ (4/3)A = 2.0 at A=1.5 — but we see no qualitative change crossing that line.

- **H_B — Amplitude-ratio threshold (outcome depends on A/u_L with O(1) critical value)**: Weakened. The retention is essentially A-only, not ratio-only. The diagonal A=u_L line (e.g. (1.0, 1.0), (1.5, 1.5)) is not a contour of retention. Some weak dependence on u_L exists (E3 zero-bore vs u_L=0.6 at A=1.5 differ by 0.11 in ratio), so the ratio is not strictly irrelevant — but it is not the principal axis.

- **H_C — Smooth crossover dominated by inelastic losses, no sharp boundary**: Supported partially. The transition along A IS smooth (Δ_A ≈ 0.4 around A_c ≈ 1.0). But "no boundary" is too weak: there IS a structural change at A ≈ 1 — n_peaks transitions 1 → ≥3 — and this aligns with the (v − 1) sign-flip in the BKdV-S7 m=0 source S = (v − 1)(6 v v_x + v_xxx). So the boundary is locatable, just not infinitely sharp.

- **H_D — m=0-instability is the dominant fragmentation mechanism, not bore-soliton coupling** (emerged after F2): SUPPORTED by E3b zero-bore control. Status: best current hypothesis.

- **Trivial / not informative**: a single high-resolution single-point run (e.g. running E1 at higher Nx or different dt) would have been a trivial "the solver is converged" check that does not address the mechanism question. We chose not to spend a round on that, citing BKdV-S1/S4 which already characterize the safe envelope and BKdV-S6 which prescribes the working u-viscosity ν=5e-2.

## Open questions / what 1 more experiment would test

A 4th round would test whether **a properly relaxed BKdV traveling-wave state** (built by Petviashvili / imaginary-time iteration as recommended by BKdV-S7's `recommended_alternative`) **survives the bore encounter intact at A=1.5**, when it would NOT have survived as a sech² ansatz. If yes: the "destruction at A>1" regime is entirely a consequence of starting with the wrong ansatz; the *real* BKdV soliton may transmit cleanly even at A=1.5 against a u_L=1.5 bore. If no: there is genuine bore-induced destruction in the full coupled system, distinct from the sech²-ansatz mismatch. This is the central residual ambiguity in our F2/F3 conclusion: we have shown that the (sech², u_L)-encounter is A-dominated, but we have not separated "wrong-ansatz radiation" from "bore-driven coupling damage". Without a true BKdV soliton reference, "transmission" at low A may itself be partially the wrong-ansatz radiation being slow enough to escape detection in T=6.

Secondary: a sweep of soliton sign and bore polarity (e.g. negative bore u_L < 0 or rarefaction) at fixed A=1.0 would test asymmetry; we predict the destructive coupling is via |u|·v through the −∂_x(uv) flux, so polarity should be near-symmetric in outcome.
