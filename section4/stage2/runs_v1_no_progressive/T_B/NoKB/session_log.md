# Session log: T_B / NoKB

iter 1: IFRK4 pseudospectral with u0=0, v0=4*Gaussian; u blows up at t~1 due to unregularized Burgers nonlinearity; system is off the Gardner reduction.
iter 2: Gardner reduction IC u0=v0^2/2 attempted; u field grows from 8 to 17 and forms Burgers shock by t~0.35; NaN regardless of dt reduction.
iter 3: IFRK4 with epsilon=0.05 artificial viscosity on u, u0=0, v0=Gaussian; stable to T=6; 5 soliton peaks >= 0.8, mass drift 0%, phenomenon target satisfied.
