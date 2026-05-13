# Reasoning: KdV Stress Test A4

## Method as written

I implemented explicit RK4 (classical 4th-order Runge-Kutta) time integration with standard 2nd-order central finite differences for both the first derivative (v_x) and third derivative (v_xxx), on a periodic domain with Nx=256. No implicit, IMEX, integrating-factor, or ETD components are used.

## Predicted vs expected

I agree with the predicted outcome of blow-up. The third-derivative term v_xxx with central FD introduces a stiffness eigenvalue of O(1/dx^3) ~ O(2000) for this grid. Even with the aggressive time step dt=1e-5, the stability region of explicit RK4 (~2.8 in magnitude for the imaginary axis) cannot encompass purely imaginary eigenvalues of this magnitude from the dispersive v_xxx term. Blow-up (NaN/Inf) is expected, likely very early in the integration. The only way to potentially survive would require dt ~ dx^3 / C which at Nx=256 means dt ~ 1.6e-6, making the computation prohibitively expensive and still likely to fail due to round-off accumulation.

## What knowledge this might produce

A future agent encountering KdV or similar dispersive PDEs should recognize that explicit time-steppers applied to the third-derivative stiffness term will blow up unless an integrating-factor or ETD/spectral method is used, or an implicit treatment of v_xxx is adopted. This run quantifies the failure mode, confirming that the stiffness of dispersive operators is not merely theoretical — it causes immediate numerical blow-up in practice at typical resolutions.
