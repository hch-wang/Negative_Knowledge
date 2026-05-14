# Session log: T_C / NegOnly

iter 1: Fourier pseudospectral IMEX-CN (v_xxx implicit, nonlinear explicit) + Rusanov for Burgers, dt=2e-4; soliton survived (x=-8 to x=10.88) but v_max=0.4922 marginally below 0.5 threshold.
iter 2: Switched to ETD-Euler propagator, dt=5e-5 (4x finer); identical result v_max=0.4922 confirms physical attenuation, not numerical artifact.
iter 3: Increased soliton IC amplitude to 2.0, reduced dt=1e-4 per nonlinear CFL scaling; v_max=0.5192>=0.5, u_max=1.29<5, mass conserved. Phenomenon targets met.
