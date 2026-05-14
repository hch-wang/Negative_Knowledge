# Reasoning: T_B / PosOnly — Gaussian -> soliton train decomposition

## Final method

**Experiment E2** is the answer.

Operator-split scheme for the coupled Burgers-swept-KdV system:

**v equation** (KdV-type with coupling):
- Fourier pseudospectral with 2/3 dealiasing
- IMEX-Crank-Nicolson: dispersive term v_xxx treated implicitly (CN denominator 1 + dt/2 * (ik)^3, unconditionally stable), nonlinear 6vv_x + d/dx(uv) treated explicitly
- dt_global = 0.002, Nx = 256, domain [-15, 15]

**u equation** (forced Burgers):
- MUSCL-van Leer + Godunov exact Riemann flux for the hyperbolic 3uu_x term
- Adaptive sub-stepping with CFL = 0.45 (dt_sub = CFL * dx / (3 * max|u|))
- Source term -d/dx(3v^2 + v_xx) evaluated spectrally at each global step
- Forward Euler with sub-steps

Operator splitting: each global step, v is advanced first (IMEX-CN), then u is advanced with MUSCL-Godunov using v_new as the constant source.

**Output**: pred_results/T_B.npy, shape (61, 2, 256), 61 snapshots at t = 0, 0.1, 0.2, ..., 6.0.

## Iteration trace

- **E1 / F1**: IMEX-CN spectral for both u and v, dt=0.0002. u equation blew up at t~1.1 (u_max reached 75 by t=1.0 as the forced Burgers equation formed a shock, violating CFL of pure spectral explicit scheme). Finding: negative.

- **E2 / F2**: Operator-split IMEX-CN (v) + MUSCL-Godunov adaptive CFL (u), dt_global=0.002. Result: 4 well-separated soliton-like peaks in v at T=6 with amplitudes [2.08, 0.87, 0.96, 1.16], all >= 0.8; mass drift = 0.00%; all finite. Finding: positive, useful=True. Early stop.

## Use of memory

**Adopted:**
- `kb-kdv-IMEX-CN-spectral-pass`: Used IMEX-CN spectral for the v_xxx dispersive term, transferring the validated KdV scheme. The CN denominator 1 + dt/2*(ik)^3 provides unconditional stability.
- `kb-burgers-MUSCL-Godunov-shock-pass`: Used MUSCL-van Leer + Godunov for the 3uu_x Burgers component of the u equation with CFL=0.45, exactly as validated for Burgers shock problems.
- `kb-kdv-spectral-solitonAmplitude-conservation`: Confirms spectral IMEX is appropriate for tracking soliton amplitudes in Gaussian decomposition tasks.
- `kb-gardner-KdV-method-transfer-moderate-amplitude`: Warned that amplitude > 2 requires caution; used smaller dt and 2/3 dealiasing accordingly.

**Considered but not directly applied:**
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`: Warns that KdV sech^2 ICs are not exact Gardner solitons and will radiate. Noted but our task WANTS decomposition/radiation from a Gaussian — this is the desired phenomenon, not a problem.
- `kb-kdv-smallAmplitude-dispersiveRegime`: Notes that amplitudes O(0.1) won't form solitons. Not a concern here since v(x,0) has amplitude 4.
- `kb-shallowWater-HLL-dam-break-pass` and `kb-shallowWater-LaxFriedrichs-stable-smeared`: Not applicable to this PDE.
- `kb-burgers-Godunov-preShock-smooth`: Subsumed by MUSCL-Godunov choice.

No negative knowledge bank was available in this PosOnly condition.

## Final self-assessment

**Yes, pred_results/T_B.npy satisfies the phenomenon target.**

Numerical diagnostics from E2:
- **Peaks with amplitude >= 0.8**: 4 peaks at x = {-1.99, 8.20, 11.02, 14.77} with amplitudes {2.08, 0.87, 0.96, 1.16} — all exceed 0.8 threshold
- **Well-separated**: minimum separation ~2.8 spatial units (~24 grid cells), clearly distinguishable
- **Mass(v) drift**: 0.00% (< 8% requirement)
- **All finite**: True
- **Output shape**: (61, 2, 256) — 61 snapshots, 2 channels (u, v), 256 spatial points

The Gaussian wave packet at amplitude 4 decomposes into 4 soliton-like peaks traveling at different speeds, consistent with KdV-type inverse scattering decomposition.
