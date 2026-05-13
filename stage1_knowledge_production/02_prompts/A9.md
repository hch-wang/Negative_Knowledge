You are running a PDE numerical stress test for a knowledge-bank study. You will write a Python script (`candidate.py`) and a reasoning note (`reasoning.md`).

# Stress test A9: Shallow water / dry-bed IC

## CRITICAL RULE
This is a STRESS TEST. You MUST follow the method constraint below EXACTLY, even if you know a better method that would work. The whole point is to record what happens with the SPECIFIED method on this problem. If you substitute a better method, the test is useless. We will check that your candidate.py implements the specified method.

## Method constraint (FORCED)
Use any STABLE scheme (LF or HLL recommended). BUT the IC has dry bed on the right half: h_R = 0 (NOT 1). u initially 0 everywhere.

## PDE
h_t + (hu)_x = 0;  (hu)_t + (h u^2 + g h^2 / 2)_x = 0  with g=1, x in [-1,1] periodic, Nx=200

## Initial condition
dry-bed dam-break: h(x,0) = 1 if x<0 else 0; u(x,0) = 0

## Final time
T = 0.3

## Output
Save your final-time solution to:
  pred_results/sw_A9.npy
with shape (2, 200) (numpy array).

## Working directory
${PROJECT_ROOT}/stage1/sandboxes/A9
- candidate.py and reasoning.md must be at this directory
- pred_results/ subdirectory already exists

## Predicted outcome (for your reasoning.md to address)
We predict: positivity violation (h<0) near the dry interface; or huge u where h~0

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
