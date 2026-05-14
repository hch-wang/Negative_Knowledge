# Session log: T_A / NegOnly

iter 1: E1 baseline (pseudospectral, NO dealiasing, explicit RK4, dt=5e-5) blew up at t~0.5-0.75 with overflow in nonlinear products and NaN through FFT. max|v|=2.04, max|u|=3.24 at t=0.5 — aliasing-driven growth then collapse.
iter 2: E2 added 2/3 dealiasing (one component change). Survived to T=8 with mass(v) conserved to machine precision. Single dominant peak at x=-9.73 with amplitude 0.635 — below the 1.0 target. Decay appears physical (driven by 0.2v perturbation from m=0 Gardner reduction).
iter 3: E3 reduced dt 2.5x to 2e-5 (one component change). Output matches E2 to 2e-8 across all snapshots — confirms the amplitude decay is genuine physics, not RK4 truncation. Final state retained as the answer in pred_results/T_A.npy.
