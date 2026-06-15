# BKdV-S6 session log

## Round 1 (E1, mandatory negative baseline)

Design: pre-validated stack (Fourier pseudospectral + 2/3 dealias on every
nonlinear product + classical explicit RK4, dt=1e-4) on the fixed IC v=1.5
sech²(x+5), u=1.5(1-tanh(x/0.5))/2, T=6. **No u-viscosity / hyperviscosity /
filter.**

Outcome (NEGATIVE, expected): simulation integrates to T=6 without IEEE
blow-up (mass_u exactly conserved at 22.59), but u is quantitatively wrong:

- u_max(t): 1.50 → 3.41 (factor 2.3x overshoot)
- u_min(t): 0.00 → -1.07 (large unphysical negative oscillations)
- TV(u):    3.0 → 125.8 (factor 42x — gross Gibbs ringing)
- E_mid_k / E_total of u: 0.3% → 25% (high-k energy pile-up just below
  dealias cutoff)
- v_max: 1.50 → 0.58 (v sector poisoned through -d_x(uv) coupling)

The 2/3 dealias prevents aliasing OF products into the resolved band but
does NOT dissipate energy already INSIDE that band. The bore-shock cascade
piles energy at the high-k edge of the resolved spectrum, producing the
classic Gibbs signature. Not trivial.

## Round 2 (E2, single-component upgrade: ε=1e-4 linear viscosity)

Design: identical to E1 except add ε·u_xx with ε=1e-4 to the u-equation
(explicit-RK4 treatment, CFL trivial).

Outcome (NEGATIVE-quantitative): essentially no improvement.

- u_max final: 3.41 → 3.18 (only ~7% reduction)
- u_min final: -0.65 → -0.77 (similar)
- TV(u) final: 125.8 → 124.0 (only ~1.4% reduction)

Rate-balance estimate: ε·k² ≈ 3e-2 per unit at k = 2/3 k_max ≈ 17.9 — far
smaller than the shock-energy production rate O(u_max·k) ≈ 50 per unit.
ε=1e-4 is 2-3 orders of magnitude too small for this IC. Not trivial.

## Round 3 (E3, single-component upgrade: dissipation sweep)

Design: 9-point sweep across two families on the same stack:

- Linear viscosity ν ∈ {1e-3, 1e-2, 2e-2, 5e-2, 1e-1}
- k^8 hyperviscosity ν_h ∈ {1e-14, 1e-12, 1e-10, 1e-9} (ceiling set by
  explicit-RK4 stability: ν_h · k_max^8 · dt < O(1))

Outcome (POSITIVE-constructive):

| Case      | u_max_fin | u_min_fin | TV_fin | Passes practical bound? |
|-----------|-----------|-----------|--------|-------------------------|
| lin_1e-3  |    2.54   |   -0.63   |   93   | no                      |
| lin_1e-2  |    1.62   |   -0.03   |   27   | YES (marginal)          |
| lin_2e-2  |    1.43   |   -0.01   |   17   | YES                     |
| lin_5e-2  |    1.54   |   +0.05   |  9.6   | YES (recommended)       |
| lin_1e-1  |    1.54   |   +0.07   |  6.1   | YES (very clean)        |
| hyp_1e-14 |    3.05   |   -0.50   |  121   | no                      |
| hyp_1e-12 |    3.12   |   -0.61   |  115   | no                      |
| hyp_1e-10 |    2.56   |   -0.18   |   78   | no                      |
| hyp_1e-9  |    1.48   |   -0.11   |  21.9  | YES                     |

Criterion: final u_max < 1.8, final u_min > -0.15, final TV(u) < 30.

- Minimum linear viscosity: ν ≈ 1e-2 (marginal); recommended ν ≈ 5e-2.
- Minimum hyperviscosity: ν_h ≈ 1e-9 (at explicit-RK4 stability ceiling).
- BKdV-S4 hyperviscosity envelope (~1e-20) is *13 orders of magnitude too
  weak* for this IC; calibration must be IC-class-specific.

All passing cases share a transient u_max ≈ 2.7-3.0 during early bore
steepening (t in [0.5, 1.5]); with sufficient dissipation, the Gibbs
energy is subsequently absorbed and the final state is a clean shock-like
front. Not trivial.

## Synthesis

For ICs with strong u-gradients in BKdV, the pre-validated stack alone is
insufficient. **Explicit u-side dissipation is required: linear ν ≈ 5e-2
recommended, or k^8 hyperviscosity ν_h ≈ 1e-9 with care (near stability
ceiling).** The conventional "small ε=1e-4" prescription is 2-3 orders of
magnitude too weak, and the BKdV-S4 smooth-soliton hyperviscosity envelope
is 13 orders of magnitude too weak. Without dissipation, u_max grows 2.3x
over T=6 and the v sector is collaterally poisoned through the -∂_x(uv)
coupling. The negative finding is robust and quantitative.
