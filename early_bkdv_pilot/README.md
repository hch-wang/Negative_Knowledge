# Early BKdV Pilot (Cases F & G)

Earlier exploratory runs on standalone Burgers shock and KdV soliton — predates the Stage 1 / Stage 2 systematic design. Kept as supplementary case studies.

## Case F: Burgers shock (positive control)

**Directory**: `burgers_T05_case_F/sonnet_4.6/round1/`
- PDE: `u_t + u u_x = 0` on [-1,1] periodic, IC `u_0 = -sin(πx)`, T=0.5
- Sonnet 4.6 chose: MUSCL + van Leer + Godunov + forward Euler, CFL=0.45
- **Outcome: ✓ PASS** (L1 = 0.003 vs reference)
- Used in the paper as the "system works on a clean control task" sanity check.

## Case G: KdV soliton (round-1 fail → round-2 fix)

**Directory**: `kdv_T2_case_G/sonnet_4.6/`
- PDE: `v_t + 6vv_x + v_xxx = 0`, IC `v_0 = 2 sech²(x+5)`, T=2.0, expected peak at x=+3
- **Round 1** (`round1/`): Sonnet chose Fourier pseudospectral + integrating-factor RK4
  - **Outcome: ✗ All-NaN**. Integrating factor exp(ik³t) overflows for high modes at this dt.
- **Round 2** (`round2_M4/`): re-prompted with M4 bounded failure record from round 1
  - Sonnet switched to: Fourier + Crank-Nicolson IMEX
  - **Outcome: ✓ PASS** (peak x=3.05, amp=2.03, mass=4.000)

This is the **killer case study** for the paper's central claim: a single structured failure record (the M4 record from round 1) drove the agent to switch from a stiffness-explicit to a stiffness-implicit method, producing a working solver in round 2.

## Files

```
burgers_T05_case_F/
└── sonnet_4.6/round1/
    ├── prompt.md          original prompt
    ├── candidate.py       Sonnet's solver code
    ├── reasoning.md       Sonnet's self-explanation
    ├── exec.log
    ├── result.json
    └── pred_results/burgers_T05.npy

kdv_T2_case_G/
└── sonnet_4.6/
    ├── round1/...               same structure (✗ NaN)
    └── round2_M4/...            same structure + memory.md (✓ PASS)
```

See `CASE_F_G_STUDIES.md` for the full prose narrative.
