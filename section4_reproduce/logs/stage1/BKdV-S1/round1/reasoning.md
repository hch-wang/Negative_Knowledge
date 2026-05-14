# Round 1 — naive baseline stack

## Design
Simplest off-the-shelf pseudospectral scheme:
- Fourier spectral derivatives (Nx=256, periodic L=30, dx≈0.117)
- Classical RK4 over the FULL RHS (no IMEX, v_xxx treated explicitly)
- NO dealiasing on any nonlinear product
- dt = 2e-4 (chosen with rough margin over the explicit-RK4 dispersion CFL)
- IC: v0 = 1.5 sech²(x+5), u0 = v0²/2 (mild, smooth, in-band)

## Why this stack
This is what a non-PDE-specialist would write first: spectral derivatives are easy, RK4 is "high-order and reliable", and dealiasing/IMEX both look like premature optimization. It also exercises the two known weak points simultaneously (stiffness from v_xxx + aliasing from quadratics 3v², uv and v·v_x). Failure here is informative; success would be surprising.

## Observation
`exec.log` shows overflow warnings then NaN well before the first scheduled diagnostic at t=0.5:
- First warning is `overflow encountered in multiply v*v`, immediately followed by the same on `u*v`.
- Then `invalid value encountered in fft` (NaN propagates through the spectral derivative).
- By t=0.5 every diagnostic is NaN, sup-norm is NaN.
- No graceful divergence — blow-up happens within the first ~2500 steps (< t≈0.5) with the field saturating to ±inf in the highest wavenumber.

## Diagnosis (candidate mechanisms)
Two plausible causes both present:
1. **Aliasing instability.** Quadratic products (v², u·v, v·v_x) populate wavenumbers above Nx/3 in the alias band; without 2/3-rule truncation, those wraparound modes feed back into resolved modes and grow without dissipation. Classic spectral failure mode for KdV-class systems.
2. **Explicit treatment of v_xxx is stiffness-marginal.** For Fourier RK4 on u_t = -u_xxx, the linear stability bound is dt ≤ 2.83 / k_max³. Here k_max = π/dx ≈ 26.8, so dt_crit ≈ 2.83 / 19305 ≈ 1.47e-4. Our dt = 2e-4 sits **above** the bound — a small high-k perturbation will grow each step under RK4.

Both effects predict early blow-up; we cannot disentangle them from one run. The "simplest stack" is therefore a confirmed dead end.

## Decision for Round 2
Change exactly ONE component. The most diagnostic single change is **add 2/3-rule dealiasing** (keep RK4 explicit, keep dt the same). Outcomes:
- If it now reaches T=10: aliasing was the root cause.
- If it still blows up near t≈0.5 with similar signature: stiffness is the dominant cause, and we will need IMEX in Round 3.
- If blow-up moves but does not vanish: both effects contribute.

This isolates aliasing vs stiffness in a single experiment.
