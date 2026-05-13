# Reasoning — T_B Round 3

## Pattern from r1+r2

Both rounds used explicit time-stepping where the stiff dispersive term `v_xxx` (eigenvalue `(ik)^3`, growing as `k^3`) dominated stability. Round 1 used manual explicit RK4 with fixed dt — the `k^3` stiffness caused immediate blow-up (NaN). Round 2 switched to scipy RK45 with adaptive stepping and 2/3 dealiasing: mass of `v` was perfectly conserved (drift ~5e-16), confirming the spatial method was fine, but `u_max` reached 59 — the Burgers coupling term `3 u u_x` for `u` was generating unbounded growth. The root cause in both cases is that the nonlinear cross-coupling terms, once `u` starts growing, feed back into `v`'s equation and vice versa; without any stiffness control on the `v_xxx` term, the nonlinear cascade can overwhelm the adaptive stepper too.

**Common failure pattern**: explicit treatment of `v_xxx` stiffness combined with no damping mechanism for `u` growth in the Burgers term.

## New method

Round 3 uses an **integrating factor (IF) pseudo-spectral RK4** scheme. The key change is that the stiffest linear part of `v`'s equation — the `v_xxx` term with Fourier multiplier `(ik)^3` — is absorbed into an exact integrating factor `exp(ik^3 t)`. This transforms the PDE for `v_hat(t)` into one driven only by nonlinear terms, removing the eigenvalue constraint on `dt` from the dispersive operator entirely. The `v_xxx` stiffness is handled exactly rather than approximately.

For `u`, standard RK4 is used since `u`'s equation lacks a `u_xxx` term; its stiffness comes only from the coupling forcing term `d/dx(3v^2 + v_xx)`, which is mild compared to third-order dispersion.

Time step: `dt = 0.002` (3000 steps for T=6). This is small enough to resolve nonlinear dynamics but not constrained by the dispersive CFL `dt ~ dx^3 / k_max^3`. The IF method makes this step unconditionally stable for the linear part.

Dealiasing: 2/3 rule applied throughout to suppress aliasing instability from nonlinear products.

The integrating factor for RK4 stages uses `IF = exp(ik^3 dt)` at full step and `IF_half = exp(ik^3 dt/2)` at half-step stages, following the ETDRK4 philosophy of Cox-Matthews.

## Use of bank

No knowledge bank available (NoKB condition).

## Final risks

1. The IF-RK4 combination used here is an approximation to the full ETDRK4 scheme — the stage-combination weights for `v` are a simplified version that may accumulate error. If `v` does not decompose into a clean soliton train, one could upgrade to the full Cox-Matthews ETDRK4 with contour integral evaluation of the `phi` functions.
2. `u` grows via Burgers nonlinearity; if it reaches very large values before solitons form in `v`, the cross-coupling `d/dx(uv)` will drive `v` chaotically. The dt=0.002 choice limits this growth per step, but the coupling is fundamentally destabilizing if `u` is large.
3. The soliton train may require longer time (T > 6) to fully separate from the dispersive radiation tail; peak amplitudes near the 0.8 threshold could be marginal.
