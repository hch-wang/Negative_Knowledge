# Session log: T_A / NoKB

iter 1: Fourier pseudospectral + explicit RK4 blew up at t=0.003 due to KdV v_xxx stiffness (k_max^3~19267 requiring dt<5e-5); switching to ETD method.
iter 2: ETD-RK4 with A=U-V decoupling reached t=2 with correct 2/3 dealiasing but u grew to 5.5 and blew up; aliasing bug (wrong dealiasing mask) discovered and fixed; method still unstable long-term.
iter 3: scipy RK45 adaptive + spectral hyperviscosity (eps=1e-7) completed T=8 successfully with no blow-up; soliton travels and preserves single-peak structure, mass conserved perfectly, but amplitude decayed from 2.0 to 0.64 (32%) due to energy transfer from v to u driven by the 0.2*v perturbation.
