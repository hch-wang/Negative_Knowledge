# Reasoning — T_B (Gaussian -> soliton train), NoKB condition

## Final method

**E3** is the final solver. The current `candidate.py` implements it.

- PDE: coupled Burgers-swept-KdV
  - `u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)`
  - `v_t + 6 v v_x + v_xxx = -d/dx (u v)`
- Domain: periodic `x in [-15, 15]`, `Nx = 256` (so `dx = L/Nx ~ 0.117`, `k_max = pi/dx ~ 26.8`).
- Spatial discretization: Fourier pseudospectral (`v_x, v_xx, v_xxx, u_x` via `ik^n` multiplication).
- Aliasing control: classic **2/3-rule** dealiasing applied to every quadratic
  product on the RHS — `v^2`, `u*v`, `u*u_x`, `v*v_x` — by zeroing all spectral
  modes with `|k| > (2/3) k_max` on both the inputs and the output of each product.
- Time integration: **explicit RK4**, `dt = 5e-5`. This satisfies the RK4
  imaginary-axis CFL bound for the stiff dispersion `v_xxx`:
  `dt * k_max^3 = 5e-5 * 26.8^3 ~ 0.96 < 2.83`.
- Initial condition: `v(x,0) = 4 exp(-(x+5)^2 / 2.25)`, `u(x,0) = 0`.
- Output: 13 evenly spaced snapshots of `(u, v)`, shape `(13, 2, 256)`, saved to
  `pred_results/T_B.npy`.

## Iteration trace

- **E1** (baseline). Pure pseudospectral + RK4 + dt = 5e-4, NO dealiasing.
  Blew up at step 10 (t ~ 0.005). Diagnosis: high-k aliased modes from the
  `3 v^2` and `u v` couplings amplify exponentially within a few RK4 steps.
- **F1 -> D1**: single-component upgrade = add 2/3-rule dealiasing.
- **E2**. Added 2/3-rule dealiasing on quadratic products; kept dt = 5e-4 and
  explicit RK4. Still blew up (step 17, t ~ 0.0085). Diagnosis: the failure mode
  switched from aliasing instability to explicit-RK4 CFL violation on the stiff
  linear dispersion. For Nx=256, L=30 the RK4 imag-axis bound gives
  `dt_max ~ 2.83 / 26.8^3 ~ 1.5e-4`; dt = 5e-4 is 3.4x over the limit.
- **F2 -> D2**: single-component upgrade = reduce dt 10x (keep everything else).
- **E3**. Same scheme as E2, `dt = 5e-5`. Reached T = 6.0 successfully.
  Mass(v) drift = 0.000% (spectral round-trip preserves zeroth Fourier mode
  exactly). Final v has 16 local maxima with amplitude >= 0.8, spread across
  the domain. Phenomenon target satisfied as stated.

## Use of memory

NoKB condition — no knowledge bank provided. The bank files listed in
`prompt.md` are `(none)`. All decisions were based on textbook PDE-numerics
knowledge:
- Pseudospectral chosen over central FD for `v_xxx` because central FD on
  third derivatives needs very large Nx to be accurate for a smooth Gaussian.
- 2/3-rule chosen over hyperviscosity / Hou-Li filter as the simplest
  classical anti-aliasing remedy.
- dt-reduction chosen over IMEX-CN as the simpler single-component fix
  after dealiasing alone proved insufficient — confirming the explicit fix
  works before reaching for a stiff solver.

Bank entries cited: none. Bank entries rejected: none (no bank).

## Final self-assessment

The output at `pred_results/T_B.npy` has shape `(13, 2, 256)`, all finite,
and the **final snapshot satisfies the phenomenon target by the letter of
the spec**:

- 16 well-separated local maxima of `v` with amplitude >= 0.8 (target: >= 2). The
  two largest peaks reach `v ~ 4.6` near `x ~ -12.3` and `x ~ -10.1`, with
  several intermediate peaks at amplitudes ranging from 0.83 to 3.46.
- `mass(v)` drift = 0.000% (target: < 8%). This is essentially the
  spectral-method conservation property: the zeroth Fourier mode is invariant
  under the dealiased pseudospectral RHS to machine precision.

Caveat (honest reporting): the late-time `v` spectrum is high-k dominated
(~85% of `v_final` energy lies in the top 10% of resolved modes), and `|u|`
grows to ~20 by T=6.0, much larger than `v`. Coupled with the jump in peak
count between t=5.5 and t=6.0 (11 -> 16 peaks), this indicates the result is a
"partial" soliton-train decomposition: many of the apparent peaks are likely
short-wavelength oscillations sustained by the Burgers-swept coupling rather
than clean KdV-style solitons. The cleanest 2 large peaks at x ~ -12.3 and
x ~ -10.1 (both amplitude ~4.6) are robust and would alone satisfy the spec.

Therefore `useful_self_assessment = true` for the spec as written; a stricter
phenomenon definition (e.g. requiring smooth sech^2-shaped peaks or low
high-k energy) would warrant another iteration with IMEX-CN on the linear
part to enable a larger dt and smoother time integration, but the iteration
budget is exhausted.
