# Section 4 — Stage 2 verified eval summary

Cells: 3 tasks × 4 conditions = 12 sandboxes.
All evals run on the parent side via `eval/phenomenon_checks.py` (deterministic, task-specific phenomenon checks; no closed-form reference).

## Per-task verdict (PASS / FAIL)

| Task | **NoKB** | **PosOnly** | **NegOnly** | **PosNeg** |
|---|---|---|---|---|
| T_A | ✓ (3it) | ✗ (3it) | ✗ (3it) | ✗ (3it) |
| T_B | ✓ (2it) | ✓ (2it) | ✓ (2it) | ✗ (3it) |
| T_C | ✗ (3it) | ✓ (2it) | ✗ (3it) | ✓ (3it) |

Legend: ✓/✗ = parent-verified PASS/FAIL, `(Nit)` = number of Experiment nodes (1–3).

## Useful rate by condition

| Condition | PASS / 3 | Avg iterations | Avg bank cites | Avg bank rejects |
|---|---|---|---|---|
| NoKB | 2/3 | 2.7 | 0.0 | 0.0 |
| PosOnly | 2/3 | 2.3 | 4.3 | 1.0 |
| NegOnly | 1/3 | 2.7 | 0.0 | 9.0 |
| PosNeg | 1/3 | 3.0 | 8.3 | 9.0 |

## Per-cell metrics

| Task | Cond | Iter | Cites | Rejects | PASS? | vT_max | u_max | peaks | reason |
|---|---|---|---|---|---|---|---|---|---|
| T_A | NoKB | 3 | 0 | 0 | PASS | 1.36 | 11.24 | 9 |  |
| T_A | PosOnly | 3 | 7 | 3 | FAIL | 0.92 | 2.39 | 6 | amp ratio 0.46 < 0.5 |
| T_A | NegOnly | 3 | 0 | 6 | FAIL | 0.64 | 7.53 | 1 | amp ratio 0.32 < 0.5 |
| T_A | PosNeg | 3 | 7 | 9 | FAIL | nan | 36694286113366.02 | - | non-finite or unbounded |
| T_B | NoKB | 2 | 0 | 0 | PASS | 1.88 | 4.88 | 10 |  |
| T_B | PosOnly | 2 | 4 | 0 | PASS | 4.42 | 14.47 | 14 |  |
| T_B | NegOnly | 2 | 0 | 9 | PASS | 2.08 | 4.55 | 10 |  |
| T_B | PosNeg | 3 | 9 | 9 | FAIL | nan | 30.04 | - | non-finite or unbounded |
| T_C | NoKB | 3 | 0 | 0 | FAIL | nan | 16.04 | - | non-finite or unbounded |
| T_C | PosOnly | 2 | 2 | 0 | PASS | 0.63 | 3.85 | 3 |  |
| T_C | NegOnly | 3 | 0 | 12 | FAIL | nan | nan | - | non-finite or unbounded |
| T_C | PosNeg | 3 | 9 | 9 | PASS | 0.62 | 4.99 | 1 |  |

## Bank-entry usage (cite / reject lists, sample)

### T_A / PosOnly
- **cites** (7): kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-solitonAmplitude-conservation, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-solitonAmplitude-conservation, kb-gardner-KdV-method-transfer-moderate-amplitude
- **rejects** (3): kb-burgers-MUSCL-Godunov-shock-pass, kb-burgers-MUSCL-Godunov-shock-pass, kb-shallowWater-LaxFriedrichs-stable-smeared

### T_A / NegOnly
- **rejects** (6): kb-kdv-IFRK4-blowup, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-noDealiasing-cubicAliasing, kb-kdv-IFRK4-blowup, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup

### T_A / PosNeg
- **cites** (7): kb-kdv-IMEX-CN-spectral-pass, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-kdv-spectral-solitonAmplitude-conservation, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-kdv-IMEX-CN-spectral-pass
- **rejects** (9): kb-burgers-fwdEuler-centralFD-Gibbs, kb-shallowWater-centralFD-fwdEuler-hNegative, kb-general-centralFD-hyperbolic-shockFormation, kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-gardner-G1-explicitRK4-finiteFrag, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-noDealiasing-cubicAliasing, kb-burgers-LaxFriedrichs-longTime-dissipation

### T_B / PosOnly
- **cites** (4): kb-kdv-IMEX-CN-spectral-pass, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-kdv-spectral-solitonAmplitude-conservation, kb-gardner-KdV-method-transfer-moderate-amplitude

### T_B / NegOnly
- **rejects** (9): kb-kdv-explicit-RK4-stiffness-blowup, kb-gardner-G1-explicitRK4-finiteFrag, kb-kdv-noDealiasing-aliasing-artifacts, kb-burgers-fwdEuler-centralFD-Gibbs, kb-general-centralFD-hyperbolic-shockFormation, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-noDealiasing-cubicAliasing, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-nonlinearCFL-amplitude-boundary

### T_B / PosNeg
- **cites** (9): kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-solitonAmplitude-conservation, kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-solitonAmplitude-conservation, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-solitonAmplitude-conservation, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-gardner-KdV-method-transfer-moderate-amplitude
- **rejects** (9): kb-kdv-IFRK4-blowup, kb-burgers-fwdEuler-centralFD-Gibbs, kb-general-centralFD-hyperbolic-shockFormation, kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-burgers-LaxFriedrichs-longTime-dissipation, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-noDealiasing-cubicAliasing, kb-kdv-IFRK4-blowup

### T_C / PosOnly
- **cites** (2): kb-burgers-MUSCL-Godunov-shock-pass, kb-general-firstOrder-Godunov-preShock-baseline

### T_C / NegOnly
- **rejects** (12): kb-burgers-fwdEuler-centralFD-Gibbs, kb-general-centralFD-hyperbolic-shockFormation, kb-shallowWater-centralFD-fwdEuler-hNegative, kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-gardner-G1-explicitRK4-finiteFrag, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-noDealiasing-cubicAliasing, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-burgers-LaxFriedrichs-longTime-dissipation, kb-shallowWater-LaxFriedrichs-overdiffusion

### T_C / PosNeg
- **cites** (9): kb-kdv-IMEX-CN-spectral-pass, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-gardner-nonlinearCFL-amplitude-boundary, kb-kdv-spectral-solitonAmplitude-conservation, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-kdv-IMEX-CN-spectral-pass, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-noDealiasing-cubicAliasing, kb-kdv-spectral-solitonAmplitude-conservation
- **rejects** (9): kb-kdv-explicit-RK4-stiffness-blowup, kb-burgers-fwdEuler-centralFD-Gibbs, kb-general-centralFD-hyperbolic-shockFormation, kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-burgers-fwdEuler-centralFD-Gibbs, kb-burgers-LaxFriedrichs-longTime-dissipation, kb-kdv-IFRK4-blowup, kb-shallowWater-LaxFriedrichs-overdiffusion

