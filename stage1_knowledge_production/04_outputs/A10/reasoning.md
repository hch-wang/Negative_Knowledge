# Reasoning for Stress Test A10: Shallow Water / HLL Riemann Solver

## Method as written

I implemented the HLL (Harten-Lax-van Leer) Riemann solver for the 1D shallow water equations with explicit Euler time stepping at CFL = 0.4. Wave speed estimates use the Einfeldt-type bounds sL = min(uL - cL, uR - cR) and sR = max(uL + cL, uR + cR), with periodic boundary conditions on a uniform grid of Nx = 200 cells over x in [-1, 1].

## Predicted vs expected

I agree with the predicted outcome. The dam-break initial condition (h = 2 left, h = 1 right, u = 0 everywhere) is a classic Riemann problem for the shallow water equations. Theory confirms a left-going rarefaction fan and a right-going shock emerge at t = 0+. The HLL solver is positivity-preserving when CFL <= 0.5 (satisfied here at CFL = 0.4), so h remains positive throughout. The solution at T = 0.4 should show a smooth rarefaction on the left, a constant intermediate state, and a sharp shock on the right, all well-captured at this resolution.

## What knowledge this might produce

A future agent solving similar hyperbolic conservation law problems can learn that the HLL solver with CFL = 0.4 reliably handles the shallow water dam-break without spurious oscillations or negativity, though it introduces numerical diffusion near the shock that smears it over a few cells. For higher accuracy, MUSCL reconstruction or HLLC (which restores the contact wave) would be preferable, but HLL suffices for robust, stable solutions at moderate resolution.
