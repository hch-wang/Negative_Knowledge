# T_B / PosOnly — Reasoning

## Final method

**E2** is the final answer. Method:

- **PDE**: coupled Burgers-swept-KdV
  - `u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)`
  - `v_t + 6 v v_x + v_xxx = -d/dx (u v)`
- **Spatial**: Fourier pseudospectral on periodic `[-15, 15]`, `Nx = 256`.
- **Aliasing control**: 2/3-rule dealiasing — every nonlinear product
  (`v^2`, `u v`, `u u_x`, `v v_x`) is FFT-projected onto `|k_idx| <= 85`
  before being differentiated.
- **Time**: classical explicit RK4 on the full RHS (including `v_xxx`),
  `dt = 1e-4`, `n_steps = 60000`, exact landing on `T = 6.0`.
- **Linear terms** (`v_xx`, `v_xxx`, `v_x`, `u_x`) are computed via direct
  spectral derivatives — no IMEX, no operator splitting, no hyperviscosity.
- **IC**: `v0 = 4*exp(-(x+5)^2/2.25)`, `u0 = 0`, both projected onto the
  resolved band at start.
- **Output**: 13 snapshots evenly spaced in time (including t=0 and t=T)
  in `pred_results/T_B.npy` of shape `(13, 2, 256)`.

## Iteration trace

- **E1 / F1 (NEGATIVE)** — clean baseline: Fourier pseudospectral, NO
  dealiasing, RK4, `dt = 1e-4`. Overflow in `v^2` at step 2779 (`t ~ 0.28`),
  NaN propagated. Diagnoses aliasing of quadratic products at amp=4 (not
  dispersive stiffness, since `dt < dispersion-CFL` for the raw band).
- **E2 / F2 (POSITIVE, useful)** — single-component upgrade: add 2/3-rule
  dealiasing to every nonlinear product. Reached `T = 6` in 18.2 s. Final
  `v` has 10 local maxima above 0.8 (min separation 1.52 in x), `mass(v)`
  conserved to ~3e-16 relative, `sup_u <= 4.88` and `sup_v <= 2.16`
  throughout the run with no spectral edge growth.

## Use of memory

Bank entries that drove decisions (cited with id):

- **`BKdV-S1` (round 2 and round 3) — deep-synthesis, strongest signal**.
  These document the exact same PDE class with the same `Nx=256 / L=30`
  stack, reaching `T=10` cleanly at amplitudes 1.5 and 3.0 using
  `2/3-dealias + RK4` with `dt=2e-4`. This is path-level proof that the E2
  recipe works for the BKdV system; I adopted the dealiasing recipe
  verbatim and tightened `dt` to `1e-4` because amp=4 is slightly above
  their validated upper bound of 3 (extra CFL margin: post-dealias bound
  is ~4.94e-4; `dt=1e-4` keeps us at ~20% of the limit).
- **`kb-kdv-spectral-solitonAmplitude-conservation`** — confirmed spectral
  IMEX-class methods preserve mass and amplitude well enough to measure
  the soliton-train phenomenon; reinforces choice of spectral over FD.
- **`kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`** — also reinforces
  2/3 dealiasing for Gardner-class problems (the m=0 reduction of this
  PDE).
- **`kb-kdv-smallAmplitude-dispersiveRegime`** — at E1 stage, reassured
  that amp=4 is far above the dispersive-only threshold so a soliton-train
  outcome is physically plausible (target not vacuous).

Bank entries considered but **not used** as direct method-drivers (still
positive, just not the tightest fit):

- **`kb-kdv-IMEX-CN-spectral-pass`** and
  **`kb-gardner-KdV-method-transfer-moderate-amplitude`** — recommend
  IMEX-CN for the dispersive sector. These would have been the natural E3
  upgrade if E2 had failed on dispersion-CFL. Since E2 succeeded, I did
  NOT layer IMEX-CN; doing so before observing an actual dispersive-CFL
  failure would violate progressive-complexity discipline.
- **`kb-burgers-MUSCL-Godunov-shock-pass`**,
  **`kb-burgers-Godunov-preShock-smooth`**,
  **`kb-general-firstOrder-Godunov-preShock-baseline`**,
  **`kb-shallowWater-HLL-dam-break-pass`**,
  **`kb-shallowWater-LaxFriedrichs-stable-smeared`** — apply to the
  Burgers / hyperbolic sector and would be relevant if `u` had developed
  a sharp bore that the pseudospectral scheme could not resolve. In F2
  the `u` field stayed band-resolved with no aliasing in the top band, so
  no Riemann-solver upgrade was needed.

No negative bank was available in this condition (`rejects_bank` left
empty on each Experiment node, as required by the protocol).

## Final self-assessment

`pred_results/T_B.npy` **satisfies** the phenomenon target:

| target | requirement | observed |
| --- | --- | --- |
| peak count (final `v` > 0.8) | `>= 2` | **10** |
| peak separation (well-separated) | implicit | min `1.52` in `x` |
| mass(`v`) drift | `< 8%` | **`~3e-16` relative** |
| snapshots in time axis | `>= 5` | **13** (every `0.5` in time) |
| no NaN / overflow | required for valid trace | all finite |

The Gaussian wave packet has visibly decomposed: a single peak at `x=-5`
with amplitude 4 evolves into a chain of ten distinct peaks spread
around the periodic ring at amplitudes between 0.82 and 1.80, with a
clean smooth `v` profile in between (no high-frequency garbage). Mass is
conserved to machine precision, confirming the spectral + dealiased
scheme is faithfully integrating the conservative form.

Conclusion: stop at E2 with high confidence.
