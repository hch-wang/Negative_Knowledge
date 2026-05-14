# Session log: T_B / NegOnly

iter 1: IMEX-CN (v implicit, u explicit Euler), dt=2e-4 -- NaN blow-up at t=1.2 due to stiff -v_xxx coupling in u equation not stabilized.
iter 2: IMEX-CN with w=u-v change of variables (no stiff linear term in w equation), explicit Euler for w, dt=2e-5 -- blow-up at t=3.9 due to explicit Euler unconditional instability on imaginary eigenvalues.
iter 3: Strang+RK4 with w=u-v, spectral filter sigma=exp(-50*(k/k_max)^8), dt=2e-5 -- SUCCESS: 5 soliton peaks >= 0.8 in v_final, mass drift = 0.000%, all 61 snapshots finite.
