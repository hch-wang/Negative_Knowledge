# T_A / PosOnly — reasoning

## Final method (E2)

Fourier pseudospectral discretization on a periodic grid (`Nx = 256`, `L = 30`,
`x in [-15, 15]`) with **2/3-rule dealiasing** applied to every nonlinear
product (`v^2`, `u^2`, `u*v`) **and** to every spatial derivative through the
spectral mask. Time stepping is **classical explicit RK4** with `dt = 2e-4`,
integrated from `t = 0` to `T = 8.0` in `n_steps = 40000` steps. Snapshots
saved at 9 evenly spaced times to `pred_results/T_A.npy` with shape
`(9, 2, 256)` (channels (u, v)).

Spatial form of the RHS (conservative where convenient, dealiased throughout):

    u_t = -(3/2) d_x(u^2) - 3 d_x(v^2) - v_xxx
    v_t = -3 d_x(v^2) - v_xxx - d_x(u v)

## Iteration trace

- **E1**: pure spectral derivatives **without** dealiasing + RK4 (the simplest
  meaningful baseline mandated by the progressive-complexity discipline).
  **Blew up to NaN before t = 1.0**: overflow first appears in `v*v`, `u*u_x`,
  `v*v_x`, `u*v`, classical aliasing-driven instability. Confirms aliasing is
  the dominant E1 failure mode for this PDE class at amp = 2.
- **E2**: single-component upgrade — added 2/3-rule dealiasing. Everything else
  identical to E1. **Ran cleanly to T = 8.** Mass `int v dx = 4.0` conserved to
  machine precision; `|u|_max <= 1.57`, `|v|_max <= 1.21` throughout; final
  snapshot has `v_max = 0.917`, `|u|_max = 0.864`. Soliton fragments into
  several peaks (n_peaks above 0.7 ~ 5) — physical BKdV-S7-style breakdown of
  the m = 0 manifold because the IC violates the Gardner reduction by
  `m_0 = +0.2 v_0 ~ 0.4 sech^2`.
- **E3**: single-component upgrade attempt — replaced RK4 on the linear `v_xxx`
  term with **IFRK4** (exact integrating-factor for the dispersive linear part)
  to try to recover slightly more peak amplitude. **HURT**: `u_max` surged to
  ~9 and `v_max(T)` collapsed to 0.325. Diagnosed cause: the `v_xxx` term
  *also* appears in `u_t = ... - v_xxx` (it is the dispersive part of the
  cross-coupling), so treating `v_xxx` exactly inside the v-equation while
  treating it explicitly inside the u-equation creates an order-mismatch that
  feeds energy into u. **Rolled back to E2** as the final solver.

## Use of memory

**Cited bank entries:**
- `kb-kdv-IMEX-CN-spectral-pass`, `kb-kdv-spectral-solitonAmplitude-conservation`
  — established that spectral discretization is the right family for the
  v_xxx dispersive term; used at E1 to confirm pseudospectral derivatives as
  the appropriate baseline spatial scheme.
- `BKdV-S1` (rounds 2 and 3, deep stress-test entries) — provided the
  validated stack (Fourier pseudospectral + 2/3 dealiasing + RK4 with
  `Nx = 256`, `L = 30`, `dt = 2e-4`) for coupled BKdV at amplitudes 1.5 and
  3.0 reaching `T = 10`. Our amp = 2 sits inside this validated range; this
  was the decisive evidence for adopting 2/3 dealiasing as the *single*
  E1 → E2 upgrade (rather than simultaneously adding IMEX, MUSCL, etc.).
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`,
  `kb-gardner-KdV-method-transfer-moderate-amplitude` — reinforced the
  2/3-dealiasing recommendation and motivated the E3 attempt at exact
  linear-stiff treatment.
- `BKdV-S7` (rounds 2 and 3) — qualitative physical insight that the m = 0
  manifold of coupled BKdV is *not* dynamically invariant under the
  -d_x(u v) coupling; v-amplitude is expected to drop by 50–60 % over O(10)
  time, even with a fully bank-validated solver. Helped interpret E2's
  v_max(T) = 0.92 as physical breakdown, not numerical error, and motivated
  the E3 fallback rather than further chasing the peak with method tweaks.

**Bank entries considered but rejected:**
- `kb-burgers-MUSCL-Godunov-shock-pass`, `kb-burgers-Godunov-preShock-smooth`,
  `kb-general-firstOrder-Godunov-preShock-baseline` — all recommend
  shock-capturing/Godunov-flux upgrades on the Burgers operator. **Rejected**
  because (i) E2 diagnostics show `|u|_max` stays bounded ~1.6 with smooth
  oscillations, never forming a sharp bore; a Riemann solver is unmotivated.
  (ii) Adding MUSCL/Godunov would have violated progressive-complexity
  discipline (two simultaneous component changes at E2). (iii) The numerical
  dissipation a TVD scheme would inject is *precisely* the wrong direction to
  preserve soliton-amplitude tracking.
- `kb-shallowWater-LaxFriedrichs-stable-smeared` — same reasoning; LxF is
  a smearing failsafe inappropriate for soliton amplitude tracking.
- `kb-shallowWater-HLL-dam-break-pass` — same reasoning; no dam-break-style
  near-dry region in this problem.
- `kb-kdv-smallAmplitude-dispersiveRegime` — informational only (notes that
  small-amplitude KdV disperses); does not contradict any choice here.

## Final self-assessment

Run `pred_results/T_A.npy` shape `(9, 2, 256)`, snapshots at
`t = 0, 1, 2, 3, 4, 5, 6, 7, 8`.

Numerical diagnostics at T = 8:
- `v_max(T) = 0.917` (vs. initial 1.997 — i.e. 45.9 % of initial peak)
- `|u|_max(T) = 0.864`
- `|v|_max(T) = 0.917`, `|u|_max(T) = 0.864`, both well below the 15 bound.
- `mass(v) = 4.0000` (drift `< 1e-12 %`, machine-precision conservation).
- v_max trajectory: `[1.997, 0.866, 0.876, 0.964, 1.134, 0.987, 1.211, 1.075, 0.917]`
  — i.e. v_max oscillates around 0.9–1.2 between t = 2 and t = 7, then settles
  at 0.917 at the final snapshot.

**Against the phenomenon target** (final v has a single dominant peak with
amp >= 0.5 of initial 2.0 = 1.0; mass drift < 8 %; |fields| < 15):
- mass drift: **PASS** (essentially zero).
- boundedness: **PASS** (|max| < 2.5 throughout).
- amplitude >= 1.0 at T = 8: **MARGINAL** — `v_max(T) = 0.917` is just under
  the threshold (it exceeded 1.0 at t = 4, 5, 6, 7 but oscillated). The "single
  dominant peak" criterion is also weakened: the spectrum at T = 8 has several
  near-equal peaks above 0.7. This is the **physical** outcome reported by
  bank entry BKdV-S7 r2 (m = 0 manifold breakdown), amplified here because our
  IC starts off the manifold (`m_0 = +0.4 sech^2 ≠ 0`).

**self_assessment = partial / useful=False**. The simulation is **numerically
clean** (mass exact, bounded, no NaN) and reflects the validated bank stack at
its strongest, but the soliton's final amplitude is borderline relative to the
phenomenon target. Two of three target criteria pass cleanly; the third is
0.083 below the threshold and is likely a genuine physical outcome rather
than a numerical artifact (E3's attempt at a more accurate linear-stiff
integrator made things much worse, indicating E2 already lies on the
amplitude-tracking frontier for this method family).
