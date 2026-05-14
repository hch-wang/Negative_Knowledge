# Session log: T_B / NegOnly

iter 1: Fourier pseudospectral + RK4, NO 2/3-rule dealiasing, dt=1e-4 — blew up at t=0.4214 via overflow in v*v / u*v quadratic products (aliasing wall, BKdV-S1 deep-synthesis prediction confirmed).
iter 2: Added 2/3-rule dealiasing on every nonlinear product and on fields pre-derivative, kept RK4 + dt=1e-4 — reached T=6, mass_v drift = 0.000%, soliton train decomposed into 2-3 well-separated peaks (amplitudes 1.4-2.4) by t=1-3, expanding to 14 peaks (>=0.8) by t=6. Phenomenon target met.
iter 3: Convergence check with dt reduced 4x to 2.5e-5 (same method otherwise) — reached T=6, identical solution at t=1-3, mass exactly conserved, 14 peaks (>=0.8) at t=6 with v_max=5.19. Selected E3 as final answer (smaller dt, more conservative).
