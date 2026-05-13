# Round-3 Reasoning: T_B — Gaussian wave packet -> soliton train decomposition

## Pattern from r1+r2

Both rounds used Fourier pseudospectral methods with explicit nonlinear treatment, and both blew up (NaN in all 3072 output elements). Round 1 used IMEX-CN at dt=0.0005; Round 2 used IFRK4 at dt=0.0001. The common failure: the Gaussian IC has amplitude 4.0, generating v^2 terms of amplitude ~16 and d_x(3v^2) terms that are large. At dt=0.0001 these still produce O(1) increments per step in spectral space that compound exponentially. IFRK4 absorbs v_xxx exactly but its explicit RK4 stages still apply the nonlinear terms four times per step — at amplitude 4 this is worse, not better.

## New method

IMEX-Crank-Nicolson spectral with dt=0.00002 (5x smaller than round 2, 25x smaller than round 1). The dispersive term v_xxx is handled implicitly via the CN denominator 1 + (dt/2)(ik^3), which has magnitude >= 1 and is unconditionally stable. The nonlinear terms -6vv_x - d_x(uv) and -3uu_x - d_x(3v^2 + v_xx) are explicit. At dt=0.00002 the explicit CFL for the leading nonlinear mode (amplitude 4, wavenumber k ~ pi/sigma ~ 2) is 6*4*2*2e-5 = 9.6e-4 << 1, well inside the stability boundary. The 2/3 dealiasing mask removes high-wavenumber aliasing energy that can seed blow-up. A hard spectral-amplitude clip at 1e6 is included as a last-resort failsafe without altering resolved dynamics.

## Use of bank

- `kb-kdv-IMEX-CN-spectral-pass`: confirms IMEX-CN is unconditionally stable for the dispersive v_xxx term. This method passed at amplitude 2.0; our amplitude 4.0 requires a smaller dt but the same scheme structure.
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` and `kb-gardner-KdV-method-transfer-moderate-amplitude`: confirm IMEX-CN + 2/3 dealiasing is the recommended stable method for KdV-family equations and transfers across problem variants. These entries also warn that IFRK4 fails (matching r2 outcome).
- `kb-kdv-spectral-solitonAmplitude-conservation`: confirms spectral IMEX methods conserve mass and amplitude needed to detect the soliton train.

## Final risks

1. dt=0.00002 gives Nt=300,000 steps — computationally expensive but feasible in pure NumPy for Nx=256 in a few minutes.
2. The u equation is fully explicit (no v_xxx stiffness) but u starts at zero; the coupling d_x(3v^2+v_xx) will drive u to grow. At amplitude 4 this coupling is strong; the dt=0.00002 should still keep u increments small.
3. The Gaussian IC is not an exact soliton of this coupled system; soliton decomposition is the phenomenon of interest. There is a risk the coupling to u absorbs too much energy and suppresses soliton formation — but that is physics, not numerics. The method is designed to be stable so the physics can play out faithfully.
