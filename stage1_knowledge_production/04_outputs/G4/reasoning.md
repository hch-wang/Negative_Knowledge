# Reasoning: Stress Test G4

## Method as written
I implemented an IMEX-CN (Implicit-Explicit Crank-Nicolson) spectral scheme: the linear dispersive term v_xxx is treated implicitly via Crank-Nicolson in Fourier space (unconditionally stable for that part), while the nonlinear terms 6 v v_x + (3/2) v^2 v_x are handled explicitly at each step. The time step is dt=1e-4 over T=2.0, using Nx=256 Fourier modes on the periodic domain [-15, 15].

## Predicted vs expected
I agree with the predicted outcome. The initial condition v_0 = 3.0 sech^2(x+5) is the standard KdV soliton form with amplitude A=3, which gives KdV phase speed c=2A=6. However, in the Gardner equation the cubic nonlinearity (3/2) v^2 v_x becomes O(A^3)=O(27) at amplitude 3, which is large compared to the quadratic term 6 v v_x ~ O(6A)=O(18). This means the initial profile is far from the Gardner soliton equilibrium shape. The wave will deform: it is likely to shed radiation, possibly split into multiple Gardner solitons of different amplitudes, and the peak will not propagate at the KdV-predicted speed c=6. Shape asymmetry and a radiative tail behind the main wave are expected.

## What knowledge this might produce
A future agent solving Gardner or coupled dispersive equations can learn that using a KdV-matched IC at large amplitude (where the cubic term is not negligible) is an excellent stress test precisely because it guarantees nonlinear mode coupling from the start — the run quantifies how quickly the wave deforms and how large the radiative component grows. This provides ground-truth reference data for validating whether a proposed Gardner soliton solver correctly handles the cubic term's contribution to the phase speed and shape, rather than silently reverting to KdV-like behavior.
