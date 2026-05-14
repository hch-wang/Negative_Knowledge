# Session log: T_B / PosNeg


iter 1: E1 baseline Fourier+2/3-dealias+explicit RK4, dt=1e-4, T=6 reached, no NaN, mass conserved; clean 2-3 peak train at t<=3.5 but u runs away (range [-12,9]) after t~4 and v develops -3.2 dips with grid-scale spikes — late-time field numerically contaminated despite passing literal eval.
iter 2: E2 same stack + linear viscosity nu=5e-2 on u_t only (single-component upgrade); T=6 reached cleanly, u and v both bounded throughout, final v shows 5 well-separated peaks of amplitude 0.81/0.84/0.88/0.96/1.79 (target >=2 met), mass(v) drift 9e-6 percent, spectral edge in top quarter band 8e-8. Useful=True, stop early.
