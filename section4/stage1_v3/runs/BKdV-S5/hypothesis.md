# BKdV-S5 hypothesis (final synthesis)

## Program research question

Does the coupled Burgers-swept-KdV system

  u_t + 3 u u_x = -∂_x(3 v² + v_xx)
  v_t + 6 v v_x + v_xxx = -∂_x(u v)

exhibit modulational instability of known stable structures (in particular,
the "approximate Gardner soliton" on the m = u - v²/2 = 0 reduction)? If so,
characterize: which perturbations grow, at what rate, into what late-time
state.

## Key findings

- **F1 (E1, partial)**: The m=0 manifold is NOT invariant under full BKdV for
  sech² ICs. Algebra: m_t|_{m=0} = (v - 1)·(6 v v_x + v_xxx), generically
  nonzero. The numerical baseline v_0 = sech²(x+5), u_0 = v_0²/2 decoheres
  within t < 1: v_peak drops from 1.0 to ~0.4, and the state becomes a
  chaotic dispersive flow with mass_v conserved (0 ppm) but m_norm growing
  0 → 2.9 and energy(u,v) drifting +679% by T=15. The "approximate Gardner
  soliton" premise of the prompt is therefore materially weaker than implied:
  there is no coherent traveling wave to perturb.

- **F2 (E2, partial / mostly negative)**: A small structured single-mode
  perturbation δv₀ = 0.05·sin(2π·5 x/L) (mode 5, ||δv₀||=0.194) does NOT
  grow appreciably for 13 time units. ||δv(t)||_{L²} fluctuates in [0.18,
  0.22] for t ∈ [0,13], then rises to 1.15 by t=15 (≈6×). Effective fit
  growth rate +0.05/unit, dominated by the late-time onset. No early
  exponential phase. Mode-5 is not a fast-amplification direction.

- **F3 (E3, positive)**: A matched-L² broadband noise perturbation
  (zero-mean Gaussian, seed=42, ||δv₀||=0.194) grows as ||δv(t)|| ~
  exp(1.02·t)·||δv(0)||, reaches a ratio of 143× over E2 at t=5, and triggers
  numerical blow-up at t=5.5. The instability is therefore strongly
  **k-selective**: high-k modulation of v is exponentially amplified, low-k
  structured modulation is inert at the same L² norm.

- **Mechanism (inferred from the equations)**: The explicit coupling term
  u_t -= ∂_x(3 v² + v_xx) injects a v_xxx forcing into u. High-k δv has small
  L² but large ||δv_xxx||, producing a large impulse on u that immediately
  drives the system off the m=0 manifold and into Burgers-shock regime, which
  then re-feeds v via the -∂_x(u v) coupling. Low-k δv has small ||δv_xxx||
  and produces a benign forcing absorbed into the chaotic baseline.

## Ruled-out routes / paths shown not to work

- **"Sech² + u = v²/2 propagates as a coherent traveling wave"** — Ruled out
  by E1: the m=0 set is not BKdV-invariant for sech² shapes; immediate
  decoherence is observed. (Algebra confirms this is not numerical:
  m_t|_{m=0} = (v-1)(6 v v_x + v_xxx) ≠ 0.)
- **"Mode-5 sinusoidal perturbation triggers fast instability"** — Ruled out
  by E2: ||δv||_{L²} essentially flat for 13 time units.
- **"Forward-Euler on u's full RHS suffices"** — Ruled out by E1 bug-fix
  history: u develops Burgers bores once forced off m=0, demanding
  MUSCL+Godunov on the u u_x flux for stability.
- **"a = 1.5 sech² with dt = 2.5e-4 is workable"** — Ruled out by E1 first
  iteration: blow-up at t≈3 from rapid off-manifold drift at this amplitude.

## Trivial-finding flag

None of the three Findings F1, F2, F3 are trivial:
- F1 reports the failure of an explicitly-presupposed invariance (the m=0
  manifold), with an algebraic explanation and numerical confirmation. Not
  tautological.
- F2 is a partial/negative finding distinguished from "zero solution stable":
  a non-trivial perturbation of a non-trivial baseline is tested and reports
  bounded behavior on a meaningful time-window. Not tautological.
- F3 reports a numerically-clear positive instability with a fitted rate and
  a comparison ratio against E2. Not tautological.

Trivial-finding count: **0**. No experiment reduced to a vacuous statement.

## Recommendation for downstream Stage-2

BKdV linear-response work should (1) drop the "Gardner soliton on m=0"
ansatz — it is not invariant; (2) construct a true coherent state numerically
(e.g. dressed soliton from time-integration relaxation) before perturbing;
(3) sweep growth-rate vs k for single-mode δv to confirm k-selectivity and
estimate λ(k); (4) re-run E3 at higher Nx to separate physical from numerical
high-k blow-up.
