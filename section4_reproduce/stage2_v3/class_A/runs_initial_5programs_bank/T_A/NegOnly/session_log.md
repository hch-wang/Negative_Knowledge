# Session log: T_A / NegOnly

iter 1: E1 baseline Fourier+RK4 with NO dealiasing blew up at step 6123/80000 (t~0.61) via overflow in v*v and u*v then NaN -- confirms BKdV-S1 (deep, depth=3) aliasing-cascade prediction.
iter 2: E2 single-component upgrade (add 2/3 dealiasing, keep RK4 and dt=1e-4) ran cleanly to T=8: stable, mass(v) exactly conserved, |u|<=6.03 and |v|<=0.64 well within |max|<15 bound, but v_peak monotonically decayed from 2.0 to 0.6351 (below the >=1.0 phenomenon target).
iter 3: E3 single-component change (dt halved to 5e-5, same method) reproduces E2 end-state to 4 decimal places -- confirms dt-convergence and that v_peak decay is PHYSICAL (off-manifold radiation per BKdV-S5 depth=3), not numerical. n_local_maxima(v_T > 0.5*max)=1 so a single coherent decayed peak survives.
