## Memory: positive-knowledge bank (12 entries, v3.A — includes BKdV stress-test entries)

Entries describe methods/regimes that WORKED. Use as guide for what to try. Note: some entries are 'deep synthesis' across multiple rounds of stage-1 BKdV programs; treat those as path-level *what works* rather than single-shot recommendations.

### kb-burgers-MUSCL-Godunov-shock-pass  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: For the Burgers component of coupled Burgers-swept-KdV, MUSCL+Godunov is a proven baseline for bore (shock) propagation. Use it as the default spatial scheme when a sharp bore must interact with a KdV soliton; its TVD property prevents Gibbs contamination in the Burgers sector.

### kb-burgers-Godunov-preShock-smooth  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: For the early-time Burgers component (before bore forms) in Burgers-swept-KdV coupled problems, even first-order Godunov is sufficient. This establishes a lower-cost option for initialization or short-time baseline runs where the bore has not yet formed.

### kb-kdv-IMEX-CN-spectral-pass  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: IMEX-CN is the recommended baseline for the KdV/swept-KdV component of coupled problems. The CN denominator (1 - dt/2 * ik^3) has magnitude >=1 so it is unconditionally stable for the dispersive stiffness — no exponential overflow. Transfer to coupled Burgers-swept-KdV: handle the swept dispersive term with CN and the Burgers-like coupling explicitly.

### kb-kdv-smallAmplitude-dispersiveRegime  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: In coupled Burgers-swept-KdV: small-amplitude KdV components (after energy exchange with the Burgers bore) will not form stable solitons — they disperse. This sets a threshold: soliton formation in the KdV/swept-KdV sector requires sufficient amplitude. Use this as a diagnostic: if post-interaction KdV amplitudes are O(0.1) or less, expect dispersive radiation rather than soliton trains.

### kb-shallowWater-LaxFriedrichs-stable-smeared  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: Lax-Friedrichs is a reliable failsafe for shallow-water or shallow-water-like components in coupled problems when robustness is paramount and sharp shock resolution is not required. In coupled Burgers-swept-KdV experiments, LxF can serve as a stability baseline for validating more accurate schemes (HLL, MUSCL), but should not be the production scheme where bore sharpness matters for the soliton interaction measurement.

### kb-shallowWater-HLL-dam-break-pass  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: HLL is the recommended Riemann solver for any hyperbolic component in a coupled Burgers-swept-KdV system when the solution may include near-dry or variable-depth regions. Its positivity-preservation and entropy compliance make it safer than Roe for robustness, and it resolves shocks more sharply than Lax-Friedrichs.

### kb-kdv-spectral-solitonAmplitude-conservation  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: Spectral IMEX methods are the preferred discretization for tracking soliton amplitude and phase in the KdV/swept-KdV sector of coupled problems. For Gaussian decomposition into a soliton train, the mass and amplitude conservation properties of these methods ensure that decomposition coefficients remain meaningful over multi-soliton propagation times.

### kb-general-firstOrder-Godunov-preShock-baseline  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: For coupled Burgers-swept-KdV: use Godunov flux as the foundation for the Burgers operator at any time horizon. Before shock formation, first-order Godunov alone suffices; after shock formation, upgrade to MUSCL+Godunov. The entropy-consistent Godunov flux ensures no spurious entropy violations in the bore region during soliton interaction.

### kb-gardner-G2-IMEX-CN-dealiased-stableRadiation  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: IMEX-CN spectral with 2/3 dealiasing is the recommended stable method for the Gardner component of Burgers-swept-KdV (m=0 reduction). However, correctness depends critically on using a proper Gardner soliton IC, not a KdV sech^2 IC. For soliton-stability and Gaussian decomposition tasks, always use the Gardner soliton parametrization; KdV ICs at the same amplitude will produce spurious radiation trains that contaminate any bore-soliton interaction measurement.

### kb-gardner-KdV-method-transfer-moderate-amplitude  (positive)
  attempted_route: 
  observation: 
  rationale: 
  recommended_alternative: For the Gardner-reduction (m=0) leg of Burgers-swept-KdV: adopt IMEX-CN spectral + 2/3 dealiasing as the baseline method, transferring directly from the validated KdV solver. No re-engineering of the dispersive (v_xxx) treatment is needed; only the nonlinear stage must be extended to include the cubic term 6vv_x + (3/2)v^2 v_x. Do NOT attempt to port IFRK4 to Gardner: it failed even on the simpler KdV equation and the Gardner cubic nonlinearity would only worsen the overflow in exp(ik^3 t) or tighten the stability constraint further. For amplitude > 2, this positive transfer no longer holds (see kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup); re-evaluate dt before any amplitude increase.

### BKdV-S1  (positive)
  attempted_route: Fourier pseudospectral + 2/3-rule dealiasing (zero |k_idx|>Nx/3=85, 171/256 modes) on every nonlinear product (v^2, u*v, v*v_x, u*u_x) + classical explicit RK4 over full RHS incl. v_xxx; Nx=256, L=30, dt=2e-4, IC v0=1.5 sech^2(x+5), u0=v0^2/2, T=10.
  observation: Reached T=10 cleanly: mass_v conserved <1e-12 (3.000000e+00), sup bounded 3.5-4.0 (final 3.97), tail_frac above 2/3 band ~2e-18 (machine zero), energy grew 2.08->3.69 (physical, not artifact), elapsed 22.66s, no NaN/warnings.
  rationale: Positive finding: 2/3-rule cutoff blocks alias-folded modes from quadratic products feeding resolved band, isolating aliasing (not v_xxx stiffness) as R1's dominant failure. Cutoff also lowers effective k_max from pi/dx to (2/3)pi/dx, raising RK4 dispersion CFL bound from ~1.47e-4 to ~4.94e-4, so dt=2e-4 is now safely below.
  recommended_alternative: Extend by raising amp from 1.5 to 3.0 (top of requested [1,3] range) with identical stack (Nx=256, dt=2e-4, 2/3-dealias, RK4) to probe second failure mode (shock-front aliasing in u from u*u_x or v gradient-steepening exceeding 2/3 band); diagnose via separate sup_u/sup_v and edge_frac in top 10% of resolved band.
  failure: layer=method_failure, scope=regime_bound_failure, action=change_method, risk=low_risk_omission

### BKdV-S1  (positive)
  attempted_route: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (dt=2e-4, Nx=256, L=30); IC v0=amp*sech^2(x+5) with amp=3.0 (top of [1,3]), u0=v0^2/2; T=10; track sup_u, sup_v, mass_v, edge_frac.
  observation: Reached T=10 cleanly: mass_v=6.0 conserved to <1e-12, sup_u rose 4.49->~10.5 with oscillations, sup_v decayed 3.0->1.16, edge_frac peaked ~3e-6 (well below 1e-4 alert), no NaN/overflow, elapsed 22.4s.
  rationale: Positive finding: the predicted second failure mode (high-amp gradient steepening of u or Burgers-side under-resolution at the 2/3 band) did not materialize at amp=3, T=10. The 2/3 cutoff raises dispersion-CFL above dt=2e-4 and u-steepening stayed band-resolved.
  recommended_alternative: To experimentally hit a second failure mode, stress an orthogonal axis: either raise dt above the post-dealias CFL bound ~4.94e-4 (e.g. dt=8e-4 with same RK4) to trigger v_xxx dispersion stiffness, or extend T to 50-100 / use Burgers-dominant IC to force shock formation requiring MUSCL-Godunov on u*u_x.
  failure: layer=hypothesis_failure, scope=regime_bound_failure, action=narrow_claim, risk=low_risk_omission
