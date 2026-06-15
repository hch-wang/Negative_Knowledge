## Memory: BKdV knowledge bank ONLY (10+20=30 entries)

This bank is from a RELATED-BUT-DIFFERENT system (Burgers-swept-KdV — Holm 2025), constructed in Section §3 of this paper. **No NLS-specific entries available.** Some BKdV entries cover shared mechanisms with B-NLS (Burgers shock methods, dealiasing, mass-conservation-not-sufficient). Other entries are mechanism-mismatched: the v_xxx KdV dispersion has no analog in B-NLS, Gardner cubic-amplitude CFL does not apply to NLS Kerr, shallow-water HLL/Lax-Friedrichs assume non-Madelung hydrodynamics. **NLS Madelung quantum pressure (sqrt N)_xx/(2 sqrt N) has NO analog in this bank — reason from general principles.**

### Section B — BKdV positive entries

### kb-burgers-MUSCL-Godunov-shock-pass  (positive, domain=burgers)
  method: MUSCL-van Leer + Godunov + forward Euler
  claim: MUSCL with van Leer limiter + Godunov exact Riemann flux + forward Euler at CFL=0.45 achieves L1 error ~0.003 for Burgers shock at T=0.5, well inside the 0.10 acceptance band.
  applicability: For the Burgers component of coupled Burgers-swept-KdV, MUSCL+Godunov is a proven baseline for bore (shock) propagation. Use it as the default spatial scheme when a sharp bore must interact with a KdV soliton; its TVD property prevents Gibbs contamination in the Burgers sector.

### kb-burgers-Godunov-preShock-smooth  (positive, domain=burgers)
  method: Godunov upwind (exact Riemann for Burgers)
  claim: First-order Godunov upwind (exact Riemann) at adaptive CFL=0.8 correctly reproduces the smooth pre-shock Burgers profile at T=0.1: amplitude_range=2.00, single local maximum, max_jump=0.053 — consistent with a slightly steepened sine.
  applicability: For the early-time Burgers component (before bore forms) in Burgers-swept-KdV coupled problems, even first-order Godunov is sufficient. This establishes a lower-cost option for initialization or short-time baseline runs where the bore has not yet formed.

### kb-kdv-IMEX-CN-spectral-pass  (positive, domain=kdv)
  method: IMEX-Crank-Nicolson spectral (Fourier + CN-dispersion + explicit-nonlinear)
  claim: IMEX-spectral (Fourier pseudospectral + Crank-Nicolson on v_xxx + explicit nonlinear, dt=0.0005, Nt=4000) successfully propagates a KdV single soliton to T=2: peak at x=3.05, amplitude=2.03, mass=4.000 — all within specification.
  applicability: IMEX-CN is the recommended baseline for the KdV/swept-KdV component of coupled problems. The CN denominator (1 - dt/2 * ik^3) has magnitude >=1 so it is unconditionally stable for the dispersive stiffness — no exponential overflow. Transfer to coupled Burgers-swept-KdV: handle the swept dispersive term with CN and the Burgers-like coupling explicitly.

### kb-kdv-smallAmplitude-dispersiveRegime  (positive, domain=kdv)
  method: IMEX-spectral integrating-factor RK4
  claim: IMEX-spectral integrating-factor RK4 remains stable for amplitude-0.1 KdV IC, correctly reproducing the linear-dispersive regime: peak amplitude decays from 0.1 to ~0.052, 8 local maxima consistent with a dispersive wave train, no blow-up.
  applicability: In coupled Burgers-swept-KdV: small-amplitude KdV components (after energy exchange with the Burgers bore) will not form stable solitons — they disperse. This sets a threshold: soliton formation in the KdV/swept-KdV sector requires sufficient amplitude. Use this as a diagnostic: if post-interaction KdV amplitudes are O(0.1) or less, expect dispersive radiation rather than soliton trains.

### kb-shallowWater-LaxFriedrichs-stable-smeared  (positive, domain=shallow_water)
  method: Global Lax-Friedrichs flux + explicit Euler
  claim: Global Lax-Friedrichs flux with explicit Euler at CFL=0.4 solves the shallow water dam-break stably: h stays positive (h_min=1.452), mass conserved (mass_h=300.0), no NaN/Inf, max_jump=0.064 (smeared but bounded).
  applicability: Lax-Friedrichs is a reliable failsafe for shallow-water or shallow-water-like components in coupled problems when robustness is paramount and sharp shock resolution is not required. In coupled Burgers-swept-KdV experiments, LxF can serve as a stability baseline for validating more accurate schemes (HLL, MUSCL), but should not be the production scheme where bore sharpness matters for the soliton interaction measurement.

### kb-shallowWater-HLL-dam-break-pass  (positive, domain=shallow_water)
  method: HLL Riemann solver + explicit Euler
  claim: HLL (Harten-Lax-van Leer) Riemann solver with explicit Euler at CFL=0.4 solves the standard shallow water dam-break accurately: h_min=1.452, h_negative=false, mass conserved (mass_h=300.0), max_jump=0.090, all-finite.
  applicability: HLL is the recommended Riemann solver for any hyperbolic component in a coupled Burgers-swept-KdV system when the solution may include near-dry or variable-depth regions. Its positivity-preservation and entropy compliance make it safer than Roe for robustness, and it resolves shocks more sharply than Lax-Friedrichs.

### kb-kdv-spectral-solitonAmplitude-conservation  (positive, domain=kdv)
  method: IMEX-CN spectral and IMEX-IF RK4 spectral
  claim: Fourier pseudospectral IMEX methods (IMEX-CN and IMEX-IF RK4) both conserve KdV soliton amplitude within ~2% and mass within <1% over T=2 when correctly implemented with stable time stepping, even without dealiasing (IMEX-CN case).
  applicability: Spectral IMEX methods are the preferred discretization for tracking soliton amplitude and phase in the KdV/swept-KdV sector of coupled problems. For Gaussian decomposition into a soliton train, the mass and amplitude conservation properties of these methods ensure that decomposition coefficients remain meaningful over multi-soliton propagation times.

### kb-general-firstOrder-Godunov-preShock-baseline  (positive, domain=general)
  method: First-order Godunov (exact Riemann) / Godunov flux as MUSCL base
  claim: First-order Godunov (exact Riemann flux) at adaptive CFL is a reliable, low-cost baseline for hyperbolic conservation laws in smooth or pre-shock regimes: demonstrated for Burgers T=0.1 (A2) with correct smooth profile, and as component of MUSCL scheme for Burgers T=0.5 pilot.
  applicability: For coupled Burgers-swept-KdV: use Godunov flux as the foundation for the Burgers operator at any time horizon. Before shock formation, first-order Godunov alone suffices; after shock formation, upgrade to MUSCL+Godunov. The entropy-consistent Godunov flux ensures no spurious entropy violations in the bore region during soliton interaction.

### kb-gardner-G2-IMEX-CN-dealiased-stableRadiation  (positive, domain=gardner)
  method: IMEX-Crank-Nicolson spectral with 2/3 dealiasing
  claim: IMEX-CN spectral with 2/3 dealiasing (CN on v_xxx, explicit on 6vv_x + (3/2)v^2 v_x, dt=0.0005) is numerically stable for Gardner at IC amplitude 1.5 over T=2: all-finite, mass=3.000 conserved. However, the KdV-style sech^2 IC is NOT a true Gardner soliton — the wave radiates and amplitude decays to 0.612, peak migrates to x=-3.52, 13 local maxima (substantial radiation).
  applicability: IMEX-CN spectral with 2/3 dealiasing is the recommended stable method for the Gardner component of Burgers-swept-KdV (m=0 reduction). However, correctness depends critically on using a proper Gardner soliton IC, not a KdV sech^2 IC. For soliton-stability and Gaussian decomposition tasks, always use the Gardner soliton parametrization; KdV ICs at the same amplitude will produce spurious radiation trains that contaminate any bore-soliton interaction measurement.

### kb-gardner-KdV-method-transfer-moderate-amplitude  (positive, domain=gardner)
  method: IMEX-Crank-Nicolson spectral with 2/3 dealiasing (positive transfer); IFRK4 (negative transfer)
  claim: IMEX-CN spectral with 2/3 dealiasing — the method validated on KdV (kb-kdv-IMEX-CN-spectral-pass, amp 2.0, dt=0.0005) — transfers cleanly to Gardner at moderate amplitudes in the range [1, 2]: G2 (amp 1.5, dt=0.0005) is all-finite with mass conserved, confirming numerical stability. By contrast, IFRK4 (kb-kdv-IFRK4-blowup) does NOT transfer: it blows up on KdV itself, making it doubly unsuitable for Gardner where the cubic term adds an additional explicit-stiffness channel.
  applicability: For the Gardner-reduction (m=0) leg of Burgers-swept-KdV: adopt IMEX-CN spectral + 2/3 dealiasing as the baseline method, transferring directly from the validated KdV solver. No re-engineering of the dispersive (v_xxx) treatment is needed; only the nonlinear stage must be extended to include the cubic term 6vv_x + (3/2)v^2 v_x. Do NOT attempt to port IFRK4 to Gardner: it failed even on the simpler KdV equation and the Gardner cubic nonlinearity would only worsen the overflow in exp(ik^3 t) or tighten the stability constraint further. For amplitude > 2, this positive transfer no longer holds (see kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup); re-evaluate dt before any amplitude increase.


### Section C — BKdV negative entries

### kb-burgers-fwdEuler-centralFD-Gibbs  (negative, domain=burgers)
  attempted_route: Forward Euler + 2nd-order central FD (no upwinding, no limiter), CFL=0.4, Burgers u0=-sin(pi*x), T=0.5
  observation: Solution is all-finite but exhibits 21 local maxima (vs 1 expected), amplitude_range=7.21 (~3.6× true amplitude), max_jump=3.61 — massive Gibbs-like oscillations, effectively blow-up in accuracy if not in finiteness.
  failure: layer=method_failure, scope=general_failure, degree=contradicted, action=change_method, risk=high_risk_false_progress
  applicability: In a coupled Burgers-swept-KdV solver, any naive central-difference treatment of the Burgers advection term will corrupt both the Burgers bore and the adjacent KdV soliton region via spurious oscillation cross-contamination. Always use an upwind or flux-limited scheme for the Burgers component.

### kb-burgers-LaxFriedrichs-longTime-dissipation  (negative, domain=burgers)
  attempted_route: Global Lax-Friedrichs FD scheme, CFL=0.5, Burgers u0=-sin(pi*x), T=10.0
  observation: Solution is all-finite but amplitude decayed to max=0.090 (vs expected O(1)), mean_jump=0.0018, single local maximum — severe over-diffusion from Lax-Friedrichs at 10× the shock timescale.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=medium_risk_drift
  applicability: In long-time coupled Burgers-KdV simulations, Lax-Friedrichs is unsuitable for the Burgers component: it will artificially damp the bore amplitude and cause the bore-soliton interaction energy to be misrepresented. Prefer MUSCL or upwind-limited schemes for T >> shock timescale.

### kb-burgers-LaxFriedrichs-periodic-longTime-contamination  (negative, domain=burgers)
  attempted_route: Any stable scheme on periodic domain for Burgers, T=10 (multiple domain-traversal times)
  observation: Result shows smooth, nearly zero-mean profile (amplitude 0.181) with periodic recirculation contaminating any shock/rarefaction structure. Genuine physics vs numerical artifact is indistinguishable at T=10 on this periodic domain.
  failure: layer=measurement_failure, scope=regime_bound, degree=artifact_driven, action=narrow_claim, risk=medium_risk_drift
  applicability: In coupled Burgers-swept-KdV experiments on periodic domains, long-time runs beyond a few domain-traversal times produce spurious bore-soliton interaction histories. Restrict comparison windows to T where neither wave has wrapped around, or use absorbing/outflow boundaries.

### kb-kdv-IFRK4-blowup  (negative, domain=kdv)
  attempted_route: Fourier pseudospectral + integrating-factor RK4 (IFRK4), dt unspecified, no dealiasing, KdV v0=2 sech^2(x+5), T=2.0, Nx=256
  observation: Output array shape (256,) is all-NaN (256 NaN/Inf). Eval score=0. Blow-up despite agent claiming correct IF-RK4 formulation.
  failure: layer=implementation_failure, scope=local_failure, degree=unstable, action=change_method, risk=medium_risk_drift
  applicability: For coupled Burgers-swept-KdV: do not use IFRK4 without (a) 2/3 dealiasing on the nonlinear term, (b) verification that |k^3 * dt| stays below the RK4 stability boundary, and (c) no sign errors in the integrating-factor back-transform. IMEX-CN is a safer default; use IFRK4 only if 4th-order time accuracy is required and the implementation is carefully validated.

### kb-kdv-explicit-RK4-stiffness-blowup  (negative, domain=kdv)
  attempted_route: Explicit RK4 + central FD for v_xxx, dt=1e-5, KdV v0=2 sech^2(x+5), T=2.0, Nx=256
  observation: Unexpectedly, output is all-finite (no NaN) with amplitude_range=1.63 and 10 local maxima — but amplitude is wrong (expected ~2.0) and 10 spurious peaks indicate the soliton has fragmented or dispersed into artifacts. Prediction of NaN blow-up was not confirmed, but the result is physically wrong.
  failure: layer=hypothesis_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=medium_risk_drift
  applicability: For coupled Burgers-swept-KdV: explicit-only treatment of the KdV dispersive term (v_xxx or swept equivalent) produces soliton fragmentation even if NaN is avoided. Any agent solving this system must use an implicit or IMEX treatment of the dispersive term; explicit RK4 alone is not sufficient even with very small dt.

### kb-kdv-noDealiasing-aliasing-artifacts  (negative, domain=kdv)
  attempted_route: Fourier pseudospectral + IMEX Euler, dt=0.005, NO 2/3 dealiasing on nonlinear term, KdV v0=2 sech^2(x+5), T=2.0, Nx=256
  observation: Output is all-finite with amplitude 2.87 (>2.0 expected) and 4 local maxima (vs 1 expected soliton) — aliasing energy has created spurious soliton-like peaks and inflated the apparent amplitude.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=medium_risk_drift
  applicability: For coupled Burgers-swept-KdV spectral implementations: always apply the 2/3 dealiasing rule (or at minimum a smooth spectral filter) to the nonlinear term. Without it, the soliton amplitude and count are unreliable, which would corrupt any soliton-bore interaction measurement. This is especially critical for Gaussian decomposition into soliton trains where individual soliton amplitudes must be accurately tracked.

### kb-kdv-amplitude-threshold-soliton  (negative, domain=kdv)
  attempted_route: KdV with amplitude 0.1 IC, expecting soliton propagation similar to amplitude-2 case
  observation: Peak amplitude at T=2 is 0.052 (nearly halved from IC), 8 local maxima (dispersive wave train), zero_crossings=12 — clearly not a soliton. The soliton-propagation expectation fails at this amplitude.
  failure: layer=hypothesis_failure, scope=regime_bound, degree=contradicted, action=narrow_claim, risk=low_risk_omission
  applicability: For Gaussian decomposition into KdV soliton trains in coupled Burgers-swept-KdV: only Gaussian components with amplitude above a system-dependent threshold (empirically >> 0.1 for standard KdV scaling) contribute solitons; sub-threshold components produce dispersive radiation. This shapes which Gaussian decomposition modes matter for the soliton-bore interaction measurement.

### kb-shallowWater-centralFD-fwdEuler-hNegative  (negative, domain=shallow_water)
  attempted_route: Forward Euler + central FD (no limiter, no upwinding, no Riemann solver), shallow water dam-break h=[2,1], T=0.4, Nx=200
  observation: h goes negative (h_min=-0.139, h_negative=true), momentum reaches |value|=5.27e10 — explosive blow-up in the momentum field while h is only marginally negative. All-finite in floating point but physically degenerate.
  failure: layer=method_failure, scope=general_failure, degree=contradicted, action=change_method, risk=high_risk_false_progress
  applicability: Directly relevant to the Burgers-swept-KdV coupled system if the swept-KdV has a shallow-water-like structure: central FD without upwinding or Riemann fluxes is catastrophic for any hyperbolic system with discontinuous ICs. Never use central FD alone for the advective terms in any wave-breaking or bore-like regime.

### kb-shallowWater-LaxFriedrichs-overdiffusion  (negative, domain=shallow_water)
  attempted_route: Global Lax-Friedrichs flux, CFL=0.4, shallow water dam-break h=[2,1], T=0.4
  observation: max_jump=0.064 vs HLL's max_jump=0.090 at same resolution — shock is ~28% more smeared than HLL. The shock-rarefaction structure is excessively broadened for physical analysis.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=low_risk_omission
  applicability: For coupled Burgers-swept-KdV where bore sharpness affects the soliton interaction timescale, prefer HLL over Lax-Friedrichs for the hyperbolic component. Smeared bores may delay or distort the interaction region, leading to incorrect soliton phase shifts in measurement.

### kb-shallowWater-dryBed-naiveClip-hu-singular  (negative, domain=shallow_water)
  attempted_route: HLL + Godunov finite volume + adaptive CFL, with positivity clip (h=max(h,0)) at dry interface h_R=0, shallow water, T=0.3
  observation: h stays non-negative (h_min=0.00153, clipped) and mass is conserved (100.0), but the momentum (hu) field has values reaching -0.295 while h is near zero — u = hu/h is ill-defined at dry cells (effective |u| > 100 near dry front).
  failure: layer=implementation_failure, scope=local_failure, degree=partial, action=change_method, risk=medium_risk_drift
  applicability: In coupled Burgers-swept-KdV if any region can develop near-zero depth or near-zero amplitude (e.g., swept-KdV in a region where the Burgers bore evacuates material), use a wet/dry front tracking scheme rather than simple positivity clips. Otherwise velocity blow-up near the front will corrupt the bore-soliton interaction.

### kb-general-centralFD-hyperbolic-shockFormation  (negative, domain=general)
  attempted_route: Central finite differences (no upwinding, no limiter) applied to any nonlinear hyperbolic conservation law with discontinuous or shock-forming initial conditions — observed in A1 (Burgers) and A7 (shallow water)
  observation: A1: 21 local maxima, amplitude 7.2×; A7: h goes negative (h_min=-0.139), momentum 5.3e10. Both cases produce physically degenerate output that is technically finite but numerically useless.
  failure: layer=method_failure, scope=general_failure, degree=contradicted, action=change_method, risk=high_risk_false_progress
  applicability: Universal rule for coupled Burgers-swept-KdV: the Burgers and any hyperbolic component must use upwind, Riemann-solver, or flux-limited spatial discretization. Central FD is acceptable only for smooth dispersive terms (like v_xxx in KdV when treated implicitly) — never for the advective nonlinear flux in a shock-forming equation.

### kb-general-finiteness-not-accuracy  (negative, domain=general)
  attempted_route: Various schemes (A1, A4, A7) that produced all-finite output arrays but with physically wrong solutions
  observation: A1: all_finite=true but 21 local maxima; A4: all_finite=true but soliton fragmented into 10 peaks with amplitude 1.63 vs 2.0; A7: all_finite=true but momentum 5.3e10. Exit code 0 in all cases.
  failure: layer=measurement_failure, scope=general_failure, degree=overclaimed, action=narrow_claim, risk=high_risk_false_progress
  applicability: For future coupled Burgers-swept-KdV evaluation pipelines: do not use NaN/Inf presence as the sole correctness criterion. Also check: local maxima count vs expected soliton count, peak amplitude vs reference, mass conservation, and maximum jump vs reference max-jump. These diagnostics distinguish catastrophic accuracy failures from true stability.

### kb-gardner-G1-explicitRK4-finiteFrag  (negative, domain=gardner)
  attempted_route: Explicit RK4 + 2nd-order central FD for all spatial derivatives (v_xxx and nonlinear), dt=1e-5, Gardner v0=1.5 sech^2(x+5), T=2.0, Nx=256, periodic
  observation: Output is all-finite (no NaN), mass=3.000, but soliton has fragmented: 14 local maxima (vs 1 expected), peak amplitude only 1.506 (down from IC amplitude 1.5 — near-stationary peak but heavily fragmented structure), peak migrated to x=2.11 (expected ~x=3-5 for KdV-speed soliton). The scheme survived only because dt=1e-5 is near the stability boundary dt~O(dx^3)~1.6e-4.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=medium_risk_drift
  applicability: For the Gardner-reduction regime of coupled Burgers-swept-KdV (m=0): pure explicit RK4 on Gardner is impractical — it requires ~200,000 steps for T=2 and still produces fragmented soliton structure. Any production solver for this regime must use IMEX or spectral-ETD methods for the dispersive term. Do not use explicit-only methods even with very small dt to 'be safe'; they do not produce accurate soliton propagation on Gardner.

### kb-gardner-G3-noDealiasing-cubicAliasing  (negative, domain=gardner)
  attempted_route: IMEX-CN spectral, NO 2/3 dealiasing, dt=0.001, Gardner v0=1.5 sech^2(x+5), T=2.0, Nx=256
  observation: Output is all-finite with peak amplitude 1.545 (slightly above IC amplitude 1.5, vs 2.87 inflation in KdV no-dealiasing case A5), 11 local maxima, mass=3.000. Aliasing artifacts are present (11 spurious peaks) but amplitude inflation is more modest than KdV case at this amplitude; no catastrophic blow-up at amp 1.5.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=medium_risk_drift
  applicability: For Gardner and the full coupled Burgers-swept-KdV system: the cubic nonlinearity adds a third aliasing channel that, even at moderate amplitude, creates more spurious peak count than the KdV quadratic term alone. Always apply 2/3 dealiasing (or higher-order filtering) when the PDE contains cubic or higher polynomial nonlinearities. For Gaussian decomposition tasks, spurious peak count from aliasing would directly corrupt soliton-train identification.

### kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup  (negative, domain=gardner)
  attempted_route: IMEX-CN spectral (CN on v_xxx, explicit on nonlinear), dt=1e-4, Gardner v0=3.0 sech^2(x+5), T=2.0, Nx=256 — same method as G2 but at 2× the IC amplitude
  observation: All 256 outputs are NaN (n_nan=256, all_finite=false). Runtime overflow encountered in the nonlinear term: 'overflow encountered in multiply' (6.0*v*vx + 1.5*v^2*vx) and 'invalid value encountered in fft' — the IMEX-CN explicit nonlinear step blew up at amplitude 3.0 even though the same method (similar dt) was stable at amplitude 1.5.
  failure: layer=method_failure, scope=regime_bound, degree=unstable, action=change_method, risk=high_risk_false_progress
  applicability: Critical for the Gardner-reduction regime and full coupled Burgers-swept-KdV: IMEX-CN with explicit nonlinear has an amplitude-dependent CFL limit driven by the combined 6vv_x + (3/2)v^2 v_x term. When amplitude doubles, the effective CFL limit tightens by more than 2×. Always re-evaluate dt when changing IC amplitude; do not assume a dt validated at lower amplitude is safe at higher amplitude. For large-amplitude Gardner or swept-KdV regimes, consider fully implicit nonlinear solvers or ETD-RK methods with accurate stability analysis.

### kb-gardner-sech2IC-not-exact-soliton  (negative, domain=gardner)
  attempted_route: Using KdV sech^2 IC (v0 = A sech^2(x+x0)) as initial condition for Gardner equation at any amplitude
  observation: G2 (amp 1.5): amplitude decayed from 1.5 to 0.612, 13 local maxima, peak migrated to x=-3.52 — substantial radiation from wrong IC. G4 (amp 3.0): complete NaN blow-up (amplitude-CFL failure exacerbated by wrong IC shape causing rapid nonlinear transient).
  failure: layer=hypothesis_failure, scope=general_failure, degree=contradicted, action=change_method, risk=high_risk_false_progress
  applicability: Essential for all Gardner-reduction sub-tasks in Burgers-swept-KdV: use the proper Gardner soliton IC (parametrized with the cubic coefficient epsilon) for soliton stability tests, not a KdV sech^2 IC. Using KdV ICs will (a) generate spurious radiation trains that corrupt bore-soliton interaction measurements, (b) potentially trigger amplitude-CFL blow-up at amplitudes where the nonlinear transient is large. For the Gaussian decomposition task, fit Gardner soliton profiles to the data, not KdV soliton shapes.

### kb-gardner-cubicTerm-tightens-nonlinearCFL  (negative, domain=gardner)
  attempted_route: Any IMEX or semi-implicit method with explicit treatment of the nonlinear terms in Gardner, re-using a dt validated on KdV at the same grid resolution
  observation: G4 (IMEX-CN, dt=1e-4, amp 3.0): complete NaN blow-up. G1 (explicit RK4, dt=1e-5, amp 1.5): survived but fragmented. KdV IMEX-CN at dt=0.0005 (amp 2.0, kb-kdv-IMEX-CN-spectral-pass): stable. The cubic term (3/2)v^2 v_x at amplitude A contributes O(1.5A^2) to the nonlinear CFL, tightening it by a factor ~(1 + 0.25A) compared to pure KdV at the same A.
  failure: layer=method_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=high_risk_false_progress
  applicability: For the Gardner-reduction regime of Burgers-swept-KdV and the full coupled system: when increasing IC amplitude from KdV baseline to Gardner or swept-KdV regimes, rescale dt by max(6A + 1.5A^2)^{-1} relative to the KdV-validated dt. The cubic coefficient makes Gardner significantly more restrictive than KdV at A > 2. Document the amplitude used when recording a 'stable dt' in the knowledge bank — it is not transferable across amplitudes.

### kb-general-massConservation-insufficient-diagnostic  (negative, domain=general)
  attempted_route: Using mass conservation alone as the correctness diagnostic for dispersive or fragmented wave solutions
  observation: G1 (Gardner explicit RK4): mass=3.000 but 14 local maxima, soliton fragmented. G3 (Gardner no dealiasing): mass=3.000 but 11 local maxima, aliasing artifacts. Earlier: A4 (KdV explicit RK4): soliton fragmented into 10 peaks with mass still conserved. A5 (KdV no dealiasing): 4 spurious solitons but mass approximately conserved.
  failure: layer=measurement_failure, scope=general_failure, degree=overclaimed, action=narrow_claim, risk=high_risk_false_progress
  applicability: Universal rule for coupled Burgers-swept-KdV evaluation pipelines: mass conservation is a necessary but not sufficient correctness criterion. The primary correctness check for soliton problems must include: (1) peak local maxima count matching expected soliton count, (2) peak amplitude within tolerance of reference, (3) peak x-position consistent with theoretical phase speed. This is especially important for Gaussian decomposition tasks where spurious peaks from aliasing or fragmentation would produce incorrect soliton-train amplitudes.

### kb-gardner-GardnerIsM0-coupledSystemInstability  (negative, domain=gardner)
  attempted_route: Assuming that a numerical method validated on the isolated Gardner equation will be equally stable when embedded in the full coupled Burgers-swept-KdV system at the same parameters
  observation: G4 demonstrates that IMEX-CN with explicit nonlinear blows up on Gardner at amplitude 3.0 (the m=0 reduction). The full coupled system at m=0 has additional coupling terms that add further explicit stiffness beyond the isolated Gardner equation.
  failure: layer=hypothesis_failure, scope=regime_bound, degree=partial, action=narrow_claim, risk=high_risk_false_progress
  applicability: Directly applicable to Burgers-swept-KdV coupled system design: validate numerical methods first on the isolated Gardner equation (m=0 reduction) before testing the full coupled system. Gardner blow-up at a given (dt, amplitude) is a necessary failure condition for the full coupled system in that regime. Treat Gardner stress tests as a prerequisite gate for coupled-system parameter sweeps.

### kb-gardner-nonlinearCFL-amplitude-boundary  (negative, domain=gardner)
  attempted_route: IMEX-CN spectral with explicit nonlinear (6vv_x + (3/2)v^2 v_x) at dt=5e-4 for Gardner amplitude escalating from 1.5 to 3.0
  observation: Empirically: dt=5e-4 is STABLE at amp 1.5 (G2, all_finite=true, mass conserved). The same scheme with dt=1e-4 BLOWS UP (all 256 NaN) at amp 3.0 (G4). Interpolating the effective nonlinear wave-speed: at amp 1.5, max|6v + 1.5v^2| ~ 9 + 3.375 = 12.4; at amp 3.0, max|6v + 1.5v^2| ~ 18 + 13.5 = 31.5. The empirical stability boundary therefore scales as dt * (6A + 1.5A^2) * k_max / (2*pi/L) < C for some O(1) constant C, where k_max is set by the steepest resolved mode.
  failure: layer=method_failure, scope=regime_bound, degree=unstable, action=narrow_claim, risk=high_risk_false_progress
  applicability: Critical design rule for any IMEX solver applied to the Gardner or swept-KdV component of the coupled Burgers-swept-KdV system: before each amplitude sweep, compute the nonlinear CFL number NL-CFL = dt * max(6*A + 1.5*A^2) * k_soliton and confirm NL-CFL < threshold (~O(0.5-1) based on G2/G4 bracket). The empirical evidence is: dt=5e-4 passes at A=1.5 (NL-CFL ~ 0.31 for k_soliton ~ 0.5), dt=1e-4 fails at A=3.0 (NL-CFL ~ 0.16 — yet blow-up still occurs, suggesting the relevant k_max is the grid Nyquist, not the soliton wavenumber). This implies agents must use dt <= C/(max_nonlinear_speed * k_Nyquist) rather than the soliton-scale wavenumber. For Burgers-swept-KdV production runs at A in [1,3], target dt in [1e-4, 3e-4] and monitor the first few steps for overflow.

