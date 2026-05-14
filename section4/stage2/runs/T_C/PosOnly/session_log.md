# Session log: T_C / PosOnly

iter 1: E1 baseline Fourier pseudospectral + explicit RK4 (no dealiasing, no MUSCL, no IMEX); blew up in u at t=0.40, |u|_max=17.4 — Burgers shock causes Gibbs/aliasing in spectral u-sector.
iter 2: E2 single-component upgrade — MUSCL-van-Leer + Godunov flux on -3 u u_x (Burgers self-flux), everything else still spectral RK4; full T=8.0 stable, |u|_max=2.67, v_max=0.63, mass conserved exactly. Phenomenon target met; stop early.
