# T_A / PosOnly — reasoning

## Final method (E3)

Fourier pseudospectral on x in [-15, 15], Nx=256, periodic, with:
- 2/3-rule dealiasing mask applied to (a) every nonlinear product (v^2, u v, v v_x, u u_x) and (b) every spectral derivative call (dx, dxx, dxxx), so no high-k content leaks back into the resolved band.
- Classical explicit RK4 time stepping, dt = 1e-4, n_steps = 80000.
- Spectral hyperviscosity term -nu_h * (k^2)^p applied ONLY to the u-equation, p=4, nu_h = 5e-10 (calibrated so the damping rate at k_cut = 2*pi*(Nx/3)/L ≈ 17.8 is ~5 per unit time, while modes with k <= 5 are essentially untouched — preserves soliton-bearing modes).
- v-equation discretization (including v_xxx) is left fully spectral so the dispersive soliton phase is unaffected.

IC: v0 = 2 sech^2(x + 5); u0 = 0.5 v0^2 + 0.2 v0 (perturbed from m=0 Gardner reduction by 0.2 v0).

Output: pred_results/T_A.npy of shape (9, 2, 256), 9 evenly-spaced snapshots from t=0 to t=8, channels (u, v).

## Iteration trace

- **E1** Fourier pseudospectral + explicit RK4, NO dealiasing (the strictest progressive-complexity baseline). **F1**: aliasing blow-up at t≈0.5, sup_u → 2.2e6, sup_v → 137; pure baseline-failure mode that the bank entry BKdV-S1 r2 attributes to high-k folding through quadratic products feeding v_xxx.
- **E2** SINGLE-component change vs E1: added 2/3-rule dealiasing on every nonlinear product and every derivative call. **F2**: reaches T=8 cleanly with mass_v drift = 6e-15 and max_v stable at >=0.87 throughout (recovering to 1.45 at T=8), BUT sup_u steepens to 20.8 — violates |u|<15. Diagnostic: top-decile of resolved band carries 6-10% of u-energy, indicating physical Burgers steepening of u (3 u u_x with no dispersion / dissipation in the u-eqn). Tail above 2/3 band is machine zero, so aliasing is fully suppressed and the failure is genuinely PDE-level steepening, not numerical aliasing.
- **E3** SINGLE-component change vs E2: added weak spectral hyperviscosity on u only. **F3**: ALL phenomenon targets met — max_v(T) = 1.013 (>= 1.0 threshold = 0.5 * 2.0), mass_v drift = 0 (machine zero), sup_u = 9.49 (< 15), sup_v = 1.01 (< 15). Dominant v peak amplitude 1.013 vs 2nd-highest local maximum 0.83 (1.22:1 ratio) — clearly distinguishable single dominant peak. Early-stop useful.

## Use of memory

**Cited positive entries (drove decisions):**
- `kb-kdv-IMEX-CN-spectral-pass`, `BKdV-S1` — confirmed the spatial baseline choice at E1 (Fourier pseudospectral, Nx=256, L=30) and the time integrator choice (explicit RK4 with dt ~ 1e-4). BKdV-S1 also pre-warned that omitting dealiasing causes aliasing blow-up via quadratic-product folding, which validates the F1 diagnosis.
- `BKdV-S1` (r2 deep-synthesis transferred entry) + `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` + `kb-gardner-KdV-method-transfer-moderate-amplitude` — motivated the E2 single-component upgrade (2/3-rule dealiasing on all nonlinear products), and the Gardner entries flagged that a KdV-IC will radiate (rationalizing why our final v(T) is a dominant peak plus radiation rather than a pristine soliton).
- `kb-burgers-MUSCL-Godunov-shock-pass`, `kb-burgers-Godunov-preShock-smooth`, `kb-general-firstOrder-Godunov-preShock-baseline` — identified Burgers steepening of u as the dominant late-time failure mode in the u-component of coupled BKdV, motivating the E3 upgrade direction (add bounded dissipation localized to high k where steepening lives). I adopted the spirit of these entries via spectral hyperviscosity rather than MUSCL+Godunov because the latter would be a multi-component swap (FV + Riemann solver) and would violate progressive-complexity discipline.

**Considered-but-rejected positive entries:**
- `kb-burgers-MUSCL-Godunov-shock-pass` rejected at E2 — switching the u-eqn to FV+Riemann would be multi-component (FV + Riemann + likely operator splitting) and would discard the spectral v_xxx accuracy needed for the soliton.
- `kb-shallowWater-LaxFriedrichs-stable-smeared` and `kb-shallowWater-HLL-dam-break-pass` rejected at E3 — shallow-water Riemann solver tropes assume a depth-like variable and dry/wet patches; our u-field is not a depth variable and there are no near-dry regions, so these are off-domain.
- `kb-kdv-smallAmplitude-dispersiveRegime` — not actively cited because our v IC at amp=2 is well above the small-amplitude dispersive regime threshold; this entry would matter for a follow-up question about post-interaction dispersion but does not constrain the simulation choice.
- `kb-kdv-spectral-solitonAmplitude-conservation` — this entry's spectral-IMEX recommendation would have been the next escalation if E3 had failed (replacing RK4 with IMEX-CN for the v_xxx stiffness). E3 succeeded, so this upgrade was not needed.

**Progressive-complexity audit:**
- E1 → E2: one change (added 2/3 dealiasing mask). All other settings identical.
- E2 → E3: one change (added spectral hyperviscosity on u). dt, Nx, time integrator, dealias mask, v-eqn discretization all identical.

## Final self-assessment

I believe `pred_results/T_A.npy` satisfies the phenomenon target. Diagnostics from F3:
- shape = (9, 2, 256), 9 snapshots at t = 0, 1, 2, ..., 8.
- final max v = 1.0132 ≥ 1.0 (= 0.5 × initial 2.0 amplitude).
- mass_v drift = 0 (machine zero), well within 8%.
- final sup_u = 9.49 < 15; final sup_v = 1.01 < 15.
- dominant peak / 2nd peak amplitude ratio at T=8 is 1.22, confirming a single dominant peak survives.

Mild caveat: max_v=1.013 only marginally clears the 1.0 threshold (1.3% margin). This is consistent with the kb-gardner-G2 prediction that a sech^2-shaped KdV IC in the m=0+0.2v perturbed Gardner setting will shed radiation; the soliton-like core does survive with sufficient mass and bounded fields, but a fraction of its initial amplitude is exchanged with the radiation field and the u-bore. Given the marginal max_v, this should be flagged as "passes phenomenon check by a tight margin" rather than "passes comfortably".
