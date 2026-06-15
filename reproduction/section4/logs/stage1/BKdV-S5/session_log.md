# BKdV-S5 session log

## Round 1 (E1) — baseline Gardner-soliton-like m=0 IC

Design: v(x,0)=a sech²(x+5), u(x,0)=v²/2, a=1.0, T=15.
Solver: Fourier pseudospectral + 2/3 dealias + IMEX-CN on v_xxx + MUSCL-Godunov
on u's self-flux + explicit Euler on coupling, dt=1e-4.
Outcome: integrates to T=15 stably (mass_v conserved to 0 ppm). The m=0 set is
NOT invariant — m_norm grows 0 → 2.92; v_peak loses coherence within t<1 and the
flow becomes a chaotic dispersive state. Energy(u,v) drifts +680%, consistent
with off-manifold cascade. Verdict: baseline is NOT a coherent traveling wave;
"approximate Gardner soliton" premise is materially weaker than the prompt
implies. Partial finding (not trivial).

(Bug-fix iterations: a=1.5/dt=2.5e-4 → blew up at t≈3; a=1.0/dt=1e-4 without
MUSCL → blew up at t≈9. Adding MUSCL-Godunov on 3 u u_x reaches T=15.)

## Round 2 (E2) — small structured mode-5 perturbation

Design: identical to E1, but add δv₀=0.05 sin(2π·5 x/L) to v while leaving u=v_base²/2.
Diagnostic: ||v_E2(t)-v_E1(t)||_{L²} at shared snapshot times.
Outcome: deviation flat at ~0.2 (= initial L²-norm) for t∈[0,13], then jumps to
1.15 at t=15 (≈6×). Effective fit growth rate +0.05/unit, dominated by late
jump; for t≤13 the growth rate is statistically zero. No blow-up. Partial /
mostly-negative finding: mode-5 perturbation is not strongly amplified.

## Round 3 (E3) — broadband-noise perturbation, matched L² norm

Design: identical to E2 but δv₀ = zero-mean Gaussian noise (seed=42) rescaled
to ||δv₀||=0.1936 (same as E2). Top spectral content at k-indices {71, 112,
14, 47, 66} — substantially higher-k than mode-5.
Outcome: deviation grows ||δv||(t) ~ exp(1.02·t)·||δv||(0); ratio E3/E2 reaches
143× at t=5; numerical blow-up at t=5.5. **Clear k-selective response**:
broadband (high-k) modulation is exponentially amplified, mode-5 is inert at
the same L² norm. Positive partial finding.

## Synthesis

BKdV does exhibit modulational instability of the "approximate Gardner soliton
on m=0" state, but the relevant unstable direction is **high-k modulation of
the v field**, not generic small-norm modulation. Low-k structured
perturbations (mode 5) are absorbed into the chaotic baseline drift without
amplification on T≤15. Late-time E2 shows onset of growth at t≈14, consistent
with nonlinear upscatter of energy from mode 5 into the unstable high-k
window. The premise of a stable Gardner soliton on m=0 is itself wrong (m=0
manifold is not BKdV-invariant for sech² ICs).
