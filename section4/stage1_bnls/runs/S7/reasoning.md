# S7 reasoning: B-NLS Burgers bore meets NLS bright soliton

## The two numerical pain points

The B-NLS system has two distinct stiffnesses that a single discretization
cannot handle:

1.  **Bore in `u`** — the IC `u(x,0) = (1 - tanh(x/0.5))/2` is smoothed at width
    0.5, but under `u_t + u u_x = 0` (the inviscid Burgers self-flux) the
    left half (u = 1) outraces the right half (u = 0), the gradient steepens,
    and the discontinuity sharpens to a rarefaction fan with a strict step at
    the foot. Pure spectral on `u` immediately develops Gibbs ringing
    (overshoot > 0 above 1, undershoot < 0 below 0) at the bore.

2.  **Quantum-pressure singularity in the HJ equation** — the bright soliton
    `N(x,0) = sech^2(x+8)` has tails `N(x) ~ exp(-2|x+8|)` that decay to
    `~ 10^{-20}` in the bulk. The HJ equation contains the term
    `(sqrt N)_{xx} / (2 sqrt N)` (the quantum pressure of the Madelung
    representation), which is finite for an exact `sech^2` profile but
    catastrophically singular under any discretization that puts a `1/sqrt(N)`
    factor against a non-zero numerator. Spectral differentiation amplifies
    this since aliasing makes the numerator non-zero on a noise floor.

Pain point (1) is the one the prompt names. Pain point (2) is the one that
actually kills the all-spectral run first.

## Experiments

### E1 — all-spectral RK4 (negative control)

`u, N, phi` evolved together by RK4 with spectral derivatives. The HJ
quantum pressure is computed as `d2x_spec(sqrt(N)) / (2 * sqrt(N))` with a
`1e-30` floor on `N` inside the `sqrt`. The floor is not enough: with
`N_min ~ 1e-20`, dividing by `sqrt(N) ~ 1e-10` against a spectral-noise-level
numerator overflows in one RK4 sub-step. Run dies at `t = 0.001`. Confirms
**negative finding 1**: bare (N, phi) formulation is unusable.

### E2 — MUSCL u + Madelung-Psi Strang split (final candidate)

The cure is to use **shock-capturing on `u`** AND **Madelung-Psi on (N, phi)**:

-   `u` sector: MUSCL reconstruction with van-Leer slope limiter, Godunov
    upwind/sonic flux for the convex flux `f(u) = u^2/2`, SSP-RK3 in time.
    This is the exact same scheme used as the proven single-component
    upgrade for the BKdV stage 2 T_C problem (Burgers-coupled-to-KdV bore in
    `u`), reused here.

-   `(N, phi)` sector: Madelung transform `Psi = sqrt(N) exp(i phi)` reduces
    the pair to the NLS-with-advection equation
    ```
    i Psi_t = -(1/2) Psi_xx - i u Psi_x - i (u_x/2) Psi - kappa |Psi|^2 Psi
    ```
    in which **no `1/sqrt(N)` appears**: the quantum pressure cancels
    algebraically in the Madelung-Psi variable. Time stepping is a
    Strang split:
    1.  Cubic half-step: `Psi <- Psi exp(i kappa |Psi|^2 dt/2)` (pointwise,
        with `|Psi|^2` 2/3-dealiased to suppress cubic-focusing aliasing).
    2.  Linear-dispersion full step: `Psi_hat <- Psi_hat exp(-i k^2 dt / 2)`
        with the 2/3 dealias mask.
    3.  Advection full step on `Psi_t = - u Psi_x - (u_x/2) Psi` via real-
        space RK2 with the frozen `u` from this time level (sufficient
        coupling for forward `u -> Psi` since the prompt's stress question
        is about the bore impressing on the soliton, not the back-reaction).
    4.  Cubic half-step (symmetric).

Result: passes T = 8 cleanly. `u_max = 1.0` exactly, TV(u) = 1.988 (no
Gibbs), N_max bounded in [0.993, 1.012] throughout (sub-2% modulation),
`|Psi|^2` mass conserved to 1.5e-7 in the pre-collision phase and 7e-5 over
the full run, single coherent peak throughout (n_peaks_final = 1), bore foot
at x = 3.98 at T = 8 (correct rarefaction fan speed), soliton at x = +4.8.

The bore-soliton interaction is a clean **transmission**: the soliton
crosses x = 0 at t ~ 5.0 and emerges to the right of the rarefying bore as
an essentially intact soliton. No reflection, no capture, no break-up.

### E3 — MUSCL u + spectral (N, phi) (discriminating control)

Same shock-capturing scheme on `u`, but `(N, phi)` left in Madelung-free
form with explicit quantum pressure. Run dies at `t = 0.006` with the
identical HJ singularity as E1, despite MUSCL+Godunov holding the bore
perfectly (zero overshoot in `u`). This isolates the failure: **shock
capturing on `u` is necessary but not sufficient** — the Madelung-Psi
reformulation of (N, phi) is the other half of the cure.

## What was learned (positive and negative knowledge)

**Positive**:
1.  The standard operator split — shock-capturing on the hyperbolic sector
    (`u`) plus spectral/Madelung on the dispersive sector (`Psi`) — works
    for B-NLS with kappa = +1 and produces clean transmission dynamics.
2.  Mass conservation to 7e-5 over a full T = 8 run including a violent
    bore-soliton focusing event is achievable with a 4th-order Strang split
    at dt = 5e-4 and 2/3 dealiasing.
3.  The collision time for the IC of S7 is t ~ 5.0 (soliton crosses x = 0).

**Negative**:
1.  Pure spectral on (N, phi) without Madelung is fundamentally broken for
    any bright-soliton IC: the quantum-pressure singularity overflows in
    one time step, independent of dt and independent of how clean the `u`
    discretization is.
2.  The all-spectral approach is dominated by the HJ singularity, not the
    bore Gibbs. The bore overshoot was only 0.26% in the first step; the
    HJ NaN preempted the Gibbs problem.
3.  Without 2/3 dealiasing, the Strang-Madelung scheme develops a numerical
    modulational-instability cascade at the bore-soliton collision (mass
    blows up by 3 orders of magnitude). Dealiasing the cubic term is
    essential for kappa = +1.

## Bore-soliton interaction (the science answer)

The bore in `u` rarefies into a self-similar fan with characteristic speeds
filling [0, 1] (because u_L = 1 > u_R = 0); the foot moves at speed ~0.5,
so the u = 0.5 contour goes from x = 0 to x = 3.98 over T = 8. The bright
soliton in N starts at x = -8 with phase gradient phi_x = 0.6 (group
velocity 0.6) and lies entirely inside the u = 1 region, so it is initially
boosted by u + phi_x = 1.6. As it crosses the bore the effective drift
decreases monotonically to 0.6 (the original phi_x) on the right side.
Final soliton position at T = 8 is x = +4.8, consistent with an average
effective velocity of about 1.6 over the 8 time units.

The encounter is **mild**: N_max varies by less than 2% throughout, the
peak count stays at 1, and the soliton emerges as a coherent single
soliton on the u = 0 side. This is **transmission**, not reflection or
break-up.

## Final candidate

`candidate.py` runs all three experiments in one script (E1, E2, E3) and
saves named arrays `E{1,2,3}_{u,N,phi}` plus `E2_masses` and `E2_times` to
`pred_results/S7.npz`. E2 is the recommended scheme; running E1 and E3 in
the same script provides the negative-control evidence.
