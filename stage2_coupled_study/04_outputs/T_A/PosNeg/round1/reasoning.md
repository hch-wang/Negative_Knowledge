# Reasoning: T_A Soliton Stability in Coupled Burgers-swept-KdV

## Method

**Spatial discretization:** Fourier pseudospectral on periodic domain [-15, 15] with Nx=256. All derivatives computed in spectral space via `(ik)^n`. The nonlinear products `u*u_x`, `v*v_x`, `u*v`, `3v^2` are evaluated in physical space and their derivatives taken spectrally, with 2/3 dealiasing applied before each nonlinear FFT.

**Time integration:** IMEX-Crank-Nicolson for the v equation, Adams-Bashforth 2 (AB2) for nonlinear terms:

- v equation: The stiff dispersive term `v_xxx` is treated with Crank-Nicolson implicitly. Each step solves `(1 - dt/2 * (ik)^3) v_hat_new = (1 + dt/2 * (ik)^3) v_hat + dt * NL_hat`, where the denominator has magnitude >= 1, guaranteeing unconditional stability for the dispersive part. The explicit nonlinear terms (`-6 v v_x - d_x(u v)`) use AB2 for second-order accuracy.

- u equation: No stiff dispersive term. Fully explicit AB2 on the nonlinear terms `-3 u u_x - d_x(3v^2 + v_xx)`. The `d_x(v_xx)` term is computed spectrally as `(ik)^3 * v_hat` (third spectral derivative of v).

**Time step:** dt = 1.5e-4 (adjusted via AB2 formula from step 1 which uses forward Euler as startup). T_final = 8.0, giving ~53,333 steps. This dt satisfies the nonlinear CFL for the coupled system: max nonlinear speed ~ max(3*|u|, 6*|v| + 1.5*v^2) ~ 18 at initial time; CFL number = dt * 18 / dx ~ 1.5e-4 * 18 / (30/256) ~ 0.23 < 0.3.

**Output:** 9 snapshots at t = 0, 1, 2, ..., 8 saved as shape (9, 2, 256) to `pred_results/T_A.npy`.

## Use of Memory

**Directly adopted:**
- `kb-kdv-IMEX-CN-spectral-pass`: IMEX-CN spectral was demonstrated stable and accurate for KdV soliton at amplitude 2.0 on the same grid (Nx=256, domain [-15,15]). Transferred directly to the v equation's dispersive term here.
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`: Confirms IMEX-CN + 2/3 dealiasing is the correct baseline for Gardner (the m=0 reduction of this system). We apply the same method here.
- `kb-kdv-noDealiasing-aliasing-artifacts` and `kb-gardner-G3-noDealiasing-cubicAliasing`: Both warn that omitting 2/3 dealiasing produces spurious peaks and amplitude inflation. Applied dealiasing throughout.
- `kb-gardner-nonlinearCFL-amplitude-boundary`: Specifies dt must satisfy dt * max(6A + 1.5A^2) * k_Nyquist < O(1). At A=2 this gives dt <= ~2e-4. Chose dt=1.5e-4 with margin.
- `kb-gardner-cubicTerm-tightens-nonlinearCFL`: Confirms that the coupled system's nonlinear speed at A=2 is O(18), requiring dt smaller than KdV baseline. Conservative dt chosen accordingly.

**Rejected:**
- `kb-kdv-IFRK4-blowup`: IFRK4 blew up on bare KdV due to exp(ik^3 t) overflow at high k. Not used.
- `kb-burgers-fwdEuler-centralFD-Gibbs` and `kb-general-centralFD-hyperbolic-shockFormation`: Central FD for Burgers-like terms causes Gibbs oscillations. Avoided by using spectral differentiation with dealiasing.
- `kb-kdv-explicit-RK4-stiffness-blowup`: Explicit-only treatment of v_xxx causes soliton fragmentation. Not used; IMEX handles the stiff term.
- `kb-burgers-LaxFriedrichs-longTime-dissipation`: LxF over-diffuses amplitude at long times. Not used as the primary scheme.
- `kb-gardner-sech2IC-not-exact-soliton`: Warns that KdV sech^2 IC is not a true Gardner soliton. This applies to the m=0 reduction. Here the prompt explicitly specifies sech^2 IC and the system is the full coupled system (not pure Gardner), so a perturbation from the Gardner soliton is expected and acceptable — the eval criterion only requires peak survival to amplitude >= 1.0, not exact soliton form.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup`: Shows IMEX-CN blows up at amplitude 3.0 with dt=1e-4. Our amplitude is 2.0 (v0 max) and dt=1.5e-4. The nonlinear speed at A=2 is 12+6=18 vs A=3 which is 31.5; we are safely below the blow-up boundary.

## Risks

1. **Nonlinear CFL of u equation:** The u equation is treated fully explicitly. If the soliton interaction generates a large transient in u (which starts at max ~2.4), the explicit CFL may be violated at some step. The chosen dt=1.5e-4 has a ~30% margin at initial conditions but may tighten during interaction. Monitor: if blow-up is detected, the script exits early with the last valid snapshot.

2. **Radiation from perturbed IC:** Since u(x,0) = v^2/2 + 0.2v (not exactly the Gardner m=0 reduction), the system is not on the Gardner reduction manifold. The 0.2v perturbation will radiate energy into dispersive tails. This is physically expected but may depress the final soliton amplitude. The eval criterion (amplitude >= 1.0) should be met if the perturbation is not too large.

3. **Periodic domain re-entry:** At T=8.0, a soliton with KdV speed c ~ 4/3 * amplitude = 8/3 ~ 2.67 travels ~21.3 length units. The domain is 30 units wide, so the soliton will re-enter the domain once. This is a property of the periodic boundary, not a numerical artifact (per `kb-burgers-LaxFriedrichs-periodic-longTime-contamination`). Re-entry does not corrupt the peak count as long as the soliton remains coherent.

4. **AB2 startup:** Step 1 uses forward Euler (first-order), which may introduce a small transient at t=dt. At dt=1.5e-4 this is negligible, but the first snapshot at t=0 is taken before any integration, so this does not affect the initial snapshot.
