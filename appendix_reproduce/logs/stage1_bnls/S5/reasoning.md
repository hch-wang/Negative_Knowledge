# S5 reasoning: Mcs preservation in B-NLS time-splittings

## Question

Does Strang-splitting B-NLS (Madelung-Psi NLS sector + RK4/upwind on u)
preserve the manifold `Mcs := {m = u - N*phi_x = 0}`? Does `||m(t)||_2`
grow numerically?

## Methods tried (3 experiments, 7 method/parameter combinations)

1. **Method A — on-manifold Madelung-Psi (Strang)**: complex state `Psi = sqrt(N) e^{i phi}`, Strang-split [boost(dt/2) - kinetic(dt/2) - nonlinear(dt) - kinetic(dt/2) - boost(dt/2)] with `u := Im(conj(Psi) Psi_x)` always reconstructed from Psi. Tested at dt ∈ {0.005, 0.001, 0.0005}.
2. **Method A-Lie**: same operators in Lie order [boost(dt); kinetic(dt); nonlinear(dt)], dt=0.001.
3. **Method B — decoupled Strang**: u evolves as standalone inviscid Burgers (upwind/Engquist-Osher flux, 4 sub-steps per dt for CFL), (N, phi) evolves as standalone Madelung-Psi NLS with **no boost coupling**. Half-u-step + full-NLS + half-u-step.
4. **Method C — decoupled Lie**: same operators in Lie order.
5. **Method D — fully coupled RK4** on `(u, N, phi)` directly, no operator split, with quantum-potential regularization `eps=1e-8` in the `1/sqrt(N)` factor.

## What works

**Method A**, in any splitting order, preserves Mcs to machine precision (||m||_2 ~ 1e-13) for the entire T=6 trajectory. This is **structural**, not a property of the time integrator: because `u` is reconstructed from `Psi` via `u = Im(conj(Psi) Psi_x)`, the residual `m = u - N phi_x = Im(conj Psi Psi_x) - N * Im(conj Psi Psi_x)/N` is **identically zero** by algebra. The time integrator only has to advance Psi accurately on Mcs; it never needs to enforce Mcs.

At dt = 0.001 the Strang split conserves mass to 1e-12 and energy to 8e-2 (≈0.5% relative) over T=6, with the bright soliton peak drifting 3.16 units. This matches the prediction `peak_velocity ≈ u_peak = N_peak * phi_x = 2 * 0.25 = 0.5`, giving `0.5 * 6 = 3.0` plus a small self-propagation contribution — **consistent with the compound-soliton hypothesis**.

Lie ordering ([boost(dt) - kinetic(dt) - nonlinear(dt)]) is numerically indistinguishable from Strang for this on-Mcs IC: the boost sub-flow approximately commutes with kinetic+nonlinear when u is a passive label of Psi.

## What fails, and how

**Decoupled splittings (B and C)** evolve `u` independently of `Psi` and never reconcile them. Even with a shock-stable upwind scheme for the u-Burgers half-step, `||m||_2` grows **linearly** from ~1e-8 (initial rounding) to 0.21 over T=6:

| t/T   | ||m||_2 (Method B/C) |
|-------|----------------------|
| 0.0   | 8.4e-8               |
| 0.25  | 8.6e-2               |
| 0.5   | 1.4e-1               |
| 0.75  | 1.7e-1               |
| 1.0   | 2.1e-1               |

The soliton peak in B/C drifts only 1.5 units (≈ `phi_x_initial * T = 0.25 * 6`), losing the larger `N*phi_x` boost — the decoupled NLS sub-step doesn't see u, and the standalone u-Burgers doesn't see N, so neither carries the compound transport.

**Fully coupled RK4 (Method D)** diverges within 3 steps. The quantum potential `Q = sqrt(N)_xx / (2 sqrt(N))` is stiff in the soliton tail where N falls below 1e-20; the `1/sqrt(N)` factor cannot be tamed by a regularization of `eps=1e-8` in an explicit RK4. Operator splitting is **necessary**: the kinetic step on Psi `i Psi_t = -(1/2) Psi_xx` absorbs the QP exactly (because `Q` is the Madelung form of `-Psi_xx/(2 Psi)`).

## dt frontier inside Method A

| dt      | ||m||_2 max | mass drift | energy drift | peak drift |
|---------|-------------|-----------|--------------|-----------|
| 0.0005  | 9.0e-14     | 3.1e-12    | 8.2e-2       | 3.16      |
| 0.001   | 8.7e-14     | 1.4e-12    | 8.2e-2       | 3.16      |
| 0.005   | 1.7e-14     | 5.9e-3     | 1.2e2        | -6.9 (!)  |

`dt = 0.005` is unstable on the dynamics side (kinetic propagator `exp(-i k^2 dt/2)` aliases at large `k`; mass and energy both deteriorate; the soliton peak wraps backwards through the periodic image). Crucially, **||m||_2 still stays at 1e-14** even when the dynamics is wrong — confirming that Mcs preservation alone is **not a sufficient certificate** of a correct B-NLS solution.

## Recommended canonical method

```
Method A: Madelung-Psi on Mcs.
  - state:  Psi = sqrt(N) exp(i phi)
  - reconstruct u := Im(conj(Psi) Psi_x) on demand
  - Strang split per step (dt = 0.001 nominal):
       Psi <- step_boost(Psi, dt/2)        # RK4 of  Psi_t = -(1/2)((u Psi)_x + u Psi_x)
       Psi <- exp(-i k^2 dt/2) Psi          # exact kinetic in Fourier space
       Psi <- exp(i kappa |Psi|^2 dt) Psi  # exact pointwise nonlinear
       Psi <- exp(-i k^2 dt/2) Psi
       Psi <- step_boost(Psi, dt/2)
```

This is what `candidate.py` runs as Method A. The natural method coupling
between the Burgers and NLS sub-systems on Mcs is **the Madelung-Psi
representation itself** — you do not need a separate Burgers solver; u is a
derived quantity of Psi.

## Take-away (one sentence)

To integrate B-NLS on Mcs, work in the Madelung-Psi representation and
reconstruct u from Psi each step — Mcs is then preserved structurally
(||m||_2 ~ 1e-13), and any reasonable Strang/Lie split at dt ≤ 0.001
gives correct dynamics with mass conserved to 1e-12.
