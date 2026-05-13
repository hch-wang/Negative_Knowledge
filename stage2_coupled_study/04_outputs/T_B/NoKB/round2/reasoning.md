# Reasoning — T_B Round 2

## Method

Pseudospectral spatial discretization (256 Fourier modes) with 2/3-rule dealiasing to suppress aliasing-driven blow-up, combined with scipy `solve_ivp` (RK45) for adaptive time-stepping with rtol=1e-6, atol=1e-8, max_step=0.01.  All nonlinear products are dealiased before differentiation.  Seven snapshots are saved at uniform intervals in [0, T=6].

## Use of r1 finding

Round 1 used fixed-step RK4 with an unconstrained time step.  The exec log showed overflow in `u * u_x` and `u * v` products within the first steps, meaning the fixed dt was far too large for the stiff coupling between the Burgers nonlinearity and the KdV dispersive term.  The nonlinear terms amplified small spectral errors until values exceeded float64 range.

Round 2 addresses this in two ways:
1. **Adaptive dt via RK45**: scipy's error control picks the largest dt that keeps local truncation error below tolerance, avoiding the hand-tuned dt problem entirely.
2. **2/3 dealiasing**: the round-1 code computed nonlinear products in physical space and fed them back to spectral differentiation without dealiasing, allowing aliased high-k modes to accumulate energy and trigger overflow.  Dealiasing zeroes the top third of wavenumbers after each FFT, removing the aliasing instability source.

## Use of bank

No knowledge bank was provided for this problem family.

## Risks

1. **RK45 stiffness**: if the dispersive term v_xxx dominates stiffness (scales as k^3 ~ 10^3 for k_max ~ 27), RK45 may still need very small steps and could be slow or fail to converge in time; a better choice might be IMEX but that exceeds the numpy/scipy-only constraint.
2. **Soliton separation insufficient**: with T=6 the Gaussian may not have fully decomposed into well-separated solitons; amplitude 4 gives KdV solitons of speed ~8 (v_soliton ~ 2*amp for KdV), so the fastest should travel ~48 units in T=6 — periodic domain wrapping may cause soliton overlap that confounds peak counting.
3. **Mass drift from dealiasing**: zeroing high-k modes changes the conserved mass integral slightly at each step; over T=6 this drift could exceed the 8% threshold if the Gaussian's mass lives significantly in the top-third wavenumber band.
