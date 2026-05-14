# reasoning.md — T_C / PosNeg

## Final method

**E2 = Fourier pseudospectral + 2/3-rule dealiasing on every nonlinear product + classical explicit RK4.**

- Domain: x in [-15, 15], Nx = 256 (periodic).
- Spatial: FFT-based derivatives for u_x, v_x, v_xx, v_xxx (linear single-field derivatives are alias-safe).
- Nonlinear products (u u_x, v v_x, v^2, u v) computed with the 2/3 truncation: each operand pre-filtered to |k_idx| <= Nx/3, product taken in physical space, FFT of result re-truncated to the 2/3 band. This blocks alias-folded modes from quadratic products feeding back into resolved wavenumbers.
- Time: classical 4-stage RK4 over full RHS (including v_xxx) at dt = 1e-4. Post-dealias RK4 dispersion-CFL bound is ~4.94e-4 (kb BKdV-S1), so dt = 1e-4 is comfortably below.
- T = 8.0, 9 snapshots saved (t = 0, 1, ..., 8). Output shape (9, 2, 256) at `pred_results/T_C.npy`.

## Iteration trace

- **E1 (baseline, simplest)**: Same Fourier+RK4 stack, NO dealiasing. Blow-up at t = 0.76 with overflow on v*v and u*v — classic aliasing cascade (matches BKdV-S1 negative kb signature). dt was below the v_xxx CFL, so aliasing — not dispersion stiffness — is the binding wall. F1: negative, useful = false. D1: change_method (single-component upgrade = add 2/3 dealiasing).
- **E2 (single-component upgrade)**: Add 2/3-rule dealiasing on every nonlinear product. Same Fourier+RK4 stack, same dt. Reached T = 8.0 cleanly: max|u| 1.5 -> 3.46 (bore steepens, bounded), max|v| 1.5 -> 0.66 (soliton survives the interaction with reduced amplitude), single coherent v peak at T = 8 (find_peaks confirms 1 peak at height 0.665), mass_u drift = 0.0 (machine), mass_v drift = 8.9e-15 (machine). F2: positive, useful = true. D2: stop_useful — phenomenon target met on first justified upgrade.

## Use of memory

### Positive bank entries cited (drove method choice)

- **BKdV-S1** (positive, depth = 3 deep synthesis): "Working stack: Fourier + 2/3-rule + classical RK4, dt <= 2e-4 reaches T = 10 cleanly with mass conserved <1e-12." This is the decisive positive precedent that justified E2 = E1 + dealiasing as the single-component fix. The deep-synthesis entry also calibrates the safe-envelope (Nx = 256, amp <= 3, T <= 10), and our task (amp = 1.5, T = 8) sits inside it.
- **kb-general-firstOrder-Godunov-preShock-baseline** (positive): Confirmed that for the Burgers operator a baseline is acceptable before shock formation; we used this as an authorisation for not jumping to MUSCL-Godunov in E1.

### Positive bank entries considered but NOT adopted (deferred)

- **kb-burgers-MUSCL-Godunov-shock-pass** and **kb-shallowWater-HLL-dam-break-pass** (positive): These advocate MUSCL+Godunov / HLL for hyperbolic shock components. Strong precedent, but adopting them at E1 would have violated progressive-complexity discipline (E1 = simplest baseline). We held them in reserve for E3 had E2 failed; E2 succeeded so they were not needed.
- **kb-kdv-IMEX-CN-spectral-pass** and **kb-gardner-G2-IMEX-CN-dealiased-stableRadiation** (positive): Recommend IMEX-CN for the dispersive v_xxx term. Not adopted because E2 confirmed explicit RK4 at dt = 1e-4 (post-dealias CFL margin ~5x) is sufficient at T = 8. IMEX-CN would have been the natural E3 single-component upgrade if E2 had exhibited dispersion-stiffness blow-up; it did not.

### Negative bank entries cited (drove what NOT to do)

- **kb-burgers-fwdEuler-centralFD-Gibbs**, **kb-general-centralFD-hyperbolic-shockFormation**, **kb-shallowWater-centralFD-fwdEuler-hNegative** (negative): Block central FD on the advective component. We used Fourier pseudospectral instead, which is the cleanest "no upwind, no limiter" alternative at this Nx.
- **kb-burgers-LaxFriedrichs-longTime-dissipation** (negative): Block LxF as default Burgers scheme at T >> shock timescale (would over-smear bore). We did not consider LxF.
- **kb-kdv-IFRK4-blowup** (negative): Block integrating-factor RK4 on v_xxx (exp(i*k^3*t) overflows at high k). We used classical RK4 instead.
- **kb-kdv-explicit-RK4-stiffness-blowup** (negative): Warns explicit-only RK4 + central FD requires impractically small dt and still fragments the soliton. We mitigate via Fourier (no central-FD truncation error) and post-dealias CFL margin.
- **kb-kdv-noDealiasing-aliasing-artifacts** (negative): Direct prediction of E1 failure mode (aliased energy creates spurious peaks / overflow). E1 reproduced this signature exactly (overflow at t < 1).
- **BKdV-S1** negative-depth = 3 entries: Confirm no-dealias + Fourier+RK4 dies before t = 0.5 (we saw t = 0.76 at Nx = 256, dt = 1e-4 — consistent), AND that lowering dt alone does NOT fix it; only the 2/3 truncation does.

### Negative bank entries considered but did not gate any decision

- **kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup**, **kb-gardner-cubicTerm-tightens-nonlinearCFL**, **kb-gardner-nonlinearCFL-amplitude-boundary** (negative): Warn about Gardner cubic term tightening CFL at A >= 3. Not applicable: our IC has v amplitude 1.5 (KdV regime, not Gardner), so cubic-CFL is not the binding wall. We checked.
- **kb-gardner-sech2IC-not-exact-soliton** (negative): Would matter if we were claiming an exact Gardner soliton on the m = 0 reduction. We are not — we set u and v independently with m != 0, and the bore-soliton interaction is genuinely in the full BKdV regime, so this entry does not apply.
- **BKdV-S5** entries (negative): Warn that sech^2 ICs are not on an invariant m = 0 manifold of BKdV — fine, our IC explicitly has m = u - v^2/2 != 0 by construction, and chaotic dispersive evolution is expected and observed (max|u| oscillates 2.7-3.7 during interaction). Phenomenon target only requires soliton survival and bounded u, both of which hold.
- **BKdV-S2 / BKdV-S3 / BKdV-S4** (negative depth-3 deep synthesis): About Hamiltonian search / coherence diagnostics / resolution sensitivity. Not directly load-bearing for T_C, but they corroborate that mass conservation alone is insufficient as a correctness diagnostic — we therefore also checked peak count, peak height, peak bound on u (find_peaks).
- **kb-general-finiteness-not-accuracy**, **kb-general-massConservation-insufficient-diagnostic** (negative): Diagnostic discipline. We followed them: beyond finiteness, we verified max|u| < 5, max|v| >= 0.5, peak count = 1, mass drift = machine.

## Final self-assessment

`pred_results/T_C.npy` has shape (9, 2, 256), all finite, 9 snapshots covering t = 0..8 in unit increments.

**Phenomenon target check:**
- Final v contains a recognizable peak with amplitude 0.665 >= 0.5 (`find_peaks` height = 0.3, prominence = 0.05 finds exactly 1 peak): **soliton survived**, in a refraction / partial-transmission regime.
- Final |u_max| = 3.46 < 5: **u bounded**.
- Bore did not blow up (max|u| stays in 2.7-3.7 across the run after initial steepening).
- mass_u drift = 0 (machine), mass_v drift = 8.9e-15 (machine): conservation laws respected.

I believe the output satisfies the phenomenon target with high confidence. The numerical method is the minimal upgrade over the simplest baseline that the bank's positive and negative deep-synthesis entries both pointed at: classical RK4 + 2/3 dealiasing on quadratic products, no IMEX, no shock-capturing, no operator splitting.
