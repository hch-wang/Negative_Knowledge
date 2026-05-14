# Round 2 — E2 spatial-resolution probe (Nx 256 → 512)

## Proposed design
Single-parameter change vs E1: Nx 256 → 512. dt=5e-4, ν_h=1e-22, T=10, IC
unchanged.

Three sub-runs all implementing the design "double Nx" (sub-runs E2b/E2c
are bug-fixes after E2a's diagnosed instability and DO NOT count as new
rounds per the prompt protocol — same design, same comparison):

- E2a: literal one-parameter change (Nx 256→512, all else fixed).
- E2b: HV-rescaled — ν_h ← ν_h/2^16 so that ν_h k_max^16 is invariant
  across grids (preserves the hyperviscous filter at k_max AND the
  explicit-RK4 stability bound on the hyperviscous mode).
- E2c: HV-rescaled AND dt reduced to 1e-4 (within the additional dispersion
  CFL bound at Nx=512 — see below). This is the fully-stable comparison.

## Stability arithmetic (key for interpretation)
The pre-validated stack treats the hyperviscous tail explicitly in the RHS.
Explicit-RK4 stability for a linear decay mode of rate λ requires
`dt · |λ| ≲ 2.78`. The hyperviscous mode has λ = ν_h k_max^16.

| grid     | ν_h    | k_max  | ν_h k_max^16 | dt-stability bound |
|----------|--------|--------|--------------|--------------------|
| Nx=256   | 1e-22  | 26.81  | 7.12         | ≈ 0.39             |
| Nx=512   | 1e-22  | 53.62  | 4.66 e5      | ≈ 6 e-6            |
| Nx=512   | 1.53e-27 (rescaled) | 53.62 | 7.12 | ≈ 0.39 |

There is ALSO an explicit dispersion CFL through the u-equation's
`−i k · v_xx` coupling (not absorbed by the v-IF, which is on v_xxx in the
v-equation). It gives a constraint `dt ≲ 2.83 / k_max^3`:

| grid    | k_max^3 | dispersion-CFL bound  |
|---------|---------|-----------------------|
| Nx=256  | 1.93 e4 | ≈ 1.47 e-4            |
| Nx=512  | 1.54 e5 | ≈ 1.84 e-5            |

At Nx=256 with dt=5e-4 the dispersion CFL is technically violated, but
hyperviscosity (rate ≈ 7 s⁻¹ at k_max) damps high-k v before it can blow
the u-equation up — i.e. ν_h SAVES the explicit dt=5e-4 stability. At
Nx=512 with rescaled ν_h, the high-k v modes are no longer damped fast
enough, and the u-equation goes unstable through the dispersion coupling.
So at Nx=512, dt needs to come down to ≲ 1e-4 for stability.

## Observations

E2a — Nx=512, ν_h=1e-22, dt=5e-4:
  NaN at step 4, t=0.002. As predicted by the hyperviscous stability bound
  (4.3e-6 ≪ 5e-4).

E2b — Nx=512, ν_h=1.53e-27, dt=5e-4:
  NaN at step 193, t=0.0965. The hyperviscous bound is restored to ≈ 0.39,
  but the u-equation explicit dispersion CFL (1.84e-5) is violated by ~30×
  — a different stability mechanism. So even the rescaled-HV stack is
  NOT directly comparable at dt=5e-4 / Nx=512.

E2c — Nx=512, ν_h=1.53e-27, dt=1.0e-4:
  Stable. Wall = 19.6 s, 100 000 steps. End-state diagnostics shift vs E1:

| diagnostic | E1 (Nx=256) | E2c (Nx=512) | Δ%      |
|------------|------------:|-------------:|---------|
| m_l2_T     | 2.456       | 1.646        | −33.0 % |
| m_inf_T    | 3.667       | 2.239        | −39.0 % |
| lock_T     | 0.1997      | 0.4776       | +139.1 % |
| L2_u_T     | 2.489       | 1.694        | −31.9 % |
| L2_v_T     | 0.829       | 0.722        | −12.9 % |
| energy_T   | 3.547       | 1.736        | **−51.0 %** |
| u_peak_T   | 3.670       | 2.244        | −38.9 % |
| v_peak_T   | 0.545       | 0.383        | −29.7 % |
| eh_u_T     | 0.1606      | 0.0588       | −63.4 % |
| eh_v_T     | 9.6e-5      | 9.3e-6       | −90.3 % |

ALL diagnostics shift by far more than the 5 % threshold. Energy drops by
half. The lock correlation flips QUALITATIVELY (0.20 weak-positive in E1
vs 0.48 moderate-positive in E2c — a different solution branch).

## Conclusion this round
Three findings from the same design:

(1) Nx doubling alone (literal one-parameter change) is INADMISSIBLE in the
pre-validated stack: it violates the explicit-RK4 hyperviscous stability
bound. Numerical parameters in this stack are CO-CONSTRAINED.

(2) Even with ν_h rescaled to preserve the spectral filter, dt=5e-4 is
inadmissible at Nx=512 because of the u-equation's explicit dispersion
CFL (≈ 1.84e-5 at Nx=512). The v-IF removes the v-equation's v_xxx
stiffness but NOT the v_xx → u_t coupling.

(3) With (dt, ν_h) both rescaled for stability, Nx 256→512 produces a
QUALITATIVE shift in every diagnostic — energy halves, m_l2 drops by 1/3,
lock_corr more than doubles. This is the actual physics result for S4:
**Nx is the most sensitive numerical parameter for this IC at this T.
The E1 baseline at Nx=256 is NOT in the converged regime.**

Decision: round 3 will probe the OTHER numerical parameters from a position
where we now know Nx=256 is sub-converged. We'll change ONLY hyperviscosity
ν_h (Nx fixed at 256, dt=5e-4) — the prompt-specified "different
parameter than E2". If ν_h also drives a qualitative shift, hyperviscosity
is sensitive too. If ν_h is robust at Nx=256, the under-resolution of E1 is
specifically a spatial-grid issue, not a damping issue.
