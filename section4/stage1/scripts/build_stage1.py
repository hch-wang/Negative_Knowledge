#!/usr/bin/env python3
"""Build 10 Stage-1 stress-test sandboxes for PDE knowledge production."""
import os, pathlib, json

ROOT = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/stage1")
SANDBOX_ROOT = ROOT / "sandboxes"

TESTS = [
    # ===== Burgers =====
    {
        "id": "A1", "pde": "burgers", "title": "Burgers / forward Euler + central diff",
        "constraint": "You MUST use ONLY forward Euler in time + 2nd-order CENTRAL finite differences in space. NO flux limiter. NO upwinding. NO TVD. NO MUSCL. NO Godunov. NO Lax-Friedrichs. If you know better methods, do not use them. CFL <= 0.5.",
        "pde_spec": "u_t + u u_x = 0 on x in [-1,1] periodic, Nx=200",
        "ic": "u_0(x) = -sin(pi x)",
        "T": 0.5,
        "output": "burgers_A1.npy",
        "shape": "(200,)",
        "predicted": "Gibbs oscillations near shock and likely numerical blow-up",
    },
    {
        "id": "A2", "pde": "burgers", "title": "Burgers / very short T (pre-shock)",
        "constraint": "Use any STABLE scheme you like (TVD/MUSCL/upwind are fine). But T MUST = 0.1 (well before shock formation at 1/pi ~= 0.318).",
        "pde_spec": "u_t + u u_x = 0 on x in [-1,1] periodic, Nx=200",
        "ic": "u_0(x) = -sin(pi x)",
        "T": 0.1,
        "output": "burgers_A2.npy",
        "shape": "(200,)",
        "predicted": "smooth wave with steepening but no actual shock features",
    },
    {
        "id": "A3", "pde": "burgers", "title": "Burgers / very long T (boundary contamination)",
        "constraint": "Use any STABLE scheme. But T MUST = 10.0 (very long compared to natural shock timescale).",
        "pde_spec": "u_t + u u_x = 0 on x in [-1,1] periodic, Nx=200",
        "ic": "u_0(x) = -sin(pi x)",
        "T": 10.0,
        "output": "burgers_A3.npy",
        "shape": "(200,)",
        "predicted": "decayed N-wave plus periodic boundary recirculation contamination",
    },
    # ===== KdV =====
    {
        "id": "A4", "pde": "kdv", "title": "KdV / explicit RK4 only",
        "constraint": "You MUST use ONLY explicit time integration (forward Euler or explicit RK4). NO IMEX. NO implicit. NO integrating-factor. NO ETD. Compute v_xxx with standard central FD. Pick whatever dt you think is needed.",
        "pde_spec": "v_t + 6 v v_x + v_xxx = 0 on x in [-15,15] periodic, Nx=256",
        "ic": "v_0(x) = 2 sech^2(x + 5)  (KdV soliton, speed 4)",
        "T": 2.0,
        "output": "kdv_A4.npy",
        "shape": "(256,)",
        "predicted": "blow-up (NaN/Inf) due to stiffness of 3rd derivative under explicit time stepping",
    },
    {
        "id": "A5", "pde": "kdv", "title": "KdV / Fourier spectral but NO dealiasing",
        "constraint": "Use Fourier pseudo-spectral with IMEX or implicit time integration (so dispersion does NOT blow up). BUT you MUST NOT apply 2/3 dealiasing rule, NO low-pass filtering, NO mode truncation on the nonlinear term. dt = 0.005.",
        "pde_spec": "v_t + 6 v v_x + v_xxx = 0 on x in [-15,15] periodic, Nx=256",
        "ic": "v_0(x) = 2 sech^2(x + 5)",
        "T": 2.0,
        "output": "kdv_A5.npy",
        "shape": "(256,)",
        "predicted": "aliasing artifacts at high wavenumbers; soliton shape may distort or extra spurious peaks may appear; mass may drift",
    },
    {
        "id": "A6", "pde": "kdv", "title": "KdV / very small amplitude IC",
        "constraint": "Use whatever STABLE scheme you like (IMEX-spectral recommended). BUT the IC amplitude MUST be 0.1 (NOT 2). Everything else same as standard KdV soliton task.",
        "pde_spec": "v_t + 6 v v_x + v_xxx = 0 on x in [-15,15] periodic, Nx=256",
        "ic": "v_0(x) = 0.1 sech^2(x + 5)  (very small amplitude)",
        "T": 2.0,
        "output": "kdv_A6.npy",
        "shape": "(256,)",
        "predicted": "essentially linear dispersive wave; soliton character lost; peak amplitude stays ~0.1, dispersive train forms",
    },
    # ===== Shallow water =====
    {
        "id": "A7", "pde": "shallow_water", "title": "Shallow water / forward Euler + central diff",
        "constraint": "You MUST use ONLY forward Euler in time + central FD in space for BOTH equations of the system. NO limiter, NO Riemann solver, NO upwinding, NO HLL/HLLE/Roe.",
        "pde_spec": "h_t + (hu)_x = 0;  (hu)_t + (h u^2 + g h^2 / 2)_x = 0  with g=1, x in [-1,1] periodic, Nx=200",
        "ic": "dam-break: h(x,0) = 2 if x<0 else 1; u(x,0) = 0  (h and hu both stored)",
        "T": 0.4,
        "output": "sw_A7.npy",
        "shape": "(2, 200) — first row h, second row hu",
        "predicted": "oscillations near the discontinuity; h may go negative; possible blow-up",
    },
    {
        "id": "A8", "pde": "shallow_water", "title": "Shallow water / Lax-Friedrichs",
        "constraint": "You MUST use the global Lax-Friedrichs numerical flux for both equations (no HLL, no Roe, no MUSCL). Explicit Euler step at CFL=0.4.",
        "pde_spec": "h_t + (hu)_x = 0;  (hu)_t + (h u^2 + g h^2 / 2)_x = 0  with g=1, x in [-1,1] periodic, Nx=200",
        "ic": "dam-break: h(x,0) = 2 if x<0 else 1; u(x,0) = 0",
        "T": 0.4,
        "output": "sw_A8.npy",
        "shape": "(2, 200)",
        "predicted": "works without blow-up but rarefaction and shock are diffusively smeared",
    },
    {
        "id": "A9", "pde": "shallow_water", "title": "Shallow water / dry-bed IC",
        "constraint": "Use any STABLE scheme (LF or HLL recommended). BUT the IC has dry bed on the right half: h_R = 0 (NOT 1). u initially 0 everywhere.",
        "pde_spec": "h_t + (hu)_x = 0;  (hu)_t + (h u^2 + g h^2 / 2)_x = 0  with g=1, x in [-1,1] periodic, Nx=200",
        "ic": "dry-bed dam-break: h(x,0) = 1 if x<0 else 0; u(x,0) = 0",
        "T": 0.3,
        "output": "sw_A9.npy",
        "shape": "(2, 200)",
        "predicted": "positivity violation (h<0) near the dry interface; or huge u where h~0",
    },
    {
        "id": "A10", "pde": "shallow_water", "title": "Shallow water / HLL Riemann solver",
        "constraint": "You MUST use the HLL (or HLLE) Riemann solver for the numerical flux. Explicit Euler time step at CFL <= 0.4.",
        "pde_spec": "h_t + (hu)_x = 0;  (hu)_t + (h u^2 + g h^2 / 2)_x = 0  with g=1, x in [-1,1] periodic, Nx=200",
        "ic": "dam-break: h(x,0) = 2 if x<0 else 1; u(x,0) = 0",
        "T": 0.4,
        "output": "sw_A10.npy",
        "shape": "(2, 200)",
        "predicted": "clean dam-break: left-going rarefaction, right-going shock; h stays positive",
    },
]

PROMPT_TEMPLATE = """You are running a PDE numerical stress test for a knowledge-bank study. You will write a Python script (`candidate.py`) and a reasoning note (`reasoning.md`).

# Stress test {id}: {title}

## CRITICAL RULE
This is a STRESS TEST. You MUST follow the method constraint below EXACTLY, even if you know a better method that would work. The whole point is to record what happens with the SPECIFIED method on this problem. If you substitute a better method, the test is useless. We will check that your candidate.py implements the specified method.

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
with shape {shape} (numpy array).

## Working directory
{cwd}
- candidate.py and reasoning.md must be at this directory
- pred_results/ subdirectory already exists

## Predicted outcome (for your reasoning.md to address)
We predict: {predicted}

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
"""

# Build sandboxes
built = []
for t in TESTS:
    cwd = SANDBOX_ROOT / t["id"]
    (cwd / "pred_results").mkdir(parents=True, exist_ok=True)

    prompt = PROMPT_TEMPLATE.format(
        id=t["id"], title=t["title"], constraint=t["constraint"],
        pde_spec=t["pde_spec"], ic=t["ic"], T=t["T"],
        output=t["output"], shape=t["shape"],
        predicted=t["predicted"], cwd=str(cwd),
    )
    (cwd / "prompt.md").write_text(prompt)
    # save meta for later eval
    (cwd / "meta.json").write_text(json.dumps(t, indent=2))
    built.append(t["id"])
    print(f"built {t['id']:>4}  ({t['title']})")

print(f"\n{len(built)} stress-test sandboxes ready under {SANDBOX_ROOT}")
