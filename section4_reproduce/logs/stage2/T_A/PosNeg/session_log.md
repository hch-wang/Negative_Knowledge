# Session log: T_A / PosNeg


iter 1: Fourier pseudospectral + RK4 with NO dealiasing -> blew up at t=0.0038 (overflow in v^2, u*v, v*v_x) confirming aliasing-driven cascade per BKdV-S1-negative.
iter 2: Added 2/3 dealiasing -> integration stable, mass drift 0.63%, but v_max(T)=0.92 misses 1.0 phenomenon target by ~9%; v_max oscillates 0.8-1.3 due to dispersive fragmentation (consistent with BKdV-S7).
iter 3: IMEX-CN/midpoint on v_xxx (+ corrected v_xxx FFT sign found and applied) -> stable, mass drift 0.09%, v_max(T)=0.64, single dominant peak at x=-9.7 (2nd peak 0.24); mass+bounds phenomenon checks pass, amplitude-retention fails (consistent with BKdV-S7 m=0 manifold instability).
