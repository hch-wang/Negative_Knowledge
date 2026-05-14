# Session log: T_A / PosOnly

iter 1: IMEX-CN spectral (v_xxx implicit, u explicit) blew up at t=0.974 due to Burgers shock formation creating Gibbs oscillations in u; bug-fixes to numpy API and coupling evaluation same iteration.
iter 2: MUSCL-van Leer + Godunov for u Burgers + IMEX-CN for v via operator splitting reached T=8 stably but v_final amplitude=0.358 (below 1.0 threshold) due to excessive TVD numerical diffusion.
iter 3: Monolithic IMEX-CN spectral with implicit spectral hyperviscosity (eps=1e-7, p=8) for u — all targets met: v_final_amp=1.298>=1.0, mass drift 0.00%, u_max=1.56 and v_max=1.30, both bounded below 15.
