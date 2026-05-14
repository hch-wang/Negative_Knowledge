# Session log: T_A / PosOnly

start: read prompt + memory bank (10 positive entries); plan E1 as simplest meaningful baseline (Fourier pseudospectral, no dealiasing, explicit RK4) per progressive-complexity discipline.
iter 1: ran E1 (Fourier pseudospectral + RK4, no dealiasing, dt=1e-4). Mass(v)=4.0 conserved up to t=1.0 but |v|_inf rapidly decayed (2.0 -> 0.86) and simulation blew up to NaN at t~1.5. Failure mode = aliasing in quadratic nonlinearities (v^2, uv, vv_x), not dispersive stiffness.
iter 2: ran E2 = E1 + 2/3-rule dealiasing (single-component upgrade), dt=1e-4 unchanged. Stable to T=8.0, mass(v)=4.0 conserved exactly, |u|,|v| bounded < 2. But final peak max(v)=0.917 at T=8 (below 1.0 threshold). Peak amplitude oscillates 0.86-1.21 throughout [1,8], indicating dispersive breather/radiation regime; 11 local maxima > 0.3 at final time -- multi-modal radiation pattern.
iter 3: ran E3 = E2 with IMEX-CN(disp) + Heun(nonlinear), dt=5e-4 (intended single-component change but inadvertently also raised dt 5x). Blew up at t=5.5 because v_xxx appears explicitly in u-equation and dt*k_max^3=9.6 violates RK2 stability. Rolling back to E2 as final answer; restoring candidate.py and regenerating pred_results/T_A.npy.
finalize: restored candidate.py to E2 method; re-ran to regenerate pred_results/T_A.npy (no new experiment). Wrote reasoning.md with final self-assessment.
