# Session log: T_B / PosOnly

iter 1: E1 baseline = Fourier pseudospectral (no dealiasing) + classical RK4, dt=1e-4, Nx=256, T=6.0. Blew up at t~0.28 (aliasing of quadratic products at amp=4). Negative finding.
iter 2: E2 = E1 + 2/3-rule dealiasing on all nonlinear products (single-component upgrade). Reached T=6.0 cleanly; final v has 10 well-separated peaks each >0.8, mass conserved to ~3e-16. Phenomenon target met; stopped early.
