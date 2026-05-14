# Session log: T_B / NLS

## t = session start
- Read prompt.md: Gaussian density packet on Mcs with phi=0.3*x boost, A=2/sigma=1.5, T=6, Nx=256 output.
- Read knowledge bank (memory.md): 21 NLS entries.
- Key bank flags identified: kb-nls-direct-n-phi-structural-failure (rule out direct (N,phi));
  kb-nls-split-linear-phase (MANDATORY: phi=0.3x is non-periodic);
  kb-nls-sign-convention (must adopt standard-NLS sign as working hypothesis);
  kb-nls-resolution-soliton-counting (Nx=256 + A>=2 Gaussian = warning);
  kb-nls-karpman-maslov-upper-bound (A*sigma=3 = "3 soliton" regime in S3).
- Initialized research_state.jsonl with Q1.

## E1 — simplest meaningful baseline
- Method: Strang split-step Fourier on Psi = sqrt(N)*exp(i*phi), phase split absorbed
  into IC as Psi(x,0) = sqrt(N0)*exp(i*0.3*x). Standard-NLS sign. No dealiasing.
- Params: Nx=256, dt=1e-3, T=6.0, 13 snapshots, kappa=1.
- CFL budget check: pi^2*Nx^2*dt/(2L^2) = 0.36 < 1. OK.
- Result:
  - mass drift 3.3e-13, energy drift 1.1e-8
  - ||m||_2 ~ 1e-17 at all snapshots (Mcs preserved structurally)
  - 2 peaks (N=2.158, 2.155) at x=-3.984, -2.461 — phenomenon target met
  - N_max trajectory shows clear breather pattern (collapse to ~11 at t=1.5, ~13 at t=5)
  - Spectral tail 4.9e-13 — well-resolved spectrally
- F1: phenomenon target met but at threshold (A*sigma=3 matches S3 over-counting regime).
- D1: change_method -> E2 add 2/3 dealiasing as single upgrade.

## E2 — add 2/3 dealiasing
- Method: E1 + 2/3-rule dealiasing on |Psi|^2 before cubic exponential and on linear FFT step.
- Params: same (Nx=256, dt=1e-3).
- Result:
  - mass drift -6.5e-6 (small non-conservation from dealiasing of |Psi|^2)
  - same 2-peak structure at SAME positions x=-3.984, -2.461 with N=2.1578, 2.1550
  - N_max trajectory matches E1 to ~0.4% throughout
- F2: dealiasing does not change the result (as expected, since spectral tail was already 1e-13).
  Strengthens confidence in the un-dealiased E1.
- D2: change_method -> E3 single upgrade = double Nx and halve dt (resolution refinement).

## E3 — resolution refinement
- Method: E2 + Nx_fine=512, dt=5e-4. Output downsampled via Fourier truncation to Nx=256.
- Params: Nx_fine=512, Nx_save=256, dt=5e-4, T=6.0, 13 snapshots.
- CFL budget: pi^2*512^2*5e-4/(2*900) = 0.72 < 1. OK.
- Result:
  - mass drift -1.6e-11 (machine precision restored)
  - energy drift -3.3e-9 (Strang dt^4 scaling)
  - IDENTICAL 2-peak structure at same x positions with same N values
  - N_max trajectory matches E1 to 4 decimal places at all 13 snapshots
  - Spectral tail on Nx=512 grid: 1.3e-22 (FP precision floor)
- F3: phenomenon target met and CONVERGED across 3 runs. useful_self_assessment = True.
- D3: stop_useful.

## End of session
- Final candidate.py: E3 method (Nx_fine=512, dt=5e-4, dealiased, downsampled).
- Final pred_results/T_B.npy: shape (13, 3, 256), 13 snapshots at t=0, 0.5, ..., 6.0.
- Iteration budget used: 3/3.
- All required output files present.
