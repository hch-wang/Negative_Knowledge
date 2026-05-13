# Reasoning for Stress Test A7

## Method as written

I implemented forward Euler time integration combined with central finite differences in space for both the continuity equation (h_t + (hu)_x = 0) and the momentum equation ((hu)_t + (hu^2/h + gh^2/2)_x = 0). No limiter, upwinding, Riemann solver, or flux splitting was used.

## Predicted vs expected

I agree with the predicted outcome. The dam-break initial condition introduces a sharp discontinuity at x=0. Central differences applied to a hyperbolic conservation law near such a discontinuity produce spurious Gibbs-like oscillations. These oscillations cause h to dip below zero, which makes the wave speed sqrt(gh) imaginary and the flux term hu^2/h singular. The forward Euler scheme offers no dissipation to suppress these modes; instead it amplifies them exponentially, leading almost certainly to blow-up before T=0.4. Even if the scheme does not formally diverge to NaN by exit, the solution will be physically meaningless (h < 0, large-amplitude noise throughout the domain).

## What knowledge this might produce

A future agent facing a shallow-water or hyperbolic system should learn that central differences without upwinding or a limiter are provably unstable for discontinuous data, and that forward Euler offers zero artificial dissipation to counteract this — making blow-up effectively guaranteed for the dam-break problem. The stable baseline for such a test is an upwind or Godunov-type scheme with an appropriate CFL condition.
