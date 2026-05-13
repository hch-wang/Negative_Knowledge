# Negative Knowledge — PDE Autoresearch Experiments

Reproducibility artifact for the paper:
> *Bounded failure records as a team-level shared asset for multi-agent autoresearch on PDE numerical methods.*

A single Sonnet 4.6 model studies the coupled **Burgers-swept-KdV** system (Holm et al. 2025, arXiv:2505.17026) under three memory conditions and measures whether a structured **negative-knowledge bank** built from prior component-PDE stress tests improves outcomes.

## TL;DR

- **30-entry knowledge bank** (10 ✓ positive + 20 ✗ negative) produced by 14 forced-method stress tests on Burgers, KdV, Shallow Water, and Gardner.
- **Three-condition comparison** on 3 coupled sub-tasks × max 3 rounds:

| Condition | Ever-useful / 3 tasks |
|---|---|
| NoKB (no bank) | **0 / 3** |
| PosOnly (10 ✓ only) | **0 / 3** |
| **PosNeg (30 ✓ + ✗)** | **2 / 3 (67%)** |

PosNeg wins at round 1 in two of three sub-tasks. NoKB and PosOnly never succeed across 3 rounds.

## Read this in order

| File | What it tells you |
|---|---|
| **[00_HOW_WE_DID_IT.md](00_HOW_WE_DID_IT.md)** | **Single-document end-to-end narrative.** Start here. |
| [01_HOW_TO_REPRODUCE.md](01_HOW_TO_REPRODUCE.md) | Replay (no API) or full re-run (with API) |
| [stage1_knowledge_production/README.md](stage1_knowledge_production/README.md) | Stage 1: how the bank was built |
| [stage2_coupled_study/README.md](stage2_coupled_study/README.md) | Stage 2: the three-condition study |
| [stage2_coupled_study/06_summary/STAGE2_REPORT.md](stage2_coupled_study/06_summary/STAGE2_REPORT.md) | Full Stage 2 results with per-round breakdown |
| [metadata/decision_log.md](metadata/decision_log.md) | Parent's design decisions (the *why*) |
| [metadata/agent_calls.csv](metadata/agent_calls.csv) | 43 sub-agent calls × token / duration / summary |

## Folder map

```
Negative_Knowledge/
├── README.md                          (this file)
├── 00_HOW_WE_DID_IT.md                ★ start here
├── 01_HOW_TO_REPRODUCE.md
│
├── stage1_knowledge_production/       30-entry knowledge bank + 14 stress tests
│   ├── README.md
│   ├── 02_prompts/                       16 prompts (14 stress + 2 curator)
│   ├── 03_scripts/                       builders / runners
│   ├── 04_outputs/                       14 sandboxes + stage1_results.json
│   ├── 05_knowledge_bank/                knowledge_bank.jsonl
│   └── 06_summary/STAGE1_INDEX.md
│
├── stage2_coupled_study/              coupled-BKdV three-condition study
│   ├── README.md
│   ├── 01_design/task_definitions.json   T_A, T_B, T_C specs
│   ├── 02_prompts/                       23 prompts (round1 × 9 + round2 × 7 + round3 × 7) + memory_blocks/
│   ├── 03_scripts/                       builders / runners / eval/phenomenon_checks.py
│   ├── 04_outputs/                       23 sandbox dirs
│   ├── 05_results/                       results_round{1,2,3}.json
│   └── 06_summary/STAGE2_REPORT.md
│
├── reference_solvers/                 Burgers / KdV / Shallow Water reference solvers
│   ├── burgers_shock_ref.py
│   ├── kdv_soliton_ref.py
│   ├── shallow_water_ref.py
│   └── ref_results/*.npy
│
├── early_bkdv_pilot/                  earlier BKdV pilot used as Cases F and G
│   ├── burgers_T05_case_F/sonnet_4.6/round1/   (✓ PASS, "positive control")
│   ├── kdv_T2_case_G/sonnet_4.6/round1/        (✗ NaN)
│   ├── kdv_T2_case_G/sonnet_4.6/round2_M4/     (✓ PASS via IMEX-CN)
│   ├── eval/*.py
│   └── CASE_F_G_STUDIES.md
│
└── metadata/
    ├── agent_calls.csv                 43-call table
    ├── decision_log.md                 parent decision narrative
    └── EXPERIMENT_MANIFEST_original.md
```

## Key statistics

- **43 sub-agent calls** total (all Sonnet 4.6)
- **~940k tokens** total
- **~80 min wall-clock**
- **~3.3 MB** on disk (no `.venv`, no `__pycache__`)
- **30 knowledge entries**, 100% with valid evidence file citations
- **131 originally hardcoded absolute paths** → anonymized to `${PROJECT_ROOT}` etc.

## What the bank schema looks like

Each entry in `stage1_knowledge_production/05_knowledge_bank/knowledge_bank.jsonl` is one JSON object on its own line. Two flavors:

### Positive (10 entries)

```json
{
  "id": "kb-kdv-IMEX-CN-spectral-pass",
  "kind": "positive",
  "domain": "kdv",
  "method": "Fourier pseudospectral + Crank-Nicolson on dispersion + explicit on nonlinear",
  "claim": "Works at dt=0.0005 with mass conserved to ~1e-6",
  "regime": "1D periodic v_t + 6vv_x + v_xxx = 0, soliton IC",
  "evidence": [{"file": "${PROJECT_ROOT}/runs/kdv_T2/sonnet_4.6/round2_M4/reasoning.md", "summary": "..."}],
  "applicability": "Stage 2 KdV component of coupled Burgers-swept-KdV system"
}
```

### Negative (20 entries)

```json
{
  "id": "kb-burgers-fwdEuler-centralFD-Gibbs",
  "kind": "negative",
  "domain": "burgers",
  "attempted_route": "Forward Euler + 2nd-order central FD, CFL=0.4",
  "observation": "21 local maxima (expected 1), amplitude_range=7.21 (~3.6× truth)",
  "failure": {
    "layer": "method_failure",
    "scope": "general_failure",
    "degree": "contradicted",
    "recommended_action": "change_method",
    "risk": "high_risk_false_progress"
  },
  "rationale": "Central differencing on a nonlinear hyperbolic equation has no upwind dissipation; post-shock oscillations grow unbounded.",
  "evidence": [{"file": "${PROJECT_ROOT}/stage1/sandboxes/A1/result.json", "summary": "21 local maxima, amplitude_range 7.21"}],
  "applicability": "Coupled Burgers-swept-KdV: any naive central-FD treatment of the Burgers advection term will corrupt both the Burgers bore and the adjacent KdV soliton region"
}
```

## Citation

(to be added once the paper is accepted)

## License

CC-BY-4.0 for documentation; MIT for code unless noted.

---

**Built with Claude Code 4.7 (Anthropic).** All sub-agent calls used Sonnet 4.6.
