## Memory: negative-knowledge bank (43 entries, v3.A — includes BKdV stress-test entries S1-S7)

Negative entries describe methods, regimes, or paths that FAILED in related settings. Deep synthesis entries (depth≥2) are strongest negative signals — they represent N-round path closures.

### kb-burgers-fwdEuler-centralFD-Gibbs  (negative)
  attempted_route: Forward Euler + 2nd-order central FD (no upwinding, no limiter), CFL=0.4, Burgers u0=-sin(pi*x), T=0.5
  observation: Solution is all-finite but exhibits 21 local maxima (vs 1 expected), amplitude_range=7.21 (~3.6× true amplitude), max_jump=3.61 — massive Gibbs-like oscillations, effectively blow-up in accuracy if not in finiteness.
  rationale: Central differencing on a nonlinear hyperbolic equation has no upwind dissipation; post-shock oscillations grow without bound in amplitude. The scheme appears to 'run' (exit 0, no NaN) but the output is physically meaningless: amplitude tripled and 20 spurious peaks appeared.
  recommended_alternative: In a coupled Burgers-swept-KdV solver, any naive central-difference treatment of the Burgers advection term will corrupt both the Burgers bore and the adjacent KdV soliton region via spurious oscillation cross-contamination. Always use an upwind or flux-limited scheme for the Burgers component.
  failure: layer=method_failure, scope=general_failure, action=change_method, risk=high_risk_false_progress

### kb-burgers-LaxFriedrichs-longTime-dissipation  (negative)
  attempted_route: Global Lax-Friedrichs FD scheme, CFL=0.5, Burgers u0=-sin(pi*x), T=10.0
  observation: Solution is all-finite but amplitude decayed to max=0.090 (vs expected O(1)), mean_jump=0.0018, single local maximum — severe over-diffusion from Lax-Friedrichs at 10× the shock timescale.
  rationale: Lax-Friedrichs is unconditionally stable and produces no NaN, but its O(dx) numerical diffusivity acts at every interface continuously. Over T=10 (>>1/pi), the integrated dissipation washes out the shock amplitude by ~10×; the result is a smooth, decayed N-wave not representative of the true inviscid solution.
  recommended_alternative: In long-time coupled Burgers-KdV simulations, Lax-Friedrichs is unsuitable for the Burgers component: it will artificially damp the bore amplitude and cause the bore-soliton interaction energy to be misrepresented. Prefer MUSCL or upwind-limited schemes for T >> shock timescale.
  failure: layer=method_failure, scope=regime_bound, action=narrow_claim, risk=medium_risk_drift

### kb-burgers-LaxFriedrichs-periodic-longTime-contamination  (negative)
  attempted_route: Any stable scheme on periodic domain for Burgers, T=10 (multiple domain-traversal times)
  observation: Result shows smooth, nearly zero-mean profile (amplitude 0.181) with periodic recirculation contaminating any shock/rarefaction structure. Genuine physics vs numerical artifact is indistinguishable at T=10 on this periodic domain.
  rationale: Even a perfect numerical scheme will show periodic wrapping at T=10: the shock and rarefaction recirculate multiple times and overlap. This contamination is a property of the periodic boundary condition, not of the scheme, and should not be interpreted as a scheme failure or as a meaningful physical solution.
  recommended_alternative: In coupled Burgers-swept-KdV experiments on periodic domains, long-time runs beyond a few domain-traversal times produce spurious bore-soliton interaction histories. Restrict comparison windows to T where neither wave has wrapped around, or use absorbing/outflow boundaries.
  failure: layer=measurement_failure, scope=regime_bound, action=narrow_claim, risk=medium_risk_drift

### kb-kdv-IFRK4-blowup  (negative)
  attempted_route: Fourier pseudospectral + integrating-factor RK4 (IFRK4), dt unspecified, no dealiasing, KdV v0=2 sech^2(x+5), T=2.0, Nx=256
  observation: Output array shape (256,) is all-NaN (256 NaN/Inf). Eval score=0. Blow-up despite agent claiming correct IF-RK4 formulation.
  rationale: The IFRK4 concept is mathematically sound, but in practice the integrating factor exp(i*k^3*t) overflows for high wavenumbers (k~100 gives k^3~10^6), or a sign/reshape error in the implementation caused phase errors cascading to NaN. Correct IFRK4 requires dealiasing plus careful handling of the complex exponential at high k.
  recommended_alternative: For coupled Burgers-swept-KdV: do not use IFRK4 without (a) 2/3 dealiasing on the nonlinear term, (b) verification that |k^3 * dt| stays below the RK4 stability boundary, and (c) no sign errors in the integrating-factor back-transform. IMEX-CN is a safer default; use IFRK4 only if 4th-order time accuracy is required and the implementation is carefully validated.
  failure: layer=implementation_failure, scope=local_failure, action=change_method, risk=medium_risk_drift

### kb-kdv-explicit-RK4-stiffness-blowup  (negative)
  attempted_route: Explicit RK4 + central FD for v_xxx, dt=1e-5, KdV v0=2 sech^2(x+5), T=2.0, Nx=256
  observation: Unexpectedly, output is all-finite (no NaN) with amplitude_range=1.63 and 10 local maxima — but amplitude is wrong (expected ~2.0) and 10 spurious peaks indicate the soliton has fragmented or dispersed into artifacts. Prediction of NaN blow-up was not confirmed, but the result is physically wrong.
  rationale: The agent chose dt=1e-5 which may be small enough to barely avoid NaN for RK4 (requiring dt~dx^3 for explicit stability of v_xxx at Nx=256), but the soliton amplitude decayed from 2.0 to ~0.87 and spawned 10 peaks — the scheme is marginally stable but deeply inaccurate. The prediction of NaN was not met; the actual failure mode is accuracy collapse, not finiteness blow-up.
  recommended_alternative: For coupled Burgers-swept-KdV: explicit-only treatment of the KdV dispersive term (v_xxx or swept equivalent) produces soliton fragmentation even if NaN is avoided. Any agent solving this system must use an implicit or IMEX treatment of the dispersive term; explicit RK4 alone is not sufficient even with very small dt.
  failure: layer=hypothesis_failure, scope=regime_bound, action=narrow_claim, risk=medium_risk_drift

### kb-kdv-noDealiasing-aliasing-artifacts  (negative)
  attempted_route: Fourier pseudospectral + IMEX Euler, dt=0.005, NO 2/3 dealiasing on nonlinear term, KdV v0=2 sech^2(x+5), T=2.0, Nx=256
  observation: Output is all-finite with amplitude 2.87 (>2.0 expected) and 4 local maxima (vs 1 expected soliton) — aliasing energy has created spurious soliton-like peaks and inflated the apparent amplitude.
  rationale: Without dealiasing, the pseudo-spectral evaluation of v*v_x wraps energy from modes |k|+|k'|>N/2 back into low wavenumbers, acting as a phantom forcing on the soliton. Over 400 steps this aliased energy visibly distorts the soliton: peak amplitude is 43% too high and three spurious peaks appear.
  recommended_alternative: For coupled Burgers-swept-KdV spectral implementations: always apply the 2/3 dealiasing rule (or at minimum a smooth spectral filter) to the nonlinear term. Without it, the soliton amplitude and count are unreliable, which would corrupt any soliton-bore interaction measurement. This is especially critical for Gaussian decomposition into soliton trains where individual soliton amplitudes must be accurately tracked.
  failure: layer=method_failure, scope=regime_bound, action=narrow_claim, risk=medium_risk_drift

### kb-kdv-amplitude-threshold-soliton  (negative)
  attempted_route: KdV with amplitude 0.1 IC, expecting soliton propagation similar to amplitude-2 case
  observation: Peak amplitude at T=2 is 0.052 (nearly halved from IC), 8 local maxima (dispersive wave train), zero_crossings=12 — clearly not a soliton. The soliton-propagation expectation fails at this amplitude.
  rationale: KdV soliton formation requires the nonlinear term (O(A^2)) to balance the dispersive term (O(A)); at A=0.1 dispersion dominates and the pulse spreads linearly. Any model predicting soliton-like behavior at this amplitude is incorrect for these parameters.
  recommended_alternative: For Gaussian decomposition into KdV soliton trains in coupled Burgers-swept-KdV: only Gaussian components with amplitude above a system-dependent threshold (empirically >> 0.1 for standard KdV scaling) contribute solitons; sub-threshold components produce dispersive radiation. This shapes which Gaussian decomposition modes matter for the soliton-bore interaction measurement.
  failure: layer=hypothesis_failure, scope=regime_bound, action=narrow_claim, risk=low_risk_omission

### kb-shallowWater-centralFD-fwdEuler-hNegative  (negative)
  attempted_route: Forward Euler + central FD (no limiter, no upwinding, no Riemann solver), shallow water dam-break h=[2,1], T=0.4, Nx=200
  observation: h goes negative (h_min=-0.139, h_negative=true), momentum reaches |value|=5.27e10 — explosive blow-up in the momentum field while h is only marginally negative. All-finite in floating point but physically degenerate.
  rationale: Central differencing on the shallow water system produces Gibbs oscillations near the dam-break discontinuity; h dips below zero making wave speed imaginary and hu/h singular; forward Euler amplifies these into exponentially growing modes. The scheme is provably inadequate for discontinuous hyperbolic systems.
  recommended_alternative: Directly relevant to the Burgers-swept-KdV coupled system if the swept-KdV has a shallow-water-like structure: central FD without upwinding or Riemann fluxes is catastrophic for any hyperbolic system with discontinuous ICs. Never use central FD alone for the advective terms in any wave-breaking or bore-like regime.
  failure: layer=method_failure, scope=general_failure, action=change_method, risk=high_risk_false_progress

### kb-shallowWater-LaxFriedrichs-overdiffusion  (negative)
  attempted_route: Global Lax-Friedrichs flux, CFL=0.4, shallow water dam-break h=[2,1], T=0.4
  observation: max_jump=0.064 vs HLL's max_jump=0.090 at same resolution — shock is ~28% more smeared than HLL. The shock-rarefaction structure is excessively broadened for physical analysis.
  rationale: Global LxF applies the maximum wave speed alpha everywhere as viscosity, not just near discontinuities. This globally adds O(alpha*dx) diffusion per step, smearing both shock and rarefaction more than Riemann-solver methods. The result is quantitatively incorrect for cases where shock width matters.
  recommended_alternative: For coupled Burgers-swept-KdV where bore sharpness affects the soliton interaction timescale, prefer HLL over Lax-Friedrichs for the hyperbolic component. Smeared bores may delay or distort the interaction region, leading to incorrect soliton phase shifts in measurement.
  failure: layer=method_failure, scope=regime_bound, action=narrow_claim, risk=low_risk_omission

### kb-shallowWater-dryBed-naiveClip-hu-singular  (negative)
  attempted_route: HLL + Godunov finite volume + adaptive CFL, with positivity clip (h=max(h,0)) at dry interface h_R=0, shallow water, T=0.3
  observation: h stays non-negative (h_min=0.00153, clipped) and mass is conserved (100.0), but the momentum (hu) field has values reaching -0.295 while h is near zero — u = hu/h is ill-defined at dry cells (effective |u| > 100 near dry front).
  rationale: Post-hoc positivity clipping prevents h<0 but breaks conservation locally; the momentum equation then computes hu/h ratios at near-zero h that are numerically huge even if not NaN. A correct dry-bed solver needs a consistent wet/dry treatment (HLLE with dry Riemann solution, or a well-balanced scheme) rather than clipping.
  recommended_alternative: In coupled Burgers-swept-KdV if any region can develop near-zero depth or near-zero amplitude (e.g., swept-KdV in a region where the Burgers bore evacuates material), use a wet/dry front tracking scheme rather than simple positivity clips. Otherwise velocity blow-up near the front will corrupt the bore-soliton interaction.
  failure: layer=implementation_failure, scope=local_failure, action=change_method, risk=medium_risk_drift

### kb-general-centralFD-hyperbolic-shockFormation  (negative)
  attempted_route: Central finite differences (no upwinding, no limiter) applied to any nonlinear hyperbolic conservation law with discontinuous or shock-forming initial conditions — observed in A1 (Burgers) and A7 (shallow water)
  observation: A1: 21 local maxima, amplitude 7.2×; A7: h goes negative (h_min=-0.139), momentum 5.3e10. Both cases produce physically degenerate output that is technically finite but numerically useless.
  rationale: Central FD lacks the upwind dissipation necessary for Godunov-type stability in hyperbolic systems; spurious oscillations at discontinuities grow without bound under either forward Euler or similar non-dissipative time steppers. This is a universal failure across PDE families, not scheme-specific.
  recommended_alternative: Universal rule for coupled Burgers-swept-KdV: the Burgers and any hyperbolic component must use upwind, Riemann-solver, or flux-limited spatial discretization. Central FD is acceptable only for smooth dispersive terms (like v_xxx in KdV when treated implicitly) — never for the advective nonlinear flux in a shock-forming equation.
  failure: layer=method_failure, scope=general_failure, action=change_method, risk=high_risk_false_progress

### kb-general-finiteness-not-accuracy  (negative)
  attempted_route: Various schemes (A1, A4, A7) that produced all-finite output arrays but with physically wrong solutions
  observation: A1: all_finite=true but 21 local maxima; A4: all_finite=true but soliton fragmented into 10 peaks with amplitude 1.63 vs 2.0; A7: all_finite=true but momentum 5.3e10. Exit code 0 in all cases.
  rationale: A scheme that produces finite (non-NaN/Inf) output can still be completely wrong. Diagnostics based only on finiteness or exit code will produce false positives; amplitude, local-maxima count, and jump statistics are necessary secondary checks.
  recommended_alternative: For future coupled Burgers-swept-KdV evaluation pipelines: do not use NaN/Inf presence as the sole correctness criterion. Also check: local maxima count vs expected soliton count, peak amplitude vs reference, mass conservation, and maximum jump vs reference max-jump. These diagnostics distinguish catastrophic accuracy failures from true stability.
  failure: layer=measurement_failure, scope=general_failure, action=narrow_claim, risk=high_risk_false_progress

### kb-gardner-G1-explicitRK4-finiteFrag  (negative)
  attempted_route: Explicit RK4 + 2nd-order central FD for all spatial derivatives (v_xxx and nonlinear), dt=1e-5, Gardner v0=1.5 sech^2(x+5), T=2.0, Nx=256, periodic
  observation: Output is all-finite (no NaN), mass=3.000, but soliton has fragmented: 14 local maxima (vs 1 expected), peak amplitude only 1.506 (down from IC amplitude 1.5 — near-stationary peak but heavily fragmented structure), peak migrated to x=2.11 (expected ~x=3-5 for KdV-speed soliton). The scheme survived only because dt=1e-5 is near the stability boundary dt~O(dx^3)~1.6e-4.
  rationale: Explicit RK4 on the Gardner v_xxx term requires dt~O(dx^3) for stability. At dt=1e-5 the run narrowly avoids NaN blow-up, but the cubic nonlinearity (3/2)v^2 v_x adds extra high-frequency forcing beyond KdV, causing soliton fragmentation into 14 pieces rather than clean propagation. The method is impractical (200,000 steps for T=2) and inaccurate at this dt.
  recommended_alternative: For the Gardner-reduction regime of coupled Burgers-swept-KdV (m=0): pure explicit RK4 on Gardner is impractical — it requires ~200,000 steps for T=2 and still produces fragmented soliton structure. Any production solver for this regime must use IMEX or spectral-ETD methods for the dispersive term. Do not use explicit-only methods even with very small dt to 'be safe'; they do not produce accurate soliton propagation on Gardner.
  failure: layer=method_failure, scope=regime_bound, action=narrow_claim, risk=medium_risk_drift

### kb-gardner-G3-noDealiasing-cubicAliasing  (negative)
  attempted_route: IMEX-CN spectral, NO 2/3 dealiasing, dt=0.001, Gardner v0=1.5 sech^2(x+5), T=2.0, Nx=256
  observation: Output is all-finite with peak amplitude 1.545 (slightly above IC amplitude 1.5, vs 2.87 inflation in KdV no-dealiasing case A5), 11 local maxima, mass=3.000. Aliasing artifacts are present (11 spurious peaks) but amplitude inflation is more modest than KdV case at this amplitude; no catastrophic blow-up at amp 1.5.
  rationale: The cubic v^2 v_x term aliases at up to 3x the Nyquist wavenumber (vs 2x for quadratic KdV term), so Gardner without dealiasing has more aliasing channels. Yet at amplitude 1.5 the absolute aliasing energy is not dramatically worse than KdV (A5 had 43% amplitude inflation; G3 has only ~3% inflation). The extra cubic aliasing channel creates more spurious peaks (11 vs 4 in KdV) but the amplitude inflation is masked by the radiation from the wrong IC. Dealiasing remains essential for accurate multi-soliton counting.
  recommended_alternative: For Gardner and the full coupled Burgers-swept-KdV system: the cubic nonlinearity adds a third aliasing channel that, even at moderate amplitude, creates more spurious peak count than the KdV quadratic term alone. Always apply 2/3 dealiasing (or higher-order filtering) when the PDE contains cubic or higher polynomial nonlinearities. For Gaussian decomposition tasks, spurious peak count from aliasing would directly corrupt soliton-train identification.
  failure: layer=method_failure, scope=regime_bound, action=narrow_claim, risk=medium_risk_drift

### kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup  (negative)
  attempted_route: IMEX-CN spectral (CN on v_xxx, explicit on nonlinear), dt=1e-4, Gardner v0=3.0 sech^2(x+5), T=2.0, Nx=256 — same method as G2 but at 2× the IC amplitude
  observation: All 256 outputs are NaN (n_nan=256, all_finite=false). Runtime overflow encountered in the nonlinear term: 'overflow encountered in multiply' (6.0*v*vx + 1.5*v^2*vx) and 'invalid value encountered in fft' — the IMEX-CN explicit nonlinear step blew up at amplitude 3.0 even though the same method (similar dt) was stable at amplitude 1.5.
  rationale: IMEX-CN treats the dispersive term v_xxx implicitly (unconditionally stable) but the nonlinear terms 6vv_x + (3/2)v^2 v_x explicitly. The explicit nonlinear CFL constraint is amplitude-dependent: the combined nonlinearity at A=3 is O(6A + 1.5A^2) ~ O(18 + 13.5) = O(31.5) vs O(9 + 3.375) = O(12.4) at A=1.5. The CFL restriction tightens by approximately 2.5×, making dt=1e-4 insufficient at A=3 even though a comparable dt worked at A=1.5.
  recommended_alternative: Critical for the Gardner-reduction regime and full coupled Burgers-swept-KdV: IMEX-CN with explicit nonlinear has an amplitude-dependent CFL limit driven by the combined 6vv_x + (3/2)v^2 v_x term. When amplitude doubles, the effective CFL limit tightens by more than 2×. Always re-evaluate dt when changing IC amplitude; do not assume a dt validated at lower amplitude is safe at higher amplitude. For large-amplitude Gardner or swept-KdV regimes, consider fully implicit nonlinear solvers or ETD-RK methods with accurate stability analysis.
  failure: layer=method_failure, scope=regime_bound, action=change_method, risk=high_risk_false_progress

### kb-gardner-sech2IC-not-exact-soliton  (negative)
  attempted_route: Using KdV sech^2 IC (v0 = A sech^2(x+x0)) as initial condition for Gardner equation at any amplitude
  observation: G2 (amp 1.5): amplitude decayed from 1.5 to 0.612, 13 local maxima, peak migrated to x=-3.52 — substantial radiation from wrong IC. G4 (amp 3.0): complete NaN blow-up (amplitude-CFL failure exacerbated by wrong IC shape causing rapid nonlinear transient).
  rationale: The Gardner equation v_t + 6vv_x + (3/2)v^2 v_x + v_xxx = 0 has soliton solutions with a different amplitude-width-velocity relationship than KdV. The KdV soliton A sech^2(sqrt(A/6)(x-ct)) satisfies 6vv_x + v_xxx = 0 but NOT the Gardner equation. Inserting a KdV sech^2 IC into Gardner creates an immediate nonlinear mismatch that radiates energy continuously. The correct Gardner soliton is parametrized differently (involving the cubic coefficient).
  recommended_alternative: Essential for all Gardner-reduction sub-tasks in Burgers-swept-KdV: use the proper Gardner soliton IC (parametrized with the cubic coefficient epsilon) for soliton stability tests, not a KdV sech^2 IC. Using KdV ICs will (a) generate spurious radiation trains that corrupt bore-soliton interaction measurements, (b) potentially trigger amplitude-CFL blow-up at amplitudes where the nonlinear transient is large. For the Gaussian decomposition task, fit Gardner soliton profiles to the data, not KdV soliton shapes.
  failure: layer=hypothesis_failure, scope=general_failure, action=change_method, risk=high_risk_false_progress

### kb-gardner-cubicTerm-tightens-nonlinearCFL  (negative)
  attempted_route: Any IMEX or semi-implicit method with explicit treatment of the nonlinear terms in Gardner, re-using a dt validated on KdV at the same grid resolution
  observation: G4 (IMEX-CN, dt=1e-4, amp 3.0): complete NaN blow-up. G1 (explicit RK4, dt=1e-5, amp 1.5): survived but fragmented. KdV IMEX-CN at dt=0.0005 (amp 2.0, kb-kdv-IMEX-CN-spectral-pass): stable. The cubic term (3/2)v^2 v_x at amplitude A contributes O(1.5A^2) to the nonlinear CFL, tightening it by a factor ~(1 + 0.25A) compared to pure KdV at the same A.
  rationale: In Gardner's combined nonlinearity 6vv_x + (3/2)v^2 v_x, the effective advection speed for the explicit CFL is proportional to max|6v + (3/2)v^2| = max|6A + 1.5A^2|. For A=2 (KdV pilot): 12+6=18; for A=1.5: 9+3.375=12.4; for A=3: 18+13.5=31.5. The ratio 31.5/12.4 ~2.5 means the same dt that was marginally safe at A=1.5 is 2.5× too large at A=3. Agents transferring KdV dt choices to Gardner without amplitude-adjustment will encounter blow-up.
  recommended_alternative: For the Gardner-reduction regime of Burgers-swept-KdV and the full coupled system: when increasing IC amplitude from KdV baseline to Gardner or swept-KdV regimes, rescale dt by max(6A + 1.5A^2)^{-1} relative to the KdV-validated dt. The cubic coefficient makes Gardner significantly more restrictive than KdV at A > 2. Document the amplitude used when recording a 'stable dt' in the knowledge bank — it is not transferable across amplitudes.
  failure: layer=method_failure, scope=regime_bound, action=narrow_claim, risk=high_risk_false_progress

### kb-general-massConservation-insufficient-diagnostic  (negative)
  attempted_route: Using mass conservation alone as the correctness diagnostic for dispersive or fragmented wave solutions
  observation: G1 (Gardner explicit RK4): mass=3.000 but 14 local maxima, soliton fragmented. G3 (Gardner no dealiasing): mass=3.000 but 11 local maxima, aliasing artifacts. Earlier: A4 (KdV explicit RK4): soliton fragmented into 10 peaks with mass still conserved. A5 (KdV no dealiasing): 4 spurious solitons but mass approximately conserved.
  rationale: Mass (integral of v) is conserved by many numerical methods even when the solution is physically wrong: fragmentation, aliasing-driven spurious peaks, and soliton amplitude errors all leave the L1 mass integral unchanged. A run reporting mass=3.000 with 14 local maxima is not a correct solution. Peak count, peak amplitude, and peak location are orthogonal diagnostics that must also be checked.
  recommended_alternative: Universal rule for coupled Burgers-swept-KdV evaluation pipelines: mass conservation is a necessary but not sufficient correctness criterion. The primary correctness check for soliton problems must include: (1) peak local maxima count matching expected soliton count, (2) peak amplitude within tolerance of reference, (3) peak x-position consistent with theoretical phase speed. This is especially important for Gaussian decomposition tasks where spurious peaks from aliasing or fragmentation would produce incorrect soliton-train amplitudes.
  failure: layer=measurement_failure, scope=general_failure, action=narrow_claim, risk=high_risk_false_progress

### kb-gardner-GardnerIsM0-coupledSystemInstability  (negative)
  attempted_route: Assuming that a numerical method validated on the isolated Gardner equation will be equally stable when embedded in the full coupled Burgers-swept-KdV system at the same parameters
  observation: G4 demonstrates that IMEX-CN with explicit nonlinear blows up on Gardner at amplitude 3.0 (the m=0 reduction). The full coupled system at m=0 has additional coupling terms that add further explicit stiffness beyond the isolated Gardner equation.
  rationale: Gardner is the m=0 reduction of the coupled Burgers-swept-KdV system from Holm et al. 2025. If IMEX-CN with explicit nonlinear blows up on the isolated Gardner equation at a given (dt, amplitude), it will certainly blow up on the full coupled system in the Gardner-reduction regime — the coupling terms add O(m) correction to the nonlinear explicit stiffness. Conversely, a dt that is stable for the coupled system at small m will not automatically be stable as m -> 0 if the Gardner nonlinear CFL becomes the binding constraint.
  recommended_alternative: Directly applicable to Burgers-swept-KdV coupled system design: validate numerical methods first on the isolated Gardner equation (m=0 reduction) before testing the full coupled system. Gardner blow-up at a given (dt, amplitude) is a necessary failure condition for the full coupled system in that regime. Treat Gardner stress tests as a prerequisite gate for coupled-system parameter sweeps.
  failure: layer=hypothesis_failure, scope=regime_bound, action=narrow_claim, risk=high_risk_false_progress

### kb-gardner-nonlinearCFL-amplitude-boundary  (negative)
  attempted_route: IMEX-CN spectral with explicit nonlinear (6vv_x + (3/2)v^2 v_x) at dt=5e-4 for Gardner amplitude escalating from 1.5 to 3.0
  observation: Empirically: dt=5e-4 is STABLE at amp 1.5 (G2, all_finite=true, mass conserved). The same scheme with dt=1e-4 BLOWS UP (all 256 NaN) at amp 3.0 (G4). Interpolating the effective nonlinear wave-speed: at amp 1.5, max|6v + 1.5v^2| ~ 9 + 3.375 = 12.4; at amp 3.0, max|6v + 1.5v^2| ~ 18 + 13.5 = 31.5. The empirical stability boundary therefore scales as dt * (6A + 1.5A^2) * k_max / (2*pi/L) < C for some O(1) constant C, where k_max is set by the steepest resolved mode.
  rationale: For the explicit nonlinear part of IMEX schemes applied to Gardner, the nonlinear CFL condition is dt <= C / (max_v * k_max) where max_v = max|6v + 1.5v^2| and k_max is determined by the steepest active spectral mode. The key distinction from linear CFL: max_v scales as O(6A + 1.5A^2) with amplitude A, so the constraint is NOT linear in A. Doubling A from 1.5 to 3 increases the nonlinear speed by a factor 31.5/12.4 ~ 2.54, requiring dt to shrink by the same factor. At A=1.5 the empirically safe dt=5e-4 implies C ~ 5e-4 * 12.4 * k_max; at A=3 this budget requires dt <= 5e-4 / 2.54 ~ 2e-4. Using dt=1e-4 at A=3 is borderline (consistent with overflow seen in G4). The nonlinear-CFL rule can be stated as: amp * (6 + 1.5*amp) * dt * k_eff < O(1), where k_eff is the effective peak wavenumber of the soliton (of order sqrt(A/6) for the KdV sech^2 IC).
  recommended_alternative: Critical design rule for any IMEX solver applied to the Gardner or swept-KdV component of the coupled Burgers-swept-KdV system: before each amplitude sweep, compute the nonlinear CFL number NL-CFL = dt * max(6*A + 1.5*A^2) * k_soliton and confirm NL-CFL < threshold (~O(0.5-1) based on G2/G4 bracket). The empirical evidence is: dt=5e-4 passes at A=1.5 (NL-CFL ~ 0.31 for k_soliton ~ 0.5), dt=1e-4 fails at A=3.0 (NL-CFL ~ 0.16 — yet blow-up still occurs, suggesting the relevant k_max is the grid Nyquist, not the soliton wavenumber). This implies agents must use dt <= C/(max_nonlinear_speed * k_Nyquist) rather than the soliton-scale wavenumber. For Burgers-swept-KdV production runs at A in [1,3], target dt in [1e-4, 3e-4] and monitor the first few steps for overflow.
  failure: layer=method_failure, scope=regime_bound, action=narrow_claim, risk=high_risk_false_progress

### BKdV-S1  (negative depth=3)
  [DEEP SYNTHESIS, 3 rounds]
  synthesised_diagnosis: Across all 3 rounds, the program established that for BKdV at amp in [1,3], T=10, Nx=256 the binding numerical wall is BROADBAND ALIASING from the quadratic products (v^2, u*v, v*v_x), not explicit-RK4 stiffness on v_xxx. R1 (no dealias) blows up by t<0.5 via overflow->NaN; R2 adds only the 2/3-rule and reaches T=10 cleanly at the SAME dt; R3 amp=3.0 leaves edge_frac<1e-5. Working stack: Fourier + 2/3-rule + classical RK4, dt<=2e-4. The predicted second failure mode (stiffness/shock band-overrun) was not experimentally triggered because (Nx, dt, amp, T) sits well inside the safe envelope.
  ruled_out_routes:
    - Fourier pseudospectral + classical RK4 over full RHS, NO dealiasing on quadratic products (v^2, u*v, v*v_x): blows up before t=0.5 with overflow->NaN signature, dead across amp range.
    - Attempting to fix the no-dealias R1 stack by lowering dt alone: aliasing modes are forced every step regardless of dt; lowering dt slows but does not stop the cascade. R2 succeeding at the SAME dt=2e-4 confirms dt was not the binding constraint.
    - Relying on classical-RK4 with effective k_max=pi/dx (no spectral truncation) for v_xxx at dt=2e-4: this dt sits above the pure RK4 dispersion CFL bound dt_crit~1.47e-4; only dealiasing-induced reduction of effective k_max to (2/3)pi/dx (CFL bound ~4.94e-4) made dt=2e-4 safe.
    - Treating the (Nx=256, dt=2e-4, T=10) configuration as a stress test for the second failure mode (explicit-RK4 stiffness or Burgers-shock band-overrun): it is well INSIDE the safe envelope at amp<=3, so it cannot expose those modes.
  recommended_alternative: For Stage-2 push the OTHER axes to expose the predicted-but-unrealized second failure mode: keep Fourier+2/3+RK4 but (a) raise dt above ~4.94e-4 (e.g. dt=8e-4, 1.6e-3) to cross the post-dealias RK4 dispersion CFL on v_xxx and observe the explicit-stiffness blow-up signature; or (b) push amp>3 or T>>10 with a steep Burgers-favoring IC (e.g. u0 dominant, smaller width sech^2) so u*u_x steepens past the 2/3 band, then switch to ETDRK4 / IMEX Crank-Nicolson on v_xxx and MUSCL-Godunov on u*u_x as the upgrade path.

### BKdV-S1  (negative)
  attempted_route: Fourier pseudospectral derivatives (Nx=256, L=30) + classical RK4 over full explicit RHS (v_xxx treated explicitly), NO 2/3-rule dealiasing, NO IMEX. IC v0=1.5*sech^2(x+5), u0=v0^2/2, dt=2e-4, T=10.
  observation: Blow-up before t=0.5: RuntimeWarning 'overflow in multiply' on v*v then u*v, then 'invalid value in fft'; first scheduled diagnostic at t=0.5 already reports sup=NaN, mass_v=NaN, finite=False, reached_T10=False.
  rationale: Quadratic products (v^2, u*v, v*v_x) on a Fourier grid populate wavenumbers above Nx/3; without 2/3 truncation those aliased modes wrap back into resolved modes with no dissipation. Co-candidate: dt=2e-4 sits marginally above the pure-RK4 v_xxx CFL ~1.47e-4 for k_max=pi/dx.
  recommended_alternative: Keep RK4 and dt=2e-4, but apply 2/3-rule spectral dealiasing on every nonlinear product (zero modes with |k_idx|>Nx/3=85; pre-dealias state at each rhs evaluation). This isolates aliasing vs v_xxx stiffness in one experiment.
  failure: layer=method_failure, scope=general_failure, action=change_method, risk=medium_risk_drift

### BKdV-S2  (negative depth=3)
  [DEEP SYNTHESIS, 3 rounds]
  synthesised_diagnosis: The 5-candidate set splits binarily by mechanism. C1=int u dx and C2=int v dx are exactly conserved at FFT round-off across all ICs and all (dt, Nx) configs — trivially, because both PDEs are in divergence form (u_t=-d/dx(...), v_t=-d/dx(...)) on a periodic domain. C3, C4, C5 exhibit O(1) physical non-conservation that is IC-invariant and dt-invariant (drift ratio ~1.000 under 5x dt change), so the drift is not numerical. The quadratic 'sum of squared fields' ansatz is structurally not the BKdV Hamiltonian — IBP yields an uncancellable cubic remainder +(5/2)int u_x v^2 + int u_x v_xx — and ||m||^2 measures distance from a reduction manifold rather than a true invariant. No 'slowly drifting' quantity exists in this candidate set.
  ruled_out_routes:
    - Quadratic energy ansatz E = 1/2 int(u^2 + v^2 + v_x^2) dx as a BKdV invariant — grows 119% on soliton IC and 1570% on multi-mode IC, dt-invariant; IBP proves +(5/2)int u_x v^2 cubic remainder cannot be cancelled by quadratic counterterms.
    - Cross moment int u v dx as an invariant — drifts O(1) with large oscillations on both ICs, dt-invariant; no conservation structure.
    - ||m||^2 = int (u - v^2/2)^2 dx as an invariant — monotonically grows whenever IC has m != 0; m=0 is a Gardner reduction manifold, not a stable invariant of the full BKdV flow.
    - Searching for 'slowly drifting near-conserved' quantities within the C1..C5 candidate set — the split is binary (machine-zero conservation for C1, C2 vs O(1) drift for C3, C4, C5); no candidate in this set occupies the slow-drift category.
    - Attributing the C3/C4/C5 drift to dt/Nx numerical artifact — A/B dt-ratio test gives implied order p ~ 0 (<1% drift change for 5x dt change), ruling out timestep/dealias error as the source.
  recommended_alternative: Search the BKdV Hamiltonian among cubic-coupled functionals that can cancel the +(5/2)int u_x v^2 + int u_x v_xx residual: try H = int (1/2 v_x^2 - v^3 - alpha u v^2 - beta u_x v_xx + gamma u^2) dx with coefficients (alpha, beta, gamma) fit by enforcing d/dt H = 0 symbolically (sympy) and verified numerically with the same Fourier+IMEX-CN solver (Nx=256, dt=2.5e-4) on both E1 soliton and E2 multi-mode ICs; also test the known KdV-side P3 = int(v_x^2/2 - v^3)dx alone to confirm whether the v-sector retains its standard KdV cubic invariant when coupled to u.

### BKdV-S2  (negative)
  attempted_route: Baseline diagnostic sweep of 5 candidate conserved functionals (C1=int u, C2=int v, C3=int uv, C4=(1/2)int(u^2+v^2+v_x^2), C5=int m^2 with m=u-v^2/2) on soliton IC v0=1.5 sech^2(x+5), u0=0, T=20, Fourier pseudospectral Nx=256, IMEX-CN + midpoint RK2, dt=2.5e-4.
  observation: C1 stayed at O(1e-15) and C2 stayed at 3.0 to O(1e-15) (machine precision); C3 drifted 0 -> +0.539 with excursions ~1.81; C4 grew 2.70 -> 5.90 (+119%); C5 grew 1.16 -> 9.54 (+724%); sup-norm ~3.5, no blowup, finite throughout.
  rationale: Both u- and v-equations are in divergence form on a periodic domain, so int u dx and int v dx are conserved by construction — numerics merely echo the analytical fact. Worse, u0=0 makes C1 conservation indistinguishable from a u=>0 invariance for this specific IC, so the C1 measurement cannot discriminate structural vs IC-symmetry conservation.
  recommended_alternative: Re-run with u0 having nonzero spatial mean (e.g. u0 = 0.4 sin(2*pi*x/L) + 0.2 cos(6*pi*x/L) + 0.15, v0 = 0.6 cos(2*pi*x/L) + 0.3 sin(4*pi*x/L) + 0.10) to break u=>0 invariance and confirm C1/C2 are IC-invariant structural conservation laws; same solver and diagnostics, T=10.
  failure: layer=measurement_failure, scope=local_failure, action=narrow_claim, risk=medium_risk_drift
  is_trivial: true (trivial_degree=2)

### BKdV-S2  (negative)
  attempted_route: IC-invariance probe: same Fourier+2/3-dealias+IMEX-CN/midpoint-RK2 solver (Nx=256, dt=2.5e-4, T=10); IC changed to smooth multi-mode periodic u0=0.4sin(2pi x/L)+0.2cos(6pi x/L)+0.15, v0=0.6cos(2pi x/L)+0.3sin(4pi x/L)+0.10; track C1..C5.
  observation: C1=4.5 and C2=3.0 held to 1.6e-14 / 3.6e-15 (IC-invariantly conserved, not just stuck at 0). C3, C4, C5 drift monotonically and faster than E1: rel_drift C3=+33, C4=+15.7, C5=+34.5 over T=10; sup-norm grows 0.9->6.5, no blowup.
  rationale: C1, C2 are divergence-form integrals so conserved by construction regardless of IC (machine-precision drift). C4 = (1/2)int(u^2+v^2+v_x^2)dx is not the BKdV Hamiltonian: by-hand IBP gives d/dt C4 = +(5/2)int u_x v^2 + int u_x v_xx (cubic residual), monotonic growth signals wrong-functional, not numerical drift.
  recommended_alternative: Run a numerical-artifact control (E3): keep E1 soliton IC and vary dt by ~5x (e.g. 5e-4 vs 1e-4 at Nx=256) and Nx by 2x (256 vs 512 at dt=2.5e-4) over T=5; if C3/C4/C5 drift ratios ~ 1 across dt, drift is physical; otherwise it scales as dt^p. Separately, search for true energy with cubic terms (int u v^2 dx, int v^3 dx, int v_x u dx).
  failure: layer=hypothesis_failure, scope=general_failure, action=narrow_claim, risk=low_risk_omission

### BKdV-S2  (negative)
  attempted_route: dt/Nx-scaling control for C1..C5 drifts: 3 configs at E1 IC (v0=1.5 sech^2(x+5), u0=0), T=5: A(dt=5e-4,Nx=256), B(dt=1e-4,Nx=256), C(dt=2.5e-4,Nx=512); Fourier pseudospectral + 2/3 dealias + IMEX-CN/RK2.
  observation: A vs B (5x dt change at Nx=256): drift ratios C3=1.002, C4=0.992, C5=0.996 (inferred order ~0). C1,C2 drifts ~1e-15 across all configs. Nx 256->512 shifts drifts by 2-15% only.
  rationale: dt-invariance of C3/C4/C5 drift (ratio~1 over 5x dt change) shows the drift is physical, not numerical: it persists in the dt->0 limit. C1,C2 sit at FFT round-off because they are exact divergence-form mass invariants. No 'slow-drift' candidate exists in the proposed C1..C5 set.
  recommended_alternative: Search for a true BKdV Hamiltonian beyond the C1..C5 candidate list: build trial functionals with cubic densities (e.g. int(u*v^2)dx, int(v^3)dx, int(v_x*u)dx) and combinations involving v_xx; re-run E3-style dt/Nx scaling to identify any quantity whose drift -> 0 as dt -> 0.
  failure: layer=hypothesis_failure, scope=general_failure, action=abandon_route, risk=low_risk_omission

### BKdV-S3  (negative depth=3)
  [DEEP SYNTHESIS, 3 rounds]
  synthesised_diagnosis: BKdV's coherence map is governed by the IC's spectral support, not its amplitude: smooth-localized seeds (single/double sech^2, Gaussian) sit inside a soliton-like attractor basin with margin sigma~0.3-0.4 of low-pass noise; broadband seeds (white noise, sinusoid) at A>=0.8 trip a hard high-k cascade that breaches the 2/3 dealias band and blows up. The boundary between regimes is soft (in noise sigma) but the broadband-L2 blow-up wall is hard, and the choice of coherence diagnostic (lock_corr / fracL_v vs npeaks_v) reshapes where the boundary appears.
  ruled_out_routes:
    - Broadband ICs (Gaussian-envelope white noise, spatial cosine K_sin) at A=0.8 on Nx=256 / L=30 / 2-3 dealias: high-k cascade exceeds dealias band -> NaN blow-up before T=10. Not a usable Stage-2 IC at that L2 budget.
    - Searching for a sharp amplitude threshold A_c for coherence inside the sech^2 family: structural coherence is universal across A in [0.1, 1.2]; only the absolute vmax>=0.5 calibration moves with A.
    - Using npeaks_v as the primary coherence label when noise is present in the IC: oversensitive to noise texture, jumps from 1 to >=10 even when 99% of energy is still in the soliton core.
    - Treating coherent->incoherent as a single sharp phase boundary in sigma: it is a soft margin spanning sigma in [0.2, 0.6]; lock_corr and fracL_v place sigma_c at different positions inside that window.
    - Single-pulse Gaussian (G) or sech^2 (S) at A=0.8 as a 'strict coherent' reference (vmax>=0.5 fails): radiation drops vmax to ~0.42-0.46 by T=12, so they only pass the relaxed retention-based criterion, not the absolute-vmax one.
  recommended_alternative: In Stage-2, fix the diagnostic stack BEFORE sweeping: replace npeaks_v with (i) the spectral low-k fraction fracL_v at k_split tuned per-IC, (ii) lock_corr between u and 0.5 v^2, and (iii) a centroid-tracked peak height after low-pass filtering v (e.g. numpy.fft mask |k|<=k_cut~2 then scipy.signal.find_peaks on the smoothed field). Then probe the broadband-blow-up wall by sweeping L2 budget at fixed IC family (e.g. K_sin amplitude A in [0.2, 0.8] with Nx=512 to push the dealias band higher) to map the HARD boundary that E1 only glimpsed.

### BKdV-S3  (negative)
  attempted_route: Scan 5 v-IC families (G_gauss, S_sech2, N_noise, P2_twopulse, K_sin) at A=0.8 on Nx=256, L=30 box, flat u, T=12, dt=2.5e-4; coherence = (npeaks_v<=3) AND (vmax>=0.5) AND (frac_low_v>=0.5).
  observation: P2_twopulse COHERENT (vmax=0.67, npk=2, fracL=1.00). G/S structurally one-peak but vmax dropped to 0.42-0.46 (fails 0.5 threshold). N_noise (vmax0=3.77) and K_sin (L2=3.10) blew up to NaN at t=1.49 and t=8.38.
  rationale: Two confounders: (i) the IC normalization fixed vmax0=A=0.8 but not L2, so noise/sinusoid carried much larger energy (L2=3.1-4.4) — their 'incoherence' is amplitude-driven, not family-driven. (ii) the vmax>=0.5 cutoff mislabels naturally-radiating single Gaussians as INCOHERENT despite single-peak, low-k spectrum.
  recommended_alternative: In E2, equalize v-L2 norm across IC families (e.g. fix L2_v0=1.3) and either lower the coherence vmax threshold to ~0.4 or replace it with a peak-prominence/lock-corr criterion; for broadband ICs (N, K) reduce A so they survive T=12 without dealiasing-band overflow.
  failure: layer=measurement_failure, scope=regime_bound_failure, action=narrow_claim, risk=medium_risk_drift

### BKdV-S3  (negative)
  attempted_route: Amplitude scan on sech^2(x+2,width=1.5) v-seed with flat u, A in {0.1,0.2,0.3,0.4,0.5,0.6,0.8,1.0,1.2}; same Fourier pseudospectral + RK4 + integrating-factor stack as E1; T=12, dt=2.5e-4 (1e-4 for A>=1). Measured vmax_late, npeaks_v, fracL_v (k<=2), lock_corr, and new retention=vmax_late/A.
  observation: Across all 9 amplitudes: npeaks=1 (or 2 at A<=0.2), fracL_v>=0.993, retention 0.51-0.63, no blowup. Strict vmax>=0.5 only met at A>=1.0 (artifact of absolute threshold). lock_corr non-monotonic, peaks 0.79 at A=0.4, drops to -0.19 (A=0.1) and 0.19 (A=1.2).
  rationale: BKdV's localized basin is amplitude-scale-free for sech^2 seeds: the cubic v^2 nonlinearity rescales with A but stays self-focusing, so any A produces a single coherent pulse with ~50-60% retention. There is no A_c inside the localized family; the phase boundary lives on the IC-spectral-shape axis, not amplitude.
  recommended_alternative: Move off the amplitude axis: fix A=0.6 sech^2 and sweep additive Gaussian-envelope white noise sigma in {0,0.05,0.1,0.2,0.3,0.4,0.6,0.8} to interpolate between localized and broadband ICs; track fracL_v and lock_corr (drop count_peaks as primary — it is noise-texture-sensitive) to locate the soft sigma_c.
  failure: layer=hypothesis_failure, scope=regime_bound_failure, action=change_method, risk=medium_risk_drift

### BKdV-S3  (negative)
  attempted_route: E3: noise-σ sweep on sech^2 seed (A=0.6, width 1.5, x0=-2) with Gaussian-envelope white noise normalized to vmax=σ; σ∈{0,0.05,...,0.80}; Fourier pseudospectral solver (Nx=256, L=30, dt=2.5e-4, T=12); diagnostics vmax_late, npeaks_v, fracL_v (|k|≤2), fracH_v (|k|≥4), lock_corr.
  observation: No blow-up at any σ. fracL_v slides smoothly 0.999→0.545 as σ:0→0.80; lock_corr stays ~0.58 up to σ=0.20 then collapses to 0.11 by σ=0.60. npeaks_v jumps 1→10 already at σ=0.05 (metric artifact: counts tail ripples). Soft transition σ_c≈0.30–0.40 by lock; no sharp phase boundary.
  rationale: The E1 coherence heuristic uses npeaks_v with a relative height_frac=0.5 threshold; under additive noise even tiny tail ripples above min_floor=0.02 register as peaks, decoupling npk from physical incoherence. The true IC→coherence map is continuous in σ — spectral-band energy and lock_corr resolve it, peak-count does not.
  recommended_alternative: Replace npeaks_v with a smoothed/prominence-based peak counter (e.g. scipy.signal.find_peaks(v, prominence=0.1*vmax, distance=Nx//20) on a Gaussian-filtered field) and adopt a multi-metric coherence label (lock_corr≥0.3 AND fracL_v≥0.7); then refine σ_c∈[0.20,0.50] at finer resolution and test x0/width robustness.
  failure: layer=measurement_failure, scope=regime_bound_failure, action=narrow_claim, risk=medium_risk_drift

### BKdV-S4  (negative depth=3)
  [DEEP SYNTHESIS, 3 rounds]
  synthesised_diagnosis: Across all 3 rounds the program established a clean sensitivity ordering Nx >> nu_h(strong) > dt > nu_h(weak) AND exposed that the pre-validated stack has two co-constraints -- explicit-RK4 HV bound dt <= 2/(nu_h k_max^16) and the u-equation v_xx dispersion CFL dt <= 2.83/k_max^3 -- so (Nx, dt, nu_h) cannot be varied one at a time. The E1 Nx=256 baseline is sub-converged: doubling Nx (with consistent rescaling) halves energy and triples lock_corr, putting the trajectory on a different solution branch.
  ruled_out_routes:
    - Naive one-parameter Nx 256->512 at fixed (dt=5e-4, nu_h=1e-22) in this pre-validated stack: violates explicit-RK4 HV stability bound dt <= 2/(nu_h k_max^16) by ~1e5x; NaN at step 4.
    - Nx 256->512 with nu_h rescaled to preserve nu_h*k_max^16 but dt=5e-4 unchanged: violates u-equation dispersion CFL dt <= 2.83/k_max^3 ~ 1.84e-5 through the -ik*v_xx coupling; NaN at step 193.
    - Strengthening nu_h (e.g. 1e-22 -> 1e-18) at fixed dt=5e-4: same explicit-HV stability bound; (nu_h, dt) are co-constrained, cannot be varied independently.
    - Treating the E1 Nx=256 end-state values (lock=0.20, energy=3.55, m_l2=2.46, u_peak=3.67) as the converged BKdV answer: E2c shows ALL of them move by 30-140% on Nx 256->512, so they are numerical artifacts of under-resolution.
    - Using strong hyperviscosity (nu_h >> 1e-22) as 'just regularization': E3c shows it actively reshapes the attractor toward a smooth, low-amplitude, strongly-locked state -- it is a physics knob, not a numerical knob.
  recommended_alternative: Re-run BKdV S4-style sensitivity at a converged operating point: numpy.fft on Nx=512 (or 1024) with stability-consistent rescaling nu_h <= 1.53e-27 = 1e-22 / 2^16 and dt <= 1e-4 (set by the dispersion CFL 2.83/k_max^3 at Nx=512). Then bisect Nx along the geometric ladder 256/512/1024 to certify convergence at 5%, and treat nu_h <= 1e-22 as the safe weak-HV regime; never use nu_h >= 1e-20 except as an explicit physics knob.

### BKdV-S4  (negative)
  attempted_route: BKdV baseline reference run on Gardner-manifold IC v0=1.5 sech^2(x+5), u0=v0^2/2 (m0=0); pre-validated Fourier pseudospectral + 2/3-dealias + IF on v_xxx + RK4 stack at dt=5e-4, Nx=256, nu_h=1e-22, T=10. Diagnostics: ||m||_L2, ||m||_inf, L2_u, L2_v, mass_u/v, energy=int 0.5(u^2+v^2+v_x^2)dx, lock_corr, low/high spectral partition.
  observation: Run completed in 3.3s, no blow-up. mass_u/v conserved to 1e-9. m_l2: 0->2.456, m_inf: 0->3.667, lock: 1.0->0.1997, L2_u: 1.076->2.489, L2_v: 1.732->0.829, energy drift +8.2% (3.279->3.547), u_peak 1.125->3.67 (front sharpening), v_peak 1.5->0.55, eh_u(T)=0.161 (high-k content in u).
  rationale: Positive setup round: the baseline ran cleanly and produced finite, mass-conserving end-state values. But energy already drifts +8.2% and u develops high-k content (eh_u=0.161) at Nx=256, hinting the spatial cutoff is being pushed; the numbers are reference values, not yet a claim about convergence. Real informativeness requires the resolution sweep planned for E2/E3.
  recommended_alternative: Run E2: double Nx 256->512 keeping dt=5e-4 and nu_h=1e-22 fixed as a one-parameter sensitivity probe. Compare t_end values (m_l2, m_inf, L2_u, L2_v, lock, energy, u_peak, eh_u) against this baseline at the prompt's 5% shift threshold. Anticipate co-constraints among (nu_h, dt, Nx) via explicit-RK4 hyperviscous stability bound dt <= 2/(nu_h*k_max^16) and u-equation v_xx dispersion CFL ~2.83/k_max^3.
  failure: layer=method_failure, scope=local_failure, action=change_method, risk=medium_risk_drift

### BKdV-S4  (negative)
  attempted_route: E2: Nx 256->512 single-parameter probe on sech^2 BKdV IC (v0=1.5 sech^2(x+5), u0=v0^2/2) at T=10, dt=5e-4, nu_h=1e-22 with k^16 hyperviscosity + 2/3 dealias + explicit RK4 on v-IF; measure end-state m_l2, energy, lock_corr
  observation: E2a (naive) NaN at step 4; E2b (nu_h/2^16 rescale) NaN at step 193; only E2c (nu_h rescaled AND dt=1e-4) stable. At Nx=512: energy -51%, m_l2 -33%, lock_corr 0.20->0.48 (+139%), all > 5% threshold
  rationale: Two distinct CFL constraints co-couple Nx with (dt, nu_h): hyperviscous bound dt < 2/(nu_h k_max^16) and dispersion CFL dt < 2.83/k_max^3 from -ik*v_xx in u-equation (not absorbed by v-IF). Naive Nx doubling violates both, so 'single-parameter' is ill-posed; once stabilized, Nx=256 is shown sub-converged.
  recommended_alternative: Round 3: hold Nx=256, vary only nu_h (e.g., 1e-22 -> 1e-24 and 1e-20) at dt=5e-4 to test if hyperviscosity is independently sensitive; ALSO add a converged-reference run at Nx=1024 with dt=5e-5, nu_h rescaled by 2^32, to certify Nx=512 itself isn't still drifting.
  failure: layer=hypothesis_failure, scope=regime_bound_failure, action=change_method, risk=high_risk_false_progress

### BKdV-S4  (negative)
  attempted_route: Vary hyperviscosity ν_h at fixed Nx=256, dt=5e-4 on IC v0=1.5*sech^2(x+5), u0=v0^2/2, T=10; four sub-runs E3a(ν_h=1e-18,dt=5e-4), E3b(1e-26,5e-4), E3c(1e-18,dt=1e-5 rescued), E3d(1e-22,dt=1e-4 trivial check). Diagnostics: m_l2, lock_corr, energy, u_peak, eh_u/v.
  observation: E3a NaN at step 6 (HV stab bound dt≲2.8e-5 violated). E3b stable, max|Δ%|=11.7% vs E1 (7/10 diags <5%). E3c stable, max|Δ%|=277% (lock 0.20→0.75, energy −71%, u_peak −76%, eh_u −97%). E3d stable, max|Δ%|=13.2% on eh_u, rest <7%.
  rationale: ν_h is asymmetrically sensitive at Nx=256: weakening is a no-op because 2/3-dealias truncation already supplies the regularization, but strengthening 1e4× actively damps high-k content and selects a different attractor branch (smooth low-amplitude locked state). The 'ν_h is harmless numerical regularization' assumption is falsified in the strong direction.
  recommended_alternative: At Nx>=512 with co-rescaled (dt, ν_h) per E2c, re-run an HV ladder ν_h ∈ {1e-30, 1e-26, 1e-22} (under-resolved regime is now removed); compare lock_corr and energy_T to E2c to test whether the strong-HV branch (E3c) persists when truncation is no longer the dominant regularizer, vs whether it was an under-resolution artifact.
  failure: layer=hypothesis_failure, scope=regime_bound_failure, action=narrow_claim, risk=high_risk_false_progress

### BKdV-S5  (negative depth=3)
  [DEEP SYNTHESIS, 3 rounds]
  synthesised_diagnosis: The 'approximate Gardner soliton on m=0' premise is materially false: the m=0 manifold is not BKdV-invariant for sech^2 ICs (m_t|_{m=0}=(v-1)(6 v v_x+v_xxx)!=0), so E1 produces a chaotic dispersive baseline rather than a coherent wave. Against this baseline the perturbation response is sharply k-selective: low-k structured dv (mode 5) is inert for ~13 units, while broadband dv with significant high-k power grows as exp(t) and blows up at t~5.5. Mechanism: u_t -= d_x(3 v^2 + v_xx) injects a v_xxx forcing into u, so small-||dv|| but large-||dv_xxx|| perturbations drive u rapidly off m=0 and into the Burgers-shock regime, which the -d_x(u v) coupling then feeds back into v.
  ruled_out_routes:
    - sech^2 v_0 + u_0=v_0^2/2 as a 'coherent Gardner-soliton-like traveling wave' under full BKdV (E1: m=0 manifold not invariant, immediate decoherence within t<1).
    - Low-k structured single-mode perturbation (sin at mode index 5, k0~1.05) as a fast-amplifying direction over T<=13 (E2: flat ||dv||_L2 for 13 time units).
    - Broadband matched-L^2 noise on a 256-point grid with 2/3 dealiasing + MUSCL-Godunov to characterize a saturated late-time state (E3: numerical blow-up at t~5.5 before saturation; cannot distinguish physical instability from high-k under-resolution).
    - Forward-Euler on u's full RHS / a=1.5 with dt=2.5e-4 (E1 bug history: blows up at t~3 once u acquires Burgers-shock amplitude; MUSCL-Godunov on u u_x is mandatory).
    - Using energy E=0.5*integral(u^2+v^2) as a convergence/conservation diagnostic for BKdV (E1: drifts +679% even when scheme is stable; it is not a BKdV invariant).
  recommended_alternative: Stage-2 should (a) abandon the m=0/sech^2 ansatz and instead construct a numerically dressed coherent state by long-time relaxation of the full BKdV system (damped time-integration or Petviashvili/Newton iteration on the traveling-wave ODE) and use THAT as the baseline; (b) sweep single-mode dv across k-index 1..N/3 to measure lambda(k); (c) re-run the broadband case at Nx=512/1024 with hyperviscosity nu_p*k^{2p} (p=4-8) on v to separate physical high-k instability from pseudospectral under-resolution; (d) replace the energy(u,v) diagnostic with the true BKdV Casimirs (mass_v, mass_u, and any quadratic invariant derivable from the variational structure).

### BKdV-S5  (negative)
  attempted_route: E1 baseline: v0=1.0*sech^2(x+5), u0=v0^2/2 (m_0=0); BKdV on [-15,15] Nx=256, T=15, dt=1e-4; Fourier pseudospectral + 2/3 dealias + IMEX-CN on v_xxx + MUSCL-Godunov on 3 u u_x; measure mass, energy, m_norm, v_peak.
  observation: m_norm grows 0 -> 2.92 by T=15; v_peak collapses from 1.00 to ~0.4 within t<1 then oscillates chaotically (range [0.40, 1.00]); energy(u,v) drifts +679%; mass_v conserved to 0 ppm; no coherent traveling peak.
  rationale: Algebra m_t|_{m=0} = (v-1)(6 v v_x + v_xxx) is generically nonzero for sech^2 ICs, so the m=0 set is NOT an invariant manifold of full BKdV. The off-manifold drift radiates the peak immediately, giving chaotic dispersive flow rather than a coherent Gardner-like soliton.
  recommended_alternative: Reframe baseline as a chaotic-dispersive reference and measure perturbation growth as ||v_perturbed - v_base||_L2 along the chaotic trajectory (E2-style); start with a structured single-mode delta_v=0.05*sin(2*pi*5*x/L) to separate Lyapunov drift from k-selective response.
  failure: layer=hypothesis_failure, scope=general_failure, action=narrow_claim, risk=medium_risk_drift

### BKdV-S5  (negative)
  attempted_route: E2: E1 baseline IC (v0=sech^2(x+5), u0=v0^2/2, amp=1.0) + structured single-mode delta_v0 = 0.05*sin(k0*x), k0=2pi*5/L (Fourier mode 5); diagnostic = ||v_E2(t)-v_E1(t)||_L2 over t in [0,15] with dt=1e-4, Nx=256, L=30.
  observation: ||delta_v||_L2 stays flat at ~0.19-0.22 (1x initial) for t in [0,13]; jumps to 0.358 at t=14 and 1.153 at t=15 (~6x). Full-window fit gives growth rate +0.0493/unit dominated by the late-time jump; early-time rate ~0.
  rationale: Mode 5 (k0~1.05) is a low-k perturbation with small delta_v_x/v_xx/v_xxx, so the coupling u_t -= d_x(3 v^2 + v_xx) injects little forcing; there is no linear dispersion-relation pole at this k, so no direct linear amplification. Late-time jump reflects indirect nonlinear cascade or onset of baseline chaotic separation, not mode-5 instability.
  recommended_alternative: E3: replace structured mode-5 sin perturbation with zero-mean Gaussian white-noise delta_v0 rescaled to the SAME L2 norm (0.1936) (np.random.default_rng(42).standard_normal scaled); track ||v_E3-v_E1||_L2 vs E2 to test k-selectivity (high-k carries large derivatives that drive coupling).
  failure: layer=hypothesis_failure, scope=regime_bound_failure, action=change_method, risk=medium_risk_drift

### BKdV-S5  (negative)
  attempted_route: E3: sech^2(x+5) baseline (amp=1.0) + zero-mean broadband Gaussian noise on v (rng seed=42), rescaled to ||delta_v0||_L2=0.1936 (matched to E2's mode-5 sin); same IMEX-CN/MUSCL stack, T=15, dt=1e-4, Nx=256, L=30. Observable: ||v_E3(t)-v_E1(t)||_L2 vs E2 trajectory.
  observation: ||dv||_L2 grows ~exp(1.02 t): 0.194@t=0 -> 0.256@t=1 -> 5.66@t=4 -> 30.8@t=5; ratio E3/E2 climbs from 1.24 to 143.5 over t=1..5; numerical blow-up (v_peak=14.7, sup=15.6, then nan) at t~5.5, while matched-norm mode-5 stayed flat.
  rationale: Positive finding for k-selectivity: high-k components of delta_v have small L2 but large v_xxx, and the explicit coupling u_t -= d_x(3 v^2 + v_xxx) injects huge forcing into u, driving runaway. But the late-time state is numerical blow-up, not a saturated physical regime, so 'into what state' is not answered.
  recommended_alternative: Re-run E3 at higher resolution (Nx=512 and 1024) with same seed and tighter dt (e.g. 2.5e-5) to test stack-dependence of the +1.02/unit growth rate; then sweep single-mode delta_v across k-index k=1..N/3 with eps fixed to map a growth-rate dispersion lambda(k) and confirm continuum k-selectivity.
  failure: layer=hypothesis_failure, scope=regime_bound_failure, action=narrow_claim, risk=medium_risk_drift

### BKdV-S6  (negative depth=3)
  [DEEP SYNTHESIS, 3 rounds]
  synthesised_diagnosis: The Burgers self-flux 3*u*u_x on the smoothed-bore IC drives a one-sided in-band high-k energy cascade that 2/3 dealiasing CANNOT dissipate (it only zeros |k|>2k_max/3, leaving the cascade to pile up just below the cutoff). The shock-energy injection rate ~u_max*k_max~50/unit must be exceeded by the dissipation rate; this requires nu*k^2>>u*k at the spectral edge, i.e. nu>>u_max/k_max~0.11. Empirically nu_lin~1e-2 (marginal) to 5e-2 (clean) works; k^8 hyperviscosity needs nu_h~1e-9 (at the RK4 stability ceiling). Without it, u is quantitatively wrong and v is poisoned via -d_x(u*v).
  ruled_out_routes:
    - Fourier pseudospectral + 2/3-rule dealias + classical RK4 with NO explicit u-dissipation on bore-like u IC (1.5(1-tanh(x/0.5))/2): produces 2.3x u_max overshoot and 42x TV inflation by T=6.
    - Adding 'standard tiny' linear viscosity eps*u_xx with eps=1e-4 on bore IC: ineffective (<7% reduction in u_max, <2% in TV); rate-balance shows 2-3 orders of magnitude undersized.
    - k^8 hyperviscosity at the BKdV-S4 smooth-soliton 'safe envelope' (nu_h ~ 1e-22 to 1e-20) on this IC: 13 orders of magnitude too weak; nu_h up to 1e-12 still yields TV_final>115 and u_max_final>3.0.
    - Linear viscosity nu=1e-3 on bore IC: insufficient (u_max_final=2.54, TV_final=93, u_min_final=-0.63).
    - Hyperviscosity nu_h<=1e-10 on bore IC: insufficient (TV_final>77, u_max_final>2.5); only nu_h=1e-9 (at explicit-RK4 stability ceiling for Nx=256/dt=1e-4) passes.
  recommended_alternative: For Stage-2 BKdV tasks with bore-like or steep u-gradient ICs: default to explicit linear viscosity nu*u_xx with nu=5e-2 (CFL-trivial at Nx=256, dt=1e-4, RK4; nu*k_max^2*dt~3.6e-3); if higher selectivity needed, use exponential / IMEX integrator (e.g. scipy.integrate.solve_ivp with method='LSODA' or a custom ETDRK4 on the linear part) to lift the explicit-stability ceiling and allow k^8 hyperviscosity above 1e-9. Always log TV(u) and mid-k spectral ratio E(k_max/3<|k|<2k_max/3)/E_total as primary diagnostics for u-side well-behavedness; re-calibrate nu per IC class rather than transferring BKdV-S4 smooth-soliton envelopes.

### BKdV-S6  (negative)
  attempted_route: Pre-validated stack (Fourier pseudospectral + 2/3-rule dealias + classical RK4, dt=1e-4, Nx=256, L=30) with NO u-side viscosity/hyperviscosity/filter on IC u=1.5(1-tanh(x/0.5))/2 (smoothed bore) + v=1.5 sech^2(x+5), T=6.
  observation: No IEEE blow-up; mass_u exactly preserved (22.589). But u_max grows IC 1.5 -> 3.41 (~2.3x), u_min dives to -1.07, TV(u) inflates 3.0 -> 125.8 (42x), mid-band spectral ratio 0.3% -> 25%; v_max collapses 1.50 -> 0.58.
  rationale: 2/3-rule dealiasing only zeroes |k|>2/3 k_max to prevent aliasing OF products into resolved modes; it does NOT dissipate energy already inside the resolved band. Burgers self-flux 3 u u_x steepens the bore and piles Gibbs energy just below the cutoff, then leaks into v via -d_x(uv).
  recommended_alternative: Add explicit linear viscosity term eps*u_xx in the u-RHS (computed spectrally as ifft(-k^2*fft(u))) with eps=1e-4 as the conventional starting value, treated explicitly inside RK4; sweep upward if insufficient.
  failure: layer=method_failure, scope=regime_bound_failure, action=change_method, risk=high_risk_false_progress

### BKdV-S6  (negative)
  attempted_route: Pre-validated Fourier+2/3-dealias+RK4 stack on BKdV with explicit linear viscosity eps*u_xx, eps=1e-4, on u-equation; IC: u0=1.5*(1-tanh(x/0.5))/2 bore + v0=1.5*sech^2(x+5); Nx=256, L=30, dt=1e-4, T=6.
  observation: eps=1e-4 essentially indistinguishable from eps=0 (E1): u_max 3.41->3.18 (~7%), TV(u) 126->124 (~1.4%), u_min still -0.77; mid-k energy ratio still grows to 0.129; Gibbs/shock blow-up not suppressed.
  rationale: Damping rate eps*k^2 ~ 0.032 at 2/3 k_max gives e^{-0.19}~0.82 over T=6, while the 3*u*u_x nonlinear cascade injects high-k energy faster; scaling needs eps*k_max^2 >> u_max*k_max, i.e. eps >> u_max/k_max ~ 0.17.
  recommended_alternative: Sweep dissipation strengths: linear viscosity eps in {1e-3, 1e-2, 5e-2} via explicit eps*u_xx, AND hyperviscosity nu_h*(-1)^{p+1}*d^{2p}/dx^{2p} with p=4 (k^8 weighting) for nu_h in {1e-8,...,1e-6}, measuring TV(u), u_max, mid-k energy ratio to find minimum sufficient floor.
  failure: layer=hypothesis_failure, scope=regime_bound_failure, action=change_method, risk=medium_risk_drift

### BKdV-S6  (negative)
  attempted_route: Sweep u-side dissipation atop Fourier+2/3-dealias+RK4 (Nx=256, dt=1e-4, T=6) for smoothed bore u0=1.5(1-tanh(x/0.5))/2 + v0=1.5 sech^2(x+5): linear nu*u_xx in {1e-3..1e-1} and k^8 hyperviscosity nu_h in {1e-14..1e-9}.
  observation: Linear nu>=1e-2 yields u_max_final<=1.62, TV(u)_final<=27, u_min_final>=-0.03 (passes practical bound); nu_h<=1e-10 fails (u_max_final~2.5-3.1, TV~80-120), only nu_h=1e-9 (near RK4 stability ceiling 4e-8) passes. All cases show transient u_max~2.7-3.4 during early bore steepening.
  rationale: The bare stack cannot bound the Burgers self-flux for strong-gradient ICs: the bore physically injects high-k energy faster than dealiasing alone can absorb. Linear viscosity at nu~1e-2-5e-2 matches the Burgers shock-thickness scale; k^8 hyperviscosity needs nu_h near the explicit-stability ceiling to be effective at this Nx.
  recommended_alternative: Adopt nu_linear=5e-2 as the default u-side dissipation for downstream BKdV runs with bore-like u-gradients (TV_final~9.6, u_min_final>=0). For higher Nx, use implicit/IMEX integration of nu*u_xx (e.g., scipy IMEX-RK or split-step exp(-nu*k^2*dt)) to remove the dt~1/(nu*k_max^2) constraint, and re-test amp/IC sensitivity.
  failure: layer=hypothesis_failure, scope=regime_bound_failure, action=narrow_claim, risk=medium_risk_drift

### BKdV-S7  (negative depth=3)
  [DEEP SYNTHESIS, 3 rounds]
  synthesised_diagnosis: Across all 3 rounds the program empirically established that the Gardner equation is the m=0 algebraic reduction of BKdV but NOT a dynamically invariant submanifold: BKdV-S5's identity m_t|_(m=0) = (v-1)(6 v v_x + v_xxx) gives a nonzero source whenever the IC has peak v > 1, and at A=1.5 this source (||S||_L2 = 1.77) drives ||m||_L2 to grow at rate ~1.2/t, fragments v via the -d_x(uv) coupling, and produces a multi-peaked dispersive state uncorrelated with the Gardner reference (||v_BKdV-v_Gardner||_L2 > ||v_BKdV||_L2) by t~2. Spectral prediction confirmed: cos-sim 0.94 between |S_hat| and observed |m_hat|/t at t=0.5; top modes n=2-6.
  ruled_out_routes:
    - Treating the Gardner reduction u=v^2/2 as a dynamically invariant set of BKdV: the m=0 manifold is a kinematic identity only and is exited at rate ~1.2/unit-t for any IC with peak v > 1.
    - Inheriting Gardner stability for BKdV stability with v_0 = A sech^2 at A >= 1: the (v-1) factor in the BKdV-S5 source flips sign over the soliton core and turns on the cubic Burgers piece, giving log-log slope ~2.5 in ||S||_L2(A).
    - Using sech^2 (KdV soliton ansatz) as a coherent BKdV state at moderate A: it is NOT a BKdV traveling wave and fragments into 8 peaks by T=10 even with mass-exact spectral/2/3-dealias/RK4 numerics.
    - Blaming Stage-1 numerics for the breakdown: mass_u/mass_v drift = 0.000000%, sup bounded ~4, no spectral pile-up — Fourier pseudospectral + 2/3 dealias + RK4 dt=2e-4 at Nx=256 is clean; the failure is physical, not numerical.
    - Hoping the m=0 manifold is preserved long enough for short-time stability arguments: ||m||_L2 already exceeds 0.74 by t=0.5 and 1.22 by t=1, well before any meaningful coherence horizon.
  recommended_alternative: Construct a coherent traveling-wave state of the FULL coupled BKdV system directly via imaginary-time / Petviashvili relaxation on (u,v) with traveling-frame ansatz u=U(x-ct), v=V(x-ct), seeded by sech^2 but iterated to fixed point; alternatively probe an amplitude regime A<1 where (v-1)<0 uniformly and S is dispersive-dominated (log-log slope ~0.22), using a Krasny/exponential time-differencing scheme for the v_xxx stiffness while keeping Nx=256 spectral + 2/3 dealias to handle the cubic Gardner nonlinearity cleanly.
