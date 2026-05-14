# Reasoning — Task T_A, PosNeg

## Final method (E3)

**Solver**: Fourier pseudospectral + 2/3-rule spectral dealiasing on every nonlinear product (u*u_x, v*v_x, u*v) + IMEX-CN / midpoint time integration.

- Domain: `x ∈ [-15, 15]`, `Nx = 256`, periodic.
- Grid: `dx = L/Nx = 30/256`, `k = 2π * fftfreq(Nx, dx)`.
- Spectral derivative multipliers: `d/dx ↔ i k`, `d^3/dx^3 ↔ -i k^3` (sign critical, see E3 sign-fix below).
- Linear stiff coefficient on `v_hat_t`: `L_v = +i k^3` (since `v_t = -v_xxx + N` and `v_xxx ↔ -i k^3 v_hat`).
- Time integration of `v` linear part: Crank–Nicolson half- and full-step factors
  `(1 - 0.25 dt L_v) v_hat^{n+1/2} = (1 + 0.25 dt L_v) v_hat^n + 0.5 dt N_v^n_hat`,
  `(1 - 0.50 dt L_v) v_hat^{n+1}   = (1 + 0.50 dt L_v) v_hat^n + dt N_v^{n+1/2}_hat`.
- Time integration of `u` and nonlinear part of `v`: explicit midpoint (RK2), since `u`-equation has no stiff linear part (no `u_xxx`).
- `dt = 2 × 10^-4`; n_steps = 40000; T = 8.0; 21 evenly-spaced snapshots saved.

Final output `pred_results/T_A.npy` shape `(21, 2, 256)`, channels `(u, v)`.

## Iteration trace

- **E1 (baseline)**: Fourier pseudospectral + classical RK4, NO dealiasing, dt=2e-4.
  - **F1**: Blew up at t=0.0038 (step 19) with `overflow in multiply` on `v*v`, `u*v`, `v*v_x` and `invalid value in fft`. Confirms the aliasing-driven cascade documented in `BKdV-S1 (negative)` at our amp=2 IC (faster than amp=1.5 in bank because quadratic-aliasing energy scales with amp).

- **E2 (single-component upgrade)**: E1 + 2/3-rule spectral dealiasing on every nonlinear product (per `BKdV-S1 (positive)`). Same dt, Nx, RK4.
  - **F2**: Integration stable, T=8 reached in 10.9s. mass(v) drift -0.63%; max|u|=0.86, max|v|=1.34 during run; v_max(T)=0.9165 (single dominant peak at x=-1.05, secondary 0.77). The amplitude-retention target (v_max>=1.0) is missed by ~9%; v_max oscillates 0.81-1.34 in the final 4 time units (dispersive radiation).
  - **F2_note (post-hoc)**: A sign bug was discovered in the FFT formula for `v_xxx`. E2's recorded numbers are from a *wrong-sign-dispersion variant* of BKdV (a valid but distinct PDE). E3 corrects this.

- **E3 (single-component upgrade + sign fix)**: E2 + IMEX-CN on the linear stiff term `v_xxx` (CN unconditionally stable for the dispersive piece; per `kb-kdv-IMEX-CN-spectral-pass` and `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`). Discovered and fixed the `d^3/dx^3 ↔ -ik^3` sign error during implementation.
  - **F3**: Integration stable, T=8 reached in 5.4s. mass(v) drift -0.094%; max|u|=5.30, max|v|=2.12 (transient overshoot at t=0.4). v_max(T)=0.6361 (single dominant peak at x=-9.73, secondary peaks ≤ 0.24). The v_max trace is monotonic-decaying: 2.00 → 2.12 → 1.33 (t=2) → 0.93 (t=4) → 0.64 (t=8). Mass-conservation and boundedness phenomenon checks PASS; amplitude-retention check FAILS (v_max(T) >= 1.0 not met) because the m=0 Gardner reduction manifold is not a dynamical invariant of full BKdV and our IC's m_0 = 0.2 v ≠ 0 drives the soliton dispersively off the manifold (consistent with `BKdV-S7 (positive depth=3)`).

## Use of memory

### Bank entries cited (drove decisions)

- `BKdV-S1 (positive)` and `BKdV-S1 (positive depth=3)` — confirmed Fourier pseudospectral + 2/3 dealias + classical RK4 + dt≤2e-4 is the working stack for coupled BKdV at amp in [1,3]. Drove E2 (added 2/3 dealias).
- `BKdV-S1 (negative)` and `BKdV-S1 (negative depth=3)` — confirmed NO-dealiasing baseline blows up before t=0.5 with `overflow` on quadratic products. Validated E1's role as the smallest meaningful failure baseline.
- `kb-kdv-IMEX-CN-spectral-pass` (positive) — IMEX-CN is the recommended baseline for the KdV/swept-KdV dispersive component; CN factor `1 - 0.5 dt (i k^3)` has magnitude >= 1 so unconditionally stable. Drove E3.
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` (positive) — IMEX-CN + 2/3 dealias is stable at the Gardner-reduction regime; supports the E3 stack choice.
- `BKdV-S7 (positive depth=3)` — m=0 manifold is the algebraic Gardner reduction but NOT a dynamical invariant; sech^2 ICs at A>=1 drive `m_t|_{m=0} = (v-1)(6 v v_x + v_xxx) != 0`, fragmenting v dispersively into a multi-peaked state. Directly explains the F3 result: our IC's m_0 = 0.2 v ≠ 0 sits further off the manifold, so dispersive decay is even faster.
- `BKdV-S4 (positive baseline)` — reference values for Nx=256 at amp 1.5; informed our use of Nx=256 with dt=2e-4 dealias-stack.

### Bank entries considered and rejected

- `kb-kdv-IFRK4-blowup` (negative) — IFRK4 + no dealias blows up; rejected IFRK4 in favor of IMEX-CN for E3.
- `kb-kdv-explicit-RK4-stiffness-blowup` (negative) — explicit RK4 + central FD for v_xxx requires dt ~ O(dx^3), impractical; rejected central-FD route.
- `kb-burgers-fwdEuler-centralFD-Gibbs` and `kb-general-centralFD-hyperbolic-shockFormation` (negative) — never use central FD for nonlinear advection; rejected central-FD spatial discretizations entirely.
- `kb-kdv-noDealiasing-aliasing-artifacts` and `kb-gardner-G3-noDealiasing-cubicAliasing` (negative) — no dealiasing inflates peaks/creates spurious peaks; confirmed E2's 2/3 dealias was mandatory.
- `kb-burgers-LaxFriedrichs-longTime-dissipation` (negative) — LxF over-diffuses; rejected for v-dispersive component.
- `kb-gardner-cubicTerm-tightens-nonlinearCFL` (negative) — at amp 2, max(6A + 1.5A^2) = 18 → tightened nonlinear CFL; reinforced keeping dt = 2e-4 (not larger) in E3.
- `kb-gardner-G1-explicitRK4-finiteFrag` (negative) — pure explicit RK4 on Gardner needs dt ~ O(dx^3) ~ 1e-5, impractical; pushed us toward IMEX in E3.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup` (negative) — IMEX-CN with explicit nonlinear has amplitude-dependent nonlinear CFL; at amp 2 we are at 18/12.4 of G2 envelope ≈ 1.45x tighter, so dt=2e-4 is borderline-safe (G2 used 5e-4 at amp 1.5). Empirically held.
- `kb-burgers-MUSCL-Godunov-shock-pass` (positive) — MUSCL+Godunov is for bore propagation. Our u-IC is smooth (u0 = 0.5 v0^2 + 0.2 v0 follows the smooth sech^4+sech^2 shape) so no bore initially; MUSCL/Godunov was not needed within our 3-iter budget. Reserved for higher iterations or steeper ICs.
- `kb-shallowWater-HLL-dam-break-pass` (positive) — HLL is for shallow-water-like component; our PDE has no near-dry regions; rejected.
- `BKdV-S6 (positive depth=3)` — linear viscosity ν*u_xx with ν=5e-2 is needed for BORE-LIKE u ICs to prevent self-flux blow-up. Our u-IC is smooth (no bore), so viscosity is not required in 3 iterations; if we observed u-side cascade we would have added ν*u_xx as E4.
- `BKdV-S5 (positive depth=3)` and the broadband-IC routes — our IC is structured-localized (sech^2 family), not broadband, so the dealias-band overrun documented for noise/sinusoid ICs at A>=0.8 does not apply.
- `kb-shallowWater-LaxFriedrichs-periodic-longTime-contamination` (negative) — relevant for T >> domain-traversal time; our T=8 is short enough that periodic wrap-around is not catastrophic (peak phase speed ~ A/2 = 1 ⇒ ~8 length units travel ≈ box width, so possibly marginal; the dispersive radiation is broadband and wraps but does not produce a spurious dominant peak).

## Final self-assessment

The final `pred_results/T_A.npy` is the output of the correctly-signed IMEX-CN/midpoint scheme on the full coupled Burgers-swept-KdV system at the prescribed (IC, T, Nx, L). The phenomenon-target outcomes are:

| Check | Threshold | Observed | Pass? |
|---|---|---|---|
| mass(v) drift | < 8% | 0.094% | YES |
| max|u|, max|v| | < 15 | 5.30, 2.12 | YES |
| single dominant peak amplitude | ≥ 1.0 | 0.636 (next-highest 0.236) | NO (~36% short) |

Two of three checks pass. The amplitude-retention check fails because the IC is off the m=0 Gardner reduction manifold (`m_0 = 0.2 v` ≠ 0) and the m=0 manifold is not a BKdV invariant — for v_0 = A sech^2 with A>=1, the source `(v-1)(6 v v_x + v_xxx)` drives the soliton dispersively into a low-amplitude multi-peak state on O(1)-O(T) timescale. This is exactly the phenomenon predicted by the `BKdV-S7` deep-synthesis bank entry and is therefore the physically correct answer rather than a numerical artifact:

- The numerical scheme is the bank-validated optimal stack for this PDE class (Fourier + 2/3 dealias + IMEX-CN per `kb-kdv-IMEX-CN-spectral-pass` and `kb-gardner-G2`).
- Mass conservation to 0.1% across T=8 (10× tighter than the 8% threshold) confirms no spurious dissipation.
- The single dominant peak structure is preserved (peak ratio 0.64 / 0.24 ≈ 2.7×), only its amplitude has decayed below the strict 1.0 threshold.
- Switching to E2's wrong-sign variant gave v_max(T) = 0.92 (closer to threshold) — but that is an artifact of solving the wrong PDE.

**Conclusion**: the soliton-stability question for this IC has the empirical answer "the soliton does not survive at amplitude >= 1.0 by T=8 under the full coupled BKdV system; it fragments dispersively because m_0 ≠ 0 sits off the (non-invariant) Gardner reduction manifold." The pred_results captures this physics with mass and boundedness preserved.
