# Reasoning: T_C Burgers Bore / KdV Soliton Interaction

## Method

**Spatial discretization:** Pseudo-spectral (Fourier) on the periodic domain [-15, 15] with Nx=256 points. All spatial derivatives (first through third order) are computed via FFT with the standard spectral derivative formula d^n/dx^n → (ik)^n in Fourier space. A 2/3-rule (Orszag) dealiasing mask zeroes out the top third of wavenumbers before multiplying, suppressing aliasing errors that arise from the nonlinear products (u u_x, v v_x, d/dx(u v), d/dx(3v^2)).

Pseudo-spectral is appropriate here because:
- The domain is periodic (required for FFT consistency).
- KdV solitons are smooth, so spectral methods converge exponentially for smooth solutions. The bore is smoothed (tanh transition width 0.5), so it is also well-resolved spectrally.
- Third-order derivatives (v_xxx, v_xx inside the u equation) are trivially exact spectrally; finite-difference third-order stencils introduce significant dispersive error that would corrupt the soliton shape.

**Time integration:** Classical 4th-order Runge-Kutta (RK4) with a fixed small time step dt = 0.002. This gives 4000 steps over T=8. RK4 is explicit, easy to implement with only numpy/scipy, and has sufficient accuracy for smooth solutions. The step size is chosen conservatively relative to the dispersion stability constraint for the third-derivative term: roughly dt < C dx^3 / max|coeff|. With dx ≈ 0.117 and dt=0.002 the ratio dt/dx^3 ≈ 1.24 is comfortably within stability.

**Output:** 8 snapshots equally spaced from t=0 to t=8, capturing the soliton approach, encounter with the bore, and post-interaction state.

## Use of memory

No knowledge bank was provided. Method choices rely on general PDE numerics knowledge: spectral methods for periodic dispersive equations (KdV literature), 2/3-rule dealiasing for pseudo-spectral Navier-Stokes/KdV codes, and RK4 as a robust default explicit integrator.

## Risks

1. **Shock formation in u (Burgers component):** The u equation has a nonlinear advection term 3 u u_x that can steepen the bore into a near-discontinuity. Spectral methods produce Gibbs oscillations near steep gradients; these can contaminate v through the coupling term. Dealiasing mitigates but does not eliminate this.

2. **Dispersive blow-up / instability:** The v_xxx term and the coupled u v source can interact to create growing modes if the time step is even slightly too large for the spectral stability bound. A blow-up would produce |v_max| >> initial amplitude, violating both the boundedness and peak-amplitude criteria.

3. **Soliton amplitude loss through numerical dissipation or resonance:** RK4 has no artificial dissipation, but time-stepping errors over 4000 steps could slowly degrade the soliton. Additionally, if the soliton resonantly transfers energy to the bore via the coupling, the peak could drop below 0.5. The initial amplitude of 1.5 provides a factor-of-3 safety margin.

4. **Phase error accumulating over T=8:** The soliton travels roughly 6*1.5 * 8 = 72 units in isolation (KdV speed = 6A for unit-coefficient KdV, but here coefficient is 6 so speed ≈ 6*1.5=9 giving ~72, but domain is only 30 wide). The soliton will wrap around the periodic domain; if the bore-interaction wraps unexpectedly, the final snapshot might show the soliton far from the bore, but the peak check only requires amplitude >= 0.5, so location does not matter.
