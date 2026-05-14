# E2 — Amplitude scan on the coherent IC family (sech²)

## Proposal
On the most reliably-coherent family from E1 (single sech^2 pulse on v, flat u),
sweep amplitude A ∈ {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2} while keeping
all other parameters and the solver stack identical. Same diagnostics + a new
*retention* metric: `vmax_late / vmax_initial`. For A ≥ 1.0 reduce dt to 1e-4
(still inside the validated dt window). Run to T=12.

This is the smallest meaningful escalation over E1: same IC family and solver,
one new axis (amplitude).

## Observations

| A    | vmax0 | vmax_late | npeaks | fracL_v | lock  | retention | strict | relaxed |
|------|-------|-----------|--------|---------|-------|-----------|--------|---------|
| 0.10 | 0.10  | 0.060     | 2      | 0.998   | -0.19 | 0.60      | no     | yes     |
| 0.20 | 0.20  | 0.125     | 2      | 0.999   | 0.20  | 0.63      | no     | yes     |
| 0.30 | 0.30  | 0.166     | 1      | 0.999   | 0.62  | 0.55      | no     | yes     |
| 0.40 | 0.40  | 0.241     | 1      | 0.999   | 0.79  | 0.60      | no     | yes     |
| 0.50 | 0.50  | 0.298     | 1      | 0.999   | 0.71  | 0.60      | no     | yes     |
| 0.60 | 0.60  | 0.304     | 1      | 0.999   | 0.58  | 0.51      | no     | yes     |
| 0.80 | 0.80  | 0.422     | 1      | 0.999   | 0.47  | 0.53      | no     | yes     |
| 1.00 | 1.00  | 0.604     | 1      | 0.993   | 0.43  | 0.60      | YES    | yes     |
| 1.20 | 1.20  | 0.682     | 1      | 0.996   | 0.57  | 0.19      | YES    | yes     |

(Note: A=1.20 has correct retention 0.568; the lock=0.19 reading is the
endpoint of an oscillating lock, not a steady value.)

## Conclusion
- **Structural coherence is universal for sech² seeds**: npeaks=1 (or 2 in the
  very-low-A radiation-dominated regime), fracL_v ≥ 0.99 at all A. There is no
  amplitude below which sech² becomes incoherent. The "phase transition" by
  IC family is not amplitude-tunable inside the localized family.
- The programme's vmax ≥ 0.5 strict threshold is satisfied only for A ≥ 1.0.
  But this is a measurement convention (the threshold is fixed in absolute
  units), not a physical boundary. The relaxed criterion (retention ≥ 0.4)
  passes uniformly.
- **Lock_corr has a non-monotonic A-dependence**: peaks near A ≈ 0.4-0.5
  (lock ≈ 0.7-0.8), drops at both ends. This suggests a *coherent-compound*
  regime where u and 0.5 v^2 lock tightly only in an intermediate amplitude
  band, not at large or vanishing A. This is the most interesting hint in
  this round.
- Retention ~50-60% is a robust feature across all A — the system radiates
  roughly half the initial vmax then settles. Suggests a 1-parameter family
  of asymptotic localized states.

## Implications for E3
- The phase boundary on the *amplitude* axis is soft / does not exist in
  npeaks_v terms for sech² seeds.
- The crisp phase boundary is between IC *family classes*: localized vs
  broadband. To probe that boundary we vary ONE parameter — the noise
  level σ added on top of a localized sech² seed. σ=0 is fully coherent;
  σ → 1 is the noise-dominated regime. Find σ_c where coherence fails.

`is_trivial = false` — the non-monotonic lock(A) is informative; the
universal-coherence-of-sech² result is a real (if simple) statement about
the basin.
