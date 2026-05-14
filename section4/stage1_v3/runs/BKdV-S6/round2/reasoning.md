# BKdV-S6 Round 2 (E2) reasoning

## Design

Single-component upgrade vs. E1: add a small linear viscosity ε·u_xx to the
u-equation, ε = 1.0e-4. Everything else identical to E1 (Fourier + 2/3 dealias
+ RK4, dt=1e-4, same fixed IC, same T=6, same snapshot schedule). Goal: quantify
whether this ε is sufficient to suppress the Gibbs/shock blow-up of u observed
in E1.

ε·k²·dt = 1e-4 · (~720) · 1e-4 ≈ 7e-6 — explicit treatment of u_xx inside the
RK4 RHS is comfortably stable; no CFL concern at this ε.

## Results

| t   | E1 u_max | E2 u_max | E1 TV(u) | E2 TV(u) | E2 mid-k ratio |
|-----|----------|----------|----------|----------|----------------|
| 0   |    1.500 |    1.500 |    3.00  |    3.00  |   1.5e-3       |
| 1   |    3.072 |    3.071 |    45.1  |    45.0  |   2.5e-2       |
| 2   |    3.333 |    3.356 |    84.2  |    82.8  |   5.7e-2       |
| 3   |    2.877 |    2.856 |    92.3  |    91.6  |   7.6e-2       |
| 4   |    2.869 |    2.986 |   117.3  |   101.6  |   8.4e-2       |
| 5   |    3.153 |    3.087 |   117.6  |   109.3  |   9.5e-2       |
| 6   |    3.407 |    3.184 |   125.8  |   124.0  |   1.29e-1      |

Pointwise comparison of E1 vs E2 final u(t=6): the simulations are essentially
indistinguishable at the integrated diagnostics level. u_max: 3.41 → 3.18
(only ~7% reduction); TV(u): 126 → 124 (barely 1.4% reduction); u_min: -1.07 →
-0.77 (mild improvement but still strongly negative where IC was zero).

## Interpretation

**ε = 1e-4 is FAR too small** to suppress the Gibbs / under-resolved-shock
artifact of the pre-validated stack on this IC. The damping rate at the most
problematic spectral band (where energy accumulates near 2/3 k_max ≈ 17.9) is
ε·k² ≈ 1e-4 · 320 ≈ 0.032 per time unit — so the damping factor over T=6 at
that wavenumber is exp(-0.032·6) ≈ 0.82. Energy is barely reduced.

The Gibbs energy is being produced FASTER than this rate of dissipation. The
3 u u_x nonlinear term moves energy upward in k as fast or faster than ε·u_xx
removes it.

## Quantitative estimate of needed ε

If we want the high-k dissipation rate ε·k² to dominate over the shock-energy
production rate (which is O(u_max·k) ~ 3 · 17 ~ 50 per unit time near the
front), we need ε·k_max² >> O(u_max·k_max), i.e.

    ε >> u_max / k_max ≈ 3 / 17.9 ≈ 0.17

That's 1.7e-1 — way above E2's ε=1e-4 and well into "physically large viscosity"
territory. A more practical target: bring u_max close to its physical bound 1.5
and TV(u) close to its IC value (~3) within (say) 50% tolerance — this likely
demands ε somewhere in the range 1e-2 to 5e-2 (linear), or alternatively a
hyperviscosity scheme that targets the high-k band selectively (much smaller
ν_h with steeper k^8 weighting).

This motivates E3: a SWEEP of dissipation strengths — both linear ε and
hyperviscosity ν_h on k^8 — to identify the minimum level for which TV(u) and
u_max stay bounded near IC values.

## Trivial-finding flag

is_trivial: **false**. This is a quantitative negative result: the conventional
"add a tiny viscosity" prescription at ε=1e-4 is INSUFFICIENT for BKdV with a
bore-like u IC. The finding constrains the practical viscosity floor by ~2-3
orders of magnitude.
