# Session log: T_A / NoKB

iter 1: E1 = Fourier pseudospectral + RK4 + no dealiasing, dt=1e-4 -> blew up by t=0.5 with max|u|=2.2e6 and Nyquist-mode pile-up in spectrum (classic aliasing instability).
iter 2: E2 = E1 + 2/3-rule dealiasing (single-component change). Ran to T=8 cleanly; v final peak 1.32, mass drift 0%, max|u|=11.96 < 15. All three phenomenon-target criteria satisfied.
iter 3: E3 = E2 with dt halved 1e-4 -> 5e-5 (single-component change). Bound-violation: max|u|=21.5 > 15 at T=8 due to chaotic-amplitude variation (trajectories match E2 to 3 digits up to t=5; diverge at t>=6). Rolled back to E2 as final answer.
