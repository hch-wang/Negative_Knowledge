# Session log: T_A / PosNeg

iter 1: IMEX-CN with explicit u (Euler) blew up immediately — d_x(v_xx)=v_xxx in u RHS is stiff and must be treated implicitly; also wrong CN signs in v update caused spurious dispersion.
iter 2: Fixed CN v_xxx source for u, but TWO bugs remained: (a) IMEX-CN sign convention was swapped causing soliton to disperse into 16 peaks at t=0.5; (b) 3uu_x central spectral differencing caused Burgers shock blow-up at t~2.2 — both identified via diagnostic traces.
iter 3 (E3, bugfix of E2): Fixed IMEX-CN signs to match kb-kdv-IMEX-CN-spectral-pass validation (amplitude=2.03 at T=2); added low-pass filter for u (keeping 10% of k-modes) to prevent Burgers shock — soliton in v survives to T=8 with amplitude 2.09 (ratio=1.047), single dominant peak, mass conserved.
