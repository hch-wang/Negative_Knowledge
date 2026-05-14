# Session log: T_A / NegOnly

iter 1: IMEX-CN baseline (v_xxx implicit, u fully explicit, dt=5e-4) — NaN blow-up due to stiff -v_xxx forcing on u equation from v_xx coupling.
iter 2: Operator-split IMEX-CN (v_xxx CN for v; semi-implicit ik^3*v for u; dt=2e-4) — partial stability to t~2 then blow-up as u grows to 15 at t=2 from soliton forcing; multiple v-peaks forming.
iter 3: scipy RK45 adaptive (rtol=1e-4, atol=1e-6, max_step=1e-3) with 2/3 dealiasing — full run to T=8, no NaN; single dominant v-peak 0.63 (below 1.0 threshold), mass conserved 0%, max|u|=6.03; physically correct but soliton depleted by coupling.
