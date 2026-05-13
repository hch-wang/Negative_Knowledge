You are running a PDE numerical stress test for a knowledge-bank study. You will write a Python script (`candidate.py`) and a reasoning note (`reasoning.md`).

# Stress test A10: Shallow water / HLL Riemann solver

## CRITICAL RULE
This is a STRESS TEST. You MUST follow the method constraint below EXACTLY, even if you know a better method that would work. The whole point is to record what happens with the SPECIFIED method on this problem. If you substitute a better method, the test is useless. We will check that your candidate.py implements the specified method.

## Method constraint (FORCED)
You MUST use the HLL (or HLLE) Riemann solver for the numerical flux. Explicit Euler time step at CFL <= 0.4.

## PDE
h_t + (hu)_x = 0;  (hu)_t + (h u^2 + g h^2 / 2)_x = 0  with g=1, x in [-1,1] periodic, Nx=200

## Initial condition
dam-break: h(x,0) = 2 if x<0 else 1; u(x,0) = 0

## Final time
T = 0.4

## Output
Save your final-time solution to:
  pred_results/sw_A10.npy
with shape (2, 200) (numpy array).

## Working directory
${PROJECT_ROOT}/stage1/sandboxes/A10
- candidate.py and reasoning.md must be at this directory
- pred_results/ subdirectory already exists

## Predicted outcome (for your reasoning.md to address)
We predict: clean dam-break: left-going rarefaction, right-going shock; h stays positive

In your reasoning.md, write 3 short sections:
- **Method as written**: confirm in 1-2 sentences which numerical scheme you implemented (so we can verify you obeyed the constraint).
- **Predicted vs expected**: do you agree with the predicted outcome? If you think the predicted outcome is wrong, say so with reasoning. If you agree, restate why.
- **What knowledge this might produce**: 1-2 sentences on what a future agent solving a similar problem could learn from this run.

## Hard constraints
1. Use Write tool EXACTLY TWICE: once for candidate.py, once for reasoning.md.
2. No Read of any file other than this prompt. No Bash. No Edit.
3. Only numpy, scipy, matplotlib are available.
4. The script must be runnable as `python candidate.py` from the working directory.
5. After the two writes, return ONE short sentence stating what method you implemented.
