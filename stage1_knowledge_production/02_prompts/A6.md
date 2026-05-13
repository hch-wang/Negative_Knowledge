You are running a PDE numerical stress test for a knowledge-bank study. You will write a Python script (`candidate.py`) and a reasoning note (`reasoning.md`).

# Stress test A6: KdV / very small amplitude IC

## CRITICAL RULE
This is a STRESS TEST. You MUST follow the method constraint below EXACTLY, even if you know a better method that would work. The whole point is to record what happens with the SPECIFIED method on this problem. If you substitute a better method, the test is useless. We will check that your candidate.py implements the specified method.

## Method constraint (FORCED)
Use whatever STABLE scheme you like (IMEX-spectral recommended). BUT the IC amplitude MUST be 0.1 (NOT 2). Everything else same as standard KdV soliton task.

## PDE
v_t + 6 v v_x + v_xxx = 0 on x in [-15,15] periodic, Nx=256

## Initial condition
v_0(x) = 0.1 sech^2(x + 5)  (very small amplitude)

## Final time
T = 2.0

## Output
Save your final-time solution to:
  pred_results/kdv_A6.npy
with shape (256,) (numpy array).

## Working directory
${PROJECT_ROOT}/stage1/sandboxes/A6
- candidate.py and reasoning.md must be at this directory
- pred_results/ subdirectory already exists

## Predicted outcome (for your reasoning.md to address)
We predict: essentially linear dispersive wave; soliton character lost; peak amplitude stays ~0.1, dispersive train forms

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
