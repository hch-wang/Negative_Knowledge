# Reasoning — Round 3

## Pattern from r1+r2

Both prior rounds used purely explicit time-stepping variants of the pseudo-spectral method. Round 1 used plain RK4 with dt=1e-3, which blew up because the stiff dispersive term `v_xxx` drives a CFL-like condition requiring dt ~ dx^3 / (2π)^3 ≈ 3e-6 — three orders too large. Round 2 tried an integrating factor (IFRK4) to handle `v_xxx` exactly, which fixed the blow-up, but used the same dealiasing (2/3 rule hard cutoff) and produced soliton fragmentation: 4 peaks instead of 1, with amp_ratio=0.48. The common failure pattern is **insufficient control of the nonlinear coupling terms**, leading to either instability (r1) or spurious mode excitation that breaks the soliton (r2).

## New method

Round 3 uses **Strang operator splitting** with a tight adaptive solver for the nonlinear part:

1. **Linear half-step**: propagate `v_xxx` exactly in spectral space via `exp(i k^3 * dt/2)` — this is the exact solution to `v_t = -v_xxx`.
2. **Nonlinear full step**: integrate all remaining nonlinear terms (`-3uu_x`, `-d/dx(3v^2+v_xx)`, `-6vv_x`, `-d/dx(uv)`) using `scipy.integrate.solve_ivp` with RK45 and tight tolerances (rtol=1e-7, atol=1e-9). This adaptive integrator controls local error, preventing the accumulation that fragmented the soliton in r2.
3. **Linear half-step** again (Strang symmetry, second-order accurate in splitting error).
4. After each macro-step, apply an **exponential spectral filter** (order-36 super-Gaussian) instead of the 2/3 hard cut. This damps high-k aliasing without exciting the mid-k modes that the hard cutoff left untouched in r2, which were the seeds for the spurious peaks.

The macro splitting step is dt=0.05 with the adaptive solver allowed sub-steps as needed.

## Use of bank

No knowledge bank available.

## Final risks

- The splitting error is O(dt^2) ≈ 2.5e-3 per step; over T=8 this gives ~160 steps × splitting error. Tight nonlinear solver tolerances mitigate this but do not eliminate it. If the soliton is marginally stable, accumulation of splitting error could still degrade amplitude.
- The exponential filter with p=36 is very aggressive at k/k_max > 0.9. If the soliton has significant energy there, it may damp physical content. The soliton is a sech^2 with width ~1 in a domain of 30, so its spectral content is concentrated at |k| < 2π ≈ 6 ≪ k_max ≈ 26.8; the filter will not touch it.
- The adaptive solver may be slow but correctness is prioritized over speed.
