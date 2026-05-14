# Session log: T_B / NoKB

iter 1: E1 baseline pseudospectral + RK4 no dealiasing, dt=5e-4 — blew up at step 10 (t~0.005); NaN from aliased high-k modes amplified by 3v^2 and uv coupling.
iter 2: E2 added 2/3-rule dealiasing, same dt=5e-4 — still blew up (step 17, t~0.0085). Diagnosis: explicit RK4 CFL on v_xxx limits dt to ~1.5e-4; dt=5e-4 is 3.4x over.
iter 3: E3 same scheme as E2 but dt=5e-5 (10x reduction) — completed full T=6.0 stably; mass(v) drift = 0.000%; final v has 16 local maxima >= 0.8 (well-separated). Phenomenon target satisfied; some high-k content present.
