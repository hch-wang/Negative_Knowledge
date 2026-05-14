# Reasoning — T_A under PosNeg condition

## Final method (E3)

Fourier pseudospectral spatial discretization on x ∈ [-15, 15] with Nx = 256 (periodic) +
IMEX-Crank-Nicolson time integrator (CN treats v_xxx implicitly; forward step for all
nonlinear and coupling terms on both u and v) +
2/3 dealiasing applied to every nonlinear product (v², u·v, u²).

dt = 2e-4, T = 8.0 → 40,000 steps; 9 evenly-spaced snapshots.

Equations as written:
  u_t + 3 u u_x = -∂_x(3 v² + v_xx)   ⇒   u_t = -3 u u_x − 6 v v_x − v_xxx
  v_t + 6 v v_x + v_xxx = -∂_x(u v)

Operationally:
  v̂^{n+1} = [v̂^n (1 − dt/2 · ik³) + dt · N̂_v^n] / (1 + dt/2 · ik³)
  u^{n+1}  = u^n + dt · N_u(u^n, v^n)
with all products formed in physical space and 2/3-dealiased by zeroing |k| > N/3 before
multiplying by ik to take the divergence.

## Iteration trace

- E1 (Fourier pseudospectral + explicit RK4, no dealiasing, dt=5e-5). F1: blew up at t=0.605, |u|max~3.7e38, mass(v) → −7.4e15. Aliasing+dispersive-stiffness explosion as kb-kdv-noDealiasing-aliasing-artifacts and kb-kdv-IFRK4-blowup warn.
- E2 (single-component change: swap RK4 → IMEX-CN, no dealiasing, dt=2e-4). F2: blew up at t=0.609 with mass(v) perfectly preserved at 4.0 but 126 spurious local maxima at end. IMEX-CN fixes the dispersion (kb-kdv-IMEX-CN-spectral-pass) but aliasing in 6vv_x and ∂_x(uv) still drives blow-up.
- E3 (single-component change: add 2/3 dealiasing). F3: clean stable physics through t=2.0 (|v|max=1.567 then 1.461; mass(v)=4.000 to machine precision; single dominant peak); u grows steadily (2.39 → 6.07 → 12.79 over t ∈ [0,1,2]) and blow-up at t=2.234. Diagnosis: explicit, non-flux-limited treatment of 3 u u_x lets u steepen into a true Burgers shock; spectral discretization without shock-capturing then bursts via Gibbs/aliasing.

The remaining single-component upgrade would be MUSCL+Godunov (or HLL) for the u advection
sector (kb-burgers-MUSCL-Godunov-shock-pass), but that would be E4 and is not permitted
under the 3-experiment cap.

## Use of memory (citations)

Bank entries that drove decisions:
- kb-kdv-noDealiasing-aliasing-artifacts (negative): warned E1 of the aliasing failure mode and informed F1/F2 diagnostics.
- kb-kdv-IFRK4-blowup (negative): rejected — narrowed away from IFRK4 toward IMEX-CN for E2.
- kb-kdv-explicit-RK4-stiffness-blowup (negative): warned that explicit RK4 on v_xxx fragments the soliton even when finite.
- kb-kdv-IMEX-CN-spectral-pass (positive): the validated IMEX-CN baseline at exactly our amplitude A=2; primary motivation for E2's time integrator switch.
- kb-gardner-G2-IMEX-CN-dealiased-stableRadiation (positive): confirmed IMEX-CN + 2/3 dealiasing is the stable recipe in a closely related (Gardner) problem; motivated E3's dealiasing addition.
- kb-gardner-KdV-method-transfer-moderate-amplitude (positive): explicit "KdV→Gardner method transfer" entry that informed taking the same recipe to a coupled system at moderate amplitude.
- kb-kdv-spectral-solitonAmplitude-conservation (positive): predicted ~2% amplitude conservation under IMEX-CN+2/3 — consistent with our observed |v|max≈1.5 down from 2.0 during t≤2 (note: drop is also physical, due to coupling).
- kb-gardner-G3-noDealiasing-cubicAliasing (negative): directly informed the F2 diagnosis of 126 spurious peaks.
- kb-gardner-nonlinearCFL-amplitude-boundary and kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup (negative): governed dt selection at A=2 (chose dt=2e-4 between the safe-at-A=1.5 dt=5e-4 and the failing-at-A=3 dt=1e-4).

Bank entries considered and rejected:
- kb-burgers-fwdEuler-centralFD-Gibbs, kb-shallowWater-centralFD-fwdEuler-hNegative, kb-general-centralFD-hyperbolic-shockFormation: ruled out central FD in favor of pseudospectral derivatives for E1 (and v_xxx in particular).
- kb-burgers-LaxFriedrichs-longTime-dissipation, kb-shallowWater-LaxFriedrichs-overdiffusion: ruled out Lax-Friedrichs because T=8 would over-damp the soliton below the 1.0 amplitude threshold.
- kb-burgers-MUSCL-Godunov-shock-pass, kb-shallowWater-HLL-dam-break-pass: NOT used in E1–E3 but would be the next move for the u sector under a 4-iteration regime. Recorded as the diagnosed-but-unused escalation direction.
- kb-shallowWater-LaxFriedrichs-stable-smeared (positive): rejected for the same over-diffusion reason on the T=8 horizon.

## Final self-assessment

`pred_results/T_A.npy` does NOT satisfy the phenomenon target. The trajectory survives
cleanly only through t ≈ 2.0 (single peak, |v|≈1.5, mass(v)=4.0 to 10 decimals, |u|max≈12.8
which is already nearing the 15 bound but still below it). After t≈2.23 the u sector
undergoes a Burgers shock formation that the IMEX-CN+2/3-dealiased spectral scheme cannot
contain; the final snapshot at t=8 is therefore numerically blown up with |u|~3.7e13,
|v|~3.6e7, and 85 spurious peaks.

Diagnostics on the final snapshot (t=8 padding):
  |u|max ≈ 3.67e13  (>> 15)
  |v|max ≈ 3.57e7   (>> 15)
  mass(v) ≈ 4.0 (still preserved by IMEX-CN's spectral structure)
  local maxima ≈ 85 (≠ 1)

useful_self_assessment = false. The blow-up isolates the *next* required single-component
upgrade as MUSCL+Godunov (or HLL) on the u-equation hyperbolic flux; this is consistent
with bank entries kb-burgers-MUSCL-Godunov-shock-pass and kb-shallowWater-HLL-dam-break-pass.
The progressive-complexity trace clearly identifies which one remaining component is
responsible for the residual failure, which is the intended deliverable of this study even
under failure.
