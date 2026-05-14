# BKdV-S7 session log

Working directory: `runs/BKdV-S7`
Python: `paper/experiments/pde_pilot_2026-05-11/.venv/bin/python`
Numerical stack: Fourier pseudospectral + 2/3 dealiasing + explicit RK4,
dt = 2e-4, Nx = 256, L = 30 (periodic, x in [-15, 15]), T = 10.

## Program target

Find an IC stable under the Gardner equation (m=0 reduction of BKdV) but
**unstable** under full BKdV when initialized with u_0 = v_0^2/2. Quantify
the breakdown mechanism.

## Round-by-round timeline

### Round 1 (E1) — Gardner-only baseline
- IC: v_0 = 1.5 sech^2(x+5).
- Equation: v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0.
- Result: clean single peak, mass/L2 exact, Hamiltonian drift 0.19%,
  v_max drift -0.14%, n_peaks = 1 throughout. **Stable positive reference.**
- Elapsed: 6.6 s wall.

### Round 2 (E2) — full BKdV with matching IC
- IC: same v_0 plus u_0 = v_0^2/2 (m_0 = 0 to machine precision).
- Equations:
    u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -d_x(u v)
- Result: m_norm grows 0 -> 1.22 by t=1, saturates ~2.55 at T=10.
  v_max collapses 1.498 -> 0.558 (-62.8%), n_peaks 1 -> 8.
  L2 distance to Gardner reaches 1.81 (> ||v_BKdV||_L2 = 0.84).
  Mass conservation exact. **Strong negative finding.**
- Elapsed: 16.0 s wall.

### Round 3 (E3) — mechanism via BKdV-S5 identity
- Source S(x) = (v_0 - 1)(6 v_0 v_0_x + v_0_xxx).
- ||S||_L2 = 1.77 per unit time = predicted initial growth rate of ||m||_L2.
- Predicted top modes: n = 4, 5, 3, 6, 2.
- Observed top modes of m at t=0.5: n = 4, 3, 5, 2, 6.
- Spectral cos-sim: **0.94**.
- Linear extrapolation matches observed within 17% at t = 0.5.
- A-sweep: source scales as A^0.22 below A ~ 1, as A^2.49 above A ~ 1
  (the (v - 1) sign-flip threshold).
- Elapsed: < 1 s (post-hoc).

## Total wall-clock: ~25 s for all three rounds.

## Deliverables in place

- `round1/{candidate.py, exec.log, reasoning.md, snapshots.npz, diag.npz}`
- `round2/{candidate.py, exec.log, reasoning.md, snapshots.npz, diag.npz}`
- `round3/{candidate.py, exec.log, reasoning.md, source_diag.npz}`
- `hypothesis.md` (final synthesis with positive + negative bank entries)
- `research_state.jsonl` (Q1, E1/F1, D1, E2/F2, D2, E3/F3, D3)
- `session_log.md` (this file)

## Trivial-flag count: 0

All three findings carry non-trivial quantitative content. None were flagged
as `is_trivial: true`.

## Headline takeaway

The Gardner reduction u = v^2/2 of BKdV is a **kinematic identity, not a
dynamical invariant set**. The IC v_0 = 1.5 sech^2(x+5) is a clean
propagating wave in Gardner (mass/L2 exact, Hamiltonian drift 0.2%, single
peak through T = 10) but breaks down catastrophically in full BKdV
(m drifts to 2.55, v_max -62.8%, L2 distance to Gardner > ||v_BKdV||_L2
itself). The first-amplified Fourier modes of m match the spectrum of
the BKdV-S5 source (v-1)(6 v v_x + v_xxx) with cos-similarity 0.94.
Predicted ||m||_L2 growth rate from the source identity (1.77/unit t)
matches observed to 17% at t = 0.5.

## Implication for Class B

Any "Gardner soliton on the m = 0 manifold" argument for compound-soliton
stability in BKdV fails because m = 0 is not preserved by BKdV dynamics
for ICs with peak v > 1. Class B B1 needs a coherent BKdV state built
directly on the coupled system, not inherited from Gardner.
