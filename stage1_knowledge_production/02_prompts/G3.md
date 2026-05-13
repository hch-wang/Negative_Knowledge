You are running a PDE numerical stress test for a knowledge-bank study. You will write a Python script (`candidate.py`) and a reasoning note (`reasoning.md`).

# Stress test G3: Gardner / spectral IMEX with NO dealiasing

## CRITICAL RULE
This is a STRESS TEST. You MUST follow the method constraint below EXACTLY, even if you know a better method that would work. The whole point is to record what happens with the SPECIFIED method on this problem. If you substitute a different method, the test is useless. We will check that your candidate.py implements the specified method.

## Method constraint (FORCED)
Use Fourier pseudo-spectral + IMEX Crank-Nicolson (CN on dispersion, explicit on nonlinear) as in G2 — BUT you MUST NOT apply any 2/3 dealiasing or low-pass filter on the nonlinear terms. dt = 0.001.

## PDE
v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0  on x in [-15,15] periodic, Nx=256

## Initial condition
v_0(x) = 1.5 * sech^2(x + 5)

## Final time
T = 2.0

## Output
Save your final-time solution to:
  pred_results/gardner_G3.npy
with shape (256,) (numpy array of v(x, T) at the 256 grid points).

## Working directory
${PROJECT_ROOT}/stage1/sandboxes/G3
- candidate.py and reasoning.md must be at this directory
- pred_results/ subdirectory already exists

## Predicted outcome (for your reasoning.md to address)
We predict: stronger aliasing than the KdV-without-dealiasing case (A5) because the cubic v^2 v_x term aliases at twice the wavenumber and three times the wavenumber. Expect amplitude inflation, spurious peaks at small scales, possibly delayed blow-up.

In your reasoning.md, write 3 short sections:
- **Method as written**: confirm in 1-2 sentences which numerical scheme you implemented (so we can verify you obeyed the constraint).
- **Predicted vs expected**: do you agree with the predicted outcome? If you think the predicted outcome is wrong, say so with reasoning. If you agree, restate why.
- **What knowledge this might produce**: 1-2 sentences on what a future agent solving a similar problem (Burgers-swept-KdV / Gardner / coupled dispersive problem) could learn from this run.

## Hard constraints
1. Use Write tool EXACTLY TWICE: once for candidate.py, once for reasoning.md.
2. No Read of any file other than this prompt. No Bash. No Edit.
3. Only numpy, scipy, matplotlib are available.
4. The script must be runnable as `python candidate.py` from the working directory.
5. After the two writes, return ONE short sentence stating what method you implemented.
