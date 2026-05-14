# B2 / PosOnly — Bore-soliton interaction phase diagram

## Best current mechanism hypothesis

The dominant control of the BKdV bore-soliton encounter is **not** a four-way phase diagram in (u_L, A) but a smooth, two-axis deformation. Outcomes vary continuously with soliton amplitude A (the primary axis) and with bore strength u_L (a secondary, non-monotone modulator). The principal mechanism is intrinsic-to-BKdV soliton instability driven by the loss of the m=0 manifold under the -∂_x(uv) coupling (the BKdV-S7 R2 phenomenology) — and the bore acts as a perturber of that instability, not its cause. The classical regime labels (transmission, reflection, fusion, destruction) are at best smooth crossovers, not discrete states with sharp boundaries.

Concretely, three observable "regimes" can be identified at horizon T=10:
- **Small-A transmission** (A ≲ 0.7): L2(v) ratio ≳ 0.6, single peak, soliton survives with mild trailing radiation. Bore promotes survival here (u_L=2 stabilizes A=0.5 from partial to clean transmission).
- **Intermediate-A destruction-with-plateau** (A ≳ 1.3): final L2(v) ratio collapses onto an attractor value ≈ 0.44 (essentially A-independent across A∈[1.3, 2.0]), with the soliton retaining a coherent residual peak at ~0.44A. This is the "destruction" regime but with a *finite-amplitude residual* rather than full fragmentation.
- **Weak-bore destabilization band** (A ≈ 1.5, u_L ≈ 0.25–0.75): a thin slice where a small but non-zero bore *amplifies* fragmentation (max_n_peaks peaks at 4), reducing L2_ratio below the u_L=0 baseline.

**Phase boundaries** in the A-direction at fixed u_L sit near A ≈ 1.0–1.3, manifest as a 4× drop in |d(L2_ratio)/dA| over a width ΔA ≈ 0.4 and a sign-flip of d(L2_ratio)/dA between A=1.3 and A=1.7 (the L2_ratio reaches its minimum at the BKdV-S7 R3 algebraic crossing point and then plateaus). This is the **observable manifestation of the BKdV-S7 R3 (v−1) sign-flip prediction**, but the soliton-survival signal is a *smoothed crossover*, not a discontinuity — the boundary has finite width on the order of A∼0.4.

**Sharpness verdict: smooth.** No first-order phase transition is observed in the explored range u_L∈[0,3], A∈[0.3,2.0]. Both the A-driven knee at A≈1 and the u_L-driven stabilization onset at u_L≈0.75 are smooth crossovers of width comparable to the underlying parameter scale. The viscosity ablation (ν ∈ {2.5e-2, 5e-2, 1e-1}) varies final-state L2_ratio by ≤3% and never crosses a classification boundary, so the smoothness is not a numerical-viscosity artifact.

## Supporting evidence (from your experiments)

- **From E1 / F1 (T=2.5, 30-point scan):** At short horizon the (u_L, A) plane shows no genuine four-way regime structure. Final v_peak/A at u_L=0 vs u_L=2 differs by <10% across A∈[0.25, 2.0]. n_peaks=1 dominates everywhere; the bore's only consistent effect is *advective* (peak position shifts +1.18 per unit u_L). NO destruction or fusion regime emerges at T=2.5.

- **From E2 / F2 (T=10, 3×4 scan + viscosity ablation):** Destruction *does* emerge at T=10 for A≥1.5, but **with u_L=0 as much as with u_L=2**. The u_L=0 control row (L2_ratio = 0.725, 0.496, 0.436, 0.455 at A = 0.5, 1.0, 1.5, 2.0) demonstrates the destruction is INTRINSIC to BKdV with sech² IC, NOT bore-driven. At fixed A=1.5, the bore *stabilizes*: L2_ratio = 0.436 → 0.588 → 0.640 as u_L = 0 → 1 → 2. This *falsifies* the naive "bore destroys soliton" expectation embedded in the prompt's regime list. Viscosity ablation at (u_L=1.5, A=1.5, T=5): ν ∈ {0.025, 0.05, 0.1} gives v_peak ∈ {0.612, 0.590, 0.575} and L2_ratio ∈ {0.709, 0.694, 0.687} — variation <6% across a 4× viscosity span, all same classification.

- **From E3 / F3 (sharpness + scaling):** Part A (dense A-sweep, u_L=0): d(L2_ratio)/dA drops in magnitude from −0.61 at A=0.4 (midpoint of [0.3, 0.5]) to −0.025 at A=1.4 (a 25× reduction), then *changes sign* at A∈(1.5, 1.7). The L2_ratio plateaus at ≈0.44 for A∈[1.3, 2.0] — the destruction attractor. The transition is **smooth** but with a clear knee near A=1, the BKdV-S7 R3 critical line. Part B (u_L-sweep, A=1.5): L2_ratio is **non-monotone in u_L**, with a *weak-bore destabilization minimum* at u_L=0.25 (L2r=0.401, worse than u_L=0) and *peak fragmentation* (max_n_peaks=4) at u_L=0.5–0.75, then monotonic stabilization to L2r=0.638 at u_L=1.5 (plateau) and a further regime jump at u_L=3 (L2r=0.679, max_n_peaks=1, vpeak/A=0.443 — soliton co-advecting with bore, near-coherent).

## Hypotheses considered and falsified / weakened (or shown trivial)

- **H_A (amplitude-ratio R = u_L/A governs outcome):** Falsified. Outcomes at fixed A vary mildly and non-monotonically in u_L; outcomes at fixed u_L vary strongly in A. The grid is not organized by R = u_L/A. (E1 F1, E2 F2.)

- **H_naive ("bore destroys soliton"):** Falsified. At A=1.5, T=10, u_L=0 (no bore) gives L2_ratio=0.436; adding a bore u_L=2 IMPROVES survival to 0.640. The bore stabilizes the soliton at moderate u_L. (E2 F2 ablation row.)

- **H_C (sharp phase boundaries from bore-shock geometry):** Falsified. All measured transitions are smooth crossovers of width ΔA∼0.4 or Δu_L∼0.5. The smoothness is robust to a 4× viscosity sweep. (E3 F3 Part A.)

- **H_D (relative-speed regime):** Not directly tested as a primary axis; subsumed by A (since soliton speed ≈ 2A) and u_L (bore advection ∝ u_L). The advection effect IS visible in E1 F1 (peak-position dependence linear in u_L) but does not produce a distinct regime by itself — it merely shifts the soliton's transit time.

- **H_stab-monotone (bore monotonically stabilizes soliton):** Falsified at fine u_L resolution. There is a weak-bore destabilization band at u_L∈[0.25, 0.75] where L2_ratio dips below the u_L=0 baseline and fragmentation peaks (max_n_peaks=4). Above u_L≈0.75 the stabilization becomes monotone. (E3 F3 Part B.)

- **H_B-sharp (BKdV-S7 R3 (v−1) sign-flip is a sharp first-order transition):** Partially supported but reframed. The R3 algebraic prediction of a slope change in m-growth at A=1 IS reflected in the observable soliton survival, but the observable manifestation is a SMOOTH knee of width ΔA∼0.4. Sharp-at-the-source-term, smooth-at-the-observable.

- **Trivial findings:** None of the three Findings are tautological. F2's "u_L=0 also shows destruction" is a *causal control* (ablation), not a tautology. F3's L2_ratio plateau at A∈[1.3, 2.0] is non-trivial — it asserts a destruction *attractor* with finite residual amplitude rather than full disintegration.

## Open questions / what 1 more experiment would test

A 4th round would directly visualize the m(x, t) field at the weak-bore destabilization point (u_L=0.5, A=1.5) using the saved snapshot data, and test the mechanism hypothesis: that weak-bore destabilization is the regime where bore-induced u-gradients are large enough to drive m off the zero manifold *and* small enough that the residual sech² shape is still subject to the (v−1)(6 v v_x + v_xxx) algebraic instability of BKdV-S7 R3. The prediction is: ||m||_L2(t) at u_L=0.5 should EXCEED both ||m||_L2(t) at u_L=0 (where there's no bore-induced m-source) AND ||m||_L2(t) at u_L=2 (where bore is strong enough to advect the soliton through the destabilization window before it fragments). A second target would be the small-A side: for A<0.3 the soliton should transition to a true dispersive regime (kb-kdv-smallAmplitude-dispersiveRegime) with no coherent residual — testing whether our 0.44A destruction attractor disappears or persists.
