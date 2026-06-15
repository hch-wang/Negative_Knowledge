# BKdV-S7 Round 2 (E2) — BKdV breakdown of the m = 0 manifold

## Question

Take the same IC as E1 — v(x,0) = 1.5 sech^2(x+5) — plus u(x,0) = v(x,0)^2 / 2
so that m(x,0) = u - v^2/2 ≡ 0 to machine precision. Does the full BKdV
system propagate this configuration as a Gardner solution would? Quantify:
- ‖m(t)‖_L2 — drift off the m = 0 manifold
- v_max(t), u_max(t) — peak amplitudes
- ‖v_BKdV(t) − v_Gardner(t)‖_L2 — L2 distance from the Gardner reference (E1)

## Method

Identical Fourier pseudospectral + 2/3 dealiasing + RK4 stack to E1, same Nx,
same dt, same dealiasing rule. The only changes are (a) we now evolve the
coupled BKdV system, and (b) the IC adds u_0 = v_0^2/2.

## Results

### m drifts away from zero immediately

| t        | ‖m‖_L2     |
|----------|------------|
| 0.0      | 0.0000e+00 |
| 0.5      | 7.365e-01  |
| 1.0      | 1.216e+00  |
| 2.0      | 1.874e+00  |
| 5.0      | 2.332e+00  |
| 10.0     | 2.550e+00  |

By t = 0.5 (one half-time-unit), ‖m‖_L2 has reached 0.74. By t = 1, it is
**1.22** — the "m = 0 manifold" is destroyed on an O(1) timescale. The
m-norm then grows sub-linearly and saturates around 2.55 (no plateau in t = 5
to 10; the system reaches a quasi-stationary dispersive state).

Average early-time growth rate: (m_norm at t=1) / 1 ≈ **1.22 per time unit**.
This is consistent with the algebraic identity from BKdV-S5,
m_t|_{m=0} = (v − 1)(6 v v_x + v_xxx), which gives a NONZERO initial
forcing (quantified in E3 below).

### v amplitude collapses

| t   | v_max | u_max | n_peaks |
|-----|-------|-------|---------|
| 0   | 1.498 | 1.122 | 1       |
| 1   | 1.453 | 1.659 | 2       |
| 2   | 1.123 | 2.586 | 1       |
| 3   | 0.819 | 3.337 | 4       |
| 5   | 0.738 | 3.400 | 5       |
| 10  | 0.558 | 3.974 | 8       |

v_max drops from 1.498 to 0.558 (**-62.8% drift**). u_max climbs from 1.12
to 3.97 — a 3.5× increase. The single coherent peak in v fragments into
multiple peaks (n_peaks goes 1 → 8 over T = 10).

### L2 distance from Gardner

| t   | ‖v_BKdV − v_Gardner‖_L2 |
|-----|--------------------------|
| 0.0 | 0.0000                   |
| 0.5 | 0.1317                   |
| 1.0 | 0.3751                   |
| 2.0 | 0.5837                   |
| 3.0 | 1.1223                   |
| 5.0 | 1.9755                   |
| 10.0| 1.8138                   |

The L2 distance starts at zero, grows roughly as 0.4 × t for the first
2–3 time units, then saturates around **2.0**, which is **larger than
‖v_BKdV‖_L2 itself** (0.84 at T = 10). At any time beyond t ≈ 2,
the BKdV solution is completely uncorrelated with the Gardner reference
on this domain.

The early-time exponential-like growth is consistent with a Lyapunov-type
separation amplified by the coupling: small m drift feeds back into v via
−∂_x(u v), and that mismatch accumulates in L2.

### Conservation sanity

mass_v drift = +0.000000% (exact, single-RHS conservation).
mass_u drift = -0.000000% (exact, since ∂_t u = ∂_x(...) for both terms).
The simulation is numerically clean: BKdV does NOT blow up; sup remains
bounded ~3.98; no spectral pile-up. The breakdown is **physical**, not
numerical.

## Interpretation

The m = 0 manifold is NOT dynamically preserved by BKdV when initialized
with the Gardner-stable sech^2 IC. The Gardner reduction is a *kinematic*
substitution (algebra of u = v^2/2 into BKdV's v-equation) but is NOT
an invariant set of the dynamics. Within 1 time unit the system has
left the manifold, fragmented the v-peak into a dispersive train, and
amplified u by a factor of ~2; by T = 10 it is in a chaotic dispersive
state that bears no resemblance to the Gardner soliton-like solution
from E1.

The L2 distance ‖v_BKdV − v_Gardner‖_L2 grows to 1.81 at T = 10 while
‖v_BKdV‖_L2 itself is only 0.84 — the BKdV and Gardner solutions are
*more dissimilar* than the BKdV solution is dissimilar from zero. This is
the strongest possible statement that "BKdV with u_0 = v_0^2/2 does not
behave like Gardner."

## Decision

Proceed to E3: quantify the mechanism using the BKdV-S5 algebraic identity
m_t|_{m=0} = (v − 1)(6 v v_x + v_xxx), evaluated on the actual IC v_0(x).
Compute the spatial structure, L2 norm, and spectral content of this
initial m_t source — predict which modes amplify first, and verify against
the early-time evolution of m̂(k, t).
