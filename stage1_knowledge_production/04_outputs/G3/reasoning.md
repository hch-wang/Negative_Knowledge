# Reasoning: G3 Gardner / Spectral IMEX without Dealiasing

## Method as written
Fourier pseudo-spectral discretization on a 256-point periodic grid over [-15, 15], with IMEX Crank-Nicolson time integration (dt = 0.001): the linear dispersion term v_xxx is treated implicitly (Crank-Nicolson), while the nonlinear terms -6vv_x and -(3/2)v^2 v_x are evaluated explicitly in physical space with no 2/3 dealiasing or low-pass filter applied.

## Predicted vs expected
I agree with the predicted outcome. The cubic nonlinearity v^2 v_x generates aliases at up to 3x the Nyquist wavenumber, compared to the quadratic 6vv_x term which aliases at 2x. Without dealiasing, these high-wavenumber aliases fold back into the resolved modes and accumulate each time step, causing spurious small-scale energy growth. This is strictly worse than the KdV-without-dealiasing case (A5), which only had the quadratic aliasing source. The result is likely amplitude inflation at high wavenumbers, possible spurious oscillations, and potentially a delayed (or accelerated) blow-up depending on whether the phase errors from the aliased modes constructively interfere with the soliton.

## What knowledge this might produce
A future agent tackling Gardner, Burgers-swept-KdV, or other dispersive equations with polynomial nonlinearities higher than quadratic should recognize that dealiasing budget scales with nonlinearity order and is not optional for long-time accuracy. This run quantifies the error penalty for omitting dealiasing on a cubic nonlinearity, providing a concrete baseline to compare against properly dealiased or filtered runs.
