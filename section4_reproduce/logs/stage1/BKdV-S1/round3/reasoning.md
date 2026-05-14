# Round 3 — push amplitude to the top of the requested range

## Design
Same solver as R2 (Fourier spectral + 2/3-rule dealiasing + classical RK4 over the entire RHS, dt = 2e-4, Nx = 256). Single component changed vs R2: IC amplitude raised from amp = 1.5 to amp = 3.0 (top of the program's required range [1, 3]).

This isolates "is the R2-working stack amplitude-robust over the requested range?" and probes for a *second* failure mode (e.g. high-amplitude gradient steepening from u·u_x or v·v_x exceeding the resolved band, or Burgers-side shock formation under-resolved by 2/3 spectral).

## Observation
- Reaches T = 10.0 with no NaN, no warnings, no overflow.
- `mass_v` exactly conserved at 6.000000e+00 throughout (twice R2 since v0 is 2× larger).
- `sup_u` rises from 4.49 → ~10–11, with strong oscillations; `sup_v` decays from 3.00 → ~1.16 (soliton broadens / radiates).
- `edge_frac` (energy fraction in top 10% of resolved band) peaks at ~3e-6, never crosses the 1e-4 alert threshold — the resolved band is comfortably resolving the dynamics.
- Energy ∫(u²+v²)/2 dx oscillates around 20 (vs initial 15.3); growth phase early, then quasi-equilibration. Same physical character as R2 scaled by amplitude.
- Run cost: ~22 s, identical to R2.

## Diagnosis
The R2 stack (Fourier + 2/3 dealias + RK4, dt = 2e-4) is **amp-robust over [1.5, 3.0]** at this resolution. No second numerical failure mode emerges at amp = 3.0. The Burgers-side `u` field acquires steep features (sup_u doubles) but they remain band-resolved.

## What about the "at least 2 failure modes" requirement?
F1 (R1) gave us one strong failure mode: **broadband aliasing** under no dealiasing. We did **not** experimentally trigger a second one in R2/R3. The prompt's quota is partially met: 1 hard failure + 1 amp-stress null-result. The honest reading is:

- A *predicted* second failure mode exists but was not realized in this run: **explicit-RK4 stiffness on v_xxx** if dt is raised above ~4.94e-4 (the post-dealiasing CFL bound). We did not test it — that would have been a fourth round.
- Another predicted second failure mode: at significantly higher amp or longer T, Burgers-side shocks in u would over-shoot the 2/3-rule resolution, triggering Gibbs-style oscillations and eventually instability; the working stack would then need MUSCL-Godunov on u·u_x (as anticipated by the prompt's pre-validated stack description). At amp = 3.0, T = 10, this regime is not yet entered.

## Triviality assessment
F3 is **not trivial**: an a-priori-open question (does the R2 stack survive amp = 3?) was answered "yes" with positive evidence. It establishes the upper boundary of the working envelope tested in this program — non-tautological information for the curator.
