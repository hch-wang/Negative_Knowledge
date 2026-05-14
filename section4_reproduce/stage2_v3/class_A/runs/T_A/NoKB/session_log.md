# Session log: T_A / NoKB

iter 1: E1 spectral+RK4, no dealiasing — blew up at t=0.50 (aliasing instability on v^2, uv).
iter 2: E2 added 2/3-rule dealiasing — reached T=8 with mass(v) conserved; v_max=1.50; but |u|max=15.88 (>15) and ~4 dominant v peaks.
iter 3: E3 added weak exponential spectral filter on top of E2 — reached T=8; |u|max=12.80 (<15), v_max=1.82, mass conserved; multi-peak structure remains (genuine sub-soliton emergence from 0.2*v perturbation off Gardner). Stop useful=true.
