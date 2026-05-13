# Round-2 Reasoning

## Method

Fourier pseudospectral Integrating Factor RK4 (IFRK4) with 2/3-rule dealiasing and dt=0.0001.

The dispersive term v_xxx is absorbed exactly into an integrating factor exp(ik^3 t). The
transformed variable w_hat = exp(-ik^3 t) v_hat satisfies an ODE with only the nonlinear
and coupling terms on the right-hand side, which are treated via classical 4th-order
Runge-Kutta. The u equation (no dispersive stiffness) is advanced in physical Fourier
space with the same RK4, using the same nonlinear/coupling RHS. Both channels use 2/3
dealiasing at every RHS evaluation to suppress aliasing energy.

## Use of r1 finding

Round 1 used IMEX-Crank-Nicolson with dt=0.0005 and blew up immediately. The exec log
shows overflow in `3.0 * u * spectral_deriv(u_hat)` and `v**2`, meaning the nonlinear
coupling amplified energy faster than the CN implicit step could damp it for the high-
amplitude (A=4) initial condition. Two changes address this:

1. **dt reduced 5x** (0.0005 -> 0.0001) to tighten the explicit stability constraint for
   the nonlinear terms.
2. **IMEX-CN replaced by IFRK4**: the integrating factor exactly handles the ik^3
   dispersive stiffness, so the dispersive piece never contributes to blow-up. The RK4
   stage for the remaining nonlinear RHS is conditionally stable under the CFL-like
   constraint on the nonlinear terms.

## Use of bank

- **kb-kdv-IMEX-CN-spectral-pass**: Confirmed IMEX-CN is stable for KdV amplitude 2 at
  dt=0.0005. Since our IC has amplitude 4 (double), the nonlinear terms are ~4x larger,
  which explains why the same dt broke down. This entry guided the dt reduction.
- **kb-kdv-smallAmplitude-dispersiveRegime**: Warns that sub-threshold amplitude leads to
  dispersive radiation rather than soliton formation. Our IC amplitude 4 is well above any
  threshold, so soliton formation is expected — this confirms the phenomenon is achievable
  if we stabilize the numerics.
- **kb-gardner-G2-IMEX-CN-dealiased-stableRadiation** and
  **kb-gardner-KdV-method-transfer-moderate-amplitude**: Both recommend 2/3 dealiasing as
  essential for stability with nonlinear wave problems. Adopted here.
- **kb-kdv-spectral-solitonAmplitude-conservation**: Endorses spectral IMEX methods for
  tracking soliton amplitude and mass conservation, which are the evaluation criteria.

## Risks

1. **IFRK4 phase accuracy at large k**: The exp(ik^3 t) factor oscillates rapidly for
   large wavenumbers at late times (t~6). If double-precision arithmetic rounds the phase
   incorrectly, high-k modes may accumulate phase error. Mitigated by dealiasing (high-k
   modes are zeroed out).
2. **Nonlinear CFL at dt=0.0001**: With max v~4 and spectral derivatives, the nonlinear
   CFL is approximately max_v * dt / dx ~ 4 * 0.0001 / (30/256) ~ 0.003, comfortably
   below 1. However, if soliton amplitudes grow (unlikely for this IC), instability could
   re-emerge.
3. **Coupling u->v blow-up from u_t equation**: The u equation receives forcing from
   d_x(3v^2 + v_xx) which is large when v is large. If u grows unboundedly and feeds
   back into the d_x(uv) term in the v equation, a secondary blow-up could occur. The
   reduced dt is the primary safeguard; if this remains a problem a TVD limiter on u_r
   would be needed.
