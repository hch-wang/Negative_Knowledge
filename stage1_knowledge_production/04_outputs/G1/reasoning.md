# Reasoning: Stress Test G1 (Gardner / Explicit RK4)

## Method as written
I implemented explicit RK4 time integration with standard 2nd-order central finite differences for all spatial derivatives (first and third). The grid is uniform with Nx=256 on x in [-15,15] with periodic boundary conditions enforced via `np.roll`. Time step is dt=1e-5.

## Predicted vs expected
I agree with the predicted blow-up/distortion outcome. The third-derivative dispersive term v_xxx introduces a stiffness constraint dt ~ O(dx^3), which for Nx=256 and dx~0.117 gives a stability threshold around dt ~ 1.6e-4; however, the additional nonlinear cubic term (3/2)v^2 v_x with amplitude 1.5 tightens this further. At dt=1e-5 the run may narrowly survive, but the combination of the cubic nonlinearity amplifying high-frequency modes and the stiffness of the third-derivative operator makes blow-up very plausible even at this small time step — and any dt larger than ~1e-5 would certainly blow up rapidly.

## What knowledge this might produce
A future agent tackling Gardner/KdV-family PDEs should learn that explicit RK4 with central FD for v_xxx is conditionally stable but requires extremely small dt (O(dx^3)), making it computationally impractical for even moderate final times; implicit or integrating-factor/ETD methods that handle the stiff linear dispersive part implicitly are essential for efficiency and robustness on this problem class.
