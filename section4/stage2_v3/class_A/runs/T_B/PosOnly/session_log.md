# Session log: T_B / PosOnly

iter 1: E1 Fourier pseudospectral + RK4, no dealiasing, dt=2e-4. Blowup at t=0.0056 (step 28) — aliasing of v^2, uv at amp=4 Gaussian. Negative finding.
iter 2: E2 add 2/3-rule dealiasing (single-component upgrade per BKdV-S1 r1/r2 bank entries). Reached T=6 cleanly, mass_v drift 0.0%, |v|_inf=4.85, final v has 15 peaks above 0.8 — phenomenon target met. Early stop.
