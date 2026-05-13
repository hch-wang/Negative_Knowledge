# Round-2 Reasoning

## Method

Fourier pseudospectral spatial discretization on the periodic domain [-15, 15] with Nx=256. For the v equation, the dispersive term v_xxx is handled exactly via an Exponential Time Differencing RK2 (ETD-RK2) integrating factor in spectral space: the linear operator L = -ik^3 is exponentiated exactly, so E = exp(L*dt) has modulus 1 and cannot overflow or destabilize regardless of dt. The nonlinear terms (6*v*v_x and the coupling -(uv)_x) are treated explicitly with a midpoint RK2 stage. For the u equation, a forward-Euler-style midpoint scheme handles the explicit -3*u*u_x - d_x(3v^2 + v_xx) terms. The 2/3 dealiasing mask is applied to all nonlinear products. Time step dt = 4e-5 (total ~150,000 steps), chosen to satisfy the nonlinear CFL for amplitude-4 initial data.

## Use of r1 finding

Round 1 used IMEX-Crank-Nicolson with the dispersive term in the CN denominator. For amplitude 4, the nonlinear explicit CFL constraint is max|6v + coupling| ~ 24-30 at peak amplitude, requiring dt ~ O(1e-4) or smaller. The round-1 dt = 2e-4 was already marginal, but the actual blow-up came from the explicit nonlinear terms overflowing first (the exec.log shows "overflow encountered in multiply" in the nonlinear products before the CN step could stabilize anything). The CN approach only stabilizes the dispersive term, not the nonlinear advection. Round 2 replaces CN with ETD (exact integrating factor), which is equivalent for the linear part but more numerically clean, and uses a smaller dt = 4e-5 to tighten the nonlinear CFL margin significantly.

## Use of bank

- **kb-gardner-nonlinearCFL-amplitude-boundary**: Critical. Established that the nonlinear CFL limit scales as dt * max(6A + 1.5A^2) * k_Nyq. For A=4 in the v equation, the effective nonlinear speed is O(6*4) = 24 for the KdV-like term; k_Nyquist ~ 26.8. Safe dt ~ 0.5/(24*26.8) ~ 7.8e-4 — but with amplitude 4 being larger than any tested case in the bank, I use dt = 4e-5 (20x safety margin).
- **kb-kdv-noDealiasing-aliasing-artifacts**: Confirmed 2/3 dealiasing is essential; without it, spurious peaks inflate amplitude and create false solitons. Applied to all nonlinear products.
- **kb-kdv-IFRK4-blowup**: Warns that naive integrating-factor methods fail without careful dealiasing. ETD-RK2 with explicit dealiasing avoids this.
- **kb-kdv-IMEX-CN-spectral-pass**: Confirms spectral IMEX works for KdV at A=2, dt=5e-4. Amplitude 4 here is 2x larger, requiring tighter dt per nonlinear-CFL scaling.
- **kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup**: Direct evidence that amplitude doubling can cause blow-up even with reduced dt; confirms aggressive dt reduction is necessary at A=4.
- **kb-general-centralFD-hyperbolic-shockFormation**: Reinforces that central FD alone is catastrophic; spectral method with dealiasing + ETD is the correct approach.

## Risks

1. **Nonlinear CFL at A=4 may still be tight**: The Gaussian initial amplitude is 4, which is larger than any validated case in the bank (max tested was A=3 in Gardner, which blew up at dt=1e-4). Using dt=4e-5 provides ~20x margin below the naive CFL estimate, but the coupled system has additional cross-terms (-d_x(3v^2 + v_xx) in the u equation) that could introduce further stiffness. The clipping safeguard at ±50 provides a last-resort guard.

2. **Soliton decomposition may not produce >= 2 peaks by T=6**: KdV inverse scattering theory predicts that a Gaussian with amplitude 4 should decompose into multiple solitons (the eigenvalue count depends on L/2 where the "potential" scales with amplitude). However, the coupling to u (which starts at 0 but evolves) may alter the decomposition dynamics compared to pure KdV. If the coupling dissipates energy or changes phase speeds, fewer peaks may emerge above the 0.8 threshold.

3. **Periodic boundary effects**: At T=6 the fastest soliton (speed ~ 6*A_soliton for the largest eigenstate) could travel O(6*4*6) = 144 units, far exceeding the domain length of 30. The fastest soliton will wrap around multiple times, potentially causing collision artifacts with slower ones that corrupt the peak count evaluation.
