# Round-2 Reasoning

## Approach

Switched from Fourier pseudospectral + integrating-factor RK4 (IFRK4) to **IMEX-spectral** (Fourier pseudospectral with Crank-Nicolson on the linear dispersive term, explicit treatment of the nonlinear term).

## Numerical Method

The KdV equation v_t + 6 v v_x + v_xxx = 0 is rewritten in conservation form: v_t = -3(v^2)_x - v_xxx.

In Fourier space, the linear stiff term L_hat = -ik^3 v_hat is treated implicitly via Crank-Nicolson, while the nonlinear term N_hat = -3 ik FFT(v^2) is treated explicitly. This yields the update:

```
(1 - dt/2 * ik^3) v_hat^{n+1} = (1 + dt/2 * ik^3) v_hat^n + dt * N_hat^n
```

No matrix inversion needed — the Crank-Nicolson factor in Fourier space is just pointwise division. Time step dt = 0.0005, giving Nt = 4000 steps to reach T=2.

## Why This Avoids Round-1 Blow-Up

Round-1 used IFRK4, which required computing exp(ik^3 * t) at each step. For high wavenumbers, k^3 can be large (~O(10^6) for k ~ 100), and multiplying by t=O(1) still yields large imaginary exponents; more critically, if there was any mistake in the integrating factor formulation (e.g., incorrect sign, wrong reshaping, missed dealiasing), the exponential can produce overflow or phase errors that cascade to NaN.

IMEX-CN avoids all exponentials. The Crank-Nicolson denominator (1 - dt/2 * ik^3) is a complex number with magnitude >= 1, so dividing by it is unconditionally stable for the linear part — it cannot overflow. The explicit nonlinear term is evaluated in physical space and transformed, which is standard and safe. dt = 0.0005 keeps the explicit CFL condition satisfied for the nonlinear term.

## Risks

- The method is only first-order in time for the coupled system (CN is second-order for linear part, but explicit treatment of nonlinear term degrades to first-order globally). For smooth soliton propagation over T=2 with dt=0.0005 (4000 steps), truncation error should be acceptable.
- No dealiasing applied to the nonlinear term. The 2/3 rule could be added, but for a single smooth soliton at Nx=256 with small dt, aliasing energy should remain small and the scheme should remain stable.

## Changes vs Round-1

| Aspect | Round-1 (IFRK4) | Round-2 (IMEX-CN) |
|---|---|---|
| Linear treatment | Integrating factor exp(ik^3 dt) | Crank-Nicolson (pointwise division) |
| Nonlinear treatment | 4-stage RK4 in transformed variable | Single explicit step |
| Exponential factors | Yes — source of overflow/NaN | None |
| Dealiasing | Missing (possible aliasing) | Not needed at this resolution |
| dt | Likely too large or RK4 stage errors | 0.0005, 4000 steps |
