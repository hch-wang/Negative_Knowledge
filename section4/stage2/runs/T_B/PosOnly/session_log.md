# Session log: T_B / PosOnly

iter 1: E1 (Fourier-pseudospec + explicit RK4, NO dealiasing): blew up at t=0.42, overflow first appears in v*v product. Aliasing-driven nonlinear instability confirmed.
iter 2: E2 = E1 + single-component upgrade (add 2/3-rule dealiasing on all nonlinear products): completed T=6 with mass drift -0.6% and 14 well-separated peaks >= 0.8 amplitude. Phenomenon target met. Stop early.
