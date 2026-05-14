# Section 4 — Stage 2 verified eval summary

Cells: 3 tasks × 4 conditions = 12 sandboxes.
All evals run on the parent side via `eval/phenomenon_checks.py` (deterministic, task-specific phenomenon checks; no closed-form reference).

## Per-task verdict (PASS / FAIL)

| Task | **NoKB** | **PosOnly** | **NegOnly** | **PosNeg** |
|---|---|---|---|---|
| T_A | ✗ (3it) | ✓ (3it) | ✗ (3it) | ✓ (3it) |
| T_B | ✓ (3it) | ✓ (2it) | ✓ (3it) | ✗ (3it) |
| T_C | ✓ (3it) | ✓ (1it) | ✓ (3it) | ✓ (2it) |

Legend: ✓/✗ = parent-verified PASS/FAIL, `(Nit)` = number of Experiment nodes (1–3).

## Useful rate by condition

| Condition | PASS / 3 | Avg iterations | Avg bank cites | Avg bank rejects |
|---|---|---|---|---|
| NoKB | 2/3 | 3.0 | 0.0 | 0.0 |
| PosOnly | 3/3 | 2.0 | 6.3 | 0.3 |
| NegOnly | 2/3 | 3.0 | 0.0 | 19.7 |
| PosNeg | 2/3 | 2.7 | 9.0 | 11.3 |

## Per-cell metrics

| Task | Cond | Iter | Cites | Rejects | PASS? | vT_max | u_max | peaks | reason |
|---|---|---|---|---|---|---|---|---|---|
| T_A | NoKB | 3 | 0 | 0 | FAIL | 0.64 | 6.09 | 1 | amp ratio 0.32 < 0.5 |
| T_A | PosOnly | 3 | 9 | 1 | PASS | 1.30 | 2.55 | 1 |  |
| T_A | NegOnly | 3 | 0 | 20 | FAIL | 0.63 | 6.12 | 1 | amp ratio 0.32 < 0.5 |
| T_A | PosNeg | 3 | 9 | 9 | PASS | 2.09 | 2.50 | 1 |  |
| T_B | NoKB | 3 | 0 | 0 | PASS | 1.79 | 8.60 | 5 |  |
| T_B | PosOnly | 2 | 6 | 0 | PASS | 2.08 | 8.34 | 4 |  |
| T_B | NegOnly | 3 | 0 | 21 | PASS | 2.02 | 6.47 | 5 |  |
| T_B | PosNeg | 3 | 11 | 16 | FAIL | nan | 184.35 | - | non-finite or unbounded |
| T_C | NoKB | 3 | 0 | 0 | PASS | 0.64 | 3.62 | 1 |  |
| T_C | PosOnly | 1 | 4 | 0 | PASS | 0.51 | 2.64 | 1 |  |
| T_C | NegOnly | 3 | 0 | 18 | PASS | 0.52 | 3.10 | 1 |  |
| T_C | PosNeg | 2 | 7 | 9 | PASS | 0.58 | 2.76 | 1 |  |

## Bank-entry usage (cite / reject lists, sample)

### T_A / PosOnly
- **cites** (9): kb-kdv-IMEX-CN-spectral-pass, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-burgers-MUSCL-Godunov-shock-pass, kb-kdv-IMEX-CN-spectral-pass, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-kdv-IMEX-CN-spectral-pass, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation
- **rejects** (1): kb-burgers-MUSCL-Godunov-shock-pass

### T_A / NegOnly
- **rejects** (20): kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-IFRK4-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-burgers-fwdEuler-centralFD-Gibbs, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-nonlinearCFL-amplitude-boundary, kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-IFRK4-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-burgers-fwdEuler-centralFD-Gibbs, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-nonlinearCFL-amplitude-boundary, kb-gardner-GardnerIsM0-coupledSystemInstability, kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-IFRK4-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-burgers-fwdEuler-centralFD-Gibbs, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-nonlinearCFL-amplitude-boundary, kb-gardner-GardnerIsM0-coupledSystemInstability

### T_A / PosNeg
- **cites** (9): kb-kdv-IMEX-CN-spectral-pass, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-kdv-spectral-solitonAmplitude-conservation, kb-kdv-IMEX-CN-spectral-pass, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-gardner-nonlinearCFL-amplitude-boundary, kb-kdv-IMEX-CN-spectral-pass, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation
- **rejects** (9): kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-GardnerIsM0-coupledSystemInstability, kb-burgers-fwdEuler-centralFD-Gibbs, kb-general-centralFD-hyperbolic-shockFormation

### T_B / PosOnly
- **cites** (6): kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-solitonAmplitude-conservation, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-kdv-IMEX-CN-spectral-pass, kb-burgers-MUSCL-Godunov-shock-pass, kb-kdv-spectral-solitonAmplitude-conservation

### T_B / NegOnly
- **rejects** (21): kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-noDealiasing-cubicAliasing, kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-gardner-G1-explicitRK4-finiteFrag, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-nonlinearCFL-amplitude-boundary, kb-burgers-fwdEuler-centralFD-Gibbs, kb-general-centralFD-hyperbolic-shockFormation, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-noDealiasing-cubicAliasing, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-nonlinearCFL-amplitude-boundary, kb-gardner-cubicTerm-tightens-nonlinearCFL, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-noDealiasing-cubicAliasing, kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-gardner-G1-explicitRK4-finiteFrag, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-nonlinearCFL-amplitude-boundary

### T_B / PosNeg
- **cites** (11): kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-solitonAmplitude-conservation, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-solitonAmplitude-conservation, kb-kdv-noDealiasing-aliasing-artifacts, kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-solitonAmplitude-conservation, kb-kdv-noDealiasing-aliasing-artifacts, kb-burgers-MUSCL-Godunov-shock-pass
- **rejects** (16): kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-cubicTerm-tightens-nonlinearCFL, kb-gardner-nonlinearCFL-amplitude-boundary, kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-nonlinearCFL-amplitude-boundary, kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-general-centralFD-hyperbolic-shockFormation, kb-burgers-fwdEuler-centralFD-Gibbs

### T_C / PosOnly
- **cites** (4): kb-burgers-MUSCL-Godunov-shock-pass, kb-kdv-IMEX-CN-spectral-pass, kb-kdv-spectral-solitonAmplitude-conservation, kb-gardner-KdV-method-transfer-moderate-amplitude

### T_C / NegOnly
- **rejects** (18): kb-burgers-fwdEuler-centralFD-Gibbs, kb-general-centralFD-hyperbolic-shockFormation, kb-burgers-LaxFriedrichs-longTime-dissipation, kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup, kb-gardner-nonlinearCFL-amplitude-boundary, kb-burgers-fwdEuler-centralFD-Gibbs, kb-general-centralFD-hyperbolic-shockFormation, kb-burgers-LaxFriedrichs-longTime-dissipation, kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-burgers-fwdEuler-centralFD-Gibbs, kb-general-centralFD-hyperbolic-shockFormation, kb-burgers-LaxFriedrichs-longTime-dissipation, kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-nonlinearCFL-amplitude-boundary

### T_C / PosNeg
- **cites** (7): kb-burgers-MUSCL-Godunov-shock-pass, kb-kdv-IMEX-CN-spectral-pass, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-gardner-KdV-method-transfer-moderate-amplitude, kb-kdv-IMEX-CN-spectral-pass, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation, kb-kdv-noDealiasing-aliasing-artifacts
- **rejects** (9): kb-burgers-fwdEuler-centralFD-Gibbs, kb-kdv-IFRK4-blowup, kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-cubicTerm-tightens-nonlinearCFL, kb-gardner-nonlinearCFL-amplitude-boundary, kb-burgers-fwdEuler-centralFD-Gibbs, kb-kdv-IFRK4-blowup, kb-burgers-LaxFriedrichs-longTime-dissipation

