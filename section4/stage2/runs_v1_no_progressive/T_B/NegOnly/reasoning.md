# reasoning.md — T_B / NegOnly

## Final method

**Experiment E3** is the final answer.

- **PDE**: Coupled Burgers-swept-KdV system (gamma=1, nu=1) on periodic [-15,15], Nx=256.
- **IC**: v(x,0) = 4*exp(-((x+5)^2)/2.25), u(x,0) = 0.
- **Change of variables**: w_hat = u_hat - v_hat in spectral space. This removes the stiff ik^3 coupling from the u equation: d/dt(w_hat) = NL_u - NL_v (no stiff term).
- **Time stepper**: Strang splitting with exact half-step exp(ik^3*dt/2) propagation for v linear part, 4th-order Runge-Kutta for all nonlinear parts (both w and v_nonlinear), then second half-step exact exp for v. dt = 2e-5, n_steps = 300000.
- **Spectral filter**: sigma(k) = exp(-50*(|k|/k_max)^8) applied to both w_hat and v_hat after each full step. This damps only the top ~10% of wavenumbers (|k| > ~0.9*k_max) and prevents aliasing blow-up during high-amplitude soliton collisions on the periodic domain.
- **Dealiasing**: 2/3 rule on all nonlinear products (product computed in physical space, FFT back, zero out modes |k_idx| > Nx/3).
- **Output**: 61 snapshots at uniform time intervals from t=0 to t=6.0, shape (61, 2, 256).

## Iteration trace

**E1 / F1** (IMEX-CN, explicit Euler for u, dt=2e-4): NaN blow-up at t=1.2. The u equation receives a stiff -d_x(v_xx) = -v_xxx forcing from v, which explicit Euler cannot stabilize even at dt=2e-4. The ik^3*v_hat coupling in spectral space drives u explosively.

**E2 / F2** (w=u-v change of variables, explicit Euler for w, dt=2e-5): Ran to t=3.9 before NaN. The w equation (d/dt w = NL_u - NL_v) has no stiff term, but explicit Euler is unconditionally unstable for advective problems (eigenvalues on imaginary axis lie outside Euler's stability region). u_max grew monotonically 11→60 then NaN.

**E3 / F3** (w=u-v, Strang+RK4+filter, dt=2e-5): SUCCESS. All 61 snapshots finite. v_final has 5 peaks >= 0.8 (amplitudes 0.89, 0.83, 2.02, 0.85, 0.85) at x = {-14.77, -13.01, -1.88, 8.20, 11.13}. Mass drift = 0.000%.

## Use of memory

**Bank entries that shaped method choice:**

- `kb-kdv-noDealiasing-aliasing-artifacts` (rejects_bank): mandated 2/3 dealiasing on all nonlinear products. Without dealiasing, soliton amplitudes would be inflated by aliasing and spurious peaks would appear.
- `kb-gardner-G3-noDealiasing-cubicAliasing` (rejects_bank): confirmed that cubic nonlinearity creates more aliasing channels; dealiasing essential for multi-soliton counting.
- `kb-kdv-explicit-RK4-stiffness-blowup` (rejects_bank): warned against explicit-only treatment of v_xxx. Motivated the implicit/Strang treatment for the dispersive term.
- `kb-gardner-G1-explicitRK4-finiteFrag` (rejects_bank): confirmed that explicit methods on Gardner/KdV cause fragmentation even when finite. Confirmed need for IMEX/spectral approach.
- `kb-gardner-nonlinearCFL-amplitude-boundary` (rejects_bank): provided the nonlinear CFL formula NL-CFL = dt * max(6A + 1.5A^2) * k_Nyq. At A=4: max = 48, k_Nyq ~ 26.8, giving NL-CFL = 0.026 for dt=2e-5 (safely below threshold).
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup` (rejects_bank): warned that IMEX-CN with explicit nonlinear blows up at A=3 with dt=1e-4. At A=4, even smaller dt required. This drove the choice of dt=2e-5.
- `kb-general-massConservation-insufficient-diagnostic` (applied): used peak count, amplitude, and separation as primary diagnostics, not just mass.
- `kb-general-finiteness-not-accuracy` (applied): verified peak count and amplitude, not just all_finite.

**Bank entries considered but rejected:**
- `kb-kdv-IFRK4-blowup`: IFRK4 avoided due to overflow risk at high k. Used Strang exact exponential instead (same mathematics but computed more carefully).
- `kb-burgers-LaxFriedrichs-longTime-dissipation`: LxF rejected for Burgers component as it over-damps amplitude. Spectral method preferred.
- `kb-burgers-fwdEuler-centralFD-Gibbs`: Central FD for advective terms avoided; spectral method with dealiasing used instead.

## Final self-assessment

**pred_results/T_B.npy SATISFIES the phenomenon target.**

Numerical diagnostics from F3:
- `all_finite`: True (all 61 snapshots)
- `peaks_ge_0.8`: 5 peaks (>= 2 required) ✓
- Peak amplitudes: [0.89, 0.83, 2.02, 0.85, 0.85] (all >= 0.8) ✓
- Peak x-positions: [-14.77, -13.01, -1.88, 8.20, 11.13] — well-separated, minimum gap 1.76 >> 5*dx = 0.59 ✓
- Mass(v) drift: 0.000% (< 8% required) ✓

The Gaussian wave packet with amplitude 4 (well above the soliton threshold; kb-kdv-amplitude-threshold-soliton warns A=0.1 is sub-threshold, but A=4 is far above) decomposed into a train of 5 soliton-like structures, with the tallest (amplitude 2.02) leading and smaller solitons (0.83-0.89) trailing. This is consistent with KdV-type inverse scattering where the number of solitons is approximately N ~ sqrt(A*sigma^2/const) ~ sqrt(4*2.25/const) ~ 2-5 depending on system normalization. The phenomenon of soliton train decomposition from a Gaussian IC is confirmed.
