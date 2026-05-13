# Reasoning Note — T_B: Gaussian Soliton Train Decomposition

## Method

**Spatial discretization:** Pseudo-spectral (Fourier) method on the periodic domain x in [-15, 15] with Nx=256 grid points. All spatial derivatives (first, second, third) are computed in Fourier space via multiplication by (ik), (ik)^2, (ik)^3 and then transformed back. This is spectrally accurate for smooth periodic fields and is the natural choice for a system containing the third-order KdV term v_xxx, which is notoriously difficult for low-order finite differences.

**Dealiasing:** 2/3-rule truncation applied after each time step — the top one-third of wavenumbers are zeroed out to suppress aliasing errors arising from the nonlinear products (u*u_x, v*v_x, u*v). This is standard practice for pseudo-spectral schemes with polynomial nonlinearities.

**Time integration:** Classic 4th-order Runge-Kutta (RK4) with a fixed small time step dt = 5e-4. This is explicit and straightforward. RK4 is well-suited here because:
- The dominant stiffness comes from v_xxx, whose spectral representation grows like k^3. With dt = 5e-4 and max |k| ~ 2*pi*128/30 ~ 26.8 rad/m, the product dt * k^3_max ~ 0.096, safely within the RK4 stability region for the imaginary axis.
- The nonlinear terms (Burgers-like u*u_x and v*v_x) add real-axis stiffness; the CFL constraint dx/|u_max| is also easily satisfied at this dt.

**Why appropriate for this PDE:** The system is a KdV-Burgers hybrid with dispersive coupling. The third-order derivative v_xxx drives soliton formation and demands spectral-quality differentiation. The periodic boundary conditions make the Fourier basis exact. The moderately short time T=6 and the expected smooth soliton structures mean that a well-dealiased pseudo-spectral + RK4 approach should faithfully capture the inverse-scattering-like decomposition of the Gaussian into a soliton train.

## Use of memory

No knowledge bank was provided. Choices are based on general PDE numerics knowledge: pseudo-spectral methods for dispersive systems (KdV literature, Fornberg 1998), the 2/3 dealiasing rule, and standard RK4 time integration.

## Risks

1. **Stability at late times:** If the Gaussian initial condition generates large-amplitude features before the solitons separate, |k|^3 growth can destabilize the explicit RK4 scheme. The dt = 5e-4 choice was made conservatively, but if amplitudes exceed ~4 significantly, a smaller dt or implicit treatment of v_xxx may be needed.

2. **Insufficient soliton separation by T=6:** The Gardner-like reduction suggests the Gaussian should decompose, but if the coupling term -d/dx(uv) slows soliton propagation or causes merging, fewer than 2 peaks with amplitude >= 0.8 may appear at the final time. The Gardner equation typically requires T > 5 for a Gaussian of amplitude 4 to produce 2+ visible solitons.

3. **Mass drift from dealiasing:** The 2/3 rule removes energy and can cause a slow drift in the integral of v. The 8% mass tolerance should be comfortably met for T=6, but aggressive dealiasing at large amplitudes could accumulate error.

4. **Aliasing in the Burgers term u*u_x:** The u-equation has a nonlinear term 3*u*u_x similar to Burgers. Without dealiasing or if u develops sharp gradients (shock-like), spectral Gibbs oscillations could contaminate the solution. The dealiasing step mitigates this, but the u-field should be monitored for pathological growth.
