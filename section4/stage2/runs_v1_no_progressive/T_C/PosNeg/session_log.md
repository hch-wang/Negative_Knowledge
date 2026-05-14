# Session log: T_C / PosNeg

iter 1: E1 - spectral pseudospectral RK2+dealiasing for u, IMEX-CN for v; blew up at t=1.7 due to coupling resonance growing u to 5.7 before soliton-bore contact.
iter 2: E2 - fully spectral IMEX-CN for both u (nu_u=0.5, mu_u=0.005) and v (nu_v=0.01, mu_v=1e-4) with 2/3 dealiasing, dt=5e-5; SUCCESS: v_max=0.580>=0.5, |u_max|=1.57<5, all 8 snapshots finite.
