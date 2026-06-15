# T_B / PosNeg — Gaussian wave packet to soliton train decomposition

## Final method

**E2** — the final solver in `candidate.py` is:

- **Spatial discretization**: Fourier pseudospectral on `x in [-15, 15]`, `Nx = 256`, periodic; spectral derivatives via FFT.
- **Dealiasing**: 2/3-rule cutoff (zero modes with `|k_index| > Nx/3 = 85`) applied to every state before forming nonlinear products, and to every nonlinear product (`u^2, v^2, u*v`).
- **u-side dissipation**: explicit linear viscosity `nu * u_xx` with `nu = 5e-2`, computed spectrally (`ifft(-k^2 * u_hat)`), added inside the u-equation RHS.
- **Time stepping**: classical explicit RK4 over the full RHS (v_xxx treated explicitly), `dt = 1e-4`, total `n_steps = 60_000`.
- **IC**: reference IC `v0(x) = 4 * exp(-(x+5)^2 / 2.25)`, `u0(x) = 0` (no adaptation).
- **Output**: `(13, 2, 256)` snapshots at `t = 0, 0.5, ..., 6.0`, channels `(u, v)`.

Equations as implemented (divergence form to keep mass conservation exact):

    u_t = -(3/2) d/dx(u^2) - 3 d/dx(v^2) - v_xxx + nu * u_xx
    v_t = -3 d/dx(v^2) - v_xxx - d/dx(u v)

## Iteration trace

- **E1** (baseline): Fourier pseudospectral + 2/3-rule dealiasing + classical RK4, `dt = 1e-4`, no viscosity. **F1**: reached T=6 with mass conservation to machine precision and no NaN. Intermediate snapshots `t in [0.5, 3.5]` show a clean 2-3 peak soliton-like decomposition (max_v in 1.8-2.6), but after `t ≈ 4` the u-field runs away to range `[-12.1, +8.9]` and v develops strong negative excursions to -3.2 with isolated grid-scale spikes (v_max = 5.798 surrounded by neighbors of -3.2 and -0.4). The spectral edge fraction in the top quarter band grows from 0 to 5e-5 — a clear u-side cascade contaminating v via the `-d_x(uv)` coupling. The literal phenomenon eval would technically pass on raw peak count, but the late-time field is numerically dirty.

- **E2** (single-component upgrade per progressive-complexity discipline): same stack + explicit linear viscosity `nu = 5e-2` on the u-equation only. **F2**: reached T=6 cleanly with mass(v) drift 9e-6 percent (mass_u also conserved — viscous term is in divergence form). The u-field stays bounded `|u| ≤ 8.1` in the transient phase and decays to `|u| ≤ 1.55` by T=6; v stays smooth and well-resolved (`v_min = -0.54`, `v_max = 1.79`); the spectral edge fraction in the top quarter band is 8e-8 (600x cleaner than E1). The final v shows **5 well-separated peaks** at `x ≈ -12.9, -4.7, 4.5, 8.2, 11.4` with amplitudes `[0.96, 1.79, 0.81, 0.88, 0.84]` — all above the 0.8 threshold and spatially separated by ≥ 3 length units. Hallmark KdV-type Gaussian-to-soliton-train decomposition. `useful_self_assessment = True`; stop early.

- E3 not run (early stop after F2 met the phenomenon target with clean diagnostics).

## Use of memory

**Positive entries cited (drove decisions):**

- `BKdV-S1 (positive, depth=3)` — validated the exact stack (Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 at `Nx=256`) for the coupled BKdV system at `amp` up to 3 with `dt=2e-4` reaching T=10 cleanly. This anchored E1 as the simplest meaningful baseline. We conservatively halved dt to 1e-4 because our Gaussian amplitude is 4 (above the bank-validated envelope).
- `BKdV-S6 (negative, depth=3, recommended_alternative)` — provided the precise upgrade for E2: linear viscosity `nu = 5e-2` is the bank-validated default for BKdV runs with bore-like u-gradient ICs at exactly our (Nx=256, dt=1e-4, RK4) configuration; passes the practical bound `u_max ≤ 1.62, TV(u) ≤ 27` in the bank. This is a *negative*-entry recommendation about which positive direction to escalate toward, since the entry's *failure* was: bare stack without u-side dissipation suffers TV inflation. Our F1 reproduced exactly this failure mode, confirming the negative entry's diagnosis applies to our IC.
- `kb-kdv-spectral-solitonAmplitude-conservation` — confirmed spectral methods are preferred for tracking soliton amplitudes in this kind of decomposition.
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` — additional motivation that dealiasing is essential for any nonlinear PDE with quadratic/cubic nonlinearity.

**Negative entries used to rule out tempting upgrades:**

- `kb-burgers-fwdEuler-centralFD-Gibbs` and `kb-general-centralFD-hyperbolic-shockFormation` — rejected: any naive central-FD-on-advective scheme. We use spectral throughout.
- `kb-kdv-noDealiasing-aliasing-artifacts` — rejected the temptation to skip dealiasing; 2/3 rule is on.
- `kb-kdv-IFRK4-blowup` — rejected the integrating-factor RK4 alternative; plain RK4 + 2/3 dealiasing is safer.
- `kb-kdv-explicit-RK4-stiffness-blowup` & `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup` & `kb-gardner-cubicTerm-tightens-nonlinearCFL` — these warn the nonlinear CFL tightens with amplitude, so we halved dt from BKdV-S1's `2e-4` to `1e-4` since amp=4 > 3.
- `BKdV-S4` synthesis (k^16 hyperviscosity at `nu_h ~ 1e-22`) — rejected as escalation route for E2: BKdV-S6 synthesis explicitly states this is 13 orders of magnitude too weak for bore-like u gradients. We chose linear viscosity instead.
- `BKdV-S6 (negative, eps=1e-4)` — rejected: `eps = 1e-4` is insufficient (<7% u_max reduction); we used `nu = 5e-2`, the bank-validated stronger floor.
- `kb-gardner-sech2IC-not-exact-soliton` and `BKdV-S5/S7 (negative depth=3)` — flagged that the m=0 (Gardner) submanifold is *not* dynamically invariant of full BKdV, so any "transfer Gardner soliton ansatz directly" approach is unreliable. We did NOT adapt the IC (we kept the reference Gaussian); the eval is on the dynamics induced by the BKdV system on the prompt's Gaussian.
- `kb-general-finiteness-not-accuracy` and `kb-general-massConservation-insufficient-diagnostic` — directly motivated the F1 decision NOT to claim victory on E1 despite all_finite=True and mass conserved: peak count and peak quality (no grid-scale spikes, no large negative dips) are required cross-checks.

**IC choice**: reference Gaussian, NOT adapted. The task spec explicitly invites IC adaptation if a bank-validated profile transfers, but `BKdV-S5/S7` (negative depth=3) showed that sech^2 ICs at amp >= 1 do not produce coherent traveling waves on the full coupled BKdV system (m=0 is a kinematic identity, not an invariant), and the prompt's phenomenon eval is on `final v` regardless of IC. The Gaussian decomposition into a soliton train is the actual scientific question; adapting the IC would change the question, not improve the answer. We keep the reference IC.

## Final self-assessment

We believe `pred_results/T_B.npy` satisfies the phenomenon target.

**Numerical diagnostics for the final snapshot (T=6.0):**
- `mass(v)` drift: 9e-6 percent (target < 8 percent) — pass with 6 orders of safety margin.
- `n_peaks(v) >= 0.8` with prominence >= 0.3 and pairwise separation >= 8 cells (~0.94 length units): **5** (target >= 2) — pass.
- Peak heights: 0.96, 1.79, 0.81, 0.88, 0.84 — all >= 0.8 with the leading soliton at amplitude 1.79.
- Peak locations: `x = -12.9, -4.7, 4.5, 8.2, 11.4` — well-separated (minimum gap 3.2 units, max 9 units).
- No NaN/Inf anywhere; no grid-scale ripples (smooth multi-cell-wide peaks); spectral edge `|k_idx| > Nx/3` at machine zero; edge in top quarter band 8e-8.
- The intermediate-time history shows the expected KdV-style Gaussian-to-soliton-train evolution: amplitude drops from 4.0 to ~2.6 by T=0.5 as the dispersive shedding kicks in, then a multi-peak structure stabilizes through T=2-3 and the train continues separating through T=6.

Cross-check: the soliton-train decomposition is consistent with `BKdV-S1`'s observation that the Fourier+2/3+RK4 stack reaches the long-time dispersive regime cleanly at our amplitude scale once u-side dissipation handles the otherwise-unbounded Burgers cascade flagged by `BKdV-S6`.
