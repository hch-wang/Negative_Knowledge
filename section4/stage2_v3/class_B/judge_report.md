# Class B Judge Report — 8-cell Comprehensive Evaluation

This report evaluates 8 mechanism-inquiry research outputs over the coupled Burgers-swept-KdV (BKdV) PDE, organized as 2 tasks × 4 knowledge-bank conditions, 3 research rounds per cell. The evaluation is structured around the rubric and oracles defined in `scripts/judge_prompt.md`.

---

## Per-cell evaluation

### B1 — Compound-soliton mechanism, basin of attraction, Gardner relation

| Cell | Mech. quality (0-3) | Empirical rigor (0-3) | Substantive contrib (0-3) | Bank use quality (0-3) | Honest limitations (0-3) | Total /15 | Verdict |
|---|---|---|---|---|---|---|---|
| B1/NoKB    | 3 | 3 | 3 | NA | 3 | 12/12 | Excellent |
| B1/PosOnly | 3 | 3 | 3 | 3  | 3 | 15/15 | Outstanding |
| B1/NegOnly | 3 | 3 | 3 | 2  | 2 | 13/15 | Strong, some overclaim |
| B1/PosNeg  | 3 | 3 | 3 | 3  | 3 | 15/15 | Outstanding |

**B1/NoKB.** Posed 7 hypotheses (H_A...H_G), discriminated 5 via 3 experiments with clean ablation (IC shape, amplitude, viscosity, multipulse). Quantitatively pinned c_meas/c_Gardner = 0.30-0.53 across runs, and observed a (v-pulse + trailing u-shock) wake structure with positive m. Honest about limitations and proposes a clear 4th-round test (co-moving frame analysis). Cleanly falsifies the prompt's "u ≈ v²/2" anchoring without bank guidance.

**B1/PosOnly.** Strongest cell of the eight. Quantitatively grounded mechanism with separate H_alpha (lifetime), H_beta (radiative cleansing — the new physical contribution), H_gamma (Gardner IC selection, falsified), and H_delta (amplitude basin). The r_local = ||m||_in/||m||_global monotone decay from 0.99 → 0.45 is a sharp, falsifiable diagnostic. Cited BKdV-S5/S7 deep identities operationally (predicted A_c ≈ 1 from (v-1) sign-flip, observed locked-phase non-monotone in A peaking near A=0.9 — exactly the predicted slope-22-to-249 transition). Even reports a bug-fix rerun (Nx=512 dt=1e-4 blew up, dt=2.5e-5 fixed) with appropriate transparency.

**B1/NegOnly.** Rigorous structural finding (u_peak/v_peak ≈ 2 stable across IC families; u-leads-v offset; phase-speed matches IC-Gardner not amplitude-Gardner). But the "phase speed matches IC-amplitude Gardner" claim warrants scrutiny — see Concerns section. Bank use is genuine (rejects shock-capturing entries with reasons, cites BKdV-S5/S6/S7 for hypothesis framing) but more selective than PosOnly. Limitations are acknowledged but somewhat soft ("compound IS an attractor" is a strong claim that the data over T=10 only partially supports).

**B1/PosNeg.** Most analytically ambitious. Derives a steady-frame traveling-wave constraint (3/2)U² − U(c+V) + cV = 0 → U₋(V;c) = [(c+V) − √(c²−4cV+V²)]/3 from the BKdV ODEs, then *tests four candidate algebraic relations* against the t=10 snapshot in order: m=0 (RMS 0.257, falsified), linear-rescaled (RMS 0.054), TW small-V leading (RMS 0.144), full TW branch (RMS 0.115). This is genuine quantitative discrimination. Amplitude sweep produces a clean basin map with upper boundary at A≈2 (shattering) and lower at A≈0.3 (dispersive). Explicit Petviashvili iteration is the proposed 4th round, the right next step. The internal consistency between empirical α≈12 "linear-rescaled lock" and the TW branch is acknowledged honestly as "slowly modulated relaxation toward TW."

### B2 — Bore-soliton phase diagram

| Cell | Mech. quality (0-3) | Empirical rigor (0-3) | Substantive contrib (0-3) | Bank use quality (0-3) | Honest limitations (0-3) | Total /15 | Verdict |
|---|---|---|---|---|---|---|---|
| B2/NoKB    | 3 | 3 | 3 | NA | 3 | 12/12 | Excellent |
| B2/PosOnly | 3 | 3 | 3 | 2  | 3 | 14/15 | Strong |
| B2/NegOnly | 2 | 3 | 2 | 2  | 3 | 12/15 | Solid but conservative |
| B2/PosNeg  | 3 | 3 | 3 | 3  | 3 | 15/15 | Outstanding |

**B2/NoKB.** Best B2 cell on rigor-for-rigor. Discovers the bore-stabilization effect (n_peaks decreases with u_L at fixed A — opposite of "bore destroys"), brackets the sharp transition at u_L=1.0 to A∈(1.00, 1.05] with ΔA=0.05 resolution, then crucially shows via Arm B (T=24) that this "transmission" regime is a *transient delayed fission*, not an attractor. Excellent ablation logic. Tests dt-convergence (boundary not numerical artifact) and reflection probe (negative). The T-dependence caveat is exactly the right honest concern.

**B2/PosOnly.** Identifies the same intrinsic-loss-dominated structure but with three-regime structure on u_L axis at A=1.5 and characterizes a *weak-bore destabilization band* at u_L≈0.25-0.75 — a novel, non-trivial finding. L2_ratio attractor at ≈0.44 for A∈[1.3, 2.0] is also nicely quantitative. Verifies viscosity invariance (ν ∈ {2.5e-2, 5e-2, 1e-1} → ≤6% drift). Bank use is moderately deep but the BKdV-S7-R3 "kink at A=1" prediction is over-interpreted: observed transition is smooth with width 0.4 and the connection is descriptive, not predictive.

**B2/NegOnly.** Cleanly identifies the A-dominated phase diagram with horizontal contours and the zero-bore control (u_L=0 still fragments at A=1.5) as the decisive falsification of "bore drives destruction." This is the same negative-knowledge conclusion the other cells reach. However, this cell is the most conservative quantitatively (only 4×4 grid plus refinement on A axis), uses only T=6-8 (so cannot see the delayed-fission asymptote that NoKB's T=24 reveals), and ends with a more cautious mechanism statement than is warranted by its data. Bank use is principled but limited mostly to BKdV-S5/S7 anchoring.

**B2/PosNeg.** Uniquely identifies a continuous *phase-shift Δx(uL,A) sign-flip* at A_c≈1.30 as the cleanest order parameter, with monotone & smooth dx_centroid trajectory in fine A-resolution (ΔA=0.15). Two independent negative controls — bore-width invariance (bw ∈ {0.25, 0.5, 1.0} → bitwise identical) and initial-separation invariance (sep ∈ {6,9,12} → dx variation <12%) — sharply falsify "bore sharpness controls outcome" and "kinematic gate." The bore-width invariance result mechanistically attributes the equilibration to the BKdV-S6-mandated viscosity smoothing the bore-front faster than the encounter — this is a real physical insight, properly traced. The "two regimes within safe envelope (acceleration vs deceleration)" framing is the most precise statement among the four B2 cells.

---

## Cross-cell consistency check

### B1 cross-cell

**Agreement points (all 4 cells):**
- The "u ≈ v²/2 inside support" anchoring of the prompt is **falsified** at the pointwise level. All four cells report u/(v²/2) at peak much larger than 1 (ratios 2-10).
- The m=0 manifold is *not* dynamically invariant. All four cells observe m growing from 0 and staying positive inside the v-peak.
- Smooth-localized ICs (Gaussian, sech², two-pulse) form *some* coherent compound; sub-threshold (A≲0.3) ICs disperse.
- The Gardner equivalence claim is at best heuristic, not pointwise.

**Disagreement / divergence points:**
1. **Persistence vs transience.** PosOnly says the compound is *transient* (fragments to ~10-15 peaks by T=10 at A=1.5, locked phase ~0.5s). NoKB, NegOnly, PosNeg all describe a more persistent compound at T=10 with single dominant peak. The discrepancy is partly methodological: PosOnly used Nx=256 with sech² A∈{0.4,…,2.0} and observed late-time fragmentation that Nx=512 convergence-checked; NoKB used A=0.6 sech² and reports a coherent compound at T=20; NegOnly used A=1.0 sech² and reports a coherent compound at T=10 with v_peak=0.387. The qualitative late-time picture (persistent compound at moderate A, fragmentation at large A or specific spectral structure) is consistent across cells if one accounts for amplitude — but the precise A threshold and time horizon differ. **This is partly substantive: the "10-15 peaks at A=1.5" in PosOnly is genuinely a different outcome from NegOnly's "single peak with u-leads-v offset" at A=1.0.**
2. **Phase speed scaling.** NoKB reports c_meas / c_Gardner = 0.30-0.53 (sub-Gardner). NegOnly reports c_BKdV = 1.71 vs c_Gardner-at-IC = 1.80 (only 5% gap) — claiming the compound preserves IC-amplitude Gardner speed via coupling. PosOnly reports c_emp during locked phase tracking the order of c_Gardner. **These three pictures are quantitatively inconsistent unless we recognize they measure different quantities at different times.** NoKB measures the late-time compound (t>13) speed against c=6A+1.5A² at *late-time A*; NegOnly compares to c at *IC-time A*. NegOnly's framing is striking but rests on equating two different reference amplitudes, which the cell itself flags partially.
3. **What the compound "is".** PosNeg gives the most rigorous local-algebra characterization (linear lock u = αv²/2 + β with α ≈ 12, R²=0.94, plus TW branch fit R²=0.73). NegOnly gives u_peak/v_peak ≈ 2 with u-leads-v offset. NoKB gives "(v-pulse + trailing u-shock-wake)". These are reconcilable if (PosNeg's algebra is the in-peak structure, NegOnly's offset is the spatial geometry, NoKB's wake is the asymmetric tail), but no single cell synthesizes all three pictures.

### B2 cross-cell

**Strong agreement (all 4 cells):**
- "Bore destroys soliton" naive framing is *falsified*. Across all cells, u_L = 0 control already produces fragmentation at A≳1.5, and increasing u_L often *stabilizes* (NoKB, PosOnly, NegOnly) or merely shifts phase (PosNeg).
- The transition is centered near A ≈ 1.0-1.3 (BKdV-S7 (v-1) algebraic threshold), and is **smooth** rather than sharp in retention (PosOnly width ΔA≈0.4; PosNeg width ≈ 0.15 resolved; NegOnly ΔA≈0.4).
- Reflection regime is *not observed* in tested envelopes.
- Intrinsic IC-mismatch (sech² not being a true BKdV state) is the dominant cause of "destruction"; all four cells reach this conclusion.

**Disagreement:**
1. **Sharp vs smooth.** B2/NoKB claims a sharp boundary in n_peaks (jump 1→2 within ΔA=0.05 at u_L=1.0, T=12); B2/PosOnly and B2/NegOnly claim smooth crossover with width ΔA≈0.4; B2/PosNeg claims smooth with resolved zero-crossing at A_c=1.30 (ΔA=0.15). The discrepancy is largely methodological: NoKB measured n_peaks as the order parameter and observed a discrete jump (which n_peaks is, by definition); the others measured L2 retention or Δx and observed continuous variation. **All four cells are correct on their own diagnostics**: n_peaks integer-valued so always jumps; retention is smooth. The paper should clearly state the *diagnostic-dependent* sharpness, not pick one.
2. **Transient vs asymptotic.** Only B2/NoKB ran to T=24 (Arm B) and discovered that the "single-peak" regime is delayed fission. Other cells used T ≤ 10. PosOnly and NegOnly accept a possibly-transient classification without flagging it; only NoKB explicitly raises the T-dependence concern.
3. **Weak-bore destabilization.** Only B2/PosOnly identifies a non-monotone u_L dependence with destabilization band at u_L≈0.25-0.75 (max_n_peaks=4) and the subsequent regimes. Other cells either did not scan u_L finely enough (NoKB, PosNeg) or did not sample below u_L=0.3 (NegOnly). **This is a substantive finding unique to PosOnly that the others missed for sampling reasons; needs cross-validation in a future round.**

---

## Physics correctness check (oracle comparison)

Mapping each cell's central claims against the 4 independent oracles:

### Oracle 1: m=0 manifold algebraic identity m_t|_{m=0} = (v-1)(6vv_x + v_xxx) → not invariant
- B1/NoKB: ✓ explicitly tested via H_D, observed m_dot_lin positive in low-A regime, falsified (v-1)-sign-flip-alone as mechanism. Consistent.
- B1/PosOnly: ✓ cited BKdV-S5/S7-deep, derived τ_alpha lifetime from source magnitude; A-sweep peaks near A=0.9 (sign-flip region) — quantitative confirmation.
- B1/NegOnly: ✓ explicit, sign-cancellation modulation observed at A=0.5 (m-escape rate halved).
- B1/PosNeg: ✓ embedded as the falsification of H_alpha (m=0 ansatz RMS 0.257 vs linear 0.054).
- B2/NoKB: implicitly consistent (bore stabilizes — interpretation differs but no direct contradiction).
- B2/PosOnly: ✓ explicit, identifies A_c≈1 as the knee with slope drop 4×, matches loglog slope 0.22 → 2.49.
- B2/NegOnly: ✓ explicit, A_c≈1.0±0.2 zero-bore control falsifies bore-driven destruction.
- B2/PosNeg: ✓ explicit, A_c=1.30 (shifted from algebraic 1.0 by 30% transient peak loss).

All 8 cells consistent with Oracle 1.

### Oracle 2: BKdV-S7 quantitative breakdown (A=1.5 sech² IC, T=10 → v_max 1.498→0.558, ||m||_L2 → 2.55, n_peaks 1→8)
- B1/PosOnly: directly cited; their own A=1.5 sech² m_0=0 IC run gives ||m||_L2=2.91 at T=2, n_peaks=11 at T=10 — close to oracle. ✓
- B2/NoKB: A=1.5 at u_L=0 fragments (consistent), n_peaks 3-4 at T=10 (lower than 8, but their analysis is at different IC geometry — bore-on-u not u₀=v₀²/2). Plausible.
- B2/NegOnly: u_L=0.6 A=1.5 T=8 → v_peak 0.36, n_peaks 4, ratio 0.24. Slight quantitative offset from oracle (oracle gives ratio 0.37 at T=10), but consistent qualitatively. ✓
- Other cells: oracle 2 less directly relevant.

### Oracle 3: BKdV-S6 viscosity (Gibbs blow-up without u-viscosity for bore IC, ν=5e-2 default)
- B1/NoKB: tested ν=0 vs 5e-2 at LO IC (no bore). Compound forms in both; ν=0 develops sharper u-wake. Consistent with oracle (no bore → ν not strictly required, but stabilizes).
- B1/NegOnly: explicit nu_u=0 ablation gives spurious Burgers cascade with TV(u) growing 6× and a fake u-peak — matches oracle's "Gibbs growth" warning. ✓
- All B2 cells use ν=5e-2 default; PosOnly's viscosity ablation across ν ∈ {2.5e-2, 5e-2, 1e-1} produces <6% drift — within oracle's "comfortable default" band. ✓
- B2/PosNeg's bore-width invariance argument explicitly leverages oracle 3: ν=5e-2 smooths bore on sub-encounter timescale. Novel mechanistic interpretation of oracle. ✓

### Oracle 4: BKdV-S3 basin geometry (smooth-localized → compound; broadband → cascade)
- B1/NegOnly: low-mode sinusoid IC (E2d) forms a compound — exceeds basin width predicted by BKdV-S3-deep (which warned of broadband blow-up at A≥0.8). The cell notes this explicitly: "BKdV-S3 deep's broadband-blow-up wall was NOT hit at this v-L2=1.155 (peak v_0=0.30)." Soft contradiction — actually the basin is *broader* than BKdV-S3 predicted at this lower amplitude. **Plausible refinement of the oracle, not a contradiction.**
- B1/PosNeg: broadband cosine IC at A=0.4 fails to form compound (R²=0.087); consistent with oracle.
- Other cells consistent.

### Beyond oracle — agent-original quantitative claims

| Claim | Cell | Judge verdict |
|---|---|---|
| c_meas / c_Gardner ≈ 0.30-0.53 across 4 runs | B1/NoKB | **Plausible** (consistent with H_F's u-wake drag mechanism) |
| r_local = ||m||_in/||m||_global decreases monotonically 0.99 → 0.45 | B1/PosOnly | **Plausible and important** — proper falsifiable diagnostic |
| α = du/d(v²/2) ≈ 12 at T=10, R²=0.94 | B1/PosNeg | **Plausible**, but tension with NegOnly's a≈0.4, b≈2.8 quadratic fit. Both can be true if fits use different windows. |
| u_peak/v_peak ≈ 2 stable across IC families | B1/NegOnly | **Plausible** at this amplitude regime, but only verified at A∈[0.5, 1.0] |
| BKdV compound speed = IC-amplitude-Gardner speed | B1/NegOnly | **Suspicious** — see Concerns. The 5% match could be coincidence given different reference amplitudes. |
| Sharp boundary ΔA=0.05 in n_peaks at u_L=1.0 | B2/NoKB | **Plausible** (n_peaks is integer; "sharp" here means observation at one diagnostic) |
| Weak-bore destabilization band at u_L∈[0.25, 0.75] | B2/PosOnly | **Plausible and novel** — needs cross-cell validation; only this cell scanned u_L finely |
| L2_ratio attractor at ≈0.44 for A∈[1.3, 2.0] | B2/PosOnly | **Plausible** at T=10; PosOnly itself flags this as a "destruction attractor with finite residual amplitude" |
| Phase-shift Δx zero-crossing at A_c=1.30 ± 0.075 | B2/PosNeg | **Plausible and clean**; novel diagnostic; well-supported by data |
| Bore-width invariance to 1e-4 (mechanism: viscosity equilibrates bore) | B2/PosNeg | **Plausible**; physically interpretable; the bitwise-identical claim is striking but explainable by viscosity smoothing timescale |

---

## Bank value analysis

Comparing bank-aware (PosOnly, NegOnly, PosNeg) vs NoKB cells:

### Did the bank help reach the correct mechanism faster / more rigorously?

**B1:** All four B1 cells reach essentially the same physics — m=0 ansatz is wrong; compound is non-Gardner; basin is broad smooth-localized. The bank-aware cells **do not arrive at the truth faster** — NoKB matches them on rigor. However:
- PosOnly's H_alpha + H_beta mechanism (lifetime + radiative cleansing) is *more analytically precise* than the corresponding NoKB language, and the bank's BKdV-S7-R3 loglog slopes directly motivated the A-sweep design that yielded the "lifetime peaks at A=0.9" finding. Bank-shaped, valuable.
- PosNeg's algebraic TW branch derivation was original (the cell notes "the traveling-wave ansatz is original derivation from the BKdV system, not in the bank") — the bank's role was to *frame* what to falsify, not to *seed* the right mechanism.
- NegOnly used bank entries mostly to motivate ablations (nu_u=0 test, Gardner companion) rather than to seed mechanism hypotheses.

**B2:** Bank-aware cells reach the *same* zero-bore-control insight as NoKB, which is the central mechanistic finding. Bank entries (BKdV-S5/S7-R3) materially shaped:
- PosOnly's "A_c=1 from (v-1) sign-flip" framing
- PosNeg's recognition that A_c shifts from 1.0 to 1.30 due to ~30% transient peak loss (BKdV-S7 deep's sech² IC drift)
- NegOnly's u_L=0 control as the m=0-instability falsifier

### Did deep entries (BKdV-S5, S6, S7) specifically anchor findings?

- BKdV-S5/S7 (algebraic source identity): anchored A_c locations in all bank-aware cells. **High value.**
- BKdV-S6 (viscosity): mostly used as solver prescription, but B2/PosNeg gave it mechanistic content via the bore-width invariance argument. **High value (rare creative use).**
- BKdV-S7-r2 (specific quantitative breakdown numbers): cited in PosOnly to anchor expected ||m||_L2 magnitudes; values matched within 15%. Moderate value.

### Was the bank misleading anywhere?

- B1/PosNeg's H_alpha (m=0 ansatz) was bank-seeded as the "physics anchoring" — but the prompt's framing itself was wrong. So the bank's "physics anchoring" was *misleadingly suggestive of m=0*; the cell properly falsified it. **Mild misleading via the anchoring claim, but the bank-aware cells recovered by reading the BKdV-S5/S7 deep entries which explicitly contradict the anchoring.**
- B1/PosOnly's E1 cited bank entry "BKdV-S7-r1-Gardner-baseline" as a positive entry — but Gardner-baseline is for the *isolated* Gardner equation, not BKdV. The cell does not seem to have been misled by this; the citation is benign.
- B2/PosOnly's BKdV-S7-R3 "loglog slope 0.22 → 2.49" was over-extrapolated: the cell describes this as a *kink* prediction at A=1, but the algebraic identity is for ||S||_L2(A) — which the cell never directly measured. The "kink" appears in their L2_ratio(A) at A≈1, but this is a derived observable, not the algebraic loglog slope. **Mild overclaim in framing; data are correctly reported.**

**Overall bank value verdict:** The bank meaningfully sharpened framing, ablation choices, and quantitative anchors in 3 of 6 bank-aware cells (B1/PosOnly, B2/PosOnly, B2/PosNeg) without leading to false mechanism. The NoKB cells reached qualitatively equivalent conclusions through hypothesis-driven trial — so bank presence improved *resolution* of the mechanism, not its correctness.

---

## Most valuable finding across all 8 cells

**The most valuable new physics insight: r_local = ||m||_in/||m||_global monotone decay (B1/PosOnly, F3) as a quantitative diagnostic of the "local-Gardner-but-not-global-Gardner" mechanism.**

This is the most analytically clean discovery. It says: BKdV continuously generates m everywhere (per the BKdV-S5/S7 source S(x)), but m generated *inside* the compound's support is preferentially expelled by dispersion-mismatch (m-modes group velocity c_g(k) = -3k² is retrograde for high-k; v-peak phase velocity is prograde at ≈ 6 v_peak). The local compound "looks Gardner-like" not because m=0 holds, but because m flows out faster than it accumulates in. The monotone decrease 0.99 → 0.45 of r_local while m_global grows from 0 to 2.4 is the falsifiable signature.

This finding:
- Goes beyond all 4 oracles (which only establish that m=0 is not invariant; they say nothing about why the local picture looks Gardner-like).
- Is consistent with what the other cells observe but no other cell quantifies it this cleanly.
- Provides a 4th-round path (flux-form measurement) that is directly testable.

**Runner-up: B2/PosNeg's bore-width invariance argument** (separation × bore-width × initial-separation 3-way negative-control falsification) is methodologically the most elegant set of *negative* discriminations and reframes B2 as a 2-regime smooth-transition problem with viscosity-mediated bore equilibration — a clean physical story.

**Secondary novel finding: B2/PosOnly's weak-bore destabilization band at u_L ∈ [0.25, 0.75]** — if it survives cross-validation, this would be a genuinely surprising regime not predicted by any oracle. Currently uncorroborated across cells.

---

## Concerns / overclaims to flag

1. **B1/NegOnly's "IC-amplitude Gardner speed match" claim.** The cell reports c_BKdV ≈ 1.71 vs c_Gardner-at-A=1.0 ≈ 1.80 (5% gap, "matched within numerical drift") and concludes the compound preserves the original phase speed through coupling. But:
   - At A=1.0, IC-Gardner c = 6×1 + 1.5×1² = 7.5, **not 1.80**. The cell appears to be quoting v_peak phase-speed *measurements* of an evolved Gardner soliton, not the analytic Gardner soliton speed at amplitude A=1.0. The Gardner companion has decayed during evolution to v_peak ≈ 0.85, at which c = 6×0.85 + 1.5×0.85² = 6.18. **The reported 1.80 is unexplained by Gardner kinematics at any plausible amplitude.** It is plausibly an empirical peak-tracking rate that has its own numerical drift; the "match" between 1.71 and 1.80 may be coincidental.
   - This conflict with B1/NoKB's c_meas/c_Gardner = 0.30-0.53 (which also tracked empirical peak speeds against c=6A+1.5A²) suggests one of the cells is misreporting either the prediction or the measurement. NoKB's numbers look internally consistent (v_peak ≈ 0.4 → c_Gardner ≈ 2.6-3 vs c_meas ≈ 1.0-1.8). NegOnly's framing reads suspicious.
   - **Flag for paper:** the "phase-speed match" framing should be checked against the raw numerics before being cited.

2. **B1/PosOnly's locked-phase fragmentation timeline.** PosOnly claims locked-phase R<0.5 by t≈0.45 for A=1.5 sech², and full fragmentation to 10-15 peaks by T=10. This is sharper than other cells' picture: B1/NegOnly at A=1.0 reports "lock_corr_local = 0.935 at T=10" (i.e., still well-locked). The difference is partly amplitude (A=1.5 vs A=1.0), but the time scales differ by an order of magnitude. **The "tau_alpha ~ 0.5s for A=1.5" estimate** is a quantitative claim that should be cross-validated; it currently rests on a single cell's interpretation.

3. **B1/PosNeg's "compound forms even from sinusoid IC" needs an asterisk.** PosNeg E2b reports lock_T=0.30, α=2.86, R²=0.087 — i.e., the broadband cosine IC at A=0.4 did *not* form a coherent compound by R² standards. But B1/NegOnly E2d reports the opposite outcome (mild sinusoid IC at v-L2=1.155 produces a compound with lock_corr_local=0.85). These IC parametrizations differ (PosNeg uses cos(2πx/L) + 0.5 cos(4πx/L) at A=0.4 amplitude; NegOnly uses cos(2π×2 x/L) at v-L2=1.155), so they may not contradict — but the framing in NegOnly that "basin extends past BKdV-S3's broadband-blow-up wall" overstates the evidence given PosNeg sees no compound for a comparable broadband seed. **Need cross-cell reconciliation.**

4. **B2/NoKB's "sharp boundary in A" claim and B2/PosOnly/NegOnly's "smooth boundary" claim are diagnostic-dependent.** NoKB's diagnostic is n_peaks (integer); the other cells use L2_ratio (continuous). All claims are correct on their own diagnostics, but the paper must not present them as if they're competing claims. They are complementary observations of the same phenomenon.

5. **B2/PosOnly's weak-bore destabilization band at u_L=0.25-0.75 is reported with confidence but not cross-validated.** Only PosOnly sampled u_L densely enough (E3 Part B: u_L ∈ {0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0}) to see this; NegOnly's coarsest spacing is u_L=0.3 minimum. Unless future cells reproduce, this is a *single-cell observation*. The cell itself proposes a 4th-round m(x,t) visualization to confirm.

6. **B2/PosNeg's "two regimes within safe envelope" framing may understate the destruction regime.** At A=1.75 the cell reports n_peaks=1 (single peak) and retention 0.612 — but other cells at A=1.75 (NegOnly extrapolation, PosOnly at A=1.7) see n_peaks=5+. The discrepancy is partly the IC seeding (PosNeg uses u_0=v_0²/2 + bore, which puts the soliton on m=0 initially; others use u_0=0). PosNeg's choice of m_0=0 seeding is a substantively different initial condition that *delays* the onset of destruction (consistent with the m=0 lifetime argument of B1/PosOnly). **PosNeg's "no destruction regime in safe envelope" claim is conditional on its IC seeding choice; the paper should note this.**

7. **All B-cells skip n_peaks definition transparency in their hypothesis.md write-ups.** "n_peaks" is computed differently across cells (different prominence thresholds, smoothing). This makes cross-cell n_peaks comparisons difficult. Not an overclaim per se, but a confound.

8. **PosOnly's bug-fix rerun in E2 is acknowledged transparently** (Nx=512 dt=1e-4 blew up at t=0.025, dt=2.5e-5 fixed). Good practice; not a concern, an example of correct handling.

---

## Recommendation for the paper

### What the 8-cell run shows

1. **The prompt's "u ≈ v²/2 inside support" physics anchoring is wrong.** All 8 cells independently falsify it. This is a strong, robust negative result.
2. **The local "compound soliton" is a real, robust object across IC families, viscosity choices, and bank conditions** — but it is *not* a Gardner soliton in any pointwise sense. It is best described as a coupled (u,v) traveling-wave-like state with characteristic algebraic relation u ≈ α·v²/2 + β (α >> 1) plus an asymmetric u-leads-v or u-wake structure.
3. **The phase boundary in (u_L, A) for bore-soliton encounter is dominated by A, not u_L**, and the transition at A_c ≈ 1.0-1.3 coincides with the BKdV-S5/S7 (v-1) algebraic sign-flip. The sharpness depends on the diagnostic: n_peaks shows a step, L2 retention shows a width-0.4 crossover, Δx phase-shift shows a smooth monotone zero-crossing at A=1.30.
4. **The "destruction" regime is largely intrinsic** (sech² IC not being a true BKdV state); the bore plays a modulating (often *stabilizing*) role, not a destructive one. This reverses the naive expectation embedded in the prompt's regime list.
5. **The four-regime classification (transmission/reflection/fusion/destruction) is not borne out** in the parameter envelope tested. Reflection does not appear. Fusion is absorbed into the "soliton survives with reduced amplitude" picture.

### What the paper should claim confidently

- The negative knowledge **"u = v²/2 is not the local compound algebra"** is unambiguously established by 8 independent runs.
- The negative knowledge **"bore does not destroy soliton; the bore can stabilize it"** is established by 4 B2 cells via zero-bore controls.
- The mechanism story **"m_t source is non-trivial; (v-1) sign-flip controls regime; sech² ICs drift off m=0"** is on solid analytical + numerical ground.
- Bank-aware cells produced more *precise* mechanism stories with the same correctness as NoKB cells. The bank's contribution is *resolution* (better quantitative anchors, sharper falsifications), not direction.

### What the paper should temper

- Specific quantitative claims that appear in *only one cell* (e.g., B1/PosOnly's r_local trajectory, B2/PosOnly's weak-bore destabilization band, B1/NegOnly's IC-amplitude-Gardner-speed match) should be presented as *single-cell findings* requiring replication — not as cross-validated facts.
- Sharpness claims must be presented diagnostic-by-diagnostic (n_peaks vs L2 vs Δx phase-shift).
- The "compound soliton" terminology should be replaced or qualified — the actual object is a coupled traveling-wave-like state, not a soliton in the integrable sense.
- Time-horizon caveats matter: T=10 conclusions may not extrapolate to T=∞ (B2/NoKB's Arm B is the only T=24 result and reveals delayed fission).

### Suggested paper framing

**"BKdV's compound state is not a Gardner soliton; the (v-1) algebraic source is the regime controller; intrinsic IC-mismatch dominates the bore-soliton phase diagram. Knowledge banks improved resolution but not correctness; NoKB and PosNeg conditions produced the cleanest analyses."**

The strongest single result to lead with: **B1/PosOnly's r_local diagnostic and B2/PosNeg's three-way negative-control falsification of bore-mediated mechanism** — both demonstrate that the right level of analysis for BKdV mechanism inquiry is *dispersion-mismatch* and *viscous-equilibration timescale comparisons*, not template-matching to known integrable solitons.
