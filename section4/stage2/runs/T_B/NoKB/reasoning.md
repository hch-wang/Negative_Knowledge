# T_B / NoKB — Reasoning

## Final method (Experiment E2)

**Spatial discretization.** Fourier pseudospectral on the periodic domain
x in [-15, 15] with Nx = 256. All derivatives (u_x, v_x, v_xxx, (uv)_x) are
computed in spectral space as (i k)^p * FFT(f), and every nonlinear product
formed in physical space is followed by a 2/3-rule dealiasing mask before its
derivative is taken. The 2/3 mask zeros all Fourier modes with |freq index| >=
N/3, which kills the spurious modes created by quadratic products on a
finite-N grid. The IC is also pre-projected onto the dealiased subspace.

**Time integrator.** Explicit RK4 with dt = 1.0e-4. This satisfies the linear
CFL estimate dt < 2.83 / k_max^3 with k_max = π Nx / L ≈ 26.8, giving
dt_lin ≈ 1.5e-4; we use 1e-4 for margin. NO operator splitting, NO IMEX, NO
hyperviscosity, NO filter beyond the 2/3-rule dealiasing.

**PDE form used (no rewriting beyond LHS-RHS rearrangement):**
- u_t = -3 u u_x - 6 v v_x - v_xxx
- v_t = -6 v v_x - v_xxx - (u v)_x

**IC:** v(x, 0) = 4 exp(-(x+5)^2 / 2.25), u(x, 0) = 0. **T = 6.0**, snapshots
stored at t = 0, 0.5, 1.0, ..., 6.0 (13 frames) into pred_results/T_B.npy with
shape (13, 2, 256), dtype float32.

## Iteration trace

- **E1 (baseline)**: Fourier pseudospectral, **no dealiasing**, explicit RK4,
  dt = 1e-4. The simplest meaningful baseline (spectral derivatives are
  required to resolve v_xxx; explicit RK4 satisfies the dispersive CFL).
  **F1 (negative)**: hard blow-up at t ≈ 0.388 (step 3883). Diagnostic
  recording every 200 steps showed the soliton train forming normally
  (max v dropping from 4 to ≈1.8) while max|u| grew from 0 to ≈3 and then
  spiked from 3 → 7.47 in a window of ~200 steps just before NaN — the
  classical fingerprint of an aliasing instability driven by the quadratic
  nonlinearities (u u_x, v^2, u v) on Nx = 256 without dealiasing.

- **E2 (single-component upgrade)**: same scheme, but add 2/3-rule dealiasing
  to every spectral derivative and to the RHS field, plus IC projection.
  RK4 and dt unchanged. **F2 (positive, useful)**: completes T = 6.0 in 14 s,
  no NaN. Final v has 11 local maxima with v >= 0.8 (target >= 2), 7+ of them
  well separated and individually above v = 1.0 (e.g. x ≈ -7.4, -3.5, +2.7,
  +7.1, +10.1, +13.4 with amplitudes 1.30, 1.52, 1.65, 1.49, 1.20, 1.74).
  Mass of v conserved to machine precision (drift = 0.0000 %).

- **E3 (not used)**: D2 = stop_useful was issued because F2 already exceeds
  both phenomenon-target thresholds with large margin.

## Use of memory

The NoKB condition supplies no knowledge bank, so `cites_bank` and
`rejects_bank` are empty for every Experiment node. The escalation logic was
purely textbook: the failure mode in F1 (rapid growth of u with high-k
content, while the dispersive part behaves well) is the canonical signature
that 2/3-rule dealiasing addresses, and it is the *smallest* single change
over E1 — it does not alter the time integrator, the spatial basis, the grid,
or dt. No bank entries were considered or rejected because none were
provided.

## Final self-assessment

I believe `pred_results/T_B.npy` satisfies the phenomenon target.

- **Target 1**: >= 2 well-separated peaks each with amplitude >= 0.8.
  Observed: 11 local maxima with v >= 0.8 at t = 6.0, spread across the
  periodic domain with pairwise distances up to ≈15 units and minimum
  separation 1.52 units; at least seven of these are above v = 1.0 and well
  separated (Δx > 2). **Pass with wide margin.**

- **Target 2**: mass(v) drift < 8 %.
  Observed drift = -0.0000 % (≈ 1e-15 relative). Spectral methods conserve
  the spatial integral exactly because each d/dx term has zero spatial mean.
  **Pass with wide margin.**

The soliton-train interpretation is consistent: an amplitude-4 Gaussian is
well above the threshold for KdV inverse-scattering decomposition into
multiple solitons, and the dispersive term v_xxx coupled with the quadratic
v v_x is the KdV core. The presence of a small-amplitude residual radiation
field is expected.
