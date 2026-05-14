# T_C / PosOnly — reasoning

## Final method (E2)

Hybrid finite-volume / pseudospectral scheme with explicit RK4 time integration:

- **u-sector (Burgers bore)**: The self-flux  `-3 u u_x  =  -(3/2) d_x(u^2)`  is discretized as a conservative finite-volume flux with **MUSCL-van-Leer** slope reconstruction and the **exact Godunov flux** for the convex Burgers flux `f(u) = (3/2) u^2` (sonic point at u=0). This is TVD and entropy-consistent, so it captures the bore without Gibbs oscillations.
- **u-coupling**: `-d_x(3 v^2 + v_xx)` evaluated with Fourier pseudospectral derivatives (these quantities are smooth in space; no shock-capturing required).
- **v-sector (swept KdV)**: `-6 v v_x - v_xxx - d_x(u v)` all evaluated with Fourier pseudospectral derivatives.
- **Time integration**: explicit classical RK4, `dt = 1e-4` (limited by spectral v_xxx dispersion stability: |dt · k_max^3| ≲ 2.78 with k_max = pi · 256 / 30 ≈ 26.8, so dt < 1.44e-4).
- No dealiasing, no IMEX, no filter, no hyperviscosity. The MUSCL+Godunov upgrade on the u-sector is the **only** change from the E1 baseline.
- Grid: Nx=256 cell-centered on x ∈ [-15,15], periodic. 21 snapshots saved (every 4000 steps).

## Iteration trace

- **E1 — pure spectral RK4 baseline** (cites_bank: []; rejects_bank: []): All derivatives Fourier spectral, no dealiasing, explicit RK4 at dt=1e-4. **F1**: blew up at t=0.40 (step 4032), |u|_max=17.4 >> 5. The Burgers bore steepened into a true shock, producing Gibbs ringing + nonlinear aliasing in the spectral approximation of 3 u u_x. v stayed bounded at blow-up time (v_max=0.81), so the failure localized cleanly to the u-sector. This is the diagnostic value of starting with the simplest baseline: I now know exactly which single component to upgrade.
- **E2 — single-component upgrade to MUSCL+Godunov on u self-flux** (cites_bank: kb-burgers-MUSCL-Godunov-shock-pass, kb-general-firstOrder-Godunov-preShock-baseline). Everything else unchanged from E1. **F2**: run completes the full T=8.0 in 80000 steps (~25s). |u|_max stays bounded in [2.4, 3.9] across all 21 snapshots, final 2.67. v_max final 0.63, with v_mass conserved exactly (3.000 → 3.000) and v_l2 decaying ~14% (1.732 → 1.492) consistent with dispersive radiation. The soliton appears partially refracted/scattered by the bore: amplitude drops from 1.5 to 0.63 and multiple competing peaks emerge in the late-time field. Phenomenon target met → `useful_self_assessment: true` → stop early.

## Use of memory

**Bank entries that drove decisions:**
- `kb-burgers-MUSCL-Godunov-shock-pass` — primary driver of the E2 method choice. The entry explicitly endorses MUSCL+Godunov for Burgers bore propagation in coupled Burgers-swept-KdV settings, which is exactly F1's localized failure mode. Note that per progressive-complexity discipline I did NOT use this entry to bypass E1; it informs the *escalation direction* from E1 to E2, not the choice of E1 itself.
- `kb-general-firstOrder-Godunov-preShock-baseline` — secondary support for the Godunov flux at the foundation of MUSCL.

**Bank entries considered but not adopted at this step:**
- `kb-kdv-IMEX-CN-spectral-pass` and `kb-kdv-spectral-solitonAmplitude-conservation` recommend IMEX-CN spectral for the KdV/swept-KdV component. I did not adopt IMEX-CN because F1 showed the v-sector did **not** fail at dt=1e-4 explicit RK4; switching the time integrator now would violate single-component discipline. If E2 had still failed in the v-sector, IMEX-CN would have been the natural E3 upgrade.
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` and `kb-gardner-KdV-method-transfer-moderate-amplitude` recommend 2/3 dealiasing for the dispersive component. Dealiasing would be the next single-component upgrade (E3) if F2 had shown aliasing-driven v-sector trouble; F2 shows mass conservation to machine precision and bounded v, so dealiasing is unnecessary for the spec.
- `kb-shallowWater-LaxFriedrichs-stable-smeared` / `kb-shallowWater-HLL-dam-break-pass` describe alternative Riemann/flux choices; Godunov was preferable because (a) the bank explicitly endorses MUSCL+Godunov for the Burgers component and (b) Godunov is sharper than Lax-Friedrichs which matters for resolving the bore–soliton interaction.
- `kb-kdv-smallAmplitude-dispersiveRegime` is informational — it warns that small-amplitude v will disperse rather than form solitons; F2's v_max=0.63 is still in the moderate range, so a recognizable peak is consistent with this guidance.

## Final self-assessment

`pred_results/T_C.npy` has shape `(21, 2, 256)` and satisfies the phenomenon target:

| Spec                          | Value at T=8                 | Pass? |
|-------------------------------|------------------------------|-------|
| `|u|_max < 5` (bore bounded)  | 2.673                        | YES   |
| `v_max >= 0.5` (soliton lives)| 0.630 (peak at x ≈ -6.8)     | YES   |
| All finite                    | true                         | YES   |
| u mass conserved              | 22.5879 → 22.5879            | YES   |
| v mass conserved              | 3.0000 → 3.0000              | YES   |
| n_snapshots ≥ 5               | 21                           | YES   |

The bore-soliton interaction is non-trivial: the soliton amplitude decays from 1.5 to ~0.63 and the L2 norm of v drops by ~14% (consistent with dispersive radiation), and the v field shows multiple competing peaks in late time. Physically this is the **partial-refraction / scattering** regime — the soliton was neither cleanly transmitted nor fully destroyed; the bore extracted energy into a dispersive wake while a reduced-amplitude peak survives. The numerics are stable and conservative, so this is a credible qualitative answer to the research question.
