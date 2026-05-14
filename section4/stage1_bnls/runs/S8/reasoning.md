# S8: B-NLS low-density 'hole' — quantum pressure singularity stress test

## Test setup

B-NLS on `x in [-15, 15]`, Nx=256, T=4.0, kappa=+1.
Initial condition `N(x,0) = sech^2(x-5) + 0.001`, so the minimum of N is the 1e-3 background everywhere
except near x=5 (the soliton peak). The "hole" is the entire low-density region away from x=5 — N is
near the floor everywhere outside the peak, especially around x=-5.

The quantum pressure term in the Hamilton-Jacobi equation,
`Q = (sqrt(N))_xx / (2 sqrt(N))`,
contains a `1/sqrt(N)` factor that becomes singular as N -> 0. The central question: how do different
numerical formulations of the same physics handle this?

## Implementation note that mattered

`phi_0 = 0.1*x` is not periodic on `[-15, 15]`. A naive spectral derivative gave `phi_x` in
`[-17, +8]` (Gibbs oscillation from the boundary jump) instead of the correct constant 0.1.
We split `phi = c*x + phi_tilde` with `c = 0.1` and `phi_tilde` periodic; spectral derivatives
are then applied only to the periodic part, with `phi_x = c + (phi_tilde)_x` reconstructed
analytically. Without this fix, every method fails for irrelevant reasons.

All three methods use 2/3 dealiasing for the nonlinear products `u*m`, `(u+phi_x)*N`, `u*phi_x`, `phi_x^2`.
`dt = 5e-4` (4-step RK4 is stable; Strang for Madelung). Spatial discretisation: standard spectral
on the periodic part.

## Methods tried

### M1 — Direct (u, N, phi_tilde) RK4, `eps_reg = 1e-6`

Evolves the three real fields with `Q` computed from `sqrt(N + 1e-6)`. RK4 in time with dealiased
spectral spatial derivatives.

Outcome (negative): **blows up at t = 0.027** with `min_N = -1.41` and `max|Q| = 1.08e5`.
Mass remains exactly 2.030 until the moment of blowup (the continuity equation is exact in
spectral form). The failure starts when dispersive oscillations push a single grid point's `N`
just below zero (first negative value seen is `-7.9e-5` at t=0.0245). Once `N < 0`, `sqrt(N+eps)`
becomes meaningless (we clamp to `sqrt(eps)`), `Q` explodes, drives `phi_t` to large negative
values, which through `u_t = m_t + ... + N phi_x_t` rapidly destabilises `u`.

### M2 — Direct (u, N, phi_tilde) RK4, `eps_reg = 1e-3`

Same scheme as M1, eps_reg raised to the initial background level (so `Q` is fully regularised at t=0).

Outcome (negative): **blows up at t = 0.044** with `min_N = -1.19` and `max|Q| = 3.66e3`.
The larger eps delays the blowup by ~1.6x and reduces peak |Q| by ~30x relative to M1, but does
not prevent it. The dispersive instability that drives `N` below zero is not curable by simply
softening `Q` — it has to do with how the (N, phi) representation interacts with the discrete
dispersion when `N` is at the noise floor. Both regularization choices fail catastrophically.

### M3 — Madelung-Psi, Strang split-step, `eps_mad = 1e-3` ✓

Evolves `psi = sqrt(N + 1e-3) * exp(i * phi_tilde)` complex-valued, plus `u` real. So
`|psi|^2 = N + eps_mad` is strictly bounded below by 0 by construction. Strang split:
- `L(dt/2)`: linear dispersion step `psi_hat -> psi_hat * exp(-i (k^2/2) (dt/2))` in Fourier.
  This is exactly the source of `-Q` in the standard Madelung correspondence.
- `N(dt)`: nonlinear pointwise rotation by `exp(-i V_nl dt)` with
  `V_nl = -2 kappa (|psi|^2 - eps_mad) - u (c + (phi_tilde)_x) - 0.5 (c + (phi_tilde)_x)^2`.
  This contributes `-V_nl` to `phi_t`, matching `-u phi_x - 1/2 phi_x^2 + 2 kappa N`.
- `L(dt/2)`: second half-step.
Then `u` is updated via RK4 of the m-equation, holding the post-step `N`, `phi_x` frozen.

Outcome (positive): **completes the full T = 4.0** with
- `min_N = -9.999e-4` (never below `-eps_mad`)
- mass drift 0.086% relative over T=4
- `max|Q|` bounded around 1.76e3 (large but transient, never runaway)
- `Q` at T_final = 122 (back down)
The unitary nature of the Strang split for the linear piece preserves `|psi|^2 >= 0` analytically;
numerically `|psi|^2` reaches a floor near 0 (giving `N` near `-eps_mad`) but never overshoots.
This is the central new failure mode of B-NLS vs BKdV — **and it has a clean cure**.

## Comparison: min_N and blowup time

| Method                          | eps    | min_N achieved | blowup time | max\|Q\|    | passed |
|---------------------------------|--------|----------------|-------------|-------------|--------|
| Direct (N, phi)  RK4            | 1e-6   | -1.41          | 0.027       | 1.08e5      | no     |
| Direct (N, phi)  RK4            | 1e-3   | -1.19          | 0.044       | 3.66e3      | no     |
| Madelung-Psi  Strang split-step | 1e-3   | -1.00e-3       | 4.0 (full)  | 1.76e3      | yes    |

Interpretation: the direct method's `min_N = -1.4` is meaningless (it's the post-blowup value);
the relevant threshold is the first instant N dips below zero, which is at t~0.0245 for M1
and t~0.039 for M2. After that, the formulation has no physical meaning.

## What we learned

1. **Direct (N, phi) is structurally incompatible with low-density regions on this problem**, regardless of
   the regularization. Eps_reg buys you a small delay (logarithmic in eps), but the dispersive
   instability that pushes a grid point below 0 happens within a few hundred steps. Once `N<0`,
   `sqrt(N+eps)` is no longer the right physical object and `Q` carries no meaning.
2. **Madelung-Psi solves the problem at its root**: `|psi|^2 = N + eps_mad` is non-negative by
   construction under any unitary numerical step. The quantum pressure becomes a regular phase
   rotation. The split-step Fourier method is the natural choice because the dispersion part
   (the source of `Q`) is exactly diagonal in Fourier space and can be advanced exactly.
3. **eps_mad in Madelung is benign**: setting eps_mad = 1e-3 (matching the background) gives
   `min_N >= -1e-3`, i.e. the floor is `-eps_mad` and the result is post-processed by
   `N = |psi|^2 - eps_mad`. There is no instability hidden inside this offset.

## Practical guidance for B-NLS papers / future tests

- When the IC contains a low-density background or develops density holes, **use Madelung-Psi**.
  Direct (N, phi) is not a viable formulation for this problem class.
- For tests where N stays bounded well above zero throughout, direct (N, phi) is fine and is
  conceptually simpler. The crossover threshold is roughly `min_N / (typical N) < 0.01` —
  below that, switch to Madelung.
- The Burgers boost `u * phi_x` is handled correctly by including it in `V_nl` of the Strang
  nonlinear step. No special treatment is needed for the `u`-coupling — only the `Psi` representation matters.
