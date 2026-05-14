# Session log: T_B / NLSBKdV

## Setup
- Working dir: /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage3/runs/T_B/NLSBKdV
- Two banks consulted: NLS (21 entries) + BKdV (30 entries) = 51 total
- Sign convention warning (kb-nls-sign-convention) noted: standard-NLS sign adopted
- Iteration budget: 3 max

## E1 — Madelung-Psi Strang, Nx=256, dt=1e-3

- Proposed via Q1, cites_bank: 10 NLS + 1 BKdV (kdv-no-dealiasing)
- Wrote candidate.py with Strang split-step on Psi=sqrt(N)exp(i phi_tilde), phi=0.3*x + phi_tilde split, kinetic absorbs Galilean boost via k -> k+c
- Ran: 6000 steps, T=6, completed in seconds
- Result: mass drift -6.4e-6, peaks at x=-3.98, -2.46 with N~2.16
- BUT: spectral tail 1.2e-3 (>>1e-4 untrustworthy threshold), upper-third energy 0.48 at peak focusing
- F1: SUCCESS_BUT_UNDERRESOLVED, useful_self_assessment=False
- D1: change_method — refine grid (Nx 256->512, dt 1e-3->5e-4, single grid component)

## E2 — Madelung-Psi Strang, Nx=512, dt=5e-4 (downsample output to 256)

- Proposed via D1, cites_bank: 4 NLS (resolution-soliton-counting, Strang, CFL, mass-conservation), BKdV not consulted (purely NLS resolution refinement)
- Wrote candidate.py with internal Nx=512, downsample every 2nd point at snapshot time
- Ran: 12000 steps, T=6, completed in ~20s
- Result: mass drift -1.4e-11 (machine precision), peaks at x=-3.98, -2.46 with N~2.158 (matches E1 to 4 decimals)
- Spectral tail 6.5e-7, upper-third energy 0.43 — converged
- F2: CONVERGED_SUCCESS, useful_self_assessment=True
- D2: stop_useful — E1 and E2 mutually corroborate, third iteration not needed

## Outputs written
- candidate.py — final solver (E2)
- reasoning.md — full reasoning incl. NLS-vs-BKdV citation discussion
- research_state.jsonl — Q1, E1, F1, D1, E2, F2, D2 nodes
- session_log.md — this file
- pred_results/T_B.npy — shape (25, 3, 256), float32

## Final assessment
Phenomenon target MET. Two well-separated peaks with N>=1.0 at T=6, mass drift at machine precision, all finite. Converged at Nx=512 (matches kb-nls-resolution-soliton-counting's effective dx=0.06).
