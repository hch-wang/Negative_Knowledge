# Session log: T_C / PosOnly

iter 1: E1 bare Fourier-pseudospectral + RK4 (no dealiasing, dt=5e-4) — blew up at t=0.003 from undealiased v^2 + sharp bore aliasing into v_xxx; F1 negative.
iter 2: E2 added 2/3 dealiasing on all nonlinear products — stable to T=8, mass conserved to machine precision, but v_peak=0.4733 (<0.5 target) and u_min growing to -2.55 from bore Gibbs; F2 partial.
iter 3: E3 added linear u-viscosity nu*u_xx (nu=5e-2) per BKdV-S6 dispatcher hint — v_peak=0.5019 (>=0.5 PASS), u_max=1.43 (<5 PASS), mass conserved, soliton transmits with ~67% amplitude loss; F3 positive, stop_useful.
