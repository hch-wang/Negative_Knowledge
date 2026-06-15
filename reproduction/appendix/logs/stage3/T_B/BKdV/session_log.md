# Session log: T_B / BKdV

Condition: BKdV-bank only (30 entries; no NLS-specific bank). Task: B-NLS
Gaussian density packet on M_cs, focusing kappa=+1, T=6.0, expect >=2 bright
solitons by modulational instability.

## Iteration 1 (E1)
- Plan: simplest meaningful for B-NLS = direct (u, N, phi) Fourier
  pseudospectral + explicit RK4. dt=2e-4. No dealiasing. No floor on Q.
- Bank cites: kb-kdv-IMEX-CN-spectral-pass (Fourier baseline).
- Bank rejects: kb-burgers-fwdEuler-centralFD-Gibbs (FD warning N/A),
  kb-kdv-IFRK4-blowup (no IF used), kb-burgers-MUSCL-Godunov-shock-pass
  (premature complexity), kb-general-centralFD-hyperbolic-shockFormation
  (Fourier exact, smooth IC).
- Result: BLEW UP at step 3 (t=0.0006), overflow in multiply. Final state
  |N| ~ 5e96. Diagnosis: 1/sqrt(N) singularity in Gaussian tails (N ~ 1e-77).
- Decision (D1): change_method -> regularize Q with sqrt(max(N, eps_N)).

## Iteration 2 (E2)
- Plan: direct (u, N, phi) Fourier + RK4 + Q-floor regularization
  (eps_N=1e-10). dt cut to 1e-4. No dealiasing (one component change only).
- Bank cites: kb-kdv-IMEX-CN-spectral-pass.
- Bank rejects: kb-shallowWater-dryBed-naiveClip-hu-singular (caution noted;
  floor confined to Q-only).
- Considered Psi switch -> dead end: derivation showed user-convention +Q
  forces a Psi equation that conflicts with the continuity sign. Direct
  (u, N, phi) retained.
- Result: BLEW UP at step 3 (t=0.0003), overflow in multiply. Final state
  |N| ~ 1e13. Diagnosis: at t=0, |phi_x|_max=53 (vs analytic 0.3), |phi_t|_max
  = 1401, because phi(x,0)=0.3*x is NOT periodic on x in [-15, 15]. Fourier
  derivatives produce massive boundary ringing.
- Decision (D2): change_method -> gauge split phi = phi_lin + tilde_phi to
  make Fourier-evolved field periodic; layer 2/3 dealiasing.

## Iteration 3 (E3)
- Plan: (u, N, tilde_phi) Fourier + RK4 + Q-floor + 2/3 dealiasing.
  dt=1e-4. Same eps_N=1e-10.
- Bank cites: kb-kdv-IMEX-CN-spectral-pass,
  kb-kdv-noDealiasing-aliasing-artifacts,
  kb-gardner-G3-noDealiasing-cubicAliasing,
  kb-general-massConservation-insufficient-diagnostic.
- Bank rejects: kb-burgers-MUSCL-Godunov-shock-pass,
  kb-gardner-cubicTerm-tightens-nonlinearCFL,
  kb-shallowWater-dryBed-naiveClip-hu-singular.
- Sanity at t=0: |u_t|=3.9, |N_t|=1.3, |tphi_t|=13 — gauge fix succeeded.
- Result: BLEW UP at step 4 (t=0.0004), |u|_max=2.6e6, |N|_max=180. Grid-scale
  oscillations (period 3*dx=0.352) visible at step 3.
- Bug-fix (same iteration): added sanity threshold so saved snapshot is the
  t=0.0003 last-sane state, not float-overflow garbage.
- Diagnosis (F3): linearization around (0, N0, 0) on M_cs gives
  d^2/dt^2(delta_N) = [k^4*(N0+1)/4 + 2*kappa*N0*(N0+1)*k^2]*delta_N.
  Strictly positive bracket for focusing kappa=+1 AND user-convention +Q
  -> UV-unstable system (Omega ~ k^2/2 as k -> infty after dealias).
  Classical ill-posedness. No explicit scheme stabilizes; even exact-linear
  integrator gives exp(Omega*t) growth on unstable modes.
- Decision (D3): stop, budget exhausted (3/3 iterations).

## Summary
- Phenomenon target NOT met. Saved output is the IC essentially unchanged.
- BKdV bank covered the dealiasing escalation cleanly but did NOT cover the
  three actual failure modes encountered (Madelung singularity, non-periodic
  phi gauge, +Q UV instability). The bank gap that the prompt anticipated
  (no Madelung-pressure entries, no sign-convention entries) was the
  dominant unaddressed mechanism.
