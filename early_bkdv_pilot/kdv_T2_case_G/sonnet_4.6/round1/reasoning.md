## Approach

Fourier pseudospectral discretization in space combined with an integrating-factor (IF) Runge-Kutta method in time. The periodic domain [-15, 15] maps naturally to a Fourier basis, giving spectral accuracy for smooth soliton profiles.

## Numerical Method

**Spatial discretization**: Standard FFT-based spectral method on Nx=256 points. All spatial derivatives (v_x for the nonlinear term, v_xxx for the dispersive term) are computed exactly in Fourier space via multiplication by ik and (ik)^3.

**Time integration — Integrating Factor RK4**:

The PDE in Fourier space is:
```
d(V_hat)/dt = -ik^3 V_hat  -  6 * FFT(v * v_x)
              [stiff linear]   [nonlinear, explicit]
```

The linear dispersive term has eigenvalues -ik^3 that grow as k^3 — this is the stiffness that causes explicit schemes to blow up. We handle it exactly by introducing the integrating factor:
```
W_hat(k, t) = exp(i k^3 t) * V_hat(k, t)
```
Then W_hat satisfies:
```
dW_hat/dt = exp(i k^3 t) * [-6 * FFT(v * v_x)]
```
The right-hand side contains only the nonlinear term, with no stiffness. Classical RK4 is applied to this equation. The CFL condition is now governed only by the nonlinear advection speed (~max|v|/dx ~ 17), allowing dt=0.005 (Nt=400 steps) without blow-up.

**Key implementation note**: At each RK4 sub-stage, the stage variable W_hat must be mapped back to V_hat = exp(-ik^3 t_stage) * W_hat before evaluating the nonlinear term.

## Risks

1. **Aliasing error**: The nonlinear term v*v_x can generate wavenumbers up to 2*k_max. With only 256 points and no dealiasing (2/3 rule), there is mild aliasing, but for a single soliton the energy at high modes is negligibly small.
2. **Phase accumulation**: Over 400 time steps, small phase errors per step accumulate. RK4 has 4th-order local truncation error, so global phase error ~ O(dt^4) * T ~ 10^{-7}, well within the ±0.5 position tolerance.
3. **Periodic wrap-around**: The soliton moves from x=-5 to x=+3, staying well within [-15,15], so periodic boundary artifacts are negligible.

## Expected Output

- **Peak position**: x ≈ 3.0 (soliton speed c=4, displacement = 4*2 = 8)
- **Peak amplitude**: ≈ 2.0 (soliton preserves shape)
- **Mass integral**: sum(v)*dx ≈ 4.0 (conserved exactly by spectral scheme on periodic domain)

All three evaluation criteria should be comfortably satisfied.
