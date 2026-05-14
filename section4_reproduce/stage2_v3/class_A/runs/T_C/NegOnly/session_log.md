# Session log: T_C / NegOnly

iter 1: E1 baseline (Fourier pseudospectral + 2/3-rule dealiasing + explicit RK4, NO u-viscosity, dt=2e-4, Nx=256, T=8) — finite but bore self-steepens explosively per BKdV-S6 prediction: u_max 1.5 -> 11.4 transient / 9.66 final (fails |u_max|<5), TV(u) 1.5 -> 320, v fragmented into 11 peaks. Phenomenon target failed.
iter 2: E2 single-component upgrade — add explicit linear viscosity nu*u_xx on u-equation only, nu=5e-2 (BKdV-S6 deep-synthesis empirical floor). Result clean: u_max bounded <=3.33 throughout / 2.18 final, v_max_final=0.63 > 0.5, TV(u) bounded 20-40, mass conserved. Phenomenon target met; stopping early.
