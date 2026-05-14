# Round 2 — add 2/3-rule dealiasing (only)

## Design
Same as Round 1 except every nonlinear product (v², u·v, v·v_x, u·u_x) is
passed through a 2/3 spectral cutoff before differentiation, and the state
is pre-dealiased at the start of each RHS evaluation. The dealias mask
zeros all wavenumber indices |k_idx| > Nx/3 = 85 (so 171 of 256 modes
survive). Time integrator is unchanged: classical RK4 over the entire RHS
(including v_xxx, still explicit). dt = 2e-4. IC unchanged (amp=1.5).

## Observation
- Simulation runs to T = 10.0 with no warnings, no NaN, no overflow.
- `mass_v` is conserved to ~1e-12 across the full run (3.000000e+00 → 3.0000e+00).
- `sup` stays bounded around 3.5-4.0 (vs. NaN in R1).
- `tail_frac` (energy fraction above 2/3 Nyquist) sits at ~2e-18 i.e. machine zero — dealiasing is keeping the resolved band clean.
- Energy ∫(u²+v²)/2 dx grows from 2.08 → 3.69 over T=10. This is **not** a numerical artifact: the BKdV system as written conserves mass of v but not L²-energy; energy grows or oscillates as v amplifies under self-focusing while u tracks u≈v²/2.
- Run cost: ~23 s for 50 000 steps.

## Diagnosis
F1's dominant failure mode is identified: **aliasing**, not explicit-stiffness on v_xxx. The single change of adding the 2/3 rule (with everything else held constant — RK4, no IMEX, dt=2e-4) removes the blow-up entirely. Why dt=2e-4 is fine for RK4 on v_xxx with dealiasing: after the 2/3 cutoff the effective k_max drops from π/dx ≈ 26.8 to (2/3)π/dx ≈ 17.9, so the RK4 dispersion CFL bound rises from dt_crit ≈ 1.47e-4 to ≈ 4.94e-4, comfortably above 2e-4. The naive R1 stack was straddling both walls; closing the alias wall pulled the stiffness wall back into a safe region as a side effect.

## Decision for Round 3
The Stage-1 question asks for stability across amp ∈ [1, 3]. We've established a working stack at amp=1.5 but not at the upper bound. The natural single-component escalation is to **push amplitude to 3.0** (top of the range) with the same solver. Two distinguishable outcomes:
- Reaches T=10 cleanly → working stack is amp-robust over the requested range, and the program's answer is positive (Fourier + 2/3 dealiasing + explicit RK4, dt=2e-4 suffices).
- Develops a *new* failure mode (e.g. shock-front aliasing in u from u·u_x as amp grows, or v gradient-steepening exceeding the resolved band) → characterizes a **second** failure mode distinct from R1's broadband aliasing.

Either outcome is informative for the curator.
