#!/usr/bin/env python3
"""Build 4 Gardner-equation stress-test sandboxes."""
import json, pathlib

ROOT = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/stage1")
SB = ROOT / "sandboxes"

GARDNER_TESTS = [
    {
        "id": "G1", "pde": "gardner",
        "title": "Gardner / explicit RK4 only",
        "constraint": "You MUST use ONLY explicit time integration (forward Euler or explicit RK4). NO IMEX, NO implicit, NO integrating-factor, NO ETD. Compute v_xxx via standard 2nd-order central FD on a uniform grid. Pick whatever dt you think is needed.",
        "pde_spec": "v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0  (Gardner equation: KdV with extra cubic nonlinearity) on x in [-15,15] periodic, Nx=256",
        "ic": "v_0(x) = 1.5 * sech^2(x + 5)  (KdV-style sech^2 IC of amplitude 1.5)",
        "T": 2.0,
        "output": "gardner_G1.npy",
        "shape": "(256,)",
        "predicted": "blow-up (NaN/Inf) or massive distortion: explicit on stiff 3rd-derivative compounded by stronger cubic nonlinearity. Stability requires dt extremely small.",
    },
    {
        "id": "G2", "pde": "gardner",
        "title": "Gardner / IMEX Crank-Nicolson spectral",
        "constraint": "You MUST use Fourier pseudo-spectral spatial discretization with IMEX Crank-Nicolson: Crank-Nicolson on the LINEAR DISPERSIVE term v_xxx (handled implicitly in Fourier space), explicit on the nonlinear terms 6 v v_x and (3/2) v^2 v_x. dt around 0.0005. Apply 2/3 dealiasing on the nonlinear terms.",
        "pde_spec": "v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0  on x in [-15,15] periodic, Nx=256",
        "ic": "v_0(x) = 1.5 * sech^2(x + 5)",
        "T": 2.0,
        "output": "gardner_G2.npy",
        "shape": "(256,)",
        "predicted": "stable propagation; the IC is not a true Gardner soliton so there will be some radiative shedding, but the main lump should remain compact with mass roughly conserved.",
    },
    {
        "id": "G3", "pde": "gardner",
        "title": "Gardner / spectral IMEX with NO dealiasing",
        "constraint": "Use Fourier pseudo-spectral + IMEX Crank-Nicolson (CN on dispersion, explicit on nonlinear) as in G2 — BUT you MUST NOT apply any 2/3 dealiasing or low-pass filter on the nonlinear terms. dt = 0.001.",
        "pde_spec": "v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0  on x in [-15,15] periodic, Nx=256",
        "ic": "v_0(x) = 1.5 * sech^2(x + 5)",
        "T": 2.0,
        "output": "gardner_G3.npy",
        "shape": "(256,)",
        "predicted": "stronger aliasing than the KdV-without-dealiasing case (A5) because the cubic v^2 v_x term aliases at twice the wavenumber and three times the wavenumber. Expect amplitude inflation, spurious peaks at small scales, possibly delayed blow-up.",
    },
    {
        "id": "G4", "pde": "gardner",
        "title": "Gardner / large-amplitude KdV-style IC (wrong soliton form)",
        "constraint": "Use any STABLE scheme (IMEX-CN spectral recommended). BUT the IC must be a KdV-amplitude sech^2 of amplitude 3.0 — this is NOT a Gardner soliton; in the Gardner equation the cubic term will be active for this amplitude.",
        "pde_spec": "v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0  on x in [-15,15] periodic, Nx=256",
        "ic": "v_0(x) = 3.0 * sech^2(x + 5)  (larger amplitude than typical KdV-pilot soliton)",
        "T": 2.0,
        "output": "gardner_G4.npy",
        "shape": "(256,)",
        "predicted": "the wave is not a stationary Gardner soliton shape because the (3/2) v^2 v_x term contributes significantly at amplitude 3. Expect shape change: peak may broaden / asymmetrize, and there will be radiative tail. Phase speed will differ from the KdV expected c=2*A=6.",
    },
]

PROMPT_TEMPLATE = """You are running a PDE numerical stress test for a knowledge-bank study. You will write a Python script (`candidate.py`) and a reasoning note (`reasoning.md`).

# Stress test {id}: {title}

## CRITICAL RULE
This is a STRESS TEST. You MUST follow the method constraint below EXACTLY, even if you know a better method that would work. The whole point is to record what happens with the SPECIFIED method on this problem. If you substitute a different method, the test is useless. We will check that your candidate.py implements the specified method.

## Method constraint (FORCED)
{constraint}

## PDE
{pde_spec}

## Initial condition
{ic}

## Final time
T = {T}

## Output
Save your final-time solution to:
  pred_results/{output}
with shape {shape} (numpy array of v(x, T) at the 256 grid points).

## Working directory
{cwd}
- candidate.py and reasoning.md must be at this directory
- pred_results/ subdirectory already exists

## Predicted outcome (for your reasoning.md to address)
We predict: {predicted}

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
"""

for t in GARDNER_TESTS:
    cwd = SB / t["id"]
    (cwd / "pred_results").mkdir(parents=True, exist_ok=True)
    prompt = PROMPT_TEMPLATE.format(
        id=t["id"], title=t["title"], constraint=t["constraint"],
        pde_spec=t["pde_spec"], ic=t["ic"], T=t["T"],
        output=t["output"], shape=t["shape"],
        predicted=t["predicted"], cwd=str(cwd),
    )
    (cwd / "prompt.md").write_text(prompt)
    (cwd / "meta.json").write_text(json.dumps(t, indent=2))
    print(f"built {t['id']}  ({t['title']})")

print(f"\n4 Gardner sandboxes ready under {SB}")
