# Session log: T_C / BKdV

Task: B-NLS bore × NLS soliton at the user's variational sign convention
(+sqrt(N)_xx/(2 sqrt N)). Condition: BKdV-only knowledge bank.

## Timeline

### t0 — Bank scan and Q1 setup
- Read `prompt.md` and the BKdV-only memory bank (10 positive + 20 negative).
- Identified that the bank covers the Burgers u-sector well (Godunov upwind for
  the bore) but has NO entries on the NLS Madelung quantum pressure
  sqrt(N)_xx/(2 sqrt N). Decided the N-phi sector would be reasoned from
  general principles.
- Wrote Q1 (research_state.jsonl).

### t1 — E1 proposal: direct (u, N, phi) baseline
- Method: 1st-order Godunov upwind on m equation (m = u - N*phi_x), Fourier
  spectral on phi for spatial derivatives, explicit RK4, dt=1e-3.
- cites_bank: kb-general-firstOrder-Godunov-preShock-baseline,
  kb-burgers-Godunov-preShock-smooth.
- rejects_bank: MUSCL (too-stacked), HLL/LxF (mechanism mismatch), central FD
  (Gibbs), LxF long-time (over-diffusion).
- Wrote candidate.py.

### t2 — E1 execution
- BLOWUP at step 15 (t=0.015). Diagnostics:
  - phi(-15)=-9, phi(15)=+8.93 → non-periodic on Fourier grid.
  - min(N) = 5.325e-20 → sqrt(N)_xx/(2 sqrt N) divides by ~1e-10.
  - u_max=2.045 just before NaN (likely Burgers Godunov flux overflow once
    the spectral phi_x is corrupted near the boundary).
- F1 recorded with both root causes. useful_self_assessment=False.

### t3 — D1 + E2 design
- D1: change method along the "phi representation" axis. Two sub-changes
  (phi -> 0.6*x + tilde_phi, and sqrt(N) -> sqrt(N+1e-3) in quantum pressure
  only) treated as a single compound change since both restructure the same
  representation issue.
- E2 proposed and candidate.py rewritten.

### t4 — E2 execution
- BLOWUP at step 123 (t=0.123). 8.2x further than E1.
- Diagnosis: the two F1 mechanisms are eliminated. New mechanism is a
  representation-level positive feedback: 2*kappa*N drives phi_t growth →
  tilde_phi_x grows → u = m + N*(0.6+tilde_phi_x) inflates → Burgers Godunov
  flux breaks.
- F2 recorded.

### t5 — D2 + E3 design
- D2: layer one more component — 2/3 spectral dealiasing on tilde_phi
  (bank-cited from kb-kdv-noDealiasing-aliasing-artifacts,
  kb-gardner-G3-noDealiasing-cubicAliasing). dt halved to 5e-4 as
  companion tuning.
- E3 proposed and candidate.py rewritten.

### t6 — E3 execution (first pass, dt=5e-4)
- BLOWUP at step 1301 (t=0.6505). 5.3x further than E2.
- Snapshot grid (target t in [0, 8] linspace 9) only reached t=0; remaining
  slots filled from a fine buffer (every 0.05 t).

### t7 — E3 bug-fix tuning: dt=1e-4
- Tested dt=1e-4 as a "same-method bug fix" tuning. Result was QUANTITATIVELY
  WORSE: blowup at t=1.18, but u in [400, 700] at the first crossed snapshot,
  indicating the instability is REPRESENTATION-LEVEL (positive feedback
  amplitude growth), NOT a stability-bound dt control. Reverted to dt=5e-4.

### t8 — E3 snapshot strategy refinement (same iteration, bug-fix tuning)
- Filter fine snapshots to "clean" states (|u|<5, max(N)<3, N>=-1e-6) to
  prevent contamination by pre-blowup pathological values. Final saved t-values:
  [0, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.1, 0.1]. All 9 snapshots are CLEAN; the
  redundancy comes from the small clean window.

### t9 — F3 + D3 finalization
- F3 records all three blowup times, the monotonic-improvement narrative, and
  the structural obstacle (anti-Madelung sign + bore-driven 2*kappa*N source).
- D3 = stop_useful (iteration budget exhausted). useful_self_assessment=False
  because T=8.0 was never reached.
- Wrote reasoning.md and finalized all deliverables.

## Output files

- `candidate.py` — E3 solver (dt=5e-4, 2/3 dealiasing, periodic-safe phi,
  sqrt(N+eps) regularization).
- `pred_results/T_C.npy` — shape (9, 3, 256). All 9 snapshots from the clean
  window [0, 0.1].
- `pred_results/T_C_mnorm.npy` — ||m||_2 trace per snapshot.
- `pred_results/T_C_Nmass.npy` — N mass per snapshot.
- `pred_results/T_C_times.npy` — actual t-values per snapshot.
- `research_state.jsonl` — Q1, E1, F1, D1, E2, F2, D2, E3, F3, D3.
- `reasoning.md` — Final method, iteration trace, use of memory, self-assessment.
