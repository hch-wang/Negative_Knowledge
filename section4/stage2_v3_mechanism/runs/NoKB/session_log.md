# Session log — stage2_v3_mechanism / NoKB

Working dir: /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3_mechanism/runs/NoKB
Solver: Fourier pseudospectral, IF-RK4 with 2/3 dealiasing + mild hyperviscosity on u
Total executions consumed: 3 rounds (E1, E2, E3). One earlier execution attempted with dt=2e-3 blew up; bug-fix re-run (smaller dt + hyperviscosity) was done WITHOUT consuming a round, per the prompt's "bug-fix re-runs that test the SAME hypothesis do NOT count".

## Round 1 — E1 (on-manifold vs off-manifold IC; H_A vs H_B vs H_C)
- IC_A (||m_0||_L2=0.063, near-Gardner) and IC_B (||m_0||_L2=0.479, mismatched), both with v-mass=1.6.
- T=20, dt=5e-4, mild hyperviscosity on u.
- KEY FINDING (F1): ||m|| GREW in BOTH cases to ≈1.20. Both ICs converged to a NEAR-COMMON late-time state, but NOT on Gardner manifold. H_A falsified. lock_corr 0.98→0.29 (A) and 0.66→0.35 (B). E_high_v dropped ~10x in both (radiative decay of v); E_high_u grew (Burgers steepening). Mass exact.

## Round 2 — E2 (coupling ablation; H_B vs H_F vs H_BALANCE)
- Three RHS variants on same IC_B: M0 (full), M1 (no v_xxx in v-eq), M2 (no 3 u u_x in u-eq).
- T=20, dt=5e-4.
- KEY FINDING (F2): M1 blew up at t=0.19 (modulational instability — partially trivial finding because removing dispersion always destabilizes). M2 did NOT blow up but L2_u grew 4.4x and L2_v 1.8x; ||m||→2.61. Both terms are essential — supports H_BALANCE (H_FORCED-BURGERS-SINK).

## Round 3 — E3 (robustness + numerical-artifact falsification)
- Four ICs at same v-mass=1.6: IC_C (noisy u), IC_D (2-pulse v), IC_E (tall narrow v), IC_F (E1 baseline with 100x hyperviscosity).
- T=20, dt=5e-4.
- KEY FINDING (F3):
  * Late-time state NOT a function of v-mass alone — IC_D, IC_E, IC_F differ in L2_u/L2_v by factors 1.5-2x at t=20. Weakens strong H_C.
  * IC_C (random noise) did NOT converge — runaway growth at ||m||=6.92. Basin of attraction does NOT include arbitrary noise on this timescale.
  * IC_F (100x hyperviscosity): ||m||_L2 shifted 1.19→0.99 (~17%), lock 0.35→0.51. Quantitative late-time observables are partly dissipation-set; qualitative compound-formation picture survives.

## Final outputs
- hypothesis.md (main deliverable)
- research_state.jsonl (Q/E/F/D nodes)
- candidate.py (most recent — E3 script)
- pred_results/E1_*.npz, E2_*.npz, E3_*.npz (numerical snapshots and time series)
- evidence/E1_summary.json, E2_summary.json, E3_summary.json (compact JSON summaries)
- evidence/E1_analysis.txt (post-process readout for E1)

Best current hypothesis: H_FORCED-BURGERS-SINK — compound coherent states form because u's Burgers self-flux absorbs v^2-driven forcing as moving fronts/shocks while v's KdV dispersion radiates excess high-k content. m=0 is NOT attracting (it is repelling); the compound state has m != 0 and partial (not strict) u/(v^2/2) locking.
