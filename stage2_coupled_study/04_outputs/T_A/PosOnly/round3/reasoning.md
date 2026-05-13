# Round-3 Reasoning: T_A Soliton Stability

## Pattern from r1+r2

Both prior rounds used a single monolithic Fourier pseudospectral IMEX loop treating all four terms (two per equation) simultaneously. Round 1 crashed from a variable naming bug (`dealias_mask` referenced before `dealias` was assigned). Round 2 fixed that but used Adams-Bashforth 2 for the fully explicit nonlinear + coupling terms, leading to NaN/Inf blow-up. The common failure pattern is: **explicit or partially-explicit treatment of the full coupled nonlinear RHS at the same timestep, without separation of the stiff dispersive operator from the hyperbolic Burgers-like operator.**

## New Method

Round 3 adopts **Strang-type operator splitting** between:

1. **Burgers sector (u equation)**: MUSCL-van Leer reconstruction + Godunov exact Riemann flux for the `3 u u_x` advection term, forward Euler update. The coupling source `−∂_x(3v² + v_xx)` is added explicitly at each step.

2. **KdV sector (v equation)**: IMEX-Crank-Nicolson spectral, treating `v_xxx` implicitly (CN denominator `1 − dt/2 · ik³` has magnitude ≥ 1, unconditionally stable) and `6vv_x` plus the coupling source `−∂_x(uv)` explicitly. Timestep reduced to `dt=0.0002` (from 0.0005 in r1/r2) for stability of the explicit nonlinear part.

The two operators are not interleaved in alternating half-steps (pure Strang) but rather applied sequentially within each full step, which avoids the explosive cross-term accumulation that caused r2 blow-up.

## Use of Bank

- **kb-burgers-MUSCL-Godunov-shock-pass**: confirms MUSCL-van Leer + Godunov at CFL≈0.45 achieves L1 error ~0.003 for Burgers — used directly for the `u` equation Burgers operator.
- **kb-kdv-IMEX-CN-spectral-pass**: IMEX-CN spectral (CN on `v_xxx`, explicit nonlinear, dt=0.0005) successfully propagated a KdV soliton to T=2. Extended here to T=8 with smaller dt=0.0002.
- **kb-gardner-KdV-method-transfer-moderate-amplitude**: IMEX-CN transfers cleanly to Gardner (which is structurally similar to swept-KdV) at amplitude ~2. This directly supports using the same IMEX-CN scheme for the `v` equation here.
- **kb-gardner-G2-IMEX-CN-dealiased-stableRadiation**: 2/3 dealiasing with IMEX-CN is stable for amplitude-1.5 Gardner at T=2. The sech² IC may radiate somewhat, but the dominant soliton peak should remain above the 0.5×2.0=1.0 threshold.

## Final Risks

1. **Coupling stiffness**: The coupling term `−∂_x(uv)` is treated fully explicitly. At T=8 with `u` amplitude potentially growing from Burgers compression, `uv` could become large and destabilize the explicit part. The clamp `clip(±20)` provides a safety net but could artificially damp the physics.
2. **Long-time soliton drift**: The sech² IC is not an exact soliton of the *coupled* system (only of the decoupled KdV). The perturbation `0.2v` in `u` will cause radiation; at T=8 the dominant peak may have decayed below the 1.0 amplitude threshold. However, bank entry `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` suggests the dominant peak survives at ≈30% of initial amplitude after radiation — here our target is 50%, which is achievable if coupling perturbation is weaker than the Gardner cubic correction.
3. **Mass conservation**: With explicit coupling and forward Euler on `u`, mass of `v` may drift up to ~5–7%, within the <8% requirement.
