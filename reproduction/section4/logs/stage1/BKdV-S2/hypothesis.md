# BKdV-S2 — hypothesis synthesis

## Program research question

What conserved or near-conserved quantities exist in BKdV time evolution?
Which are exact physical conservation laws, which are numerical artifacts,
and which appear conserved but actually drift slowly?

Candidates probed: C1=∫u dx, C2=∫v dx, C3=∫u v dx, C4=½∫(u²+v²+v_x²)dx,
C5=∫m² dx with m=u−v²/2.

## Key findings

- **F1 (E1, soliton IC, T=20):** With v0=1.5 sech²(x+5), u0=0, the
  candidates split into two groups: C1 and C2 are conserved to machine
  precision (~1e-15); C3, C4, C5 drift visibly. C1's "0 → 1e-15" is
  ambiguous because u0=0 (could be u≡0 invariance rather than structural).

- **F2 (E2, multi-mode periodic IC, T=10):** With nonzero-mean smooth IC
  (mean_u=0.15, mean_v=0.10), C1 stays at 4.5 (its IC value) to 1.6e-14
  and C2 stays at 3.0 to 3.55e-15 — confirming structural (not
  IC-specific) conservation. C3, C4, C5 drift *more* than in E1
  (C4 grows 16×, C5 grows 34×). The drift is IC-invariant in qualitative
  character.

- **F3 (E3, dt and Nx variation, E1 IC, T=5):** A 5× change in dt
  (5e-4 → 1e-4 at fixed Nx=256) changes the end-state drift of C3, C4,
  C5 by < 1% (ratios 1.002, 0.992, 0.996). The implied numerical order
  is p ≈ 0, i.e. drift is independent of dt. Conclusion: the drift is
  **physical non-conservation**, not numerical artifact. C1, C2 stay at
  FFT round-off across all three configs.

- **Synthesized verdict on each candidate**

  | C  | functional                | verdict |
  |----|---------------------------|---------|
  | C1 | ∫u dx                    | **EXACT physical conservation** (trivial — divergence form) |
  | C2 | ∫v dx                    | **EXACT physical conservation** (trivial — divergence form) |
  | C3 | ∫u v dx                  | **Physically NOT conserved** (drift is dt-invariant) |
  | C4 | ½∫(u²+v²+v_x²)dx        | **Physically NOT conserved** (this is not the BKdV energy) |
  | C5 | ∫m² dx, m=u−v²/2        | **Physically NOT conserved** (off-Gardner-manifold drift) |

- **Negative-knowledge piece for downstream Stage-2:** the naive "sum of
  squared fields" energy is structurally NOT the BKdV invariant. A
  by-hand integration-by-parts shows
  d/dt(½∫(u²+v²)dx) = +(5/2)∫u_x v² dx + ∫u_x v_xx dx,
  which has a non-vanishing cubic remainder for generic IC. Adding the
  v_x² piece (as in C4) cannot cancel this. The real BKdV Hamiltonian
  (if it exists in non-Gardner regime) must include cubic field couplings.

## Ruled-out routes / paths shown not to work

- **The naive "sum of squared fields" energy as a BKdV invariant**:
  tested as C4 in r1 (T=20 soliton) and r2 (T=10 multi-mode). Grew by
  119% and 1570% respectively. Confirmed (r3) that the growth is not
  a numerical artifact. Energy of this form is structurally wrong.

- **Cross moment ∫u v dx as an invariant**: tested as C3 in r1, r2, r3.
  Grew by orders of magnitude with large oscillations. No conservation
  signal. Not an invariant.

- **||m||² (distance from Gardner reduction) as an invariant**:
  tested as C5 in r1, r2, r3. Grows monotonically for any IC with m≠0
  at t=0. m=0 is a reduction manifold, not a stable invariant of the
  general BKdV flow.

- **The "near-conserved but slowly drifting" category**: none of the five
  candidates fall into this class. The split was binary (machine-zero
  conservation vs O(1)-magnitude drift). The program question's third
  category received zero hits in this candidate set.

## Trivial-finding flag

- **F1 (partially) and F2 (partially) — C1, C2 conservation:**
  C1=∫u dx and C2=∫v dx are conserved because both PDEs are written as
  u_t = −∂_x(...), v_t = −∂_x(...) on a periodic domain. The result is
  true-by-construction (divergence-form mass conservation). Numerics
  merely reproduce the analytic fact, and the finding does not
  distinguish BKdV from "any divergence-form periodic PDE". Flagged
  `is_trivial=true` for the C1, C2 conservation sub-claims within
  F1 and F2.

- **F3 dt-invariance of C1, C2 residuals:** Re-derivation of the same
  triviality under finer/coarser dt. Trivial in the sense that the
  divergence-form invariant cannot become *less* conserved by changing
  dt (would only change FFT round-off magnitude, which is what we see).

The full F1, F2, F3 records are NOT trivial as wholes: the non-trivial
piece is the screening of C3, C4, C5 as drifting → physically
non-conserved.

## Recommendation for downstream Stage-2

Adopt: C1=∫u dx and C2=∫v dx as the only mass invariants of BKdV (both
trivial). Avoid: the C4 quadratic-energy ansatz — search Hamiltonian
candidates with cubic terms instead.
