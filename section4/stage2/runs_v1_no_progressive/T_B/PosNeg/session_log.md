# Session log: T_B / PosNeg

iter 1: IMEX-CN spectral with dt=2e-4, forward Euler on u equation - blow-up at t=0.69 due to u equation instability from large coupling forcing (-d/dx(3v^2+v_xx) with v~4).
iter 2: Strang splitting (exact dispersion for v_xxx) + RK4 nonlinear with dt=1e-3 - still blows up at t=1.35 because u grows to amplitude 25 without any dissipation/upwinding; pure spectral for u is unstable for this hyperbolic equation (consistent with kb-general-centralFD-hyperbolic-shockFormation).
iter 3: Strang splitting + RK4 (dt=5e-4) + Hou-Li spectral filter on u - completes T=6 run, soliton decomposition observed during t=0-5 (9-13 peaks, amps 1.7-2.8), but late-time blow-up at t~5.9 corrupts final snapshot (v_max=23, 66 spurious peaks); mass conserved exactly (drift 0%).
