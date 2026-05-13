# Reasoning: T_C Burgers Bore + KdV Soliton

## Method

**Spatial discretization:** Fourier pseudospectral on the periodic domain [-15, 15] with Nx=256. All spatial derivatives (u_x, v_x, v_xx, v_xxx) are computed via FFT multiplication by ik or ik^3. 2/3 dealiasing is applied to nonlinear products (u*u_x, v*v_x, v^2, u*v) to suppress aliasing errors.

**Time integration:** IMEX-Crank-Nicolson with dt=0.0005 (Nt~16000 steps):
- The dispersive stiffness term v_xxx is handled **implicitly** via Crank-Nicolson: the CN denominator (1 + dt/2 * ik^3) has magnitude >= 1, guaranteeing unconditional stability for the dispersive operator regardless of dt. This avoids the severe CFL constraint that explicit treatment of v_xxx would impose (dt < C * dx^3 ~ 1e-6 for Nx=256).
- All nonlinear terms (3u*u_x, 6v*v_x, coupling terms -dx(3v^2+v_xx) and -dx(uv)) are handled **explicitly**.
- The u equation has no dispersive term and is advanced with a forward Euler step (consistent with the IMEX split).

This combination is appropriate because: (1) the KdV-like dispersive stiffness of v requires implicit treatment; (2) the Burgers bore in u has no dispersive stiffness and explicit treatment is sufficient; (3) pseudospectral methods resolve both the sharp bore transition and the smooth soliton profile with spectral accuracy.

## Use of Memory

**Adopted:**
- `kb-kdv-IMEX-CN-spectral-pass`: Primary justification for IMEX-CN on the v equation. Validated for KdV soliton amplitude=2, T=2 with dt=0.0005, Nx=256 on the same domain. The CN denominator argument for unconditional dispersive stability is directly from this entry.
- `kb-kdv-spectral-solitonAmplitude-conservation`: Confirmed spectral IMEX methods conserve soliton amplitude within ~2% — critical for meeting the amplitude >= 0.5 survival criterion.
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`: Confirmed that IMEX-CN + 2/3 dealiasing is stable for amplitude 1.5 IC (same as our v IC) over T=2. Also warned that KdV sech^2 IC is not a true Gardner soliton and will radiate — relevant because the initial v is a KdV soliton, which may radiate when it hits the bore and enters the coupled system.
- `kb-gardner-KdV-method-transfer-moderate-amplitude`: Confirmed positive transfer of IMEX-CN from KdV to Gardner at amplitude 1.5. Our system is more complex but the stability argument carries over.

**Considered but not adopted:**
- `kb-burgers-MUSCL-Godunov-shock-pass` and `kb-general-firstOrder-Godunov-preShock-baseline`: These finite-volume schemes would be appropriate for a pure Burgers solver, but in a pseudospectral framework for the coupled system, switching to a finite-volume stencil for u while using spectral methods for v would create inconsistency. The Burgers nonlinearity in the coupled system is treated explicitly with spectral derivatives, which is sufficient given the coupling terms are smooth.
- `kb-shallowWater-LaxFriedrichs-stable-smeared` and `kb-shallowWater-HLL-dam-break-pass`: Not applicable — these are finite-volume methods for a different system (shallow water); not needed here.
- `kb-kdv-smallAmplitude-dispersiveRegime`: Useful as a diagnostic (post-interaction v amplitude O(0.1) signals dispersive radiation rather than soliton survival), but does not influence method choice.

## Risks

1. **Bore shock and Gibbs oscillations in u:** The Burgers bore creates a near-discontinuity in u. Fourier pseudospectral methods develop Gibbs oscillations near sharp gradients. The 2/3 dealiasing mitigates but does not eliminate this. If u develops large oscillations near the bore, the coupling term -dx(uv) will be polluted, potentially corrupting the soliton amplitude.

2. **Operator splitting error / IMEX instability from large coupling:** The coupling terms -dx(3v^2 + v_xx) and -dx(uv) are treated explicitly. If u or v develop large amplitudes (e.g., bore steepening), the explicit coupling may become stiff and require smaller dt. At dt=0.0005 this risk is moderate for the given amplitudes.

3. **Soliton radiation:** As noted in `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`, a KdV sech^2 IC at amplitude 1.5 is not a true soliton of the coupled system; it will shed radiation. After encountering the bore, the surviving peak amplitude may fall below 0.5. This is a physics risk rather than a numerical one.

4. **Periodic domain reflections:** The soliton starts at x=-8 moving rightward. After transmission through (or reflection from) the bore near x=0, it may re-enter the bore from the other side via periodic wrapping at T=8. This secondary interaction could complicate the evaluation, though the amplitude check is on the final state only.
