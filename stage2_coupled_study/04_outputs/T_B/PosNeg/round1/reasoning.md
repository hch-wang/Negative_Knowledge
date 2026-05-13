# Reasoning — T_B: Gaussian wave packet → soliton train

## Method

**Spatial discretization:** Fourier pseudospectral on the periodic domain x ∈ [−15, 15], Nx = 256. All derivatives computed in spectral space (ik)^n; the 2/3 dealiasing rule is applied to every nonlinear product before transforming back to physical space.

**Time integration — v equation:** IMEX-Crank-Nicolson. The dispersive term v_xxx is handled implicitly (CN): the spectral denominator `1 − dt/2·(ik)³` has modulus ≥ 1 for all k, so the dispersive stiffness cannot cause exponential overflow regardless of dt. The explicit nonlinear terms (−6v v_x − ∂_x(uv)) are stepped with Adams-Bashforth 2 (forward Euler on step 0 for initialization).

**Time integration — u equation:** Fully explicit Adams-Bashforth 2 (forward Euler on step 0). The u equation has no v_xxx-type dispersive stiffness; only the nonlinear Burgers-like advection −3u u_x and the coupling force −∂_x(3v² + v_xx) appear. The coupling force includes v_xx which is computed spectrally and dealiased.

**Time step:** dt = 2×10⁻⁴. At IC amplitude A = 4, the effective explicit nonlinear speed for the v equation is max|6v| ~ 24, and the Nyquist wavenumber k_max = π/dx ≈ 26.8, giving a nonlinear CFL number ~ 24 × 2×10⁻⁴ × 26.8 ≈ 0.13, safely below the AB2 stability limit of ~0.7.

## Use of memory

**Adopted:**
- `kb-kdv-IMEX-CN-spectral-pass`: primary template — IMEX-CN with CN on v_xxx is unconditionally stable for dispersive stiffness and was validated for KdV at A=2, dt=5×10⁻⁴. Transferred here with reduced dt to accommodate larger amplitude.
- `kb-kdv-noDealiasing-aliasing-artifacts` and `kb-gardner-G3-noDealiasing-cubicAliasing`: mandatory 2/3 dealiasing applied to all nonlinear products; without it spurious peaks and amplitude inflation corrupt soliton counting.
- `kb-gardner-nonlinearCFL-amplitude-boundary` and `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup`: at A=4 the nonlinear CFL is far more restrictive than at A=1.5; dt was tightened from 5×10⁻⁴ to 2×10⁻⁴ accordingly.
- `kb-gardner-cubicTerm-tightens-nonlinearCFL`: estimated the nonlinear speed as max(6A) ≈ 24 and sized dt to keep the nonlinear CFL comfortably below 0.5.
- `kb-general-massConservation-insufficient-diagnostic`: diagnostic script checks peak count and amplitude, not just finiteness or mass.

**Rejected:**
- `kb-kdv-IFRK4-blowup`: IFRK4 produces NaN via exp(ik³t) overflow at high wavenumbers; rejected outright.
- `kb-kdv-explicit-RK4-stiffness-blowup` / `kb-gardner-G1-explicitRK4-finiteFrag`: explicit-only RK4 on v_xxx requires dt ~ dx³ ~ 1.6×10⁻⁴ and still fragments solitons; rejected.
- `kb-burgers-fwdEuler-centralFD-Gibbs`: plain central FD without upwinding for the Burgers-like u advection produces Gibbs blow-up; rejected in favor of spectral with dealiasing.
- `kb-burgers-LaxFriedrichs-longTime-dissipation`: Lax-Friedrichs over-diffuses at long T; rejected.

## Risks

1. **Large-amplitude explicit CFL:** The IC amplitude is A = 4, larger than any validated case in the knowledge bank (max tested A = 3 blew up in G4 with dt = 1×10⁻⁴). The chosen dt = 2×10⁻⁴ is conservative but the nonlinear CFL estimate assumes the solution amplitude does not grow beyond the IC; transient focusing during soliton formation could temporarily exceed A = 4 and destabilize the explicit nonlinear step.

2. **Soliton count uncertainty:** The Gaussian IC of amplitude 4 may decompose into more or fewer than 2 solitons depending on the coupled-system inverse-scattering spectrum. If the coupling term −∂_x(uv) drains energy from v, the resulting solitons could fall below the 0.8 amplitude threshold required by the eval criterion.

3. **Periodic domain wrapping:** Domain length is 30; at T = 6 a soliton with speed ~ 6v_max/3 ~ 8 travels ~ 48 units, enough to wrap. Soliton overlap after wrapping could merge peaks and reduce the apparent count below 2.

4. **u-equation spectral aliasing for v_xx coupling:** The coupling force −∂_x(v_xx) is fourth-order in spectral differentiation of v; high-k modes accumulate factor k⁴ which may amplify any residual aliasing energy in u even with dealiasing. This could corrupt the u field and feed back into the v coupling −∂_x(uv).
