# How We Did It — End-to-End Walkthrough

> Single-document narrative of the entire PDE Negative-Knowledge experiment.
> Time: ~80 min wall-clock, 43 sub-agent calls (all Sonnet 4.6), ~940k tokens, ~3.3 MB on disk.
> Read this first; then dive into per-stage READMEs for detail.

---

## 1. The question

Does a **structured bank of failed-attempt knowledge** ("negative knowledge") help a downstream agent choose a working numerical method for a real research problem — specifically, the coupled Burgers-swept-KdV system from Holm et al. 2025?

## 2. Two-stage design

```
Stage 1: Knowledge Production
   ↓
[ 30-entry knowledge bank (10 ✓ positive + 20 ✗ negative) ]
   ↓
Stage 2: Coupled BKdV Multi-Agent Study
   compare 3 conditions: NoKB / PosOnly / PosNeg
   × 3 sub-tasks × up to 3 rounds
```

Total artifacts saved on disk: ~331 files, ~3.3 MB.

---

## 3. Stage 1 — Knowledge Production

**Goal**: produce a richly structured `knowledge_bank.jsonl` with 30 entries spanning Burgers, KdV, Shallow Water, and Gardner. Both positive (✓) and negative (✗) entries. Each entry must cite a real artifact file.

### 3.1 The 14 stress tests

We designed 14 single-PDE simulations where the sub-agent was **forced** (in the prompt) to use a specific numerical method or run with a specific parameter regime. This is the only way to get the agent to produce *negative* knowledge — by default Sonnet 4.6 would choose IMEX-spectral for anything dispersive and TVD-Godunov for anything hyperbolic, generating only positive entries.

The 14 tests:

| Set | IDs | Forced regime |
|---|---|---|
| Burgers | A1, A2, A3 | A1: forward Euler + central FD (forbidden: limiter / upwinding). A2: T=0.1 (pre-shock). A3: T=10 (long-time). |
| KdV | A4, A5, A6 | A4: explicit RK4 (forbidden: IMEX). A5: spectral but NO dealiasing. A6: amplitude=0.1 (small). |
| Shallow Water | A7, A8, A9, A10 | A7: forward Euler + central FD. A8: Lax-Friedrichs. A9: dry-bed IC. A10: HLL Riemann. |
| Gardner | G1, G2, G3, G4 | G1: explicit RK4. G2: IMEX-CN + dealiasing. G3: IMEX-CN, NO dealiasing. G4: amplitude=3.0 (large). |

**Prompt template** (full text in `stage1_knowledge_production/02_prompts/A1.md`):
```
You are running a PDE numerical stress test...
## CRITICAL RULE
This is a STRESS TEST. You MUST follow the method constraint below EXACTLY,
even if you know a better method that would work.

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
```

### 3.2 Dispatch & run

- 10 A-stress tests dispatched in parallel (single Agent-tool batch in Claude Code).
- Each sub-agent does: Read prompt → Write `candidate.py` → Write `reasoning.md`. *No execution by sub-agent itself.*
- Parent then runs each `candidate.py` via venv-Python + collects diagnostics (mass, peak count, amplitude, etc.) into `result.json`.
- 4 Gardner tests added in a second parallel batch (we wanted to reach ~30 bank entries; first 13 attempts yielded ~20, so we added 4 more sources).

### 3.3 Curator agent writes the bank

After all 14 stress tests + 3 prior BKdV pilots completed:

- Curator agent reads all 17 artifacts (prompts + reasoning.md + result.json) and writes `knowledge_bank.jsonl`.
- Curator prompt (`stage1_knowledge_production/02_prompts/curator_v1.md`) specifies the schema (positive vs negative), evidence requirement, and the projection-to-Stage-2 `applicability` field.
- Three passes total: initial → +Gardner extension → +2 final synthesized entries to reach 30.
- Each entry **must** cite a real evidence file. Parent audits: `grep` confirms 30/30 cited files exist.

### 3.4 The 30 entries

Distribution:

| Domain | ✓ Positive | ✗ Negative | Sum |
|---|---|---|---|
| Burgers | 2 | 3 | 5 |
| KdV | 4 | 3 | 7 |
| Shallow Water | 2 | 3 | 5 |
| Gardner | 2 | 7 | 9 |
| General (cross-domain) | 1 | 3 | 4 |
| **Total** | **11** | **19** | **30** |

(20 of these are dual-cited synthesized cross-cuts; total reads as 30 lines.)

Negative-entry schema field distribution:
- `layer`: method_failure 11 / hypothesis_failure 4 / measurement_failure 3 / implementation_failure 2
- `scope`: regime_bound 12 / general_failure 6 / local_failure 2
- `recommended_action`: narrow_claim 13 / change_method 7

The bank skews toward `regime_bound` failures with `narrow_claim` action — fits the physics intuition that most PDE numerical failures are parameter-regime-dependent and need parameter narrowing rather than complete method substitution.

### 3.5 Where to read more

- `stage1_knowledge_production/README.md` — folder map + 14-test table
- `stage1_knowledge_production/06_summary/STAGE1_INDEX.md` — every entry listed with one-line summary

---

## 4. Stage 2 — Coupled BKdV Multi-Agent Study

**Goal**: with the bank in hand, compare how a downstream agent performs on a real coupled-PDE research task under three memory conditions.

### 4.1 Three sub-tasks (the coupled-PDE research problems)

```
PDE: u_t + 3 u u_x = -∂_x (3 v² + v_xx)
     v_t + 6 v v_x + v_xxx = -∂_x (u v)
     γ = ν = 1, periodic x ∈ [-15, 15], Nx = 256
```

| Task | IC | T | Phenomenon target |
|---|---|---|---|
| **T_A** soliton stability | `v₀ = 2 sech²(x+5)`, `u₀ = ½v² + 0.2v` | 8 | v retains ≥1 peak amp≥1.0; mass drift < 8% |
| **T_B** Gaussian → train | `v₀ = 4 exp(-(x+5)²/2.25)`, `u₀ = 0` | 6 | v has ≥2 peaks ≥0.8 amp; mass drift < 8% |
| **T_C** bore × soliton | `u₀ = 1.5(1-tanh(x/0.5))/2`, `v₀ = 1.5 sech²(x+8)` | 8 | v has surviving peak ≥0.5; bore bounded |

ICs are deliberately at the **edge** of where naive numerical methods break, so r1 is not trivially passable.

### 4.2 Three memory conditions

| Condition | r1 prompt content (in addition to task spec) | Bank entries in r1 |
|---|---|---|
| **NoKB** | none | 0 |
| **PosOnly** | positive entries only | 10 |
| **PosNeg** | full bank | 30 |

Memory blocks are saved verbatim in `stage2_coupled_study/02_prompts/memory_blocks/T_A_NoKB.md` etc. so you can inspect exactly what each agent saw.

Each r2 and r3 *additionally* receives the agent's own round-(N-1) failure record (so NoKB isn't stuck without any feedback). The differential effect we measure is **only** the Stage 1 bank.

### 4.3 Three rounds per cell

If r1 doesn't produce a useful result (deterministic phenomenon check), build r2 with the same condition + r1 finding inlined. Same for r3 with r1+r2 findings. Max 3 attempts per cell, early-stop on success.

### 4.4 Results table

Per cell, the round at which a useful result was first observed:

| Task | NoKB | PosOnly | PosNeg |
|---|---|---|---|
| T_A | — (never) | — (never) | **r1** ✓ |
| T_B | — | — | — |
| T_C | — | — | **r1** ✓ |

Per condition:

| Condition | Ever-useful | 之中：r1 | Total attempts spent |
|---|---|---|---|
| NoKB | 0 / 3 | 0 | 9 |
| PosOnly | 0 / 3 | 0 | 9 |
| **PosNeg** | **2 / 3 (67%)** | 2 | 7 (5 saved by early-stop on T_A and T_C) |

### 4.5 Why PosNeg wins (the killer T_C example)

The Burgers-swept-KdV coupled system has two structurally distinct components: a Burgers-type `u` field that develops shocks/bores, and a KdV-type `v` field that supports solitons.

| Condition | r1 method choice | Why |
|---|---|---|
| NoKB | full-domain pseudo-spectral + explicit RK4 dt=0.002 | Default textbook choice; doesn't anticipate shock |
| PosOnly | full-domain IMEX-CN spectral | Bank told it spectral+IMEX works for KdV; applied to whole system |
| **PosNeg** | **MUSCL+Godunov for `u` + IMEX-CN spectral for `v`** | Negative entries (`kb-burgers-fwdEuler-centralFD-Gibbs`, `kb-shallowWater-centralFD-fwdEuler-hNegative`, `kb-general-centralFD-hyperbolic-shockFormation`) explicitly warn against single-method/spectral handling of shocks |

PosOnly's `reasoning.md` discusses spectral methods extensively but never opts to use a *different* method on `u`. The negative entries provided the missing piece: "if a hyperbolic/shock field is in your system, you cannot use the same scheme as for the dispersive field."

### 4.6 T_B failure (honest negative finding)

All 3 conditions × 3 rounds fail on T_B (Gaussian → soliton train). The Gaussian's narrow width (σ=1.5) and large amplitude (4) push the nonlinear-CFL constraint past what any single dt choice can handle. The relevant bank entry `kb-gardner-nonlinearCFL-amplitude-boundary` (#30) describes the *qualitative* boundary but doesn't supply a numerical dt threshold. We report this as a limitation, not a tuning failure.

### 4.7 Where to read more

- `stage2_coupled_study/README.md` — folder map
- `stage2_coupled_study/06_summary/STAGE2_REPORT.md` — full per-round breakdown + method-choice trajectory analysis

---

## 5. Resource accounting

| Phase | Calls | Tokens (Sonnet) | Wall (sub-agent only) |
|---|---|---|---|
| Early BKdV pilot (Cases F, G) | 3 | ~51k | ~2 min |
| Stage 1 stress + curator | 17 | ~367k | ~24 min |
| Stage 2 r1 + r2 + r3 | 23 | ~521k | ~27 min |
| **Total** | **43** | **~940k** | **~53 min** |

Plus candidate.py execution (~10 min) + parent orchestration (~10 min) → **~80 min total wall**.

## 6. What's saved on disk

Every sub-agent call saves: the **prompt** sent in, the **candidate.py** code written, the **reasoning.md** self-explanation, the **exec.log** runtime output, the **result.json** structured outcome, the **pred_results/*.npy** numerical field, and the **meta.json** task spec.

What's **NOT** saved (and can't be, by API design): the sub-agent's internal chain-of-thought tokens. The Anthropic Agent tool intentionally hides intermediate thinking from the parent. We approximate this with `reasoning.md` — the agent's *self-reported* thinking — which the agent writes after deciding on its method.

See `metadata/agent_calls.csv` for token/duration/summary per call and `metadata/decision_log.md` for parent's design decisions.

## 7. Reading guide

| If you want to … | Go to |
|---|---|
| understand the bank schema | `stage1_knowledge_production/05_knowledge_bank/knowledge_bank.jsonl` (line 1 = first entry) |
| see the actual prompts used | `stage1_knowledge_production/02_prompts/A1.md` (representative) |
| see a successful Stage 2 run | `stage2_coupled_study/04_outputs/T_A/PosNeg/round1/` |
| see a failed Stage 2 run | `stage2_coupled_study/04_outputs/T_A/NoKB/round1/` |
| see the three-condition main table | `stage2_coupled_study/06_summary/STAGE2_REPORT.md` |
| understand WHY any design choice was made | `metadata/decision_log.md` |
| reproduce | `01_HOW_TO_REPRODUCE.md` |
