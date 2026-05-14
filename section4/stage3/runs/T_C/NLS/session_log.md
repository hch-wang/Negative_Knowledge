# Session log: T_C / NLS

## Setup
- Task: T_C — Burgers bore in u (u_L=1, u_R=0, w=0.5 at x=0) interacting with a
  bright NLS soliton in N (sech^2 at x=-8, amplitude 1) boosted by phi_x=0.6.
- Domain: x in [-15, 15], Nx=256, kappa=+1 (focusing), T=8.
- Condition: NLS bank (21 entries) available. Direct BKdV T_C analog.

## Memory consulted
- Read full 21-entry NLS bank (memory.md / prompt.md sections).
- Key entries flagged:
  - `kb-nls-muscl-madelung-bore-soliton` — DIRECT match for this exact IC; S7
    cross-validated to T=8.
  - `kb-nls-direct-n-phi-structural-failure` — rules out direct (N,phi).
  - `kb-nls-split-linear-phase` — REQUIRED for non-periodic phi_0 = 0.6*x.
  - `kb-nls-sign-convention` — user's +Q sign is parabolic-unstable.

## E1 — simplest meaningful baseline
- Method: spectral RK4 on m + Madelung-Psi Strang on Psi_tilde + phi-split.
  No MUSCL, no dealiasing. dt=1e-3.
- Result (T=8, no blow-up):
  - mass = 2.00 (exact)
  - peak amp = 0.999 throughout, position -8 -> -3.16, speed 0.60
  - **FAILURE: u Gibbs-rings** (u in [-0.19, 1.32], TV=23.9, spectral high-1/3
    ratio 6.3e-3)
  - ||m||_2 flat (3.59 -> 3.61) — Gibbs noise drowns out attractor signal
- F1: useful=False. D1: single-component escalation -> add MUSCL on u (drives
  toward kb-nls-muscl-madelung-bore-soliton).

## E2 — MUSCL-Godunov on u + Madelung-Psi Strang (no dealias)
- Method: van-Leer-limited MUSCL, Godunov flux f(u)=u^2/2, SSP-RK3 on u.
  Madelung-Psi Strang on Psi_tilde, phi-split kept. dt=5e-4. No dealiasing.
- Result (T=8, no blow-up):
  - mass = 1.999998 (drift 2e-6, fine for FV/spectral mix)
  - u in [0, 1], TV=2.0 — bore completely clean
  - peak amp = 0.999, x -8.03 -> -3.22, speed 0.60
  - **||m||_2 monotonically DECREASES** 3.58 -> 3.42 (-4.5%) over T=8
  - u high-1/3 ratio 1.4e-4 (borderline at 1e-4 flag)
- F2: useful=True. D2: meets target; do one more iter for confidence ->
  add 2/3 dealiasing per kb-nls-23-dealiasing-cubic.

## E3 — full S7 stack (E2 + 2/3 dealiasing)
- Method: E2 + 2/3 dealias mask on linear-step Psi_tilde and on |Psi|^2
  before the cubic exponential.
- Result (T=8, no blow-up):
  - mass = 1.999998
  - **E_NLS = 0.0267 constant to 4 digits** across all 17 snapshots
  - ||m||_2 monotone 3.5819 -> 3.4200 (-4.52%)
  - peak amp 0.999, x = -3.22, speed 0.60
  - u in [0, 1], TV=2.0
  - N spectral high-1/3 ratio: **3.4e-11** (70x cleaner than E2)
  - u high-1/3 ratio 1.4e-4 (unchanged — this floor is from the FV bore
    projected onto the spectral basis, not aliasing)
- F3: useful=True. D3: stop_useful. Final solution = E3.

## Final outputs
- candidate.py = E3 solver
- pred_results/T_C.npy shape (17, 3, 256) channels (u, N, phi)
- reasoning.md
- research_state.jsonl: Q1, E1, F1, D1, E2, F2, D2, E3, F3, D3

## Phenomenon assessment
- N peak >= 0.3 at T=8: 0.999  [PASS]
- |u_max| < 5 at T=8: 1.000     [PASS]
- Bore stable: yes              [PASS]
- ||m||_2 decreases (bonus): yes, monotone -4.5%  [PASS]

Physical reading: within T=8 the bright soliton has reached the leading edge of
the bore (peak at x=-3.2, tail extends to ~x=0) and ||m||_2 is decreasing
monotonically toward the Mcs surface — early-onset compound-soliton attractor
signature. The peak overlap collision proper is at t~13, beyond the T=8
window.
