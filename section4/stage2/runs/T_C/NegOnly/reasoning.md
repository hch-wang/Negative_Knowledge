# Reasoning: T_C (Burgers bore + KdV soliton), condition = NegOnly

## Final method

**E3: Fourier pseudospectral spatial discretization + IMEX Crank–Nicolson time stepping + 2/3 dealiasing rule on the nonlinear products.**

Concretely:
- All spatial derivatives are computed in spectral space (multiplication by `ik`, `ik^3`).
- The PDE is rearranged so the linear stiff dispersive term `-v_xxx` is treated implicitly (Crank–Nicolson) in both the u- and v-equations:
  - `u_hat^{n+1} = u_hat^n + dt * N_u_hat + (ik^3 dt/2)*(v_hat^n + v_hat^{n+1})`
  - `v_hat^{n+1} = ( v_hat^n*(1 + ik^3 dt/2) + dt*N_v_hat ) / (1 - ik^3 dt/2)`
  where `N_u = -3 u u_x - 6 v v_x` and `N_v = -6 v v_x - (u v)_x` (both explicit).
- Each nonlinear product (`u*u_x`, `v*v_x`, `u*v`) is computed pointwise after 2/3-filtering the inputs, then its FFT is multiplied by the 2/3 dealiasing mask before any spectral differentiation. This removes aliasing energy that would otherwise feed back into the lowest-k modes.
- Grid: `Nx = 256` on periodic `[-15, 15]`. Time: `dt = 1e-3`, `n_steps = 8000`, `T = 8.0`, `n_snapshots = 9`.

This is the final candidate.py in the working directory.

## Iteration trace

- **E1 / F1**: Baseline. Fourier pseudospectral + explicit RK4, dt = 1e-4, no dealiasing. Per progressive-complexity discipline I had to run a baseline FIRST even though the bank predicted failure. Blew up to NaN at t = 0.56 (step 5605) with “overflow encountered in multiply” in the nonlinear products. Localized the failure as a combination of borderline-stable explicit treatment of v_xxx and un-dealiased nonlinear aliasing.
- **E2 / F2**: Single-component upgrade — explicit RK4 → IMEX-CN (CN on v_xxx, explicit on nonlinear). dt raised to 1e-3 since the v_xxx CFL constraint is now removed. No dealiasing yet (one change at a time). Blew up at t = 0.78 — only 1.4× further than E1, despite v_xxx now being implicit. This isolated the binding constraint as **nonlinear aliasing**, not v_xxx stiffness.
- **E3 / F3**: Layer one more component on E2 — add 2/3 dealiasing. Lasted to t = 1.47 (1.9× further than E2). Snapshot at t = 1.0 shows physically meaningful state: `max|u| = 3.13` (Burgers bore steepening from IC max 1.5), `max v = 0.82` (soliton alive in interaction region). Subsequent blowup is **shock-formation** driven, not aliasing-driven — once u_x grows without bound the central/spectral derivative injects energy at the top of the resolved (post-dealias) band that no IMEX or dealiasing can damp. The trace cleanly localizes the residual failure as “Fourier spectral is a central-derivative method, and central methods cannot represent a forming Burgers shock — bank kb-burgers-fwdEuler-centralFD-Gibbs and kb-general-centralFD-hyperbolic-shockFormation flag this universally.”

## Use of memory

Negative-bank entries that **shaped the rejection lattice** at each step:

- E1 baseline choice: rejected central-FD baselines based on `kb-burgers-fwdEuler-centralFD-Gibbs`, `kb-general-centralFD-hyperbolic-shockFormation`, `kb-shallowWater-centralFD-fwdEuler-hNegative` (all warn that any naive central-FD on a hyperbolic Burgers term produces unbounded Gibbs / spurious peaks). Chose Fourier pseudospectral instead because the IC bore is smoothed and v_xxx is naturally spectral.
- E1 → E2 escalation: chose IMEX-CN over IFRK4 based on `kb-kdv-IFRK4-blowup` (explicit recommendation: “IMEX-CN is a safer default”). Also chose IMEX-CN over reducing dt further based on `kb-kdv-explicit-RK4-stiffness-blowup` and `kb-gardner-G1-explicitRK4-finiteFrag` (200k steps still produced 14 spurious peaks — accuracy collapses even when finiteness is preserved).
- E2 dt selection: used `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup` and `kb-gardner-nonlinearCFL-amplitude-boundary` to verify dt = 1e-3 at amplitude 1.5 gives NL-CFL ≈ 0.45, safely below the empirical 0.5–1 stability bracket (the bank says doubling amplitude shrinks dt by 2.5×, so at A=1.5 dt=1e-3 is on the safe side).
- E2 → E3 escalation: chose 2/3 dealiasing based on `kb-kdv-noDealiasing-aliasing-artifacts` (KdV no-dealias gave 43 % amplitude inflation and 4 spurious peaks) and `kb-gardner-G3-noDealiasing-cubicAliasing` (Gardner no-dealias gave 11 spurious peaks). Rejected Lax–Friedrichs as an alternative based on `kb-burgers-LaxFriedrichs-longTime-dissipation` and `kb-shallowWater-LaxFriedrichs-overdiffusion` (severe over-diffusion that would smear the bore).
- Diagnostics interpretation: used `kb-general-finiteness-not-accuracy` and `kb-general-massConservation-insufficient-diagnostic` to flag that even an all-finite output isn't proof of correctness — peak count, amplitude, position must be checked. (In my case the issue is much more obvious — all NaN — but I still ran multi-snapshot diagnostics.)

Bank entries considered but **not directly cited** because they applied to regimes outside this run: `kb-burgers-LaxFriedrichs-periodic-longTime-contamination` (warns T >> domain-traversal triggers periodic wrap; T=8 here is roughly 1 traversal time so this is borderline but not the dominant failure mode); `kb-gardner-sech2IC-not-exact-soliton` (warns KdV-sech^2 IC into Gardner produces radiation — relevant if we were in the m=0 reduction regime, but our v IC is acceptable for the full coupled system); `kb-shallowWater-dryBed-naiveClip-hu-singular` (no dry-bed regime here); `kb-gardner-GardnerIsM0-coupledSystemInstability` (informs that Gardner failures transfer to the coupled system — used implicitly when reading bank kb-gardner entries as relevant to this task).

## Final self-assessment

I do **NOT** believe `pred_results/T_C.npy` satisfies the phenomenon target.

Evidence:
- Snapshot 0 (t=0): IC, `max|u|=1.5`, `max v=1.50`. Within bounds.
- Snapshot 1 (t=1): `max|u|=3.13`, `max v=0.82`. Both bounds (|u|<5, v>=0.5) satisfied — at this instant the simulation IS faithful.
- Snapshots 2–8 (t=2..8): all NaN. The phenomenon target requires the FINAL snapshot (T=8) to have v amplitude ≥ 0.5; my final snapshot has v=NaN.

The trace honestly localizes why: my final method (Fourier spectral + IMEX-CN + 2/3 dealiasing) cleanly handles the v_xxx dispersive term and the aliasing problem but cannot represent the Burgers shock that forms in u by t ≈ 1.5. The progressive-complexity discipline correctly localized this through three escalations:
1. E1 → identified BOTH v_xxx stiffness and aliasing as candidate failure modes;
2. E2 → ruled OUT v_xxx stiffness as the dominant bottleneck (implicit treatment alone bought only 0.2 s of extra integration time);
3. E3 → confirmed aliasing was a real factor (1.9× further integration time) and isolated the residual failure as shock-formation in u.

The next single-component upgrade (had a 4th iteration been allowed) would be either (a) replace the spectral u-flux with an upwind/MUSCL finite-volume treatment while keeping spectral IMEX on v, or (b) add a spectral filter / hyperviscosity on the highest-k modes of u to provide artificial dissipation in the shock region. Per discipline, that work is documented in F3 and D3 but not executed.

`useful_self_assessment = False` for all three findings. The session ends with an unmet phenomenon target but a clean, debuggable failure trace that explicitly names the missing component.
