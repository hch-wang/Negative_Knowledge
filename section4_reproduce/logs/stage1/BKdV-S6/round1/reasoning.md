# BKdV-S6 Round 1 (E1) reasoning

## Design

Mandatory negative baseline: the pre-validated stack (Fourier pseudospectral +
2/3-rule dealias on every nonlinear product + classical explicit RK4, dt=1e-4)
with NO explicit u-side dissipation. Fixed IC:

    v(x,0) = 1.5 sech^2(x+5)
    u(x,0) = 1.5 (1 - tanh(x/0.5)) / 2     (smoothed bore, width ~0.5)

The bore has u_L = 1.5, u_R = 0 with characteristic transition width ~0.5 spatial
units. With dx = L/Nx = 30/256 ≈ 0.117, the IC transition resolves on ~4 grid
points: this is BORDERLINE resolution for a Burgers-like step.

T = 6.0 lets the bore-front propagate and steepen multiple times under its own
self-flux 3 u u_x while interacting with the leftward-moving v-soliton at x ≈ -5.

## What was measured

For each of 25 snapshots over t∈[0,6]:
- u_max=|u|_∞, u_min, v_max
- Conserved/diagnostic quantities: mass_u, mass_v, energy=0.5∫(u²+v²)
- Spectral high-k content of u in the band (k_max/3, 2·k_max/3) — i.e. above
  half the dealias cutoff. Gibbs oscillations at a shock should populate this
  band. (Pure dealias zeros |k|>2·k_max/3, so we look just below the cutoff.)
- Total variation TV(u) = Σ|u_{i+1}-u_i| + |u_N - u_1| — direct Gibbs / shock
  oscillation indicator. For a monotone bore IC, TV(u) ≈ 1.5; growth above
  this means oscillations.

## Results

| t   | u_max | u_min   | v_max | TV(u)  | E_mid_k / E_total |
|-----|-------|---------|-------|--------|-------------------|
| 0.0 | 1.500 |  +0.000 | 1.498 |   3.00 |   3.0e-3          |
| 1.0 | 3.072 |  -0.364 | 0.813 |  45.10 |   4.5e-2          |
| 2.0 | 3.333 |  -0.706 | 0.582 |  84.21 |   1.0e-1          |
| 3.0 | 2.877 |  -0.701 | 0.583 |  92.33 |   1.2e-1          |
| 4.0 | 2.869 |  -0.586 | 0.621 | 117.28 |   2.2e-1          |
| 5.0 | 3.153 |  -1.075 | 0.614 | 117.63 |   2.5e-1          |
| 6.0 | 3.407 |  -0.652 | 0.792 | 125.78 |   2.5e-1          |

- mass_u exactly preserved at 22.589 (spectral derivative + dealias is
  conservative in mass for the d_x form used here).
- The simulation runs to T=6 WITHOUT IEEE Inf/NaN — no formal "blowup".
- BUT u_max grows from the IC bound 1.5 to a peak of 3.41 (≈2.3×); u develops
  large NEGATIVE excursions (u_min ≈ -1.07) where the IC had u ≈ 0 — pure
  Gibbs ringing with no physical justification.
- TV(u) explodes from 3.0 to 125.8 — a 42× growth, signaling that the field
  is now dominated by short-wavelength oscillation, not the smooth bore.
- Spectral mid-band energy ratio E(k_max/3 < |k| < 2k_max/3) / E_total
  grows from 0.3% to 25%. Energy is piling up just below the dealias cutoff
  — the textbook signature of Gibbs accumulation at an under-resolved shock.
- v sector is also damaged: v_max collapses from 1.50 to 0.58 by t≈2, never
  recovers to the soliton-like coherent state. The chaotic high-k content of
  u is being injected into v through the -∂_x(uv) coupling.

## Interpretation

The pre-validated stack is INSUFFICIENT for this IC. The smoothed bore in u
steepens under 3 u u_x; intrinsic high-k content of the shock that develops
is NOT physically dissipated by 2/3 dealiasing (which only zeroes |k| > 2/3
k_max but does nothing to absorb energy below that cutoff). Energy piles up
at the cutoff, manifests as Gibbs ringing visible in u_max/u_min/TV, and
poisons the v sector via the (uv)-coupling.

This is the expected negative finding. The simulation is not "blown up" but
is QUANTITATIVELY WRONG: u_max ≈ 3.4 has no physical justification given a
monotone IC with u_max = 1.5 and a self-steepening (but bounded) flux.

## Trivial-finding flag

is_trivial: **false**. This is a non-tautological numerical demonstration that
2/3-rule dealiasing is not by itself sufficient regularization for an IC with
sharp u-gradients — the prevailing "pre-validated stack" recipe needs an
explicit dissipation term on the u-side, otherwise quantitative trust in
u(t) is lost from t≈1 onward.
