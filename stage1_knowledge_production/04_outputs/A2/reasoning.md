# Reasoning: Stress Test A2 — Burgers / Very Short T (Pre-Shock)

## Method as written

I implemented the Godunov upwind scheme for the inviscid Burgers equation using the exact Godunov flux (based on the convex structure of f(u) = u²/2). Time stepping uses an adaptive CFL condition (CFL = 0.8) with periodic boundary conditions enforced via `np.roll`. This scheme is first-order in space and time, and is provably TVD and entropy-stable.

## Predicted vs expected

I agree with the predicted outcome. At T = 0.1, which is well before the shock formation time of 1/π ≈ 0.318, the solution starting from u₀(x) = −sin(πx) will have only undergone moderate steepening. The wave compresses near x = 0 (where the initial condition transitions from negative to positive slope), but no discontinuity has formed yet. The result should be a smooth, slightly steepened sinusoidal profile — no entropy violations, no Gibbs-like oscillations, and no shock features.

## What knowledge this might produce

A future agent tackling Burgers pre-shock problems can learn that first-order Godunov is reliable and sufficient for smooth-regime runs: the numerical diffusion is acceptable when the solution has no sharp gradients, and the CFL-adaptive stepping keeps the run stable without needing higher-order reconstruction. This run also establishes a baseline: if a later run at T ≥ 1/π shows artifacts, the cause is the shock physics, not the scheme.
