# Reasoning: Stress Test A9 — Shallow Water / Dry-Bed IC

## Method as written
I implemented the **HLL (Harten–Lax–van Leer) Riemann solver** with a Godunov-type first-order finite volume scheme and CFL-based adaptive time-stepping (CFL ≈ 0.45). The wave-speed estimates use Einfeldt's formula (min/max of characteristic speeds from both sides), and a positivity clip is applied after each step to prevent h from going negative.

## Predicted vs expected
I partially agree with the predicted outcome. The HLL scheme is positivity-preserving in principle when wave-speed estimates are correct, and the explicit positivity clip provides a further safeguard. However, at the dry interface (h_R = 0), the numerical flux computation involves division by h ≈ 0, which produces large or undefined velocities even with an epsilon guard. This means u = hu/h can blow up near the dry front, producing the "huge u where h ~ 0" failure mode the prediction describes — even if h itself stays non-negative due to the clip. The positivity clip breaks conservation locally, so the momentum equation can yield nonsensical hu/h ratios in dry cells, consistent with the prediction.

## What knowledge this might produce
A future agent can learn that naive positivity fixes (clipping h, zeroing hu) are insufficient for the dry-bed problem: they mask h<0 violations but leave u = hu/h ill-defined at dry cells, and periodic boundary conditions further contaminate the solution by wrapping dry-cell artifacts back into the wet region. A well-conditioned dry-bed solver requires a consistent wet/dry front treatment (e.g., Roe with entropy fix, HLLE with proper dry-state Riemann solution, or a well-balanced scheme) rather than post-hoc clipping.
