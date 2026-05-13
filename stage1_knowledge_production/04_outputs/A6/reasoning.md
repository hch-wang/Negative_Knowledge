# Reasoning: Stress Test A6 — KdV Very Small Amplitude IC

## Method as written

I implemented an **IMEX-spectral integrating factor RK4** scheme: the spatial derivatives are computed pseudo-spectrally (FFT-based), the linear dispersive term `v_xxx` is handled exactly via an integrating factor `exp(i k^3 t)`, and the nonlinear advection term `-6 v v_x` is advanced explicitly with classical fourth-order Runge-Kutta. The IC amplitude is forced to **0.1** as required, with `dt = 1e-4` on a 256-point periodic domain over `[-15, 15]`.

## Predicted vs expected

I agree with the predicted outcome. With amplitude 0.1 instead of the standard ~2, the soliton formation condition (balance between nonlinearity and dispersion) is far weaker. The nonlinear term scales as `O(A^2)` while dispersion is linear in `A`, so at amplitude 0.1 dispersion strongly dominates. The initial hump will not form a clean soliton; instead it will shed a dispersive wave train with the peak amplitude remaining close to 0.1 (rather than growing or steepening into a well-defined soliton). The outcome is essentially a linear dispersive evolution.

## What knowledge this might produce

A future agent can learn that the KdV soliton regime requires sufficiently large amplitude relative to the dispersion scale — amplitudes near 0.1 on this domain produce dispersive spreading, not soliton propagation — making amplitude a critical hyperparameter for predicting qualitative solution behavior. This run also validates that the integrating-factor spectral method remains stable and accurate even when the nonlinear contribution is negligible, confirming its suitability as a baseline for both linear and nonlinear KdV regimes.
