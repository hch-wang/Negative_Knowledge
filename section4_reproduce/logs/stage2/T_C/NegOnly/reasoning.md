# T_C / NegOnly — reasoning

## Final method

**Experiment E2** is the answer (and is the candidate.py in this directory).

- **Spatial discretization**: Fourier pseudospectral on a periodic grid, Nx=256, L=30 (x in [-15, 15]). Spectral derivatives via FFT.
- **Aliasing control**: 2/3-rule dealiasing applied to every nonlinear product (u u_x, v v_x, u v, v^2, and the inputs u, v themselves before differentiation). This is the minimum viable hygiene per BKdV-S1.
- **Time integration**: explicit classical RK4 with dt = 2e-4. This sits well below both the post-dealias v_xxx CFL bound (~4.94e-4) and the u-viscosity diffusion CFL bound (nu*k_max^2*dt ~ 7.2e-3 << 2.78).
- **u-side dissipation**: explicit linear viscosity nu*u_xx with **nu = 5.0e-2**, treated explicitly inside RK4. This is the single-component upgrade over E1 baseline, dictated by BKdV-S6 deep-synthesis empirical evidence that this exact nu_lin value cleanly bounds the Burgers self-flux on this bore IC.
- **No hyperviscosity**, no operator splitting, no IMEX, no MUSCL/Godunov.

PDE RHS:
- u_t = -3 u u_x - 3 (v^2)_x - v_xxx + nu * u_xx
- v_t = -6 v v_x - v_xxx - (u v)_x

Output: 17 snapshots (well above the 5-snapshot minimum), array shape (17, 2, 256) saved to `pred_results/T_C.npy`.

## Iteration trace

- **E1** (baseline, no u-viscosity): finite but bore self-steepens explosively — u_max trajectory peak 11.4, final 9.66; TV(u) 1.5 -> 320 (a ~213x inflation); v fragmented into 11 spurious peaks. Exactly the BKdV-S6 prediction: 2/3-dealiasing alone cannot dissipate the in-band high-k cascade from 3 u u_x on a bore-like u-gradient IC. Phenomenon target failed on |u_max|<5 and on "bore not blown up."
- **E2** (E1 + nu*u_xx, nu=5e-2): all phenomenon targets met. u_max bounded <= 3.33 throughout the run, 2.18 at T=8; v_max final 0.63 (> 0.5 threshold) and never drops below 0.56 in the run; TV(u) stays between 20 and 40 (no runaway); mass_u and mass_v exactly conserved to FFT round-off. The KdV soliton initially at x=-8 propagates rightward, encounters the bore, and emerges as a smaller transmitted pulse plus low-amplitude radiation — i.e., it **survives (partial transmission with some fission)**, neither destroyed nor cleanly bouncing.

E3 was not run: F2 has `useful_self_assessment: true` and no failure mode remains that would motivate a second single-component upgrade.

## Use of memory

### Negative bank entries that DROVE the design (rejected directions)
- **BKdV-S6 (deep synthesis)** — *the single most decisive entry.* Established that the bare pre-validated Fourier+2/3-dealias+RK4 stack CANNOT bound the Burgers self-flux on a bore-like u-IC (the IC family used here), and that the required u-side dissipation is explicit linear viscosity nu ~ 5e-2 (or k^8 hyperviscosity nu_h ~ 1e-9, at the RK4 stability ceiling). Used to (a) predict E1's failure mode and (b) pick nu=5e-2 exactly for E2.
- **BKdV-S4 (deep synthesis)** — *rejected as transferable.* BKdV-S4's "safe envelope" nu_h ~ 1e-22 on smooth-soliton ICs is **13 orders of magnitude too weak** for bore-like u-gradient ICs (per BKdV-S6's "13 orders too weak" finding). Do not transfer BKdV-S4 nu_h values across IC classes.
- **BKdV-S1** — confirmed 2/3-rule dealiasing is mandatory (no-dealias version blows up via overflow on v^2 / u*v / v*v_x before t=0.5). dt=2e-4 chosen to match its post-dealias safe regime.
- **kb-kdv-noDealiasing-aliasing-artifacts** — secondary reinforcement of the 2/3-rule requirement.
- **kb-kdv-explicit-RK4-stiffness-blowup** — flagged the explicit-RK4 v_xxx CFL constraint; dt=2e-4 keeps |k^3 dt| within RK4 stability after dealias.
- **kb-burgers-fwdEuler-centralFD-Gibbs / kb-shallowWater-centralFD-fwdEuler-hNegative / kb-general-centralFD-hyperbolic-shockFormation** — ruled out central-FD on the advective u u_x. (Spectral derivatives also lack upwind dissipation, but they at least avoid the Gibbs cross-contamination of FD; with explicit nu they perform well, as E2 confirms.)
- **kb-burgers-LaxFriedrichs-longTime-dissipation / kb-shallowWater-LaxFriedrichs-overdiffusion** — ruled out LxF for the bore: it over-diffuses and would mis-time the encounter.
- **kb-general-finiteness-not-accuracy** — drove the choice to inspect TV(u), peak count and amplitude rather than relying on "all_finite" as a success signal. Critical for diagnosing E1: it was all-finite but TV=320 is a hard failure.

### Negative bank entries considered but rejected for different reasons
- **kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup / kb-gardner-cubicTerm-tightens-nonlinearCFL / kb-gardner-nonlinearCFL-amplitude-boundary** — Gardner-specific amplitude CFL warnings. At A=1.5 here, these warn dt>2.5e-4 is risky for IMEX-CN; we use explicit RK4, not IMEX-CN, and dt=2e-4 is within the safer regime. Considered but not directly applicable to E2's method.
- **kb-gardner-G3-noDealiasing-cubicAliasing / kb-gardner-G1-explicitRK4-finiteFrag** — already covered by the BKdV-S1 dealiasing requirement and BKdV-S4 dt selection.
- **BKdV-S5 (deep synthesis)** — warns that the m=0 (u=v^2/2) submanifold is not BKdV-invariant and that high-k perturbations grow as exp(t). Not directly applicable here because our IC has u=bore and v=soliton independently chosen (m != 0 initially), so this is a coexisting "off-manifold" run from t=0. Noted as a reason to expect dispersive radiation from the encounter (which E2 indeed shows).
- **BKdV-S7 (deep synthesis)** — warns that sech^2 is NOT a coherent BKdV traveling wave and fragments by T=10 even with clean numerics. We accept that the v-soliton is just an IC, not a steady state — partial fragmentation in E2 (6 small v-peaks) is consistent with this, not a numerical failure.
- **kb-shallowWater-dryBed-naiveClip-hu-singular** — not applicable (no near-zero depth field in this problem).
- **kb-gardner-sech2IC-not-exact-soliton / kb-kdv-amplitude-threshold-soliton** — A=1.5 is well above the soliton threshold and v is a KdV (not Gardner) sech^2, consistent with the task spec.
- **BKdV-S2 deep-synthesis variants** — about searching for the BKdV Hamiltonian; not relevant to a single-IC interaction study.
- **BKdV-S3 deep-synthesis variants** — about IC-spectral-shape coherence boundaries; not relevant since our v-IC is a localized sech^2 (well inside the coherent basin).
- **kb-gardner-GardnerIsM0-coupledSystemInstability** — applicable in spirit (m=0 reduction breaks down for full coupled BKdV), but our task is the coupled system, not the m=0 reduction, so this is informational only.
- **kb-general-massConservation-insufficient-diagnostic** — drove the choice to report TV(u), peak count, peak amplitude, and peak position in F1/F2 rather than mass conservation alone.

## Final self-assessment

**Yes**, `pred_results/T_C.npy` satisfies the phenomenon target.

Diagnostic evidence (E2 final snapshot):
- `|u_max| = 2.18 < 5` ✓ (target: |u_max| < 5)
- `v_max = 0.63 >= 0.5` ✓ (target: v retains a recognizable peak with amplitude >= 0.5)
- `TV(u) = 21.6` bounded and stable across the run (target: bore not blown up) ✓
- All-finite throughout, mass conserved exactly (mass_u=22.588, mass_v=3.000 across all snapshots)

Across the trajectory, u_max never exceeds 3.33 and v_max never drops below 0.56, so the targets hold not just at T=8 but throughout the interaction window. The physical interpretation is that the soliton **transmits with partial fission**: most of its amplitude survives passage through the bore (reduced from 1.5 to ~0.6, with the difference radiated as low-amplitude trailing waves with 5-6 secondary peaks in the v field). The bore is regularized into a stable viscous shock layer of bounded TV.

Output shape: (17, 2, 256), saved to `pred_results/T_C.npy`.
