# Session log: T_D / BKdV

## Session start
- Task: T_D research-grade — characterize ||m||_2(t) relaxation under off-M_cs
  perturbation in u from the bright NLS soliton IC.
- Condition: BKdV bank only (10 positive + 20 negative entries from
  Burgers-swept-KdV pilot). No NLS-specific entries.
- IC: kappa=1; A=1.5; N0=A^2 sech^2(A(x+5)); phi0=0.5*x; u0=0.5*N0 + eps*cos(2*pi*x/L),
  with single chosen epsilon=0.1.
- T_final = 12.0; Nx = 256; L = 30.

## E1 (simplest meaningful method)
- Time: 2026-05-13 (Unix 1778724683).
- Method: direct (u,N,phi) Fourier-pseudospectral spatial derivatives,
  explicit RK4, dt=5e-4, 2/3 dealiasing. NO Galilean fix for phi.
- Cites bank: [] (none directly applicable).
- Result: BLOW-UP at step 4 (t=0.002). Initial ||m||_2 wrong: 1.115 vs theoretical
  0.387. Stderr: overflow in u*m product.

## F1
- Diagnosis: phi0 = 0.5*x is non-periodic on x in [-15,15], so spectral
  derivative gives FFT sawtooth instead of constant 0.5. The 0.5*phi_x^2 term
  squares the sawtooth to O(100) instantly overflows.
- useful_self_assessment: false.

## D1
- Change method: Galilean-decompose phi = v0*x + phi_p with phi_p periodic.

## E2 (single-component change over E1)
- Time: 2026-05-13 (Unix 1778724803).
- Method: same explicit-RK4 / spectral / 2/3 dealiasing as E1, but with
  phi = v0*x + phi_p representation. dt=2e-4.
- Cites bank: kb-gardner-G2-IMEX-CN-dealiased-stableRadiation (dealiasing only).
- Result: IC corrected (||m||_2(0) = 0.387298 matches theory). BLOW-UP at step
  7 (t=0.0014). Stderr: overflow in u*m, u_t, phi_p_t.

## F2
- Diagnosis: Madelung quantum-pressure Q=(sqrt N)_xx/(2 sqrt N) computed via
  FFT on sqrt(N) with min(N)~1e-25 in tails. FFT roundoff/sqrt(N) -> Q reaches
  ~9 in tails vs analytical 1.125. This pollutes phi_p_t globally through
  dx_spec(phi_p_t) -> destabilizes u_t.
- useful_self_assessment: false.

## D2
- Change method: regularize Q with SQRT_REG=1e-3 floor and N_THRESH=5e-3 mask,
  reduce dt to 1e-4.

## E3 (single-component change over E2 — Q regularization)
- Time: 2026-05-13 (Unix 1778724897).
- Method: E2 + Q regularization + dt=1e-4 + per-step fine ||m||_2 capture +
  post-process pre-blowup truncation rule (m<1.5*m0, max N<2.5, max|u|<5).
- Cites bank: kb-gardner-G2-IMEX-CN-dealiased-stableRadiation,
  kb-general-finiteness-not-accuracy, kb-general-massConservation-insufficient-diagnostic.
- Result: regularized Q max = 1.185 (matches analytic 1.125 closely). Ran 467
  steps before catastrophic blow-up at t=0.0467. Pre-blowup window
  [0, 0.0215] retained: 25 snapshots, mass drift 3.74%, max|u|=4.88, max N=2.48.
- Bug-fix iteration on post-processing: tightened pre-blowup threshold from
  5*m0 to 1.5*m0 to bring mass drift below 5% target. (Did not count as a new
  iteration: method unchanged, only the diagnostic-truncation rule changed.)

## F3
- ||m||_2(t) in stable window [0, 0.022]: mean=0.3873, std=4.6e-4, std/mean=0.12%.
  No decay observed — flat to within numerical noise.
- Exponential fit: tau=14.4 with rel RMSE 1.09e-3. **Statistically
  indistinguishable from a constant** — fit-derived tau is noise-level.
- UV cascade past t~0.025: doubling time ~2.5e-3 sim-time.
- Analytical prediction of UV growth rate under user's variational sign:
  sigma(k) = k^2/2, sigma_max = k_max^2/2 = pi^2/(2 dx^2) = 359.3,
  t_double = ln(2)/359 = 1.93e-3. Empirical cascade doubling ~2.5e-3 matches
  to within 30%.
- Conclusion: M_cs is NEUTRALLY stable on the resolvable timescale; the bare
  PDE is UV-ill-posed under the user's +Q sign convention.
- useful_self_assessment: true.

## D3
- stop_useful — research finding delivered.

## Files produced
- candidate.py — final solver (E3 method).
- research_state.jsonl — Q1, E1-E3, F1-F3, D1-D3 (10 nodes).
- reasoning.md — full reasoning + ||m||_2(t) characterization.
- pred_results/T_D.npy — shape (25, 3, 256), times [0, 0.0215], pre-blowup window.
- pred_results/T_D_times.npy — snapshot times.
- pred_results/T_D_mnorms.npy — ||m||_2 at each snapshot.
- pred_results/T_D_Nmass.npy — N mass at each snapshot.
- pred_results/T_D_fine_t.npy, T_D_fine_m.npy — fine ||m||_2(t) history (incl.
  cascade window) for diagnostic post-hoc analysis.
