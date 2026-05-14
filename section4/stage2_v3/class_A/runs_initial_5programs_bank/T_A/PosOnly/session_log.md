# Session log: T_A / PosOnly

iter 1: E1 — baseline Fourier pseudospectral (no dealiasing) + explicit RK4, dt=1e-4, on coupled BKdV with v0=2 sech^2(x+5), u0=0.5 v0^2+0.2 v0, T=8. Result: ALIASING BLOWUP at t=0.5, sup_u=2.2e6 — expected baseline failure mode.
iter 2: E2 — single-component upgrade: added 2/3-rule dealiasing on all nonlinear products (kept RK4, dt, Nx). Result: v sector clean (mass conserved <1e-14, max_v=1.45 at T=8 > 1.0 threshold) but sup_u grew to 20.8, violating |u|<15 due to Burgers steepening of the u-eqn at the resolved-band edge.
iter 3: E3 — single new component on top of E2: weak spectral hyperviscosity on u only (p=4, nu_h=5e-10 such that rate at k_cut ~5/time-unit, k<=5 untouched). Result: ALL four phenomenon targets met: max_v(T)=1.013 >= 1.0, mass_v drift=0, sup_u=9.49<15, sup_v=1.01<15. Stopping early as useful.
