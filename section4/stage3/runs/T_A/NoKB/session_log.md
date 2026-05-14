# Session log: T_A / NoKB

## Setup
- Working directory: /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage3/runs/T_A/NoKB
- Condition: NoKB — no knowledge bank, general PDE/numerical knowledge only.
- Task: B-NLS T_A, bright soliton on M_cs, T = 8.0, Nx = 256, x in [-15, 15].
- Critical: user's sign convention is +sqrt(N)_xx / (2 sqrt(N)) — OPPOSITE to standard NLS Madelung.

## Iteration 1 — E1 (simplest meaningful baseline)
- Plan: direct (u, N, phi) Fourier pseudospectral + explicit RK4, dt = 1e-3, eps_N = 1e-12.
- Advanced u via algebraic identity u_t = m_t + N_t*phi_x + N*phi_xt (since at t=0, m=0 on M_cs and the m-equation gives m_t directly).
- Ran into NumPy 2.x compatibility (np.trapz removed); fixed to use np.trapezoid (same iteration; minor API fix).
- Re-ran. Step 1 blow-up: |u| reached 8.9e15 in a single RK4 step.
- Initial diagnosis: 1/sqrt(N) amplification in Q because N_min ~ 1e-25 in sech^2 tails.
- Deeper probe: also non-periodic phi(x, 0) = 0.5*x produces Gibbs spikes of ~80 in spectral phi_x at the boundary, which is the DOMINANT failure mode.
- F1 records both findings.

## Iteration 2 — E2 (N-floor regularization)
- Plan: same as E1 but with eps_N = 1e-6 in sqrt(N + eps_N) for Q.
- One single-component change vs E1.
- Result: still blows up at step 1; NaN-everywhere by t = 1e-3.
- F2 confirms N-floor alone is insufficient: the dominant non-periodic-phi failure mode is unaddressed.
- D2: switch phi representation in E3 to a periodic-compatible psi = phi - v*x.

## Iteration 3 — E3 (periodic-compatible psi representation)
- Plan: E2 + replace phi with psi := phi - 0.5*x; psi(x, 0) = 0 is genuinely periodic.
- PDE structure unchanged: phi only enters through phi_x = psi_x + 0.5. u_t formula uses psi_xt instead of phi_xt (numerically equivalent).
- Output reconstructs phi = psi + 0.5*x.
- Result: step 0 RHS is now physical (k1 magnitudes O(1)–O(10), no boundary spikes). But u jumps from peak 1.13 to ~256 in one RK4 step (200x amplification), then to ~1e17 by step 2.
- F3 diagnoses: the +Q sign convention is intrinsically anti-diffusive at high k. Nonlinear products on a 256-grid create high-k content that the +Q amplifies as exp(+k^2 dt / 2). Explicit RK4 cannot integrate this stably without dealiasing or implicit handling of the anti-diffusive operator.
- D3: stop_useful (3 iterations consumed). Useful self-assessment = FALSE.

## Final state
- candidate.py: E3 (best attempt, periodic-psi + N-floor + Fourier pseudospectral + RK4).
- pred_results/T_A.npy: shape (17, 3, 256), E3's snapshot trajectory. The first snapshot is the exact IC; subsequent snapshots are blow-up.
- reasoning.md: full iteration trace and final self-assessment.
- research_state.jsonl: Q1, E1, F1, D1, E2, F2, D2, E3, F3, D3.

## Headline result
Direct explicit Fourier-RK4 with the user's +Q sign convention cannot integrate B-NLS task T_A. Three iterations identified the structural obstacle: the +Q sign produces backward-heat-like amplification of high-k modes that any explicit scheme without dealiasing or implicit treatment will catastrophically amplify. The bright soliton initial condition is well-posed continuously, but the explicit numerical methods explored here are not adequate for it. Recommended next step (out of scope here): IMEX or ETD with +Q treated implicitly, or 2/3-dealiased pseudospectral with spectral hyperviscosity.
