# Session log: T_B / PosOnly

iter 1: IMEX-CN spectral with explicit u (dt=0.0002) — u equation blows up at t~1.1 due to CFL violation as u_max reaches 75; switching to MUSCL-Godunov for u with adaptive CFL.
iter 2: Operator-split IMEX-CN (v) + MUSCL-Godunov adaptive CFL (u), dt_global=0.002 — SUCCESS: 4 peaks with amp>=0.8, mass drift 0.00%, all finite; early stop.
