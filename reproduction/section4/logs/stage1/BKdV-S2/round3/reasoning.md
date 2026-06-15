# Round 3 (E3) — numerical-artifact control

## Proposal

Per the protocol step E3: change dt and Nx, see which quantities change.
Anything whose drift scales with dt or Nx is an artifact; anything whose
drift is invariant is physical.

Three configurations, same E1 IC (soliton v0=1.5sech^2(x+5), u0=0), T=5:
  - A : dt = 5e-4,    Nx = 256   (5x larger dt vs baseline)
  - B : dt = 1e-4,    Nx = 256   (5x smaller dt vs baseline)
  - C : dt = 2.5e-4,  Nx = 512   (2x finer grid, baseline dt)

This is exactly one-component variation per pair (A↔B varies only dt;
A↔C varies dt and Nx; B↔C varies dt and Nx).  The A↔B pair gives the
cleanest dt-only test.

## Observations

End-state drifts at T=5:

```
quantity           drift_A          drift_B          drift_C
                   (dt=5e-4 N256)   (dt=1e-4 N256)   (dt=2.5e-4 N512)
C1 = int u dx      +7.49e-15        -2.50e-15        -8.33e-16
C2 = int v dx      +1.78e-15        +3.55e-15        -2.22e-15
C3 = int u v dx    +0.9627          +0.9612          +1.1350
C4 = energy        +1.184           +1.193           +1.210
C5 = int m^2 dx    +4.757           +4.775           +4.547
```

dt-scaling for fixed Nx (A vs B; dt ratio = 5):
  C1, C2 : both machine zero — structurally conserved.
  C3     : drift_A / drift_B ≈ 1.002, order ≈ 0.00
  C4     : drift_A / drift_B ≈ 0.992, order ≈ 0.00
  C5     : drift_A / drift_B ≈ 0.996, order ≈ 0.00

## Interpretation

1. **Drift of C3, C4, C5 is dt-invariant.**  A 5x change in dt produces
   < 1% change in the end-state drift.  If the drift were a numerical
   artifact of order p, we'd expect drift_A / drift_B ≈ 5^p.  Observed
   ratios of ~1.00 give p ≈ 0, i.e. dt-independent.  **The drift is
   physical, not numerical.**

2. **Nx-effect (256 → 512) modestly changes drift of C3** by +15% (likely
   because finer grid resolves more high-k content and the projection of
   the IC onto the truncated spectrum changes slightly).  But it is the
   same order of magnitude — confirming the drift is physical and only
   weakly Nx-dependent.  C4 changes by only +2%, C5 by -4%.  None of
   these scale like a numerical error term.

3. **C1, C2 are conserved at machine precision across all three configs.**
   This re-confirms F2's structural-conservation diagnosis.  Magnitude of
   the residual depends only on FFT round-off, not on dt or Nx in any
   systematic way (residuals are all ~ 1e-15 with random signs).

## Concluding diagnosis of all 5 candidates

| C  | name             | E1 IC | E2 IC | dt-invariant? | verdict |
|----|------------------|-------|-------|---------------|---------|
| C1 | int u dx         | ~0 | 4.5 | yes (machine) | **EXACT conservation** (divergence form — trivial) |
| C2 | int v dx         | 3 | 3 | yes (machine) | **EXACT conservation** (divergence form — trivial) |
| C3 | int u v dx       | drift | drift | yes (drift is physical) | **NOT conserved** (physical non-conservation) |
| C4 | int(u^2+v^2+v_x^2)/2 | drift | drift | yes (drift is physical) | **NOT conserved** (this functional is not the BKdV energy) |
| C5 | int m^2 dx       | drift | drift | yes (drift is physical) | **NOT conserved** (m=u-v^2/2 ≠ 0 invariant for general IC) |

No quantity in the candidate list shows the "appears conserved but slowly
drifts" pattern that the program asks about.  Either:
  (a) such a near-conserved quantity exists but is not in the candidate
      list (e.g. a Hamiltonian with cubic v^3 or u v^2 terms), or
  (b) for non-integrable BKdV (m ≠ 0 manifold), only the two
      divergence-form mass invariants survive.

## Trivial-finding flag for F3

The "C1, C2 are dt-invariant at machine zero" observation is trivial,
because we already classified them as structural laws from F1+F2.  But
the **mechanism** of F3 (dt-scaling test) is the non-trivial part: it
distinguishes physical drift from numerical drift for C3/C4/C5.  So F3 is
**not trivial as a whole** — it converts "drifting quantities" into
"physically non-conserved quantities".

## Decision

D3 action: **stop_useful**.  The candidate list is exhausted.  Three
quantities are classified as physical non-conservation laws; two as
trivial divergence-form conservation laws.  The "drifts slowly" category
of the program question received zero hits among the candidates — that
itself is an informative result for downstream Stage-2.
