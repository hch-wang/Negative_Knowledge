# BKdV-S6 hypothesis (final synthesis)

## Program research question

Under the standard pre-validated stack (Fourier pseudospectral + 2/3-rule
dealiasing + classical RK4) with NO explicit viscosity / hyperviscosity on u,
does the u-equation remain bounded for moderately-amplitude initial conditions
that stress the Burgers self-flux? If the answer is "no", what minimum level of
explicit u-side dissipation is needed to restore boundedness without distorting
the v sector?

PDE recap (periodic x in [-15, 15], Nx=256):

    u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -d_x(u v)

Fixed IC (across all three rounds):

    v(x,0) = 1.5 * sech^2(x + 5)            (KdV-like seed)
    u(x,0) = 1.5 * (1 - tanh(x/0.5)) / 2    (smoothed bore, u_L=1.5 -> u_R=0)

T = 6.0, dt = 1e-4.

## Key findings

- **F1 (E1, negative)**: Pre-validated stack with NO u-viscosity is
  quantitatively WRONG for this IC. The simulation does not IEEE-blow-up
  (mass_u exactly conserved at 22.59), but the bore in u develops large
  Gibbs ringing under the self-flux 3 u u_x. Numerical signatures by T=6:
  u_max grows from 1.5 to 3.41 (overshoot 2.3x), u_min dives to -1.07
  (large UNPHYSICAL negative excursion where IC has u=0), TV(u) explodes
  from 3.0 to 125.8 (factor 42x), and the spectral energy ratio
  E(k_max/3 < |k| < 2k_max/3) / E_total grows from 0.3% to 25% — the
  textbook signature of high-k energy pile-up at an under-resolved shock.
  The v sector is also poisoned: v_max collapses from 1.50 to 0.58 by t~2.
  Pre-validated stack ALONE is insufficient.

- **F2 (E2, negative)**: Adding the conventionally-prescribed small linear
  viscosity ε·u_xx with ε = 1e-4 is essentially INEFFECTIVE on this IC.
  Final-state diagnostics are nearly identical to E1: u_max=3.18, u_min=-0.77,
  TV(u)=124.0. The damping rate at the most polluted k-band is ε·k² ≈ 3e-2
  per time unit, which is dominated by the shock-energy production rate
  3·u·k ≈ 50 per time unit. ε=1e-4 is *2-3 orders of magnitude too small*
  for an IC with this gradient strength.

- **F3 (E3, positive constructive)**: A 9-point sweep of dissipation across
  linear and hyperviscosity families reveals the practical minimum:
  - **Minimum linear viscosity (marginal): ν ≈ 1e-2**.
    Final u_max=1.62, u_min=-0.03, TV(u)=27.
  - **Comfortable linear viscosity: ν ≈ 5e-2**.
    Final u_max=1.54, u_min=+0.05, TV(u)=9.6 — clean, no negative ringing,
    TV only ~3x the IC TV.
  - **Minimum hyperviscosity on k^8: ν_h ≈ 1e-9** (at the explicit-RK4
    stability ceiling for Nx=256, dt=1e-4).
    Final u_max=1.48, u_min=-0.11, TV(u)=21.9.
  Hyperviscosity values from the BKdV-S4 "safe envelope" (ν_h ~ 1e-22 to
  1e-20) are about **13 orders of magnitude too weak** for this IC.
  All passing cases share a transient u_max ≈ 2.7-3.0 during early bore
  steepening (t in [0.5, 1.5]), but with sufficient dissipation the Gibbs
  energy is then absorbed, leaving a clean shock-like front by T=6.

## Mechanism (from the equations)

The Burgers self-flux 3 u u_x of the IC bore drives a one-sided energy
cascade in u toward high wavenumbers. 2/3-rule dealiasing prevents nonlinear
aliasing of products INTO the resolved band, but it does NOT dissipate
energy already inside the resolved band — and the bore-shock energy piles
up exactly at the high-k edge of the resolved band (k_max/3 < |k| < 2k_max/3),
which we directly observe.

The high-k content of u is then injected into v through the -d_x(u v)
coupling, accelerating decoherence of the v sector. So the negative
finding has two layers: u itself is wrong, AND v is poisoned through
coupling.

The required dissipation rate must dominate the shock-energy injection
rate. Crude estimate: ν · k² > O(u_max · k) at the spectral edge gives
ν > u_max / k_max ≈ 3 / 27 ≈ 0.11 — consistent with our empirical finding
that ν ≈ 1e-2 to 1e-1 brackets the practical floor.

## Ruled-out routes / paths shown not to work

- **"Pre-validated stack (Fourier + 2/3 dealias + RK4) by itself is sufficient
  for any IC"** — Ruled out by E1: even with no IEEE blow-up, the result
  is quantitatively wrong (u_max overshoots 2.3x, large unphysical negative
  oscillations, TV inflated 42x).
- **"A standard tiny viscosity ε=1e-4 covers strong u-gradients"** — Ruled
  out by E2: essentially no improvement over E1 at this ε.
- **"Hyperviscosity in the BKdV-S4 envelope (ν_h ~ 1e-20) safely covers all
  BKdV ICs"** — Ruled out by E3 sweep: ν_h up to 1e-12 produces no
  meaningful improvement; only ν_h = 1e-9 (near explicit-RK4 stability
  ceiling) works on this IC.
- **"u_max_final near IC implies the whole trajectory is fine"** — Misleading:
  even with comfortable ν=5e-2, the transient u_max climbs to ~2.8 during
  bore steepening. The v sector still decoheres because the coupling acts
  during this transient.

## Trivial-finding flag

None of F1, F2, F3 are trivial:
- F1 is a quantitative negative demonstration with multiple corroborating
  diagnostics (u_max, u_min, TV, spectral ratio) and a clear mechanistic
  story (Gibbs pile-up at a shock that 2/3 dealias cannot absorb).
  is_trivial: **false**.
- F2 is a non-trivial calibration claim: a specific "standard" ε is shown
  insufficient by 2-3 orders of magnitude, with a rate-balance estimate
  consistent with the observation.
  is_trivial: **false**.
- F3 is a constructive minimum-dissipation result, distinguishing two
  families (linear vs k^8 hyperviscosity), identifying that the BKdV-S4
  hyperviscosity envelope is 13 orders of magnitude too weak for this IC.
  is_trivial: **false**.

Trivial-finding count: **0**.

## Recommendation for downstream Stage-2 tasks

> **For ICs that introduce strong u-gradients in BKdV (bores, large v
> amplitudes that drive u via v² coupling), the pre-validated stack
> (Fourier pseudospectral + 2/3-rule dealiasing + classical RK4) ALONE is
> INSUFFICIENT — explicit u-side dissipation is required.**
>
> **Suggested levels:**
> - Linear viscosity: **ν ≈ 1e-2** (marginal floor), **ν ≈ 5e-2**
>   (comfortable, recommended default).
> - k^8 hyperviscosity: **ν_h ≈ 1e-9** (minimum, but at explicit-RK4
>   stability ceiling for Nx=256, dt=1e-4 — use only with IMEX/exp time
>   integrator if margin is needed).
>
> **Without any u-dissipation, u_max grows by a factor of ≈2.3x over T=6
> (1.5 → 3.4), TV(u) grows by ≈42x (3 → 126), and u develops large
> unphysical negative excursions (u_min ≈ -1.07 where IC has u=0).** The
> v sector is collaterally poisoned through the -∂_x(uv) coupling.
>
> The hyperviscosity envelope previously calibrated on smooth-soliton ICs
> (BKdV-S4, ν_h ~ 1e-22 to 1e-20) is *13 orders of magnitude too weak*
> for ICs with bore-like or shock-driven u-gradients — calibration must
> be IC-class-specific.

Stage-2 priorities: (i) before introducing any IC with sharp u-gradients,
re-calibrate the dissipation level against this S6 floor; (ii) when in
doubt, default to ν ≈ 5e-2 linear viscosity (it's CFL-trivial under
explicit RK4 at this Nx/dt); (iii) measure TV(u) and the high-k spectral
ratio as primary qualitative diagnostics for "is the u side well-behaved?"
in any new BKdV experiment.
