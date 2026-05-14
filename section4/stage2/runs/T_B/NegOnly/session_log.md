# Session log: T_B / NegOnly

iter 1: E1 explicit RK4 + spectral (no dealiasing), NaN at t=0.388 — overflow in nonlinear products, aliasing-driven amplitude CFL violation.
iter 2: E2 explicit RK4 + spectral + 2/3 dealiasing, mass 0.000%, 10 peaks above 0.8 (target >=2). Phenomenon target met. Stopping early.
