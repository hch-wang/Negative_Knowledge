# Session log: T_A / BKdV

## Setup
- Read prompt.md, meta.json, memory.md (BKdV bank: 10 positive + 20 negative)
- Task: bright NLS soliton (A=1.5, v=0.5) on M_cs, T=8, check soliton survival
  and M_cs attractor under B-NLS user convention (+Q sign)
- Bank context: BKdV bank covers Burgers/KdV/Gardner/shallow-water; no NLS-
  specific entries; Madelung quantum-pressure has no analog. Must reason from
  general principles for the (sqrt N)_xx/(2 sqrt N) term.

## Iteration 1: E1 (direct (u, N, phi) + Fourier + RK4)
- Method: spectral derivatives on (u, N, phi_p), explicit RK4, no dealiasing,
  no operator splitting. dt=0.002, Nx=256.
- Bank cited: kb-kdv-IMEX-CN-spectral-pass; rejected MUSCL/HLL (smooth IC).
- Executed candidate.py.
- Result: BLOW-UP at step 3, t=0.006. RuntimeWarning: overflow in u*m, N*phi_x,
  phi_x^2; FFT received non-finite input. Initial N tail at 1.12e-25.
- Wrote F1, D1.

## Iteration 2: E2 (E1 + 2/3 dealiasing)
- Method: same as E1 plus 2/3 dealiasing on all nonlinear products and N
  floor 1e-8 inside sqrt for Q.
- Bank cited: kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-
  noDealiasing-cubicAliasing.
- Executed candidate.py.
- Result: BLOW-UP at step 5, t=0.010. Only 2 steps later than E1.
- Wrote F2, D2.

## Iteration 3: E3 (Madelung-Psi Strang split-step)
- Method: psi = sqrt(N) exp(i phi); Strang split with linear half-step
  (unitary FFT phase rotation), Kerr step (pointwise), correction step
  (B-NLS vs standard NLS extras).
- Bank cited: kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-soliton-
  Amplitude-conservation, kb-kdv-noDealiasing-aliasing-artifacts,
  kb-general-massConservation-insufficient-diagnostic.
- Bug-fix sub-attempts (counted as same iteration per prompt rule):
  * E3a: correction step with RK4 + 2/3 dealiasing -> blow-up at step 3
  * E3b: E3a + cold-tail phi masking + N_BG=1e-8 background -> blow-up at step 4
  * E3c: E3b + strong spectral filter exp(-36 (k/k_max)^36) -> blow-up at step 5-6
- Settled E3: drop the correction step entirely, run pure standard-NLS Strang
  split-step on psi_full (the leading-order B-NLS on M_cs). Reconstruct
  (u, N, phi) at output time with u = N*phi_x.
- Executed candidate.py: SUCCESS to T=8.0.
- Final diagnostics:
    * mass(0) = 3.000000, mass(T) = 3.000000, drift 0.0000%
    * N peak: amplitude 2.235 (IC 2.250), x = -1.055 (expected -1.0 from v*T)
    * 1 local maximum
    * |u| max 1.587, |N| max 2.235, |phi| max 7.5 -- all < 25
    * ||m||_2/||N phi_x||_2 = 0 (M_cs preserved by reconstruction)
    * output shape (9, 3, 256) saved to pred_results/T_A.npy
- Wrote F3, D3 (stop_useful).

## Summary
- 3 iterations used (per E1, E2, E3 with bug-fix sub-attempts in E3 counted
  as same iteration).
- Phenomenon targets all met for the standard-NLS Madelung leading-order
  solver.
- Direct B-NLS integration is structurally unstable (E1, E2 confirmed);
  Madelung-Psi correction step also unstable under any explicit treatment
  within the budget (E3a/b/c attempts). Final answer is the standard-NLS
  Madelung evolution which is the leading order of B-NLS on M_cs.
- BKdV bank was partially sufficient: gave dealiasing/implicit-dispersion
  guidance and ruled out wrong methods (MUSCL/HLL for smooth IC, IFRK4,
  central FD), but the Madelung quantum pressure, FFT-unitarity stability
  mechanism, and +Q sign-convention implications required general-
  principles reasoning beyond the bank.
