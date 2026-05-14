# Session log: T_A / NLS

## Setup
Task: T_A — Bright NLS soliton stability in the Burgers frame (compound-soliton attractor test).
Working dir: /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage3/runs/T_A/NLS
Condition: NLS (21-entry NLS bank available; no BKdV bank).

## IC analysis
- Domain x in [-15, 15], Nx=256 (dx ~ 0.117).
- N(x,0) = 2.25 * sech^2(1.5*(x+5)) — bright sech with peak amplitude 2.25 centered at x=-5, width 1/A=2/3.
- N tails at x=+/-15: N(15) = 2.25*sech^2(30) ~ 1.6e-26, well below noise floor.
- phi(x,0) = 0.5*x — NON-periodic; kb-nls-split-linear-phase mandates Galilean factor extraction.
- u(x,0) = 0.5*N(x,0); m(x,0) = u - N*phi_x = 0 exactly (on Mcs).
- Group velocity from phi_x=0.5 is v_g = 0.5; over T=8 the soliton centroid translates to x_center = -5 + 0.5*8 = -1. Stays inside the box.

## Sign convention
The user's literal phi equation has +(sqrt(N))_xx/(2 sqrt(N)) sign — opposite standard NLS Madelung.
Per kb-nls-sign-convention, the user's literal sign makes the Psi-equation parabolic-unstable.
The IC is described in the prompt as "an exact bright NLS soliton (Madelung form)", which is only well-defined under the standard NLS sign. Operationally I integrate the standard-sign Madelung-Psi (i Psi_t = -(1/2) Psi_xx - kappa |Psi|^2 Psi).
This is recorded as a hypothesis-level transfer (kb-nls-sign-convention recommended_action (ii)).

## Iteration 1: E1 — Strang split-step Madelung-Psi

Plan: simplest meaningful baseline per progressive-complexity rule.
- Direct (N, phi) excluded a priori by kb-nls-direct-n-phi-structural-failure (depth=family-level).
- Madelung-Psi Strang split-step Fourier as E1 (kb-nls-recommended-default-bnls, kb-nls-strang-splitstep-bright-soliton).
- Galilean factor extraction: Psi = exp(i*0.5*x) * Psi_tilde with Psi_tilde periodic (kb-nls-split-linear-phase).
- Nx=256, dt=1e-3, dealiasing OFF, no regularization. CFL-phase budget = 0.36 < 1 (kb-nls-cfl-split-step).

Implementation notes:
- Linear half-step in Fourier of Psi_tilde uses symbol -(1/2)(k+c)^2 with c=0.5 (Galilean wavenumber shift).
- Nonlinear pointwise: Psi *= exp(i*kappa*|Psi|^2*dt) with kappa=+1.
- u reconstructed only at snapshots from Im(conj(Psi)*Psi_x) so that m=u-N*phi_x is structural identity (kb-nls-madelung-psi-structural-coupling).

Execution: 8000 steps via `cd ... && /Users/dietcoke/.../python candidate.py`.
Run completed without error.

Diagnostics observed:
- IC checks: N_max=2.2423, M0=3.0000, m(x,0)=0 exactly.
- CFL phase budget: 0.3593 (< 1).
- Final (T=8): N_max=2.2349 (99.7% of initial), |dM|/M=6.45e-13, ||m||/||N*phi_x||=5.38e-17, |u|_max=1.12, |phi|_max=3.14, peak_x=-1.055 (predicted -1.0).
- Spectral tail (high-k third): 2.57e-15 (well below kb-nls-resolution-soliton-counting trust threshold 1e-4).
- All four phenomenon targets PASS with 5-13 orders of margin.

Per-snapshot peak: N_max(t) oscillates within [2.2349, 2.2497] over t=0..8 — drift <0.5%.
Peak position: -5.04, -4.45, -3.98, -3.52, -3.05, -2.46, -1.99, -1.52, -1.06 — clean linear translation at 0.50 units/sec.
Mass drift: monotonically linear from 0 to 6.45e-13 over 8 sec (accumulated roundoff).

## F1 Finding
E1 PASSES with overwhelming margin. Five independent diagnostics (mass, ||m||, peak amp, peak position, spectral tail) all cross-validate. Soliton is a clean traveling bright sech with Galilean translation matching prediction to within dx/2.

## D1 Decision: stop_useful
Progressive-complexity discipline: do not escalate when E1 already meets all targets with no diagnostic signal of under-resolution. Spectral tail at 2.6e-15 (11 orders below trust threshold) is decisive proof that Nx=256, dt=1e-3 is sufficiently resolving. Escalation to E2 (dealiasing) or E3 (Nx=512/dt=2.5e-4) would not yield new information.

## Output
- pred_results/T_A.npy: shape=(9, 3, 256), dtype=float64, snapshots at t=0,1,...,8.
- Channels: (u, N, phi). phi stored as the standard atan2-wrapped angle.

## Files at session end
- candidate.py (E1 solver, final)
- reasoning.md
- research_state.jsonl (Q1, E1, F1, D1)
- session_log.md (this file)
- pred_results/T_A.npy

## Bank entries summary
- Cited (8): kb-nls-recommended-default-bnls, kb-nls-strang-splitstep-bright-soliton, kb-nls-madelung-psi-structural-coupling, kb-nls-madelung-psi-handles-zero-density, kb-nls-direct-n-phi-structural-failure, kb-nls-split-linear-phase, kb-nls-cfl-split-step, kb-nls-sign-convention.
- Rejected (6, with reasons in research_state.jsonl): kb-nls-23-dealiasing-cubic (smooth IC + adequate resolution), kb-nls-muscl-madelung-bore-soliton (no shock), kb-nls-antiperiodic-basis-dark-soliton (bright not dark), kb-nls-etd-rk1-mass-destruction (we use symplectic), kb-nls-lie-splitting-uneconomical (we use Strang), kb-nls-hard-floor-counterproductive (no regularization needed).
- Consulted: kb-nls-mass-conservation-not-sufficient, kb-nls-mcs-not-sufficient, kb-nls-resolution-soliton-counting, kb-nls-energy-drift-vs-mass-drift, kb-nls-mcs-not-attractor-standard-sign.
