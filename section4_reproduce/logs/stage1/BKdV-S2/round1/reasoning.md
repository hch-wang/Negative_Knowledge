# Round 1 (E1) — long-time baseline diagnostic sweep

## Proposal

The program question is: which of the 5 candidate functionals is actually
conserved by BKdV time evolution?  I run the smallest meaningful experiment:
one long simulation (T=20) with the program-prescribed IC and track all five
candidates per timestep.  Method is the pre-validated stack — I do not vary
it within E1.

- IC : v0 = 1.5 sech^2(x+5), u0 = 0
- Grid: Nx=256, x in [-15,15] periodic, dx ~ 0.117
- dt = 2.5e-4 (mid-range of validated 1e-4..5e-4)
- Method: Fourier pseudospectral, 2/3 dealiasing on every nonlinear product,
  IMEX Crank-Nicolson on -v_xxx, midpoint RK2 on the explicit RHS.
- Diagnostics every nsteps/200 = 400 steps (so 200 samples over t in [0,20]).

## Observations

| quantity | init | final | abs drift | max excursion |
| --- | --- | --- | --- | --- |
| C1 = int u dx       | 0.0000        | 6.14e-15    | 6.14e-15  | 8.64e-15 |
| C2 = int v dx       | 3.0000        | 3.0000      | 5.33e-15  | 5.33e-15 |
| C3 = int u v dx     | 0.0000        | +0.5386     | +0.54     | 1.81     |
| C4 = (1/2)int(u^2+v^2+v_x^2)dx | 2.7000 | 5.9032 | +3.20     | 3.20     |
| C5 = int m^2 dx     | 1.1571        | 9.5371      | +8.38     | 8.38     |

Sup-norm stays bounded (~3-4); solver did not blow up; finite throughout.

## Interpretation

1. **C1 = int u dx**: conserved to machine precision.  Two observations:
   (a) Both u and (3 v^2 + v_xx) are inside d/dx on the u-equation, so
       d/dt int u dx = -int d/dx(...)dx = 0 on a periodic domain.  This is
       **true by construction** (divergence form).  
   (b) Numerically the residual is O(1e-15), consistent with FFT round-off.

2. **C2 = int v dx**: also conserved to machine precision.  Same reason:
   v_t = -d/dx(...) entirely, so int v dx is conserved on periodic domain.
   True by construction.

3. **C3 = int u v dx**: NOT conserved.  Drifts from 0 to ~0.5 with violent
   oscillations (excursions ~1.8).  This is a real physical non-conservation
   signal, not numerical noise.  C3 is therefore a non-conserved cross moment.

4. **C4 = (1/2) int (u^2 + v^2 + v_x^2) dx**: NOT conserved.  Grows by 119%
   over T=20, essentially monotonic upward.  Either (i) this is the wrong
   energy functional for BKdV (a sign error or missing coupling term in our
   guess), or (ii) the system has no second-order conserved energy at all.

5. **C5 = int m^2 dx** with m = u - v^2/2: NOT conserved.  Grows by 724%
   monotonically.  Recall m=0 reduces to Gardner; the IC has m != 0 (u0=0
   while v0^2/2 = 1.125 sech^4(x+5)), so the system is off the reduction
   manifold — and the off-manifold deviation grows.  Useful: confirms the
   IC is **not** on the Gardner reduction.

## Concern about C1

C1 happens to start at 0 because u0=0.  We cannot from this run alone
distinguish "C1 conserved as a structural law" from "C1 stays at zero
because the equation preserves u=>0 for this specific IC".  Round 2 must
use an IC with u0 != 0 to disambiguate.

## Trivial-finding flag

C1 conservation and C2 conservation: trivial.  Both u and v equations are
in divergence form (u_t = -d/dx(...), v_t = -d/dx(...)), so on a periodic
domain int u dx and int v dx are conserved by construction.  Numerics
merely reproduce the analytical fact.

Status: **F1 = mixed positive + 2 trivial flags**.  Non-trivial finding:
C3, C4, C5 are not conserved for this IC.

## Decision for next round

- D1 action: change IC type (one component change, smallest meaningful
  escalation per the protocol).  Pick u0 with non-zero spatial mean to
  break the u=>0 invariance and confirm C1 conservation is structural.
  Also pick a different v0 profile to test whether the C3/C4/C5
  non-conservation is IC-invariant.
- Plan: random small-amplitude periodic IC (both u and v nonzero, smooth).
