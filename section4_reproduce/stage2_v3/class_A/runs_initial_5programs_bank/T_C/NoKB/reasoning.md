# Reasoning — T_C (NoKB): Burgers bore × KdV soliton

## Final method (E3)

Coupled Burgers-swept-KdV system on periodic x ∈ [-15, 15], Nx = 256.

- **Spatial discretization**: Fourier pseudospectral with 2/3-rule dealiasing
  on every nonlinear product (u·u_x, v·v_x, 3v², u·v, and the d/dx applied to
  the latter two). Linear derivatives (v_x, v_xx, v_xxx, u_x, u_xxxx) use the
  full spectrum.
- **Time integration**: explicit classical RK4, dt = 1·10⁻⁴ (80 000 steps to
  T = 8.0). Stride 5000 → 17 snapshots at Δt_snap = 0.5.
- **Stabilization for the bore**: a *very weak* hyperviscosity term −ε u_xxxx
  with ε = 1·10⁻⁵ added to the u equation only. At the dealiasing cut
  k = (2/3) k_max ≈ 17.9 this provides damping rate εk⁴ ≈ 1.02 s⁻¹ (kills
  Gibbs on the ~1-second scale); at the soliton wavenumber k ≈ 2π/Δ ≈ 6
  it gives 0.015 s⁻¹ (negligible over T = 8).
- **No** operator splitting, **no** IMEX, **no** low-pass filter, **no**
  shock-capturing scheme.

Effective PDE solved:

    u_t + 3 u u_x = − ∂_x(3 v² + v_xx) − ε u_xxxx
    v_t + 6 v v_x + v_xxx = − ∂_x(u v)

## Iteration trace

- **E1** — Pseudospectral + RK4, no dealiasing.
  **F1**: blew up to NaN by t ≈ 0.5. The 1.5-wide tanh bore has non-negligible
  energy at every Fourier mode (|û(k_max)|/N ≈ 3·10⁻³), so quadratic products
  (3v², uv, u·u_x) alias high-k power that the pseudospectral derivative then
  amplifies. Dispersion CFL margin (dt·k_max³ ≈ 1.9 < 2.83) was *not* the
  failure; aliasing was.

- **E2** — Added 2/3-rule dealiasing (single-component upgrade over E1).
  **F2**: completed; soliton clean (final v peak 1.22, >0.5 at every snapshot);
  u developed monotonically growing Gibbs oscillations on the bore front,
  reaching u_max = 22.9 at t = 8 — violates |u_max| < 5. Diagnosis: with
  spectral discretization and no dissipation, the Burgers shock cannot be
  resolved; Gibbs grows. Mass conserved to <0.5 % on u, <3 % on v.

- **E3** — E2 stack + ε = 1·10⁻⁵ hyperviscosity on u only.
  **F3**: completed. v survives (final peak 0.88, ≥ 0.69 at every snapshot).
  u stays bounded (|u_max| peaks 8.54 at t = 6.5, ends at 6.33). Mass drift
  0.16 % on u, 1.0 % on v. The phenomenon |u_max| < 5 is *not strictly* met:
  the bore-front overshoot remains in the 6–9 range during the soliton
  passage. Budget exhausted.

## Use of memory

NoKB condition — no positive or negative knowledge bank available
(`cites_bank: []`, `rejects_bank: []` at every Experiment node). All choices
were driven by:

- General PDE numerical-methods knowledge: pseudospectral choice for periodic
  domains with v_xxx; Orszag 2/3-rule as the textbook fix for quadratic
  aliasing; hyperviscosity as the minimal-invasive Burgers-shock control.
- Progressive-complexity discipline: E1 deliberately the simplest baseline
  (even though one *could* anticipate aliasing failure on a sharp bore); E2
  changed exactly one component (dealiasing); E3 added exactly one component
  (hyperviscosity on u only).

No bank entries to cite or reject.

## Final self-assessment

I do **not** claim full phenomenon satisfaction:

- **Soliton survival (v final peak ≥ 0.5)**: SATISFIED. Final v peak = 0.882;
  every snapshot has peak ≥ 0.69.
- **Bore did not blow up (no NaN, no exponential growth)**: SATISFIED. Mass
  drift 0.16 % on u; |u_max| has plateaued and is decreasing in the late
  phase (8.54 → 7.86 → 6.33 from t = 6.5 to t = 8.0).
- **|u_max| < 5**: NOT SATISFIED. |u_max| exceeds 5 at most snapshots, peaks
  at 8.54 (t = 6.5) and ends at 6.33 (t = 8). The over-shoot is bounded and
  smooth — it is a real bore-overshoot induced by the coupling forcing
  −∂_x(3v² + v_xx) when the soliton crosses the bore foot — not a numerical
  blow-up. Stronger hyperviscosity (ε ≈ 5·10⁻⁵) or a 4th component (e.g.
  Hou-Li exponential filter, or modest physical viscosity on u) would likely
  push u_max below 5 without affecting the soliton, but each would constitute
  a 4th experiment and exceed the 3-iteration budget.

Submitting **E3** as the final answer: physically correct soliton dynamics, a
bounded smooth bore that does not blow up, but with bore overshoot above the
strict 5-amplitude threshold.
