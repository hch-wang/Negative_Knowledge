# S2 reasoning: direct (N, phi) vs Madelung-Psi for NLS focusing bright soliton

## Setup

Focusing NLS (kappa = +1), no Burgers boost. Bright soliton IC:

    Psi(x, 0) = sqrt(2) * sech(sqrt(2) * (x + 5)) * exp(i * 0.25 * x)
    => N(x, 0) = 2 * sech^2(sqrt(2) * (x + 5))
    => phi(x, 0) = 0.25 * x

Domain x in [-15, 15] periodic, Nx = 256, dt = 0.001, T = 4.0 (4000 steps).
The tails of the soliton at |x| >> 5 decay to N ~ 3e-24 (numerical zero in float64).

The stress question is: does direct evolution of (N, phi) using the quantum
pressure Q = (sqrt(N))_xx / (2 sqrt(N)) survive? Where and how does it fail?

## Method A: Madelung-Psi split-step Fourier (reference)

Strang split-step on Psi:
- half linear step in Fourier: Psi_hat *= exp(-i k^2 / 2 * dt / 2)
- full nonlinear step in real: Psi *= exp(i kappa |Psi|^2 dt)
- half linear step in Fourier

Notably no Q appears — the |Psi|^2 nonlinearity is benign because |Psi|^2 = N
is conserved by the rotation phase.

Result: mass drift 1.1e-13 over T=4.0, peak amplitude 1.999 (target 2), peak
position x = -3.984 (target -4, dx = 0.117 grid spacing). Machine precision
behavior on a clean reference soliton.

## Method B: direct (N, phi) spectral FFT + RK4

The PDE pair is

    N_t = -d_x(phi_x * N)
    phi_t = -(1/2) phi_x^2 - Q + 2 kappa N
    Q     = (sqrt(N))_xx / (2 sqrt(N))

implemented with FFT spectral derivatives and RK4 in time. Eight variants tested:

| variant                          | regularization                 | dealias | blowup_step | qmax     |
| -------------------------------- | ------------------------------ | ------- | ----------- | -------- |
| hard_eps0                        | none                           | no      | 1           | 6.8e+07  |
| hard_eps1e-12                    | sqrt(max(N, 1e-12))            | no      | 1           | 2.4e+11  |
| hard_eps1e-6                     | sqrt(max(N, 1e-6))             | no      | 2           | 2.4e+08  |
| hard_eps1e-3                     | sqrt(max(N, 1e-3))             | no      | 6           | 5.2e+12  |
| soft_eps1e-6                     | sqrt(N + 1e-6)                 | no      | 2           | 2.4e+08  |
| soft_eps1e-3                     | sqrt(N + 1e-3)                 | no      | 5           | 1.3e+07  |
| soft_eps1e-1                     | sqrt(N + 1e-1)                 | no      | 13          | 3.3e+06  |
| soft_eps1e-3 + 2/3-rule          | sqrt(N + 1e-3)                 | yes     | 21          | 2.2e+24  |

Compare: 4000 steps are needed to reach T = 4.0. The BEST direct variant
survives 21 steps (0.5%).

## Why direct (N, phi) fails

Three layered reasons:

1. **Non-Lipschitz coupling at N = 0.** Q ~ 1/sqrt(N) is unbounded as N -> 0.
   The soliton tails reach N ~ 3e-24, so Q is mathematically singular at the
   boundary in float64 unless regularized.

2. **Hard-floor regularization injects spectral Gibbs.**  Replacing N with
   max(N, eps) creates a discontinuous-derivative joint at the boundary
   between core and floor. Spectral d^2/dx^2 of this step has high-k content
   proportional to 1/dx. Dividing the high-k oscillation by sqrt(eps) (tiny)
   amplifies it catastrophically — this explains why eps=1e-3 (hard) gave
   qmax = 5.2e12 while eps=0 gave only 6.8e7.

3. **Smooth regularization (sqrt(N + eps)) is monotonically healthier.**
   Survival improves smoothly from 2 -> 5 -> 13 steps as eps grows from
   1e-6 -> 1e-1, and qmax decreases (2.4e8 -> 1.3e7 -> 3.3e6). 2/3-rule
   dealiasing extends survival to 21 steps but cannot eliminate the
   underlying medium-k coupling between sqrt(N+eps) curvature and phi.

The clincher: even eps = 0.1 (5% of N_peak = 2) doesn't save us. The
issue is structural — the (N, phi) PDE pair has an effectively-elliptic
right-hand side at low N (Q is essentially a Laplacian on sqrt(N)
divided by sqrt(N)) that, when combined with explicit RK4 time stepping,
exceeds the linear stability boundary almost immediately.

## Conclusion

For the focusing NLS bright soliton on a periodic spectral grid:

- **Madelung-Psi is the unique stable method** of those tested.
- **Direct (N, phi) is fundamentally unstable**, independent of regularization
  choice (hard or soft) or dealiasing in the practical range eps in [0, 1e-1].
- The Madelung transform isn't a convenience — it is the mathematical operation
  that converts a non-Lipschitz nonlinear-PDE pair into a globally Lipschitz
  cubic-NLS, removing the obstruction.

This justifies S5-S8 using Madelung-Psi as the standard (N, phi) integrator
inside the full B-NLS scheme. The Burgers (u) sub-system still needs its own
treatment (RK4 or MUSCL-Godunov per S7), but the Schroedinger-Madelung sector
should always use Psi rather than (N, phi) directly when N can touch zero.

## Best-working method

`candidate.py` runs all variants in one execution; the Madelung-Psi result is
saved as `N_madelung`, `phi_madelung`, `masses_madelung` in
`pred_results/S2.npz`. This is the recommended method for the (N, phi) sector
of B-NLS in all downstream tests.
