# BKdV-S7 Round 1 (E1) — Gardner-only baseline

## Question

Does the IC v(x,0) = 1.5 sech^2(x+5) propagate as a clean coherent single peak
under the Gardner equation v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0 over
T = 10 on x ∈ [-15, 15], Nx = 256? This establishes the **positive baseline**
against which BKdV (E2) will be compared.

## Method

Fourier pseudospectral spatial derivatives with 2/3 dealiasing on every
nonlinear product. Explicit RK4 in time with dt = 2e-4 (well within the
RK4 stability bound for the v_xxx dispersive term at Nx = 256: the 2/3-dealiased
k_eff_max ≈ 17.87 gives a stability dt < 4.95e-4). A final dealiasing pass
is applied after each RK4 step to suppress aliasing accumulation.

Diagnostics tracked at 21 evenly-spaced snapshots over [0, 10]:
- mass_v = integral v dx
- L2v = sqrt(integral v^2 dx)  (Gardner Casimir)
- Gardner Hamiltonian H = integral [ v_x^2/2 − v^3 − (3/8) v^4 ] dx
- v_max(t), v_max_x(t) (peak amplitude and location)
- single-peak count above 5% threshold
- finite, sup

## Result

| Diagnostic        | t=0          | t=T=10      | drift          |
|-------------------|--------------|-------------|----------------|
| mass_v            | +3.000000e+0 | +3.00000e+0 | +0.000000%     |
| L2v (Casimir)     | 1.732051     | 1.73205     | +0.000000%     |
| H (Hamiltonian)   | -4.135714    | -4.12794    | +0.188%        |
| v_max             | 1.4977       | 1.4957      | -0.137%        |
| n_peaks           | 1            | 1           | constant       |

- v_max range over the full window: [1.4957, 1.5067]; amplitude oscillates
  ±0.5% but never decays.
- Single coherent peak maintained for the entire integration; n_peaks = 1
  at every snapshot.
- Phase speed from linear fit of peak position (with periodic unwrap): c ≈ 3.56.
  The peak wraps the domain twice (L = 30, c·T = 35.6).
- Solution propagates to the right cleanly; no shedding visible in snapshots.

## Interpretation

The chosen IC (A = 1.5 sech^2) is a clean propagating wave for the cubic-Gardner
equation. While it is not an *exact* Gardner soliton (the exact Gardner soliton
involves a sech^2 ratio for the cubic case, not a pure sech^2 ansatz), the
profile is sufficiently close to a coherent traveling shape that radiative
shedding is below the percent-level over T = 10. This is consistent with
sech^2 being an exact KdV soliton and the cubic term (3/2) v^2 v_x being a
mild perturbation at A = 1.5 (cubic/quadratic ratio in flux ~ A/4 = 0.375 at
peak).

This establishes the **positive baseline**: Gardner with this IC is numerically
stable and coherent. Any breakdown observed in E2 (BKdV) under the *same* IC
plus u_0 = v_0^2/2 cannot be blamed on Gardner-side instability or on the
numerics — it must come from the coupling.

## Decision

Proceed to E2: rerun the same IC under full BKdV with u_0 = v_0^2/2
(so m_0 = 0 to machine precision) using the *identical* spectral / dealias /
RK4 stack. Track ‖m‖_L2(t), v_max(t), u_max(t), and the L2 distance
‖v_BKdV(t) − v_Gardner(t)‖_L2 over [0, 10].
