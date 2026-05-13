You are solving a 1-D PDE numerical-method task. This is your SECOND attempt. Your first attempt failed with all-NaN output. A bounded failure record from that attempt is below.

You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/runs/kdv_T2/sonnet_4.6/round2_M4/candidate.py
2) ${PROJECT_ROOT}/runs/kdv_T2/sonnet_4.6/round2_M4/reasoning.md (under 500 words: Approach / Numerical method / Risks / Use of memory — explain specifically what you changed vs round-1)

# Task — BKdV-T2: KdV single-soliton propagation

**PDE**: v_t + 6 v v_x + v_xxx = 0
**Domain**: x in [-15, 15], periodic
**Nx**: 256, grid x_j = -15 + j*dx, dx = 30/256
**IC**: v_0(x) = 2 * sech^2(x + 5)
**T**: 2.0; expected final peak at x ≈ +3 with amplitude ≈ 2.0
**Output**: pred_results/kdv_T2.npy, shape (256,)

# Memory: bounded failure record from round 1 (your previous attempt)

## Round-1 failure record (M4 schema)

- **target**: Solve KdV: v_t + 6 v v_x + v_xxx = 0 with single soliton IC, propagate to T=2.0
- **observation**: Output array of shape (256,) contains all-NaN values. Eval rejected: 256 NaN/Inf. Numerical blow-up.
- **candidate approach (round 1)**: Fourier pseudospectral + integrating-factor RK4 (IFRK4)
- **failure dimensions**:
  - layer: implementation_failure
  - scope: local_failure
  - degree: unstable
  - reproducibility: observed_once
  - recommended_action: change_method
  - risk: medium_risk_drift
- **rationale**: "Agent reasoned correctly that explicit schemes are stiff for v_xxx and chose Fourier + integrating-factor RK4. However the implementation produced NaN -- likely because: (a) integrating-factor expansion has overflow in exp(i*k^3*t) for high k modes, (b) dealiasing was missing, or (c) timestep was still too large. The CONCEPT was right, the EXECUTION was wrong."

# Round-2 instructions

The recommended_action is `change_method`. Three concrete alternatives that are KNOWN to work for KdV (you should pick one and justify):

1. **IMEX (semi-implicit) finite differences**: Treat v_xxx implicitly with Crank-Nicolson, treat 6 v v_x explicitly. dt = 0.0005 is enough.

2. **Fourier pseudospectral + Crank-Nicolson on dispersion + explicit on nonlinear** (NOT integrating factor — avoid overflow). This is sometimes called IMEX-spectral. Concretely: in Fourier domain,
   `(1 - dt/2 * ik^3) v_hat^{n+1} = (1 + dt/2 * ik^3) v_hat^n + dt * N_hat^n`
   where `N_hat^n = -3 ik * FFT(v^2)` (nonlinear term in conservation form).

3. **ETDRK4** (Cox-Matthews): exponential time differencing 4th-order Runge-Kutta. Robust for stiff dispersive equations. Be careful with the exponential factors — use Trefethen's contour-integral formula to avoid cancellation for small k.

If you try integrating-factor RK4 again, you MUST address the failure modes that produced NaN:
- Use 2/3 dealiasing rule on the nonlinear term
- Cap exp(i k^3 t) magnitude or use rescaled variable
- Choose dt small enough that |k_max^3 * dt| < some threshold

# Environment

Working dir: ${PROJECT_ROOT}/runs/kdv_T2/sonnet_4.6/round2_M4

Available packages: numpy, scipy, matplotlib only.

# Eval criteria (same as round 1)
- argmax x in [2.5, 3.5]
- amplitude in [1.85, 2.15]
- mass within 1% of 4.0

# Hard constraints
1. Write tool EXACTLY TWICE.
2. No Bash/Read of other files/etc.
3. After writes, return ONE sentence describing what method you switched to and why it should avoid the round-1 blow-up.
