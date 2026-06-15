# Round 2 (E2) — IC change to test IC-invariance

## Proposal

Single-component escalation over E1: keep solver and dt/Nx identical;
change ONLY the IC.  Goal — disambiguate "structural conservation" from
"IC-specific coincidence" for C1, and probe whether the C3/C4/C5 drift
in E1 was tied to the soliton-like IC or is generic.

- IC : v0 = 0.6 cos(2πx/L) + 0.3 sin(4πx/L) + 0.10
       u0 = 0.4 sin(2πx/L) + 0.2 cos(6πx/L) + 0.15
       (smooth multi-mode periodic, nonzero means in u and v)
- T  = 10 (shorter than E1 — drift patterns visible by t~3 from E1).
- Other parameters unchanged.

## Observations

| quantity | init | final | abs drift | rel drift |
| --- | --- | --- | --- | --- |
| C1 = int u dx       | 4.5000   | 4.5000     | 1.6e-14 | 3.6e-15 |
| C2 = int v dx       | 3.0000   | 3.0000     | 3.6e-15 | 1.2e-15 |
| C3 = int u v dx     | 0.4500   | 15.29      | +14.84  | +32.99  |
| C4 = (1/2)int(u^2+v^2+v_x^2)dx | 5.5994 | 93.54 | +87.94 | +15.71 |
| C5 = int m^2 dx     | 2.3913   | 84.84      | +82.45  | +34.48  |

Solver finite throughout; sup-norm grows from ~0.9 to ~6.5 over T=10.

## Interpretation

1. **C1, C2 confirmed structurally conserved.**  C1 starts at 4.5 (nonzero)
   and stays at 4.5 to machine precision (1.6e-14).  C2 similarly.  This
   rules out the "u stays at 0 because u0=0" hypothesis from E1.
   Verdict on C1, C2: **exact conservation laws, both due to divergence
   form** of the respective equations (still trivial-by-construction —
   the IC change just confirmed they are not IC-specific).

2. **C3 not IC-invariant either.**  Drifts even faster here (+33x relative
   in T=10) than E1 (+5.4e11 relative... but base was ~zero).  In absolute
   terms the drift here is much larger and monotonic-ish.  Confirms C3 is
   **NOT a conservation law**.

3. **C4 (the proposed energy) — clearly NOT conserved**.  Grows by 16x.
   Either:
   (a) The functional (1/2)int(u^2 + v^2 + v_x^2)dx is the wrong energy
       for BKdV (e.g. missing a cross-coupling term like -int(v_x u) or
       cubic terms like int(v^3)), or
   (b) BKdV has no Hamiltonian / energy structure preserved in time.

   The growth is monotonic (not oscillatory), which is the signature of a
   "wrong" energy guess rather than numerical drift of a true conservation
   law.  (A true conservation law violated by numerics would oscillate
   around the conserved value.)

4. **C5 (||m||^2) — NOT conserved**.  Grows ~34x in this run; in E1 it grew
   ~8x.  m=u-v^2/2 measures distance from Gardner reduction; non-trivial
   IC drifts away from the reduction manifold.  This is **not** a
   conservation law — it's a diagnostic for "how non-Gardner the state
   is", and it grows.

## Cross-check on energy guess

Note from PDE form:
   u_t + 3 u u_x = -d/dx(3 v^2 + v_xx)
   v_t + 6 v v_x + v_xxx = -d/dx(u v)

Multiply u-eqn by u, v-eqn by v, integrate:
   d/dt (1/2 int u^2) = -int u d/dx(3 v^2 + v_xx) = ... = +3 int u_x v^2 + int u_x v_xx
   d/dt (1/2 int v^2) = -int v_xxx v - int v d/dx(uv) = (1/2)int v_x^2 ... not -- actually
                       -int v v_xxx = (1/2)int(v_x^2)' dx... hmm wait
                       Use IBP: -int v v_xxx = int v_x v_xx = (1/2) (v_xx^2)' int = 0
                       So -int v_xxx v contribution = 0
                       And -int v(uv)_x = int(uv) v_x = int u v v_x = (1/2) int u (v^2)_x
                                       = -(1/2) int u_x v^2  (IBP)
So d/dt (1/2 int v^2) = -(1/2) int u_x v^2.

Adding:
   d/dt (1/2 int (u^2+v^2)) = +3 int u_x v^2 + int u_x v_xx - (1/2) int u_x v^2
                             = +(5/2) int u_x v^2 + int u_x v_xx

Not zero generically.  So even the simpler (1/2)int(u^2+v^2) is not the
conserved energy.  Adding the +(1/2)int v_x^2 piece won't cancel the
+(5/2)int u_x v^2 cubic remainder.  The proposed C4 is structurally NOT
the BKdV energy.  Real energy (if it exists) must include cubic terms.

This is a useful **negative knowledge** for downstream Stage-2: the naive
"sum of squared fields" energy is NOT the BKdV invariant.

## Trivial-finding flag

C1, C2 conservation in this round is the same divergence-form fact verified
under a new IC.  Still trivial-by-construction — the new IC doesn't change
that this is tautological.

Status: F2 confirms F1's structural laws (trivial, IC-invariantly true),
and refutes IC-dependence of C3/C4/C5 drift — they are also IC-invariantly
non-conserved.

## Decision

D2 action: numerical-artifact control (E3).  Change dt and Nx to test
whether the C3/C4/C5 drift depends on the numerical method.  If the drift
is unchanged across dt and Nx variants -> physical non-conservation; if it
shrinks -> numerical artifact.  This is exactly the protocol step 3.
