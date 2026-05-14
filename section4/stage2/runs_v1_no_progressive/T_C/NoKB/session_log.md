# Session log: T_C / NoKB

iter 1: Explicit RK4 pseudo-spectral blew up at t=0.5 (step 1000): dt=0.0005 far exceeds the v_xxx dispersive stability limit (need dt < 0.0001). Switching to Integrating Factor RK4.
iter 2: IFRK4 also blew up at t=0.5: u equation has effective k^3 stiffness via -d/dx(v_xx) coupling not handled by IF; timing test confirmed explicit RK4 with dt=0.00008 runs ~21s for 100k steps. Switching to explicit RK4 + 2/3 de-aliasing.
iter 3: Explicit RK4 with dt=0.00008 and 2/3 de-aliasing ran to T=8 successfully; final v_peak=0.6366 >= 0.5, |u_max|=3.6174 < 5, no NaN; phenomenon target met; early stop.
