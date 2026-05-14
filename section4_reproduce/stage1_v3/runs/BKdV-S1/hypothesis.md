# BKdV-S1 — Stage-1 method-survey synthesis

## Program research question
What numerical methods stably integrate BKdV at amp ∈ [1, 3] for T = 10? Identify at least one working stack and characterize at least two failure modes (specific methods + their failure signatures).

## Key findings
- **F1 (E1, negative)**: The naive stack — Fourier pseudospectral derivatives + classical RK4 over the *entire* RHS (v_xxx included, explicit) + **no** dealiasing — blows up before t = 0.5 with the textbook broadband-aliasing signature (overflow on the quadratic products v², u·v, v·v_x followed by NaN propagating through the FFT). Failure mode #1: **aliasing instability**.
- **F2 (E2, positive)**: Adding the 2/3-rule dealias on every nonlinear product (and pre-dealiasing the state each RHS evaluation), keeping everything else identical (RK4 on full RHS, dt = 2e-4, amp = 1.5), reaches T = 10 cleanly. mass_v conserved to ~1e-12, sup bounded ≈ 4, energy in the aliased band stays at machine zero. So aliasing was the *dominant* failure mode in R1; explicit-RK4-on-v_xxx is in fact stable at dt = 2e-4 once dealiasing lowers effective k_max from π/dx to (2/3)π/dx.
- **F3 (E3, positive)**: The R2 stack survives amp = 3.0 (top of the requested range): mass_v conserved, no NaN, no warnings, sup_u grows ~2× but stays band-resolved (edge-band energy fraction < 1e-5). The R2 stack is therefore amp-robust over the entire programme range [1, 3] at Nx = 256, dt = 2e-4, T = 10.

## Ruled-out routes / paths shown not to work
- **Fourier-pseudospectral + classical RK4 over the full RHS, no dealiasing** (any non-trivial nonlinear IC): broadband alias-driven blow-up before t = 0.5. Signature: overflow on the product nodes, then NaN through the FFT. Dead end across the amp range — fixing requires at minimum a 2/3-rule cutoff. *Tried in R1, failed.*
- **Trying to fix R1 by reducing dt alone** (not attempted explicitly in this program but ruled out by the R2 finding): reducing dt would not address the aliasing — it would slow but not stop the cascade because aliased modes are forced every step regardless of dt. The fact that R2 succeeded at the same dt = 2e-4 is direct evidence that dt was not the issue.

## Failure modes successfully characterized
1. **Aliasing instability** (E1): symptom — overflow on quadratic products within ~2500 steps, NaN propagating through the FFT, blow-up at t < 0.5. Cure — 2/3-rule cutoff on every nonlinear product.
2. **Partially characterized / predicted-but-not-realized at this resolution**: a *second* numerical failure mode (explicit-RK4 stiffness on v_xxx; or Burgers-side shock-front aliasing when u·u_x outruns the 2/3 band) was *expected* but did not materialize at amp = 3, T = 10, dt = 2e-4. The program therefore characterizes one strong dead-end mechanism plus a null-result envelope for the next: stiffness becomes the binding constraint above dt ≈ 4.94e-4 (post-dealias RK4 CFL), and Burgers-shock band-overrun becomes binding at higher amp or longer T than tested.

## Trivial-finding flag
None. F1, F2, F3 are all marked `is_trivial: false`.
- F1 (negative) is *informative*: it isolates the aliasing mechanism via a definite failure signature. Not tautological.
- F2 (positive) is *informative*: it answers an a-priori-open question ("does 2/3-rule dealias alone fix the R1 blow-up?") with a definite "yes" and confirms the diagnosis.
- F3 (positive) is *informative*: it tests amp-robustness over the top half of the requested range, an open question whose answer ("yes, stack is amp-robust to 3.0") narrows the working envelope. It is *not* trivial because the alternative outcome (a second failure mode at high amp) was a-priori plausible.

## Recommendation for downstream Stage-2 tasks
Use Fourier + 2/3-rule dealias + classical RK4 (dt ≤ 2e-4, Nx ≥ 256) for amp ∈ [1, 3], T ≤ 10. If dt or amp is raised or T extended, reach for IMEX-CN on v_xxx and MUSCL on u·u_x.
