# T_A — Soliton stability in coupled Burgers-swept-KdV (PosOnly)

## Final method

**Experiment E2** is the final answer. `candidate.py` implements it; `pred_results/T_A.npy` is its output.

- **Spatial**: Fourier pseudospectral on Nx=256 grid over periodic [-15, 15].
- **Dealiasing**: 2/3-rule mask applied to fields and to all quadratic nonlinear products (u^2, v^2, uv) before differentiation. Conservative form is used: `u u_x = (1/2)(u^2)_x`, `v v_x = (1/2)(v^2)_x`, `∂_x(uv)` via dealiased uv. The state itself is also dealiased once per RK4 step to suppress slow accumulation at the retained-mode boundary.
- **Time**: explicit RK4 applied uniformly to (u, v). `dt = 1.0e-4` (Nt = 80,000 steps for T=8.0). Choice: RK4 linear stability for the dispersive symbol ik^3 requires `dt * k_max^3 < 2.83`; with k_max = pi/dx = 26.81 → k_max^3 = 19,287 → dt_max ≈ 1.47e-4. We pick 1e-4 for margin.
- **Coupling**: PDE coded directly as
  - `u_t = -3·(1/2)(u^2)_x − 3·(v^2)_x − v_xxx`
  - `v_t = −3·(v^2)_x − v_xxx − (uv)_x`
  - All quadratic products dealiased; linear derivatives via spectral ik / ik^3.

## Iteration trace

- **E1** (baseline, mandatory): Fourier pseudospectral + RK4 + **no** dealiasing, dt=1e-4. **F1: blew up at t≈1.5 to NaN.** Mass(v)=4.0 conserved up to t=1.0 then |v|_inf cratered as energy aliased into high modes; classic pseudospectral aliasing instability in the quadratic nonlinearities. Decision D1 = add 2/3-rule dealiasing as the **single** component that addresses the diagnosed failure mode.
- **E2** (single-component upgrade: + 2/3 dealiasing): same RK4 + dt=1e-4 + dealias mask. **F2: stable to T=8.0; mass(v)=4.0 conserved to 13 decimals; |u|,|v| < 2 throughout (target ceiling 15).** Final peak max(v)=0.9165 at T=8 — just below the 1.0 threshold; the v-field shows 11 local maxima above 0.3, i.e. multi-modal dispersive radiation rather than a single soliton. Peak amplitude oscillates 0.86–1.21 throughout [1, 8]. Decision D2 = try one-component change of the time integrator (RK4 → IMEX-CN) to see if more accurate dispersive evolution shifts the final-snapshot landing above 1.0.
- **E3** (intended single-component upgrade: + IMEX-CN(disp) + Heun(nonlinear)): incorrectly raised dt 5x to 5e-4 at the same time. **F3: blew up at t≈5.5.** Diagnosis: v_xxx appears as explicit forcing in the u-equation (u has no stiff linear part), so its explicit-RK2 treatment in IMEX-Heun still requires dt·k_max^3 < 2.83; with dt=5e-4 we have 9.6, far outside. Decision D3 = roll back to E2 as the final candidate; the IMEX-CN advantage would have required either dt=1e-4 (no cost saving over E2) or a coupled-IMEX treating v_xxx implicitly in both equations (would have been more than one component change anyway).

## Use of memory (positive bank)

**Cited (used)**:
- `kb-kdv-IMEX-CN-spectral-pass` — informed the *recognition* that Fourier pseudospectral is appropriate for the v_xxx dispersion (used for E1 baseline confirmation) and pointed to IMEX-CN as the natural E3 escalation; however, per progressive-complexity discipline this entry was NOT used as a shortcut to skip the baseline.
- `kb-kdv-spectral-solitonAmplitude-conservation` — same: confirmed that spectral IMEX conserves amplitude/mass, motivating E3.
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` — explicitly endorses 2/3 dealiasing for the Gardner-class cubic nonlinearity; applies here because our quadratic pseudospectral nonlinearities (3v^2, vv_x, uv) require the same alias suppression. This entry drove **E2**'s single-component upgrade (dealiasing). Also predicted the radiation-into-non-soliton outcome we observed: "the KdV-style sech^2 IC is NOT a true Gardner soliton — the wave radiates and amplitude decays".
- `kb-gardner-KdV-method-transfer-moderate-amplitude` — confirmed IMEX-CN + 2/3 dealiasing transfers cleanly at amplitudes in [1, 2], which is exactly our case. Used as supporting evidence for the E3 attempt.

**Rejected**:
- `kb-burgers-MUSCL-Godunov-shock-pass` and `kb-burgers-Godunov-preShock-smooth` — rejected for E2/E3 because switching the Burgers component to finite-volume Godunov while keeping spectral on the dispersive component would require operator-splitting, i.e. >=2 simultaneous changes. Furthermore, F1 diagnostics showed the failure mode was aliasing, not Burgers shock formation (the u-equation had `|u|_inf ≈ 1.1` at the time of E1 blow-up, no actual bore yet). MUSCL is therefore not the right escalation direction.
- `kb-shallowWater-LaxFriedrichs-stable-smeared`, `kb-shallowWater-HLL-dam-break-pass` — rejected: this PDE is not the shallow-water system and the dispersive v_xxx + uv coupling is not Riemann-solver-amenable.
- `kb-general-firstOrder-Godunov-preShock-baseline` — same rationale as MUSCL rejection.
- `kb-kdv-smallAmplitude-dispersiveRegime` — used as *diagnostic context*: it warns that amplitude < O(0.1) gives dispersive radiation rather than soliton. Our final v_inf is 0.92, which is at the boundary between soliton and radiation regimes; this entry helps interpret why the system sits near threshold.

## Final self-assessment

**Phenomenon target check (parent will run a deterministic check on `pred_results/T_A.npy`):**

| sub-criterion | required | observed (E2 final, t=8) | pass? |
|---|---|---|---|
| max(v) at T_final | >= 1.0 (=0.5 × 2.0) | 0.9165 | **fail (close)** |
| mass(v) drift | < 8% | 3e-11 % | pass |
| `|u|_inf` at T | < 15 | 0.864 | pass |
| `|v|_inf` at T | < 15 | 0.917 | pass |
| single dominant peak | required | 11 peaks above 0.3, multi-modal | likely fail |

**Self-assessment: USEFUL = FALSE.**

The simulation is numerically clean (mass conserved to machine precision, stable to T=8.0, boundedness perfect), so the result faithfully describes the dynamics under this perturbed initial condition. The phenomenon-target shortfall is a **physics outcome of the IC choice**, not a numerical error: the perturbation `u = v^2/2 + 0.2 v` (i.e. `m = 0.2 v ≠ 0`) drives the coupled system off the m=0 Gardner manifold, and the KdV-shaped sech^2 IC at amplitude 2.0 is not a true Gardner soliton even on the manifold (kb-gardner-G2 warns of this), so the v-field sheds amplitude as bidirectional dispersive radiation. The peak amplitude oscillates 0.86–1.21 during [1, 8] but lands at 0.917 at T=8.

A method-side fix is not available within iteration budget. The only escalations that might have nudged the final-snapshot peak above 1.0 — finer time resolution, IMEX-CN with dt=1e-4 (no cost win), or hyperviscosity to suppress remaining noise — are either explicitly forbidden by the discipline at this stage or would not change the underlying physics. The answer to the research question Q1 is **"the soliton structure does not survive: the system enters a multi-modal dispersive-radiation regime"**, supported by clean numerics.
