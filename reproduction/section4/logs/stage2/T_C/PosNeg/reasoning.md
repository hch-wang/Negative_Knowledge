# Reasoning — T_C / PosNeg

## Final method

**Final method = E2**: Fourier pseudospectral on periodic `x ∈ [-15, 15]` with
`Nx = 256`, 2/3-rule dealiasing on every nonlinear product (`u^2`, `v^2`,
`u v`), classical explicit RK4 over the full coupled RHS (including `v_xxx`),
and an added explicit linear viscosity `ν * u_xx` with **ν = 5e-2** acting
only on the `u`-equation. Time step `dt = 1e-4`, `T = 8.0`, 17 snapshots
saved at `t ∈ {0, 0.5, 1.0, ..., 8.0}`.

Stability budget:
- post-dealias RK4 dispersion CFL on `v_xxx`: `dt_crit ~ 4.94e-4`, we use `dt = 1e-4`.
- parabolic-RK4 bound for `ν * u_xx`: `ν * k_max^2 * dt ~ 3.6e-3`, well below the
  RK4 real-axis stability boundary `~2.78`.

## Iteration trace

- **E1** (baseline, no u-viscosity): Fourier+2/3-dealias+RK4 at dt=1e-4, no
  ν. **F1**: reached T=8 without IEEE blow-up; mass exactly conserved
  (u: 22.5879, v: 3.0); but bore-driven Burgers self-flux cascaded into a
  Gibbs-like field with `u_max = 3.42`, `u_min = -1.99`, `TV(u) = 248.2`
  (~165× the IC TV of 1.5). The `-d_x(u v)` coupling poisoned v, fragmenting
  the soliton into 6 peaks with final `v_max = 0.448` — just below the
  `≥ 0.5` phenomenon target. This is exactly the failure mode catalogued by
  `BKdV-S6` round 1. **D1**: change_method → add ν*u_xx with ν=5e-2.
- **E2** (E1 + ν=5e-2 on u_xx, single-component escalation): everything else
  identical. **F2**: `v_max_final = 0.506` (passes), `u_max_final = 1.340`
  (passes |u_max|<5), `TV(u) = 4.91` (3.3× IC TV — the bore is now
  physically smoothed, not numerically poisoned), mass exactly conserved.
  v trajectory shows the soliton dipping to 0.418 during the t=3-4 encounter
  window, then partially recovering to 0.506 by T=8 (consistent with
  transmission with partial energy loss to bore radiation). **D2**:
  `stop_useful`.

E3 was not consumed: F2 satisfies the phenomenon target on all three
criteria, and progressive-complexity discipline says to stop at the minimum
sufficient method.

## Use of memory

Bank entries that drove the decisions (cited):

- `BKdV-S1` (positive, round 1, kb-id BKdV-S1-pos-r1): established that
  Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 at dt=2e-4
  is a clean, stable baseline for the v-side dispersive dynamics at Nx=256
  on this class of IC; mass exactly preserved, no aliasing pile-up. This
  confirmed our E1 choice of stack at the **time-integrator and
  discretization layer**.
- `BKdV-S1` (positive, round 2, kb-id BKdV-S1-pos-r2): showed the same
  stack survives at amplitude 3.0 — gives confidence that the v-side does
  not need IMEX-CN at our amplitude 1.5.
- `BKdV-S6` (positive, round 3, kb-id BKdV-S6-pos-r3): the critical
  positive entry for **E2**. Round-3 dissipation sweep established that
  ν ∈ {1e-2, 5e-2} both pass for bore-like u IC, with ν=5e-2 giving
  `TV(u)_final ~ 9.6` and `u_min_final ≥ 0` — the best balance between
  bore-shock control and physical preservation. We adopted ν = 5e-2 exactly.
- `BKdV-S6` deep-synthesis (positive, kb-id BKdV-S6-deep-synthesis-pos):
  formulated the rate balance `ν >> u_max / k_max ~ 0.11` that justifies
  why ν must be at the 1e-2 scale and not orders of magnitude smaller.

Bank entries that drove the decisions (rejected, with reason):

- `BKdV-S4` deep-synthesis (negative, kb-id BKdV-S4-deep-synthesis-neg):
  explicitly REJECTED. BKdV-S6 deep-synthesis warns that the BKdV-S4 "safe
  envelope" ν_h ∈ [1e-22, 1e-20] for k^8 hyperviscosity is **13 orders of
  magnitude too weak** for bore-like u IC. The S4 envelope was validated on
  smooth Gardner-manifold ICs (`v0 = 1.5 sech^2(x+5), u0 = v0^2/2`), not on
  steep bores; transferring it would yield the E1 failure mode. We chose
  linear ν=5e-2 explicitly to avoid the S4 hyperviscosity pitfall.
- `BKdV-S6` round 1 (negative, kb-id BKdV-S6-r1-neg): rejected the
  no-viscosity stack at the bore IC — exactly the failure we reproduced in
  our E1 to confirm the diagnosis (TV inflation 165×, u_max 2.3× IC).
- `BKdV-S6` round 2 (negative, kb-id BKdV-S6-r2-neg-eps-1e-4): rejected
  the "standard tiny" ε=1e-4 viscosity choice; rate-balance shows it is
  2-3 orders of magnitude under-sized. This is why E2 jumps to ν=5e-2,
  not ν=1e-4.
- `BKdV-S1` round 1 (negative, kb-id BKdV-S1-neg-no-dealias): rejected
  any Fourier+RK4 variant without dealiasing — blows up before t=0.5 via
  overflow. Our E1 retained 2/3-rule dealiasing for this reason.
- `kb-burgers-fwdEuler-centralFD-Gibbs` (negative): rejected naïve central
  FD on the Burgers component; even with finite output, gives 21 spurious
  peaks. Our E1 keeps the Fourier+dealias stack instead.
- `kb-kdv-noDealiasing-aliasing-artifacts` (negative): rejected
  no-dealiasing Fourier; gives spurious soliton-like peaks at wrong
  amplitude. Reinforces the 2/3-rule choice.
- `kb-kdv-IFRK4-blowup` (negative): rejected integrating-factor RK4
  without dealiasing — would short-circuit our progressive-complexity
  ramp. We use plain explicit RK4 instead.
- `kb-shallowWater-centralFD-fwdEuler-hNegative` and
  `kb-general-centralFD-hyperbolic-shockFormation` (negative): rejected
  central-FD-only treatment for any hyperbolic component — the bore-like
  u IC is exactly the regime these warn against.
- `kb-burgers-LaxFriedrichs-longTime-dissipation` and
  `kb-shallowWater-LaxFriedrichs-overdiffusion` (negative): rejected
  global Lax-Friedrichs as the u-side dissipation mechanism — over T=8 it
  would severely over-smear the bore. Explicit linear ν*u_xx is locally
  proportional to curvature, much milder.

The positive entries told us **where to escalate** (add linear ν=5e-2 on u_xx,
keep Fourier+dealias+RK4); the negative entries told us **where not to
escalate** (don't reuse the S4 hyperviscosity envelope, don't drop
dealiasing, don't try central FD, don't use Lax-Friedrichs global diffusion,
don't use IFRK4). Both were essential at E2: positives picked the magnitude
ν=5e-2, negatives ruled out the otherwise-tempting "just transfer the S4
ν_h envelope" shortcut that would have left u poisoned again.

## Final self-assessment

`pred_results/T_C.npy` has shape `(17, 2, 256)` with snapshots at
`t ∈ {0.0, 0.5, ..., 8.0}`. The phenomenon target asks:

1. **Final v should contain a recognizable peak with amplitude ≥ 0.5.**
   - `v_max(T=8) = 0.506` ✓ (margin 0.006; below threshold only at the
     mid-encounter dip t=4.0 where v_max = 0.418).
   - n_peaks (height > 0.1) at T=8 = 3; the dominant peak is recognizable.
2. **u should stay bounded (|u_max| < 5).**
   - `u_max(T=8) = 1.340`, max-over-all-snapshots = 2.707 at t=2.0. ✓
3. **Bore should not have blown up.**
   - No NaN, no Inf. `TV(u)` ratio 3.27 (vs E1's 165) → physically smoothed
     bore. `u_min ≥ -0.245` (the bore stays nearly monotone, only a small
     residual oscillation downstream). Mass exactly conserved. ✓

I believe the file satisfies the phenomenon target. The qualitative
interpretation of the bore × soliton encounter at T=8: the KdV soliton
(amplitude 1.5 at x=-8) propagates rightward, encounters the bore (u_L=1.5
to u_R=0 transition at x=0), loses ~67% of its peak amplitude during the
t≈3-4 transit, and emerges on the right with a partial recovery to v_max ≈
0.5 — i.e. **transmission with substantial energy loss**, rather than clean
reflection, fusion, or destruction. The energy lost from the soliton
appears as dispersive radiation on either side of the surviving peak
(visible as the 3-peak structure at T=8) and as bore-side smoothing.
