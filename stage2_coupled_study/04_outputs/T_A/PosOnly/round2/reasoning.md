# Round-2 Reasoning: T_A Soliton Stability

## Method

Fourier pseudospectral IMEX scheme on the coupled Burgers-swept-KdV system:

- **v equation**: Crank-Nicolson (CN) on the stiff dispersive term `v_xxx`; explicit Adams-Bashforth 2 (AB2, with a single forward-Euler bootstrap step) on the nonlinear + coupling terms `−6vv_x − ∂_x(uv)`.
- **u equation**: fully explicit AB2 (no stiff dispersive term; all terms `−3uu_x − ∂_x(3v²+v_xx)` are treated explicitly).
- **Dealiasing**: 2/3-rule mask applied consistently to every spectral quantity — spatial derivatives, the source term `v_xx`, and the AB2 predictor.
- **Time step**: dt = 0.0005, 16 000 steps to T = 8.

## Use of r1 finding

Round 1 crashed with `NameError: name 'dealias_mask' is not defined` at the very first step of the main loop. The variable was named `dealias` at declaration but referenced as `dealias_mask` inside the RHS functions and the loop. The fix is simple: use a single, consistently named module-level variable `dealias` throughout all functions and the loop. No algorithmic change was necessary to fix the crash.

## Use of bank

- **kb-kdv-IMEX-CN-spectral-pass**: Directly validates IMEX-CN with explicit nonlinear + implicit `v_xxx` on KdV at the same amplitude (2.0), same domain and Nx=256 over T=2. Confirms dt=0.0005 and the CN denominator `1 + dt/2 * (ik)^3` are stable and accurate. Adopted verbatim as the v-equation integrator.
- **kb-kdv-spectral-solitonAmplitude-conservation**: Confirms IMEX-CN (even without dealiasing) conserves soliton amplitude to ~2% and mass to <1% over T=2. Gives confidence the scheme will satisfy the ≥50% amplitude and <8% mass-drift criteria at T=8.
- **kb-gardner-KdV-method-transfer-moderate-amplitude**: Confirms IMEX-CN transfers cleanly from KdV to Gardner-like problems at amp∈[1,2], which is structurally analogous to this coupled system. No re-engineering needed.
- **kb-burgers-MUSCL-Godunov-shock-pass** and **kb-burgers-Godunov-preShock-smooth**: Both are finite-volume approaches; not adopted here because the u equation has no shock (u is smooth at t=0 and couples weakly to v), and a spectral approach matches the v-equation's spectral treatment for consistency.

## Risks

1. **Long-time drift of the soliton peak**: At T=8 (4× longer than the validated T=2 in the knowledge bank), accumulated phase errors or energy leakage from the coupling could reduce the v peak below 50% of 2.0. The AB2 scheme's second-order accuracy in time should limit this, but is not guaranteed for 8 time units.
2. **Coupling instability in u**: The u equation involves `∂_x(v_xx)` (a third-derivative source), which can amplify high-frequency modes. Dealiasing mitigates this, but if large-amplitude high-frequency v modes develop, the u equation could see spurious growth.
3. **Snapshot count vs. step alignment**: Snapshot collection uses a set of integer steps; rounding errors in `int(round(...))` could slightly mis-place snapshots. The code explicitly adds `n_steps` to `snapshot_list` to guarantee the final snapshot, but intermediate counts could theoretically produce fewer than 9 if rounding collapses two steps together. This is extremely unlikely at dt=0.0005 / n_steps=16000.
