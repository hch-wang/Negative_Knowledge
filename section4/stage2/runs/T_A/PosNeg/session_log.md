# Session log: T_A / PosNeg

iter 1: E1 Fourier pseudospectral + explicit RK4 (dt=5e-5, no dealiasing). BLEW UP at t=0.605 (|v|max~3.6e32). Aliasing+stiffness explosion exactly as bank predicted.
iter 2: E2 single change = swap RK4 for IMEX-CN (CN on v_xxx, explicit on rest). BLEW UP at t=0.609 with mass(v) preserved at 4.0 but 126 spurious peaks. IMEX-CN fixed dispersion; aliasing still kills it.
iter 3: E3 single change = add 2/3 dealiasing to all nonlinear products. Clean physics through t=2.0 (|v|max=1.46, mass=4.0, single peak); u then grows from 2.4 -> 6.07 -> 12.79 and blow-up at t=2.23 — Burgers-side shock formation in u. Cannot upgrade to MUSCL/Godunov (would be 4th iteration).
