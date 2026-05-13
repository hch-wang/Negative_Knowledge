You are solving a 1-D PDE numerical-method task. Produce a single Python script + a short reasoning note via Write.

You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/runs/kdv_T2/sonnet_4.6/round1/candidate.py
2) ${PROJECT_ROOT}/runs/kdv_T2/sonnet_4.6/round1/reasoning.md (under 500 words: Approach / Numerical method / Risks / Expected output)

# Task — BKdV-T2: KdV single-soliton propagation

Solve the Korteweg-de Vries equation and report the solution at the final time.

**PDE**: v_t + 6 v v_x + v_xxx = 0

**Spatial domain**: x in [-15, 15], periodic boundary conditions

**Initial condition**: v_0(x) = 2 * sech^2(x + 5)
  — This is a soliton of amplitude 2, centered at x = -5, with theoretical speed c = 4.

**Final time**: T = 2.0
  — By T = 2.0 the soliton should have moved to x = -5 + 4*2 = +3.

**Output grid**: Nx = 256 points x_j = -15 + j*dx, where dx = 30/256, for j = 0, 1, ..., 255.

**Output file**: pred_results/kdv_T2.npy — a numpy array of shape (256,) containing v(x_j, T=2.0) at the 256 grid points.

# Physical context (you can use this to choose a scheme)

The KdV equation is dispersive with a *third* spatial derivative. The single soliton 2*sech^2(x - 4t + x_0) is a known exact solution that propagates at speed 4 without changing shape. Key physics:
- Mass ∫ v dx is conserved (= 4 for this soliton)
- Energy ∫ v^2/2 dx is conserved
- The third derivative makes any explicit scheme STIFF: stability requires dt ~ dx^3, which is prohibitive

Numerical methods that work:
- Fourier spectral in space (since periodic) + implicit/exponential integrator in time
- Finite differences with implicit treatment of the dispersive term (IMEX, treat 6 v v_x explicitly, v_xxx implicitly)
- Symplectic / Hamiltonian-preserving integrators

Naive choices that fail:
- Explicit Euler / RK4 on the full PDE → blow-up for any reasonable dt
- Fully implicit on nonlinear term → may dampen soliton

# Environment

Working dir: ${PROJECT_ROOT}/runs/kdv_T2/sonnet_4.6/round1
Layout:
```
.
├── candidate.py        (you write this)
├── reasoning.md        (you write this)
└── pred_results/kdv_T2.npy  (your script must produce this)
```

Available packages: numpy, scipy, matplotlib. NOT available: any specialty PDE libraries.

# Evaluation criteria (deterministic, all three must hold)

1. **Position**: argmax of your output should be at x in [2.5, 3.5] (theoretical x=3 ± 0.5 tolerance)
2. **Amplitude**: max of your output should be in [1.85, 2.15] (within ±0.15 of theoretical 2.0)
3. **Mass conservation**: sum(v) * dx should be within 1% of 4.0 (the integral of the initial soliton)

Failures detected automatically:
- NaN/Inf → numerical blow-up (likely explicit on dispersion)
- amplitude << 2 → over-damping
- soliton at wrong position → wrong speed or large phase error
- mass drift > 1% → non-conservative scheme

# Hard constraints

1. Write tool EXACTLY TWICE.
2. No Read of any file other than this prompt. No Bash. No Edit. No Grep/Glob.
3. Script self-contained, runnable as `python candidate.py` from working dir.
4. numpy/scipy/matplotlib only.
5. After both Writes, respond with ONE short sentence describing your numerical scheme.
