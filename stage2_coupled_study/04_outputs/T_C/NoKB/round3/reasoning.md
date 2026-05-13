# Round 3 Reasoning: T_C Burgers Bore / KdV Soliton

## Pattern from r1+r2

Both rounds used explicit RK4 with spectral (Fourier) derivatives and 2/3-rule dealiasing. Round 1 blew up to NaN immediately — the dt was too large relative to the stiff v_xxx term (CFL for third-order dispersion scales as dt ~ dx^3). Round 2 tried a much smaller dt (1e-4) and added amplitude clipping at ±5 as a safety valve; it finished without NaN but the clipping itself was triggered on u, producing the exact boundary value u_max=5.0 and a completely unphysical result (mass drift 35%). The common failure: both relied on explicit time integration without adequately controlling the third-order dispersive stiffness, and Round 2's "fix" (clipping) masked the instability rather than resolving it.

## New method

Round 3 stays with explicit RK4 but addresses the root cause directly:

1. **No clipping at all.** The clip was causing the u_max=5 artifact. Removing it forces the method to be genuinely stable, not just bounded.

2. **Much smaller dt = 2e-5.** For v_xxx with k_max ~ 2*pi*85/30 ~ 17.8, the dispersive CFL condition is dt < dx^3 / (some constant). dx = 30/256 ~ 0.117, so dx^3 ~ 1.6e-3. A factor-of-80 safety margin gives dt ~ 2e-5, comfortably below the stability threshold.

3. **Dealiasing applied inside every derivative call.** The dealias mask is applied to the hat coefficients before computing each derivative, preventing aliasing errors from accumulating and triggering blow-up.

4. **Real FFT (rfft/irfft).** Using rfft halves the Fourier array size, reduces floating-point noise from conjugate inconsistency, and speeds up each step.

The total number of steps is ~400,000 which is computationally feasible and correctly resolves the stiff dispersive term without resorting to implicit solvers or operator splitting (which would require solving a nonlinear system or introducing splitting errors).

## Use of bank

No knowledge bank available (NoKB condition).

## Final risks

- **Runtime:** ~400k RK4 steps with 4 FFT pairs per stage = ~6.4M FFTs. Each rfft on 128 complex points is fast; total wall time estimated 30–120 seconds in CPython. Within typical evaluation limits.
- **Residual instability:** If the nonlinear coupling still generates high-k energy faster than the dealiasing removes it, blow-up could still occur. However, with dt=2e-5 the explicit stability region comfortably covers the dispersive eigenvalues.
- **Soliton survival:** The soliton amplitude 1.5 is large enough that the bore (u_L=1.5) will noticeably perturb it, but the KdV soliton is a robust solitary wave and should survive the encounter with reduced amplitude, satisfying the >=0.5 criterion.
