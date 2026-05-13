# G2 Reasoning

## Method as written
Fourier pseudo-spectral spatial discretization on the periodic domain [-15, 15] with Nx=256 modes. Time integration uses IMEX Crank-Nicolson: the linear dispersive term v_xxx is treated implicitly via the exact Fourier multiplier -ik^3 with Crank-Nicolson averaging (dt=0.0005), while the nonlinear terms 6vv_x and (3/2)v^2 v_x are treated explicitly (forward-Euler in spectral space). A 2/3 dealiasing mask is applied to both the input fields and the nonlinear product before advancing.

## Predicted vs expected
Agreement with the prediction is moderate. The initial condition 1.5 sech^2(x+5) is not an exact Gardner soliton (the Gardner soliton has a more complex amplitude-velocity relationship than pure KdV), so the wavepacket will partially radiate small-amplitude dispersive tails while the bulk remains roughly compact and mass-like conserved. The CN implicit treatment of v_xxx should keep the dispersion stable. The explicit treatment of the stronger combined nonlinearity (KdV + mKdV cross-term) may introduce mild growth near peak amplitude if the nonlinear CFL is tight, but with dt=0.0005 and Nx=256 this should remain within acceptable bounds. Overall: stable propagation with minor radiative shedding is the expected and agreed outcome.

## What knowledge this might produce
A future agent tackling Gardner / Burgers-swept-KdV or coupled dispersive problems can learn that IMEX-CN with spectral dealiasing provides stable integration of the linear dispersive backbone at low cost, while the explicit treatment of composite nonlinearities (mixed KdV/mKdV) is viable if dt is kept small relative to the nonlinear CFL. The run also illustrates the importance of 2/3 dealiasing when two nonlinear terms of different polynomial degree are present simultaneously.
