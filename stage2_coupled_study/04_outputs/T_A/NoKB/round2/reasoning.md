# Reasoning — Round 2

## Method

Pseudo-spectral spatial discretisation (Nx=256, periodic, 2/3 de-aliasing) with an **integrating-factor RK4 (IFRK4)** time integrator.

The key change is that the dominant stiff term `v_xxx` is handled analytically via an exponential integrating factor. We work in the interaction-picture variable `w_hat = exp(-i k^3 t) * v_hat`. In this picture the dispersive `v_xxx` linear operator is exact, so only the nonlinear terms drive the ODE; the stiffness barrier that caused blow-up in round 1 is removed. For `u`, which has no standalone linear dispersive term, the full equation is treated explicitly inside the IFRK4 stage evaluations.

Time step: `dt = 1.5e-4`, giving ~53 000 steps over T=8. The CFL-like constraint from the nonlinear Burgers piece (`3 u u_x`) with `u ~ O(2)` and `dx ~ 0.117` gives `dt_safe ~ dx/(6*u_max) ~ 0.01`, so `dt=1.5e-4` is very conservative. A blow-up guard aborts integration early if NaN/Inf appears.

Ten snapshots are saved from t=0 to t=T.

## Use of r1 finding

Round 1 used plain RK4 with `dt=1e-3` and no integrating factor. The `v_xxx` term with Fourier wavenumber up to `k_max ~ 2pi/30 * 128 ~ 26.8` contributes a linear growth rate `|i k^3|` up to `~1.9e4`. The RK4 stability region requires `dt * |lambda| <= 2.83`, giving `dt_max ~ 1.5e-4`. Round 1 used `dt=1e-3`, which is ~7x above the stability limit for the highest modes — guaranteed blow-up. The IFRK4 scheme removes this stiffness entirely for the linear part; the remaining nonlinear terms have much smaller effective Lipschitz constants.

## Use of bank

No knowledge bank was provided; no bank entries cited.

## Risks

1. **Nonlinear stiffness**: The coupling term `d/dx(u v)` can amplify energy at high `k` if `u` or `v` develop sharp gradients. The 2/3 de-aliasing mask and small `dt` mitigate this but cannot guarantee stability for arbitrarily large amplitudes.
2. **Mass drift**: The integrating-factor construction preserves the linear part exactly but the nonlinear quadrature errors (RK4 local truncation `O(dt^5)`) can cause slow mass drift over 53 000 steps. The target allows <8% drift, which should be achievable at `dt=1.5e-4`.
3. **Peak amplitude criterion**: The soliton is launched from `x=-5` and travels right; wrapping through the periodic boundary could cause the peak to appear fragmented at evaluation time. The initial position `x+5=0` centred at `-5` with domain `[-15,15]` gives ~10 units of margin before the right edge, which should be sufficient for T=8 at soliton speed ~6 (KdV soliton speed `~4*amplitude/2=4`).
