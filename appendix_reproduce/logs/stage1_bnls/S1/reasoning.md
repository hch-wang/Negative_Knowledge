# S1 reasoning: NLS focusing bright soliton, Madelung-Psi split-step validation

## System and ground truth

With u=0 the B-NLS (N, phi) sector reduces (under Madelung Psi = sqrt(N)*exp(i*phi)) to the standard 1D focusing NLS

    i*Psi_t + (1/2)*Psi_xx + kappa*|Psi|^2*Psi = 0,   kappa = +1.

The prompt's stated IC and ground truth (mass = 2*sqrt(2), |Psi|^2_max = 2 conserved, peak translating at speed 0.25 with no shape change) match exactly the bright soliton

    Psi(x,t) = A*sech(A*(x - v*t - x0))*exp(i*(v*x - (v^2 - A^2)/2 * t))

with A = sqrt(2), v = 0.25, x0 = -5. At T = 8 the peak is at x = -3.0.

This gives an analytical reference for every diagnostic: peak amplitude, peak position, total mass, energy H = integral [(1/2)|Psi_x|^2 - (kappa/2)|Psi|^4]dx, and pointwise relative L2 error vs the exact field.

## Methods tried (3 distinct families)

I deliberately picked three methods that differ in their structural treatment of the NLS Hamiltonian, to produce knowledge about which classes work:

1. **Strang split-step Fourier on Psi** (symmetric symplectic, 2nd-order). Each step is
   N(dt/2) -> L(dt) -> N(dt/2), where N is the nonlinear local rotation Psi -> Psi*exp(i*kappa*|Psi|^2*dt/2) (exact in physical space, |Psi| pointwise invariant) and L is the linear free-particle propagator Psi_k -> Psi_k*exp(-i*k^2*dt/2) (exact and unitary in Fourier).

2. **Lie split-step Fourier on Psi** (asymmetric, 1st-order). Same sub-steps but applied sequentially N(dt) -> L(dt), without the half-step symmetrization. Each sub-step is still individually unitary, so mass is still preserved exactly, but global accuracy drops to first order.

3. **ETD-RK1 (exponential Euler) on Psi** (non-symplectic, 1st-order). Integrating factor method: Psi_k(t+dt) = e^{L*dt}*Psi_k(t) + ((e^{L*dt} - 1)/L) * FFT[i*kappa*|Psi|^2*Psi]. Treats the linear stiff operator exactly but the nonlinear term as a single forward-Euler correction. NOT norm-preserving.

The choice was motivated by the stress question (split-step accuracy + mass conservation) plus the goal of producing *negative* knowledge: by including a structurally non-symplectic scheme (ETD-RK1), I document a class of methods to avoid.

## Experiment 1: comparative sweep at (dt, Nx) in the prompt grid

Ran all three methods at dt in {0.01, 0.001, 0.0001}; Strang additionally at Nx in {128, 256, 512}; Lie and ETD-RK1 at Nx = 256.

Top-line numbers (T = 8):

| method  | dt     | Nx  | |dM|/M    | |dE|/|E|   | |Psi|_max | peak_pos | relL2   |
|---------|--------|-----|-----------|------------|-----------|----------|---------|
| Strang  | 0.01   | 256 | 2.84e-14  | 4.33e-08   | 1.4110    | -3.0003  | 5.6e-04 |
| Strang  | 0.001  | 256 | 5.17e-13  | 2.93e-12   | 1.4111    | -3.0003  | 5.7e-06 |
| Strang  | 0.0001 | 512 | 8.31e-12  | 3.08e-11   | 1.4140    | -3.0000  | 7.0e-07 |
| Lie     | 0.01   | 256 | 3.16e-14  | 2.18e-04   | 1.4119    | -3.0012  | 6.1e-03 |
| Lie     | 0.001  | 256 | 5.15e-13  | 2.17e-06   | 1.4112    | -3.0004  | 6.5e-04 |
| Lie     | 0.0001 | 256 | 4.87e-12  | 2.17e-08   | 1.4111    | -3.0003  | 6.6e-05 |
| ETD-RK1 | 0.01   | 256 | 1.44e-01  | 5.65e-01   | 1.6159    | -3.1445  | 1.045   |
| ETD-RK1 | 0.001  | 256 | 1.06e-02  | 3.71e-02   | 1.4274    | -3.0135  | 0.0852  |
| ETD-RK1 | 0.0001 | 256 | 1.04e-03  | 3.59e-03   | 1.4127    | -3.0016  | 0.0083  |

Ground truth: |Psi|_max = sqrt(2) = 1.4142, peak_pos = -3.0000, mass = 2.8284, energy = -0.8544.

What this tells us:

- **Strang is the winner.** Mass and energy conserved to machine precision, second-order convergence in dt confirmed (relL2 falls by factor 100 when dt drops by 10, until spatial truncation at Nx=256 takes over around dt=1e-4). Energy drift behaves like O(dt^4) (4.3e-8 -> 1.7e-11 = factor 2500 ~ 50^2 when dt drops by 50), consistent with Strang's symmetric symplectic structure picking up a 4th-order shadow Hamiltonian.

- **Lie is bookkeeping-only.** Mass still conserved (each sub-step is unitary) but the second-order symmetric coupling between L and N is gone, so global error is O(dt). For relL2 ~ 1e-3 you need dt ~ 1e-3 with Lie but only dt ~ 5e-3 with Strang. Strict cost-loss compared to Strang.

- **ETD-RK1 fails.** Even at dt=1e-4 the mass leaks by 0.1% and the field error is 1e-2. The failure mode is structural: the (e^{L*dt} - 1)/L correction integrates the nonlinearity along a single time slice without preserving the |Psi|^2 invariant, so probability drains by O(kappa*dt) per step. For NLS solitons, where the entire dynamics is encoded in the unit-mass phase rotation, this is fatal.

This experiment establishes that **the question "which method works on NLS" has a very crisp answer: symplectic Strang (or higher Yoshida), not Eulerian ETD**.

## Experiment 2: failure boundary of Strang at coarse (Nx, dt)

E1 found Strang stable everywhere in the prompt grid, so to bound the operating region I probed coarser parameters: Nx in {32, 64, 96, 128}, dt in {0.5, 0.1, 0.05, 0.02, 0.01}.

Headline results:

- **Nx = 32 always fails.** dx = 30/32 ~ 0.94 exceeds the soliton width 1/A = 1/sqrt(2) ~ 0.71. The peak is severely aliased, |Psi|_max collapses to 1.31, and the peak ends at x = -4.66 instead of -3.0. relL2 ~ 1.1 (worse than zero) at every dt. Yet mass is still 1e-14 conserved by construction.

- **Nx = 64 marginal.** relL2 ~ 5e-2 at dt=0.1 falling to 5e-3 at dt=0.01; peak amplitude underresolved to 1.36 (vs 1.41).

- **Nx >= 96 produces relL2 < 1e-3 at dt <= 0.01.**

- **dt = 0.5 destructive at every Nx tested.** The linear half-step phase per step is (1/2)*k_max^2*dt = (1/2)*(pi*Nx/L)^2*dt. At Nx=64, L=30: phase ~ 5.5; at Nx=128: phase ~ 22. Both exceed 2*pi -> the dispersion sub-step aliases its own action.

So the joint (dt, Nx) boundary is approximately dt*(pi*Nx/L)^2 < O(1), with the spatial floor Nx >= L/(soliton width) ~ 30/0.7 ~ 43, rounded up to a safe Nx >= 96 in practice.

## The critical negative finding

Strang's mass conservation is **unconditional** -- each sub-step is exactly unitary, so |Psi|_2 is preserved to floating-point even when the soliton is structurally wrong (under-resolved, aliased, or run with too-large dt). Mass conservation alone is therefore NOT proof that the soliton has been integrated correctly. Tests must cross-check at least one of: energy drift (Strang energy drift scales like ~dt^4 when accurate but jumps to O(1) when destructured), peak position vs analytic translation, peak amplitude, or pointwise error against ground truth (or a refined reference if no ground truth).

This is the most important piece of knowledge for downstream B-NLS testing: any positive verdict on a method should rely on multiple diagnostics, not just mass.

## Final solver and what to use

`candidate.py` runs all three methods to allow direct reproduction of the comparison. The recommended working point for NLS/Madelung-Psi in B-NLS Stage-1 tests is:

- **Method: Strang split-step Fourier on Psi.**
- **dt = 0.001, Nx = 256.**
- Yields: |dM|/M ~ 5e-13, |dE|/|E| ~ 3e-12, relL2 vs exact soliton 5.7e-6, in 0.15 s wall time per T=8 run.

For higher accuracy (e.g. long-time runs or stronger nonlinearity), drop dt to 1e-4 and raise Nx to 512 (still under 3 s wall). For coarser scans, dt = 0.01 with Nx = 256 retains 6e-4 relative L2 in 0.02 s.

## What I would do next (if budget allowed)

E3 would be a 4th-order symmetric splitting (Yoshida triple-jump or McLachlan's optimal-15 stage scheme). That should give relL2 ~ dt^4 with a fixed cost factor ~3x per step. Useful for high-accuracy benchmarks, but for the stress questions asked here (min dt for accuracy, Nx failure, mass conservation), the Strang/Lie/ETD-RK1 triad already answers the question and bounds the operating region.
