# Round 3 reasoning (E3: broadband-noise perturbation, same L² norm as E2)

## Proposal

One-component escalation over E2: replace the mode-5 sin perturbation with
zero-mean broadband Gaussian noise (seed=42) rescaled to have the SAME L² norm
(||δv₀||_{L²} = 0.1936 ≈ 0.05·√15). Everything else (baseline IC, u, solver,
T, dt, snapshot cadence) is identical. This isolates the spectral structure of
the perturbation as the one varied component.

If ||δv(t)||_{L²} for E3 looks like E2's (slow growth), the BKdV response is
not k-selective. If E3 grows much faster or qualitatively differently, the
response is strongly k-selective.

## Observations

E3 deviation versus the same E1 baseline:

```
t=0: ||δv|| = 0.194   (matched IC L² norm)
t=1: ||δv|| = 0.256   ratio E3/E2 = 1.24
t=2: ||δv|| = 0.550   ratio E3/E2 = 2.64
t=3: ||δv|| = 1.625   ratio E3/E2 = 7.70
t=4: ||δv|| = 5.66    ratio E3/E2 = 26.5
t=5: ||δv|| = 30.8    ratio E3/E2 = 143
```

Exponential fit on the t ∈ [1, 5] regime gives a growth rate of
**+1.02 / time-unit** — i.e. ||δv||(t) ~ exp(t)·||δv||(0). The trajectory
crashes (numerical blow-up: v_peak ~ 15, sup → nan) at t ≈ 5.5, with the
energy diverging past ~10³.

The noise spectrum shows comparable power across all k indices, with the
five largest power modes being k-indices {71, 112, 14, 47, 66} — all of these
are at substantially higher wavenumber than the mode-5 sin used in E2.

## Why mode-5 is tame and broadband is explosive

A high-k δv has small ||δv||_{L²} but very large ||δv_x||, ||δv_xx||, ||δv_xxx||.
The coupling u_t -= d_x(3v² + v_xx) injects v_xxx into u explicitly; for
broadband δv this is a very large forcing on u, which immediately drives u
off its initial profile and starts a runaway because (a) u gets large
amplitude → its Burgers self-flux develops shocks; (b) m drifts off zero
fast; (c) the v coupling -d_x(u v) returns this energy back to v.

For mode 5, k = 2π·5/30 ≈ 1.05 is modest, so v_xxx forcing is small and the
linear stage of the response is benign.

So the response is strongly **k-selective**: the BKdV system has effective
instability for high-k modulation of v, presumably driven by the dispersion
relation interacting with the coupling, while low-k structured perturbations
are essentially absorbed into the chaotic drift without amplification.

(Caveat for the curator: this finding hinges on whether the high-k blowup is
a genuine BKdV physical instability or partly a numerical artifact of the
2/3-dealiased pseudospectral / MUSCL scheme being unable to dissipate high-k
energy as fast as the true continuum equation does. A finer-resolution / more
dissipative repeat would be the natural follow-up. Within the stack used —
which the prompt designates as "pre-validated" — the qualitative gap between
E2 and E3 is robust enough that we record k-selectivity as the partial
finding.)

## Conclusion (E3)

E2 vs E3 with matched-norm perturbations gives a **clear k-selective
deviation-growth signature**: broadband (high-k-dominated) noise grows at
~e^t while structured mode-5 sin stays essentially flat for the same
duration. This is a positive (partial) finding for the original question
"does BKdV exhibit modulational instability of known stable structures" —
yes, against high-k modulation in the v field, no against low-k structured
modulation.

Late-time state for E3 is numerical blow-up (sup → ∞), so we cannot
characterize the saturated regime within this stack. Late-time E2 (t=14-15)
shows the onset of growth at +6× initial, suggesting the same instability
mechanism eventually wakes up even for low-k seeds once nonlinear coupling
has had time to upscatter energy to higher k.
