# Reference Solvers

Numerical reference solutions for the three component PDEs in Stage 1.

Each `*_ref.py` script writes its output to `ref_results/<name>_REF.npy` (and `_REF_x.npy` for the grid).

## Files

| Script | PDE | Method | Output |
|---|---|---|---|
| `burgers_shock_ref.py` | `u_t + u u_x = 0` on [-1,1] periodic, Nx=200 | Lax-Friedrichs on Nx=4000 → downsample 20× | `ref_results/burgers_T05_REF.npy` |
| `kdv_soliton_ref.py` | `v_t + 6vv_x + v_xxx = 0` on [-15,15], Nx=256 | Fourier spectral + IMEX-CN | `ref_results/kdv_T2_REF.npy` |
| `shallow_water_ref.py` | `h_t + (hu)_x = 0;  (hu)_t + (hu² + gh²/2)_x = 0` on [-1,1], Nx=200 | HLL Riemann + explicit Euler | `ref_results/sw_T04_REF.npy` |

These references were used **only for** the Burgers and KdV stress tests (A1-A6 in Stage 1) — to verify the diagnostic eval scripts. The reference solver was **not** disclosed to the stress-test sub-agents. Stage 2 has no reference solver (no closed-form for the coupled BKdV system).
