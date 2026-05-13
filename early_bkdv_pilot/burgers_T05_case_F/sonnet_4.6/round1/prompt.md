You are solving a 1-D PDE numerical-method task. Produce a single Python script + a short reasoning note via Write.

You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/runs/burgers_T05/sonnet_4.6/round1/candidate.py
2) ${PROJECT_ROOT}/runs/burgers_T05/sonnet_4.6/round1/reasoning.md (under 500 words: Approach / Numerical method / Risks / Expected output)

# Task — BKdV-T1: Inviscid Burgers shock formation

Solve the inviscid Burgers equation numerically and save the solution at the final time.

**PDE**: u_t + u u_x = 0   (equivalently u_t + (u^2/2)_x = 0, conservation form)

**Spatial domain**: x in [-1, 1], periodic boundary conditions

**Initial condition**: u_0(x) = -sin(pi * x)

**Final time**: T = 0.5

**Output grid**: Nx = 200 cells, cell-centered: x_i = -1 + dx/2 + i*dx, where dx = 2/200 = 0.01, for i = 0, 1, ..., 199.

**Output file**: pred_results/burgers_T05.npy — a numpy array of shape (200,) containing u(x_i, T=0.5) at the 200 cell centers, in order i=0..199.

# Physical context (you can use this to choose a scheme)

The initial condition is smooth, but characteristic curves carrying values u > 0 (from x < 0) and u < 0 (from x > 0) collide at x=0. A shock forms at time t* = 1/pi ≈ 0.318. By T = 0.5 the shock has been present for some time.

Inviscid Burgers admits a unique entropy-satisfying weak solution past the shock. A numerical method must:
- Be conservative (so total mass is preserved)
- Capture the shock without spurious oscillations (TVD or essentially non-oscillatory)
- Pick the entropy-correct flux (upwind / Godunov / Lax-Friedrichs / WENO / Roe)

# Environment

Working dir: ${PROJECT_ROOT}/runs/burgers_T05/sonnet_4.6/round1
Layout:
```
.
├── candidate.py  (you write this)
├── reasoning.md  (you write this)
└── pred_results/burgers_T05.npy  (your script must produce this)
```

Available packages: numpy, scipy, matplotlib. NOT available: any specialty PDE libraries (FEniCS, FiPy, Firedrake), torch, tensorflow, jax.

# Evaluation criterion

Your output `pred_results/burgers_T05.npy` will be compared to a high-resolution reference solution (Lax-Friedrichs on Nx=4000) downsampled to the same 200-cell grid. PASS if L1 error < 0.10. Failure modes that will be detected automatically:
- NaN/Inf in output → numerical blow-up (unstable scheme, CFL too large)
- High-frequency jumps between adjacent cells (> 3× reference's max-jump) → Gibbs-like oscillations near the shock
- amplitude squashed (max(|u|) << 1) → over-diffusive scheme

# Hard constraints

1. Use Write tool EXACTLY TWICE (candidate.py + reasoning.md).
2. No Read of any file other than this prompt.md. No Bash. No Edit. No Grep/Glob.
3. The script must be self-contained, runnable as `python candidate.py` from the working directory.
4. Use only numpy/scipy/matplotlib. No installs.
5. After both Writes, respond with ONE short sentence describing your numerical scheme.
