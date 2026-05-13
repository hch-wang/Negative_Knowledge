# Reasoning: BKdV-T1 Inviscid Burgers Shock Formation

## Approach

The inviscid Burgers equation u_t + (u^2/2)_x = 0 with IC u_0 = -sin(pi*x) forms a shock at t* = 1/pi ≈ 0.318. At T=0.5 the shock is well-established at x=0. The solution jumps from u ≈ +1 (left) to u ≈ -1 (right) at the shock, with smooth rarefaction regions on either side.

## Numerical Method

**Finite volume method** on a uniform cell-centered grid with Nx=200 cells, dx=0.01.

**Spatial reconstruction**: MUSCL (Monotone Upstream-centered Scheme for Conservation Laws) with a van Leer flux limiter. The van Leer limiter phi(r) = (r + |r|)/(1 + |r|) is smooth, second-order accurate in smooth regions, and reduces to first-order near discontinuities to avoid spurious oscillations. The slope for each cell uses the harmonic-mean formula: sigma_i = 2*(u_{i+1}-u_i)*(u_i-u_{i-1}) / (|u_{i+1}-u_i| + |u_i-u_{i-1}|), which is zero when either neighboring difference is zero and grows only when both differences have the same sign.

**Interface flux**: Godunov flux (exact Riemann solver for Burgers). Given left state uL and right state uR at each interface:
- If uL >= uR (shock): Rankine-Hugoniot speed s=(uL+uR)/2; flux = uL^2/2 if s>=0 else uR^2/2
- If uL < uR (rarefaction): flux = uL^2/2 if uL>=0, uR^2/2 if uR<=0, else 0 (sonic rarefaction)

This automatically selects the entropy-satisfying weak solution.

**Time integration**: Explicit forward Euler with adaptive CFL condition dt = 0.45*dx/max|u|. This keeps the scheme stable (CFL <= 0.45 < 1 for first-order, and with MUSCL the effective CFL limit is tighter; 0.45 provides a comfortable margin).

**Boundary conditions**: Periodic, implemented via numpy.roll operations.

## Risks

1. **Stability**: The van Leer MUSCL scheme with forward Euler requires CFL <= 0.5 for stability; using CFL=0.45 gives adequate margin.
2. **Over-diffusion**: First-order Godunov alone would smear the shock over many cells; MUSCL reconstruction reduces this to O(dx^2) away from the shock.
3. **Gibbs oscillations**: The van Leer limiter is TVD, preventing oscillations near the shock. The limiter degrades gracefully to first-order in non-smooth regions.
4. **Sonic point**: The Godunov flux correctly returns 0 at the sonic point (uL < 0 < uR), avoiding entropy violations.

## Expected Output

At T=0.5 the solution should show:
- A sharp shock at x=0, jumping from u ≈ +0.9 to u ≈ -0.9 (slightly less than 1 due to characteristics not all from the extrema)
- Smooth sinusoidal-like profiles on either side
- No oscillations near the shock
- max|u| close to 1.0 (not diffused to << 1)
- L1 error vs. the Nx=4000 reference expected to be well below 0.10
