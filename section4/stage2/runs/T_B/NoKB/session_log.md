# Session log: T_B / NoKB

iter 1: E1 (Fourier pseudospectral, no dealiasing, explicit RK4, dt=1e-4) — F1: aliasing-driven NaN at t=0.388 (max|u| explodes from 3 to 7.5 in 200 steps). D1: add 2/3 dealiasing as single-component upgrade.
iter 2: E2 (Fourier pseudospectral + 2/3 dealiasing + RK4, dt=1e-4) — F2: completes to T=6.0; final v has 11 peaks with v>=0.8 (target >=2), mass drift 0%. STOP EARLY (D2: stop_useful).
