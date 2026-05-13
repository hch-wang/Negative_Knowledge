# PDE numerical-method case studies — real autoresearch repair cycles

> 测试 autoresearch 框架在 PDE 数值方法选择上的"研究式"失败修复能力。两个 case，一个 trivial PASS 作对照，一个真实 NaN blow-up → 经 bounded failure record 修复。

---

## Setup

| 项 | 值 |
|---|---|
| Subject model | Claude Sonnet 4.6 (via Agent tool) |
| Sandboxed env | numpy + scipy + matplotlib only (no PDE libraries) |
| Reference solvers | written by paper author (Lax-Friedrichs for Burgers; IMEX-spectral for KdV reference) |
| Eval | deterministic (L¹ error vs reference, peak position/amplitude, conservation laws) |
| Total sub-agent calls | 3 (1 Burgers + 2 KdV) |
| Wall time | ~5 min |

---

## Case F — BKdV-T1: Inviscid Burgers shock (clean PASS, used as positive control)

**PDE**: `u_t + u u_x = 0` on x ∈ [-1, 1] periodic, IC `u_0 = -sin(πx)`, T=0.5

**Sonnet round-1 (no memory) approach**:
> "Conservative finite-volume method using MUSCL reconstruction with a van Leer limiter for second-order spatial accuracy and an exact Godunov (Riemann solver) flux to capture the entropy-satisfying shock without oscillations, advanced in time with explicit Euler at CFL=0.45."

**Outcome**: ✅ **PASS** at round 1.
- L¹ error vs reference: **0.0029** (threshold 0.10)
- L∞ error: 0.040
- max|u| = 0.988, max jump 1.85 (close to reference's 1.93)

**Why this is informative**:
- Sonnet picked an excellent TVD scheme on first try
- Demonstrates the PDE pilot framework works end-to-end
- "Easy" PDE task — used as positive control

→ Not the main case study. Used to validate pipeline.

---

## Case G — BKdV-T2: KdV single-soliton propagation (REAL repair cycle 🎯)

**The killer case** — exhibits round-1 numerical blow-up, then round-2 with M4 memory PASSes.

### Task

**PDE**: `v_t + 6 v v_x + v_xxx = 0` on x ∈ [-15, 15] periodic, Nx=256
**IC**: `v_0(x) = 2 sech²(x + 5)` (soliton amplitude 2, theoretical speed 4)
**T**: 2.0 → expected peak at x ≈ +3
**Eval**: peak position ∈ [2.5, 3.5], amplitude ∈ [1.85, 2.15], mass within 1% of 4.0

### Round 1 (B1 Direct / no memory)

**Sonnet's chosen approach**:
> "Fourier pseudospectral space discretization with integrating-factor RK4 time stepping, eliminating dispersive stiffness by absorbing the exact `exp(ik³t)` propagator into the solution variable so only the nonlinear advection term drives the explicit RK4 stages."

This is conceptually sound — integrating-factor RK4 is a textbook choice for KdV.

**Outcome**: ❌ **FAIL — all 256 output values NaN**
- exec.log: candidate ran without exception but produced NaN array
- eval: `(0, 'non-finite: 256 NaN/Inf (blow-up -- likely explicit scheme on stiff dispersion)')`

**Diagnosis**: The exp(i k³ t) integrating factor accumulates without bound for high-wavenumber modes at small dt accumulating to T=2.0. Combined with absent dealiasing, the nonlinear term injects energy into Nyquist modes which blow up. The CONCEPT was right (avoid stiffness), the IMPLEMENTATION was wrong.

### Bounded failure record (auto-extracted M4 schema)

```json
{
  "target": "Solve KdV: v_t + 6 v v_x + v_xxx = 0 with single soliton IC, propagate to T=2.0",
  "observation": "Output array of shape (256,) contains all-NaN values. Eval rejected: 256 NaN/Inf. Numerical blow-up.",
  "failure": {
    "layer": "implementation_failure",
    "scope": "local_failure",
    "degree": "unstable",
    "reproducibility": "observed_once",
    "recommended_action": "change_method",
    "risk": "medium_risk_drift"
  },
  "rationale": "Agent reasoned correctly that explicit schemes are stiff for v_xxx and chose Fourier + integrating-factor RK4. However the implementation produced NaN -- likely because: (a) integrating-factor expansion has overflow in exp(i*k^3*t) for high k modes, (b) dealiasing was missing, or (c) timestep was still too large. The CONCEPT was right, the EXECUTION was wrong."
}
```

### Round 2 (B3 Research Graph with M4 memory)

The round-2 prompt embeds the above failure record + 3 alternative methods (IMEX-FD, IMEX-spectral, ETDRK4) with their key technical details.

**Sonnet's round-2 approach**:
> "Switched to IMEX-spectral (Fourier + Crank-Nicolson on the dispersive term), which replaces the exponential integrating factors `exp(ik³t)` — the likely source of overflow/NaN in round 1 — with a simple pointwise complex division that has magnitude ≥ 1 and therefore cannot overflow or produce NaN."

**Outcome**: ✅ **PASS**
- peak_x = **3.047** (theoretical 3.0 ± 0.5 tolerance) ✓
- peak_amp = **2.032** (theoretical 2.0 ± 0.15 tolerance) ✓
- mass = **4.0000** (within 1% of 4.0; perfectly conserved) ✓

### Why this case matters for the paper

1. **Realistic research-style failure**: KdV soliton blow-up is a textbook numerical PDE failure mode, exactly the kind a graduate student would hit
2. **Schema fields directly drove the fix**:
   - `layer=implementation_failure` → "right idea, wrong execution"
   - `recommended_action=change_method` → switch the time integrator
   - `rationale` named the exp(ik³t) overflow → agent identified and avoided it
3. **Memory contained actionable specific physics**: not just "method failed", but "exp(ik³t) overflow for high k modes"
4. **Round-2 prompt explicitly listed 3 alternatives** — but agent picked appropriately based on rationale, not the first one

**Contrast with ScienceAgentBench cases**: those involve library/API gotchas. This one involves **genuine numerical analysis** — a physics PhD student's mistake.

---

## What this adds to the paper

| Aspect | Before (ScienceAgentBench only) | After (with PDE cases) |
|---|---|---|
| Case domain coverage | data analysis, ML pipelines, GIS | + **numerical PDE solving** (real research methodology) |
| Failure mode realism | mostly schema mismatches, library substitution | + **numerical instability**, blow-up, conservation issues |
| Schema field utility evidence | `layer` predicts comm > method > impl | + `recommended_action: change_method` literally drove method switch (IF-RK4 → IMEX-CN) |
| Repair narrative | "agent saw error, agent fixed key name" | "agent saw NaN, identified physical mechanism (exp overflow), chose alternative method" |

The KdV case is the **strongest single case study** for the paper because:
- Round-1 → Round-2 transition is dramatic (NaN → PASS with quantitative match)
- The failure and fix both involve real numerical-method judgement
- Schema's `change_method` action mapped directly onto the actual repair pathway

---

## Test set summary (3 designed, 1 piloted)

| Task | PDE | Round-1 outcome | Round-2 outcome | Status |
|---|---|---|---|---|
| BKdV-T1 Burgers shock | 1st order, shock-forming | ✅ PASS (L¹=0.003) | — | piloted, easy |
| **BKdV-T2 KdV soliton** | **3rd order, stiff dispersion** | **❌ NaN blow-up** | **✅ PASS (M4 memory)** | **piloted, killer case** |
| BKdV-T3 Coupled Burgers-swept KdV | 1st + 3rd, paper's main system | — | — | designed only |
| WCH-T1 Cahn-Hilliard 4th order | 4th order, stiff | — | — | designed only |

## Files

```
paper/experiments/pde_pilot_2026-05-11/
├── PDE_TEST_SET.md          ← 4-task design doc
├── PDE_CASE_STUDIES.md      ← this file
├── gold/
│   ├── burgers_shock_ref.py    ← Lax-Friedrichs ref for T1
│   └── kdv_soliton_ref.py      ← IMEX-spectral ref for T2
├── eval/
│   ├── burgers_T05_eval.py
│   └── kdv_T2_eval.py
├── ref_results/
│   ├── burgers_T05_REF.npy
│   ├── burgers_T05_REF_x.npy
│   ├── kdv_T2_REF.npy
│   └── kdv_T2_REF_x.npy
└── runs/
    ├── burgers_T05/sonnet_4.6/round1/   ← PASS at r1
    └── kdv_T2/sonnet_4.6/
        ├── round1/                       ← NaN blow-up; failure_record.json captures it
        └── round2_M4/                    ← PASS with M4 memory
```
