# Reasoning: T_A Coupled Burgers-swept-KdV Soliton Stability

## Method

**Spatial discretization:** Pseudo-spectral method using the Fast Fourier Transform (FFT) on the periodic domain x in [-15, 15] with Nx=256 grid points. All spatial derivatives (u_x, v_x, v_xx, v_xxx) are computed exactly in Fourier space by multiplying by (ik)^n, then transforming back. A standard 2/3-rule dealiasing mask is applied to suppress aliasing errors from the nonlinear terms (u*u_x, v*v_x, u*v). This is appropriate for this PDE because both equations contain dispersive terms (v_xxx) and nonlinear convective terms; spectral methods provide spectral accuracy for smooth solutions and handle dispersion precisely.

**Time integration:** Classical 4th-order Runge-Kutta (RK4) with a fixed timestep dt=5e-4. The timestep is chosen small enough to satisfy the CFL-like constraint from the nonlinear wave speed (peak amplitude ~2) and the dispersive stability condition from the v_xxx term (dt ~ dx^3 for explicit schemes on KdV). With dx = 30/256 ~0.117, we need dt << dx^3/6 ~ 2.7e-4 for pure KdV; dt=5e-4 is slightly above this but the 2/3 dealiasing removes the highest modes most prone to dispersive instability. Snapshots are saved at n=9 evenly-spaced times from t=0 to t=8.

## Use of Memory

No knowledge bank was provided. Choices are based on general PDE numerics: spectral methods are the standard choice for periodic KdV-type equations, and RK4 is reliable for stiff-free time integration at moderate T.

## Risks

1. **Dispersive instability:** The v_xxx term is treated explicitly. If dt is too large relative to dx^3, high-frequency modes can blow up. The 2/3 dealiasing partially mitigates this by removing the top third of modes, but the timestep may still be marginal.

2. **Aliasing from nonlinear coupling:** The cross terms u*v and u*u involve products in physical space; without dealiasing they alias onto lower modes. The 2/3 rule helps but is not a guarantee for the Burgers-type u*u_x term which can form shocks. If u develops near-shock structure, spectral accuracy degrades and Gibbs oscillations may corrupt the solution.

3. **Soliton phase drift and mass drift:** The perturbation (0.2*v term in u IC) breaks the exact m=0 Gardner reduction. Radiation may be emitted, shifting soliton speed and causing slow amplitude decay. If the radiated energy is large, the peak may fall below the 0.5*2.0=1.0 threshold, failing the eval criterion.

4. **Periodic boundary interactions:** The soliton starts at x=-5 and travels rightward. With T=8 and soliton speed ~6 v_peak = 12, it may traverse the domain once or interact with its own periodic image, potentially causing spurious amplitude change or mass drift beyond 8%.
