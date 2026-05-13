# Reasoning: Stress Test A8 — Shallow Water / Lax-Friedrichs

## Method as written

I implemented the global Lax-Friedrichs (LxF) scheme for the 1D shallow water equations in conservative form (q1 = h, q2 = hu). The numerical flux at each cell interface i+1/2 is the global LxF flux: F_LxF = 0.5*(F_L + F_R) - 0.5*alpha*(q_R - q_L), where alpha is the global maximum wave speed (max |u| + sqrt(g*h)) over all cells. Time integration uses explicit Euler with CFL = 0.4.

## Predicted vs expected

I agree with the predicted outcome. Global Lax-Friedrichs is the most diffusive first-order scheme; it adds numerical viscosity proportional to alpha*dx across every interface, not just near discontinuities. For a dam-break initial condition, the true solution features a left-moving rarefaction wave and a right-moving shock. With LxF at Nx=200 and CFL=0.4, both features will be resolved but substantially smeared over several cells. The scheme is stable (satisfying the CFL condition ensures |alpha*dt/dx| <= CFL <= 1 for explicit LxF), so blow-up is not expected.

## What knowledge this might produce

A future agent can learn that global Lax-Friedrichs reliably avoids blow-up for shallow water equations at moderate CFL but produces noticeably wider shock/rarefaction profiles compared to upwind or Riemann-solver-based fluxes (HLL, Roe) at the same resolution, quantifying the cost of maximum-diffusion stability. This benchmark result can serve as a baseline diffusion reference when comparing flux choices for first-order hyperbolic systems.
