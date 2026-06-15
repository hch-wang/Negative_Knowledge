# Session log: T_A / PosOnly

iter 1: E1 = Fourier pseudospectral (no dealiasing) + RK4, Nx=256, L=30, dt=2e-4 — baseline blew up to NaN before t=1.0 (aliasing-driven overflow in v^2 and u*u_x).
iter 2: E2 = Fourier pseudospectral + 2/3 dealiasing + RK4 — ran clean to T=8, mass conserved, |fields|<2.5, but v_max(T)=0.917 just under 1.0 target. Soliton fragmented to 5-6 peaks (physical BKdV-S7-style breakdown of the m=0 manifold).
iter 3: E3 = IFRK4 on v_xxx + RK4 on u + 2/3 dealias — HURT: cross-coupling caused u to surge to ~9 and v collapsed to 0.325. Rolling back to E2 as final.
iter final: E2 reinstated as candidate.py and pred_results/T_A.npy regenerated.
