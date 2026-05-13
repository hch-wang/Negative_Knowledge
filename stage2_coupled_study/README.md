# Stage 2 — Coupled Burgers-swept-KdV Study

## What this stage does

For three coupled-PDE sub-tasks (T_A, T_B, T_C), compare how well three "memory conditions" let a Sonnet 4.6 agent find a working numerical solver:

- **NoKB**: no knowledge bank
- **PosOnly**: only positive entries (10 ✓)
- **PosNeg**: full bank (10 ✓ + 20 ✗)

Each cell allows up to 3 rounds of internal iteration. Phenomenon-based eval (no closed-form reference solution exists).

## Headline result

| Condition | Ever-useful / 3 tasks |
|---|---|
| NoKB | 0/3 (0%) |
| PosOnly | 0/3 (0%) |
| **PosNeg** | **2/3 (67%)** |

PosNeg wins T_A and T_C at **round 1**. NoKB and PosOnly fail across all 3 rounds.

## Folder map

```
stage2_coupled_study/
├── 01_design/
│   ├── task_definitions.json              T_A, T_B, T_C specs (IC / T / phenomenon target)
│   ├── PDE_TEST_SET_original.md           full design narrative
│   └── PDE_EXPERIMENT_PLAN_original.md    earlier full plan doc
├── 02_prompts/
│   ├── round1/T_A_NoKB.md ... T_C_PosNeg.md    9 r1 prompts
│   ├── round2/T_A_NoKB.md ... T_C_PosOnly.md   7 r2 prompts (cells that failed r1)
│   ├── round3/...                              7 r3 prompts
│   └── memory_blocks/T_A_NoKB.md ... T_C_PosNeg.md   the bank content given per condition
├── 03_scripts/
│   ├── build_round1.py / build_round2.py / build_round3.py
│   ├── run_round1.py / run_round2.py / run_round3.py
│   └── eval/phenomenon_checks.py          deterministic useful/not-useful classifier
├── 04_outputs/
│   └── T_A/{NoKB,PosOnly,PosNeg}/{round1,round2,round3}/
│       prompt.md | memory.md | candidate.py | reasoning.md | exec.log | result.json | eval_result.json | meta.json | pred_results/T_A.npy
│       (T_B, T_C have identical structure; r2/r3 missing when r1 PASSed)
├── 05_results/
│   ├── results_round1.json    all 9 r1 cells
│   ├── results_round2.json    all 7 r2 cells
│   └── results_round3.json    all 7 r3 cells
└── 06_summary/
    └── STAGE2_REPORT.md       full three-condition comparison + case studies
```

## The three sub-tasks

All run on the coupled system:
```
u_t + 3 u u_x = -∂_x (3 v² + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```
γ = ν = 1, periodic x ∈ [-15, 15], Nx = 256.

| Task | Initial condition | T | Phenomenon target |
|---|---|---|---|
| **T_A** soliton stability | `v₀ = 2 sech²(x+5)`, `u₀ = ½v² + 0.2v` (non-pure m=0) | 8.0 | v final has ≥1 peak with amplitude ≥1.0; mass drift < 8% |
| **T_B** Gaussian → soliton train | `v₀ = 4·exp(-(x+5)²/2.25)`, `u₀ = 0` | 6.0 | v final has ≥2 peaks, each ≥0.8 amplitude; mass drift < 8% |
| **T_C** bore × soliton | `u₀ = 1.5(1-tanh(x/0.5))/2`, `v₀ = 1.5 sech²(x+8)` | 8.0 | v final has surviving peak ≥0.5; bore bounded |

## How three conditions differ (and how they don't)

| condition | r1 prompt sees | r2/r3 prompt sees (additionally) |
|---|---|---|
| NoKB | only the task spec | own round-(N-1) failure record |
| PosOnly | task + 10 positive bank entries | same + own round-(N-1) failure |
| PosNeg | task + 30 entries (10 ✓ + 20 ✗) | same + own round-(N-1) failure |

**Crucial**: all three conditions get internal iteration memory in r2/r3. The difference between conditions is **exclusively the Stage 1 bank content** (which never changes across rounds).

## Phenomenon-based eval

See `03_scripts/eval/phenomenon_checks.py` for the deterministic classifier. Each task has its own check; no closed-form reference is used. The classifier returns `(useful: bool, diag: dict)`.

## Most striking finding (Case H — T_C)

| Condition | r1 method choice | Outcome |
|---|---|---|
| NoKB | full-domain spectral + explicit RK4 | NaN (bore blow-up) |
| PosOnly | full-domain IMEX-CN spectral | NaN (bore still blow-up — single method can't handle shock + dispersion) |
| **PosNeg** | **MUSCL+Godunov for `u` (bore) + IMEX-CN spectral for `v` (soliton)** | **✓ PASS** |

The PosNeg agent's *split-method* decision was driven directly by negative bank entries warning against central FD / spectral methods on shock-like fields. PosOnly's reasoning.md cites those concerns implicitly but doesn't have the explicit "split methods" instruction the negative entries provide.

## See also

- `06_summary/STAGE2_REPORT.md` — full numerical results + per-round breakdown
- `../00_HOW_WE_DID_IT.md` § 4 for the narrative
- `../metadata/decision_log.md` § C for design decisions
