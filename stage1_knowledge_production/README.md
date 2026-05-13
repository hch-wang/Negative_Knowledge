# Stage 1 — Knowledge Production

## What this stage does

Generate a **30-entry knowledge bank** (`05_knowledge_bank/knowledge_bank.jsonl`) of positive (✓) and negative (✗) findings about numerical methods for three component PDEs: Burgers, KdV, and Shallow Water — plus Gardner (the m=0 reduction of the coupled system that Stage 2 will study).

The bank entries are designed to be **reusable** by future agents working on a coupled Burgers-swept-KdV system (Stage 2).

## How

1. **14 stress tests** (`04_outputs/A1..A10, G1..G4/`), each a single PDE simulation where the sub-agent is **forced** to use a specific (often naive) numerical method or parameter regime.
2. **Curator agent** (`02_prompts/curator_v1.md`, `curator_v2_extension.md`) reads all stress-test outputs + 3 prior BKdV pilot runs and writes the bank as JSONL.
3. **Audit**: every entry must cite a real evidence file; the audit script verifies all 30 entries reference existing artifacts.

## Folder map

```
stage1_knowledge_production/
├── 01_design/                  (currently empty; design lives in 00_HOW_WE_DID_IT.md)
├── 02_prompts/                 16 prompt files
│   ├── A1.md ... G4.md             14 stress-test prompts (each forces a specific method)
│   ├── curator_v1.md               first curator pass (read 10 A-stress + 3 pilot, write 20 entries)
│   └── curator_v2_extension.md     extension pass (add Gardner findings → 30 entries)
├── 03_scripts/                 3 scripts
│   ├── build_stress_tests.py      builds sandboxes A1-A10
│   ├── build_gardner_tests.py     builds sandboxes G1-G4
│   └── run_stress_tests.py        runs all 14 candidate.py + collects diagnostics
├── 04_outputs/                 14 sandbox dirs + 1 aggregate JSON
│   ├── A1/  candidate.py | reasoning.md | exec.log | result.json | meta.json | pred_results/*.npy
│   ├── ...  (same structure for A2-G4)
│   └── stage1_results.json        all 14 runs' diagnostics
├── 05_knowledge_bank/
│   ├── knowledge_bank.jsonl       ★ 30 entries (10 ✓ + 20 ✗)
│   ├── audit_report.md            evidence-existence audit (30/30 pass)
│   └── entries_by_domain.md       human-readable grouping
└── 06_summary/
    └── STAGE1_INDEX.md            full index with all 30 entries listed + Stage 2 mapping
```

## The 14 stress tests at a glance

| ID | PDE | Forced constraint | Outcome |
|---|---|---|---|
| A1 | Burgers | forward Euler + central FD | Gibbs oscillations, 21 peaks vs expected 1 |
| A2 | Burgers | T=0.1 (pre-shock) | smooth wave, no shock features |
| A3 | Burgers | T=10 (long-time) | amplitude decay to ±0.09 |
| A4 | KdV | explicit RK4 | soliton fragments into 10 peaks |
| A5 | KdV | spectral, NO dealiasing | amplitude inflation 2.87 vs 2.0, 4 spurious peaks |
| A6 | KdV | amplitude 0.1 (small) | soliton character lost (8 peaks) |
| A7 | SW | forward Euler + central FD | h goes negative (-0.139); explosive blow-up |
| A8 | SW | global Lax-Friedrichs | works, diffusive |
| A9 | SW | dry-bed IC | positivity barely held (h_min=0.002 via clip) |
| A10 | SW | HLL Riemann | clean dam-break |
| G1 | Gardner | explicit RK4 | mass=3.000 but soliton fragments to 14 peaks |
| G2 | Gardner | IMEX-CN + dealiasing | stable, IC radiates (not Gardner soliton) |
| G3 | Gardner | spectral, NO dealiasing | cubic aliasing (11 peaks at amp 1.5) |
| G4 | Gardner | amp = 3.0 | full NaN (nonlinear CFL violated) |

## How prompts are organized

- **Template common across all 14**: every stress-test prompt has identical structure, only `constraint`, `pde_spec`, `ic`, `T`, `predicted` vary. See `02_prompts/A1.md` for the exact template — substitute fields to get any other test.
- **Curator prompts** are independent: they instruct the curator on schema (positive vs negative), evidence requirements, and per-entry constraints.

## Knowledge bank schema (30 entries)

Each line of `knowledge_bank.jsonl` is a JSON object. Two variants:

```json
// Positive (10 entries)
{
  "id": "kb-burgers-MUSCL-Godunov-shock-pass",
  "kind": "positive",
  "domain": "burgers | kdv | shallow_water | gardner | general",
  "claim": "...",
  "method": "...",
  "regime": "...",
  "evidence": [{"file": "...", "summary": "..."}],
  "applicability": "..."  // projects entry onto coupled BKdV sub-tasks
}

// Negative (20 entries)
{
  "id": "kb-burgers-fwdEuler-centralFD-Gibbs",
  "kind": "negative",
  "domain": "burgers",
  "attempted_route": "...",
  "observation": "...",
  "failure": {
    "layer": "method_failure | implementation_failure | measurement_failure | hypothesis_failure",
    "scope": "local_failure | regime_bound | general_failure",
    "degree": "contradicted | partial | unstable | overclaimed | artifact_driven",
    "recommended_action": "retry | change_method | narrow_claim | abandon_route",
    "risk": "low_risk_omission | medium_risk_drift | high_risk_false_progress"
  },
  "rationale": "...",
  "evidence": [{"file": "...", "summary": "..."}],
  "applicability": "..."
}
```

## See also

- `STAGE1_INDEX.md` (in `06_summary/`) — full bank table with all 30 IDs and their mapping to Stage 2 sub-tasks.
- `../00_HOW_WE_DID_IT.md` § 3 for the narrative.
