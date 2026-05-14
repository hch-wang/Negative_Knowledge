# Session log: B2 / PosNeg

Class B mechanism-inquiry sub-agent. Task: BKdV bore-soliton interaction
phase diagram. Bank: 58 entries (15 positive + 43 negative, 7 deep).

Pre-validated stack: Fourier pseudospectral (Nx=256, L=30) + 2/3 dealias
+ classical RK4 + dt=1e-4 + explicit nu=5e-2 on u-equation (BKdV-S6).

## Round 1 (E1 / F1 / D1)
- E1: 4x4 coarse (u_L, A) scan in {0.5,1.0,1.5,2.0}^2, T=4, bore on LEFT
  (x=-7), soliton on RIGHT (x=+5). 24 cells in 351.8 s wall.
- F1: classification grid is row-invariant in u_L; outcome depends on A
  only. But T=4 contaminated by periodic wrap (soliton speed c~2A
  traverses ~12 units in T=4 on L=30 domain). Falsifies H_beta coarsely.
- D1: redesign with bore on RIGHT, soliton on LEFT moving RIGHT, T=2,
  u0=v0^2/2+bore (Gardner-seeded soliton per BKdV-S7).

## Round 2 (E2 / F2 / D2)
- E2: redesigned geometry, 8-point A grid in [0.3, 2.5] x 3 u_L levels
  {0, 0.5, 1.5}, T=2, time-resolved diagnostics. 24 cells in 146.8 s.
- F2: dx_centroid (interaction - free) flips sign between A=1.2 and
  A=1.5, coinciding with BKdV-S5 deep (v-1) algebraic threshold;
  retention non-monotonic (dips at A=1.8, rises at A=2.5).
- D2: 3-part E3 to (A) localize the transition finely, (B) test bore
  sharpness orthogonally, (C) falsify kinematic gate by separation.

## Round 3 (E3 / F3 / D3)
- E3: PART A (8 fine A in [0.7,1.75] x 2 uL, T=2), PART B (bore_w in
  {0.25,0.5,1.0} at A=1.5, T=3), PART C (sep in {6,9,12} at A=1.5).
  ~30 cells total in 235.8 s.
- F3: (A) dx_centroid(A) monotone-smooth, zero-crossing A_c ~ 1.30 for
  both uL values; (B) bore_w INVARIANT to 1e-3, falsifying bore-
  sharpness mechanism; (C) separation INVARIANT to 12%, falsifying
  H_alpha kinematic gate. Single coherent mechanism: amplitude-driven
  SMOOTH transition at A_c ~ 1.30.
- D3: wrap up. Two regimes (acceleration / deceleration), smooth
  boundary, mechanism = BKdV-S5 (v-1) source threshold shifted by
  transient peak reduction.

## Wall-time totals
E1 351.8 s, E2 146.8 s, E3 235.8 s. Total ~12 minutes.

## Output map
- hypothesis.md      : main report (regimes, boundary, sharpness, evidence)
- research_state.jsonl: Q/E/F/D nodes with cites/rejects/rationale
- candidate.py       : E3 driver (most recent experiment)
- evidence/E1_*.npz  : 24 cells of E1 snapshots
- evidence/E2_*.npz  : 24 cells of E2 trajectories + snapshots
- evidence/E3_*.npz  : ~30 cells of E3 PART A + PART B + PART C
- evidence/E*_summary.json: top-level diagnostics per round
- evidence/E*_stdout.log : raw stdout per round
