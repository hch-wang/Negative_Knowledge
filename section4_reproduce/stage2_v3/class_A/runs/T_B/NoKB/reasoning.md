# T_B (NoKB) — Reasoning

## Final method

**Experiment E3** is the final answer.

Method:
- **Spatial discretization**: Fourier pseudospectral on x ∈ [-15, 15], Nx = 256 (periodic). All derivatives (∂_x, ∂_xx, ∂_xxx) evaluated in spectral space via FFT.
- **Anti-aliasing**: 2/3-rule applied to every nonlinear product. For each quadratic Q(a, b) the inputs are filtered by zeroing modes |k| > (2/3) k_max, multiplied pointwise, and the result re-filtered.
- **Dissipation regulator**: high-order spectral hyperviscosity -ε k^8 applied to both u and v. Strength ε = 10 / k_c^8 ≈ 9.6 × 10⁻¹⁰ where k_c = (2/3) k_max, chosen so that the dissipative timescale at the dealiasing cutoff is ~0.1 s. At the soliton spatial scale (σ ≈ 1.5, k ≈ 4) the hyperviscous rate is negligible (~10 × (4/k_c)^8 ≪ 1).
- **Time integration**: explicit RK4 with dt = 5 × 10⁻⁵. dt is well below the v_xxx stability bound (2.83 / k_max^3 ≈ 1.5 × 10⁻⁴) and the hyperviscous bound (2.78 / |ε k_max^8| ≈ 1.1 × 10⁻²).
- **IC**: as specified — v(x, 0) = 4 exp(-(x+5)²/2.25), u(x, 0) = 0. Not adapted (no positive knowledge bank available to motivate adaptation).
- **Output**: 13 snapshots saved uniformly on t ∈ [0, 6], shape (13, 2, 256).

The PDE actually integrated reads (mass-conservative form maintained):
```
u_t = -3 ded(u, u_x) - ∂_x[3 ded(v, v) + ∂_xx v]      - ε k^8 û
v_t = -6 ded(v, v_x) - ∂_xxx v - ∂_x[ded(u, v)]       - ε k^8 v̂
```
where ded(a, b) denotes 2/3-dealiased product.

## Iteration trace

- **E1 (Fourier + RK4, no dealiasing)** — F1: blow-up at t = 0.28, max|v| → 1.17 × 10³ with 125 spurious peaks monotonically growing toward the spectral grid edge. Textbook aliasing cascade fed by v_xxx amplification. Mass(v) drift 0%.
- **E2 (+ 2/3 dealiasing)** — F2: aliasing fixed; remained bounded until t ≈ 3.0 (max|v| ≈ 13.7, max|u| ≈ 92), then between t = 3.0 and t = 3.5 the u-channel ran away to |u| ≈ 1170, |v| ≈ 600. Diagnosis: u(x, 0) = 0 leaves the system **off** the Gardner reduction manifold m = u − v²/2 = 0; the inviscid Burgers term 3 u u_x in the u-equation steepens to a shock with no dissipation. Mass(v) drift still 0%.
- **E3 (+ k^8 hyperviscosity)** — F3: completed to T = 6.0; max|v| = 4.37, max|u| = 49.3; mass(v) drift 0.000%; 25 local peaks ≥ 0.8 in final v, organized into 6 well-separated clusters (pairwise gap > 1.5 spatial units, i.e. > one soliton width). Cluster-peak amplitudes ∈ [2.42, 4.37], comfortably above the 0.8 threshold.

## Use of memory

No knowledge bank (NoKB). `cites_bank: []` and `rejects_bank: []` for every Experiment node. The dispatcher instructions explicitly directed against IC adaptation absent a positive bank, so the reference Gaussian IC was kept verbatim.

## Final self-assessment

`pred_results/T_B.npy` satisfies the phenomenon target with margin.

Diagnostics on the final snapshot (t = 6.0):
- 6 well-separated peak clusters in v (pairwise gap > 1.5 ≈ one soliton width), all with cluster-peak amplitude ≥ 0.8 — the spec requires ≥ 2.
- Cluster-peak amplitudes: {2.72, 3.11, 4.37, 3.05, 2.42, 2.56}.
- mass(v) drift: 0.000% (spec ≤ 8%).
- max|v| evolves modestly between 2.1 and 4.4 over [0, 6] — no blow-up, no exponential growth.

Caveats:
- The IC u(x, 0) = 0 is **not** on the Gardner reduction manifold (m₀ = −v²/2 ≠ 0), so the late-time field is not the textbook clean Gardner soliton train; it is a multi-peaked dispersive-coupling structure with several distinct local maxima. The phenomenon spec ("≥ 2 well-separated peaks with amp ≥ 0.8") is satisfied, but a strict KdV-IST sorted-by-speed soliton train would require initializing on the manifold (u = v²/2) — which I deliberately did not do, per the NoKB instruction to stick to the reference IC.
- The k^8 hyperviscosity is a numerical regularizer, not a physical term in the PDE. Its strength is small (ε ≈ 10⁻⁹) and inertial-range scales (where solitons live) are essentially untouched, but it does modify the exact conservation of higher Casimirs of the system. The first conserved quantity — mass(v) = ∫ v dx — is unchanged because the hyperviscous operator is itself a derivative.
