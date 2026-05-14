# Session log: T_B / PosNeg

iter 1: E1 baseline (Fourier spectral + explicit RK4, no dealiasing, dt=1e-4) blew up to NaN at t=0.45 due to amplitude-driven nonlinear stiffness + aliasing (amp=4 far above bank's amp 1.5 stable point).
iter 2: E2 single-component upgrade (explicit RK4 -> IMEX-CN on linear v_xxx, no dealiasing, dt=5e-4) still NaN'd at t=0.5 -- confirms failure is on the explicit nonlinear branch, not the linear stiff branch; need dealiasing (kb-gardner-G3) and smaller dt (kb-gardner-nonlinearCFL-amplitude-boundary).
iter 3: E3 layered 2/3-rule dealiasing on top of E2's IMEX-CN spectral solver; same-method dt re-tunes (1e-4 -> 2e-5 -> 1e-5) needed for amp=4. Final run with dt=1e-5 reached T=6 all-finite, mass(v) drift 0.0%, 12 peaks above 0.8 distributed across the domain -- a clean soliton-train decomposition.
