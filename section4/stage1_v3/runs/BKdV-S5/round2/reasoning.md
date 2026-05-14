# Round 2 reasoning (E2: structured single-mode perturbation)

## Proposal

Single-component escalation over E1: same baseline IC, but add
`δv(x,0) = ε sin(k₀ x)` to v with ε = 0.05 and k₀ = 2π·5/L (Fourier mode index
5). u(x,0) is left as u = v_base²/2 (we do NOT correct u to keep m=0; the
perturbation is on v only). All other solver/timing/IC parameters held fixed.

The deviation norm ||δv(t)||_{L²} ≡ ||v_E2(t) - v_E1(t)||_{L²} (and the same
for u) is the primary diagnostic.

## Observations

At E1-aligned snapshot times t ∈ {0, 1, 2, ..., 15} the deviation series:

```
t=0:    ||δv|| = 0.194    (the IC perturbation L² norm)
t=1-13: ||δv|| ∈ [0.183, 0.224]   (essentially flat, fluctuates ~ ±10%)
t=14:   ||δv|| = 0.358   (starts rising)
t=15:   ||δv|| = 1.153   (≈6× initial)
```

So the structured mode-5 perturbation **stays bounded near its initial L² norm
for ~13 time units**, then grows by a factor ~6 by t=15. An exponential fit
gives an effective growth rate of +0.05/time-unit but is dominated by the
late-time excursion; for t ≤ 13 the rate is essentially zero.

(Important caveat: the intermediate diagnostic outputs printed every
nsteps/30 ≈ 0.5 time-units showed wide oscillations between ~0.2 and ~1.5.
These are NOT the same as the E1-aligned snapshot deviations — they compare
v(t) to the nearest E1 snapshot in time, so the apparent oscillation is a
phase-mismatch / sampling artifact between two chaotic trajectories, not a
true growth.)

## Conclusion (E2)

The mode-5 structured perturbation does **not** trigger fast / runaway
instability over T=15; the deviation L² norm is essentially flat at ~1× initial
for the bulk of the run and rises ~6× only in the last 1–2 time units. This is
consistent with mode 5 being a relatively "tame" low-k perturbation: the BKdV
system has no dispersion-relation pole at this k, and the existing baseline
chaotic drift dominates over any specific mode-5 amplification.

This is a partial / negative finding for "structured perturbation growth at
mode 5" but is informative — it tells us the response is not generic-and-fast.

E3 should contrast with this by using broadband perturbation at the same L²
norm; if E3 grows similarly slowly, response is independent of structure
(broad negative for instability); if E3 grows much faster, the response is
strongly k-selective.
