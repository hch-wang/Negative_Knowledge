# Reasoning — T_A / PosNeg

## Final method

**E3 — Fourier pseudospectral + 2/3-rule dealiasing + IMEX-CN on the linear stiff v_xxx + explicit midpoint-RK2 on the nonlinear remainder.**

- Domain: x ∈ [-15, 15], Nx = 256, dx = L/Nx ≈ 0.117, periodic
- IC (as given): v(x,0) = 2 sech^2(x+5), u(x,0) = 0.5 v(x,0)^2 + 0.2 v(x,0)
- Time: dt = 2.5e-4, T_final = 8.0 → 32 000 steps
- Snapshots saved at t ∈ {0, 2, 4, 6, 8} → shape (5, 2, 256), channels (u, v)
- 2/3 dealias: zero Fourier modes with |k_idx| > Nx/3 = 85 on every nonlinear product (v^2, v·v_x, u·v, u·u_x) and on the assembled RHS in spectral space
- v_xxx integrated with Crank-Nicolson (factor (1 + dt/2 · ik^3)/(1 − dt/2 · ik^3), magnitude ≥ 1 so unconditionally stable for dispersive stiffness)
- Nonlinear remainder integrated with one-stage midpoint-RK2 (second order, NL-CFL = dt · (6A + 1.5A²) · k_max_eff ≈ 0.08 << 1 at A=2)

## Iteration trace

- **E1** (Fourier, no dealias, RK4, dt=1e-4): blow-up at t = 0.6123 with overflow in v² and u·v — classic broadband aliasing failure. Confirmed the BKdV-S1 negative depth-3 diagnosis.
- **E2** (E1 + 2/3 dealias, RK4 retained): reached T=8 cleanly; mass(v) drift = -0.09 %, |max u| = 6.03, |max v| = 2.0; but v_peak decayed 2.0 → 0.635 with 4 peaks. Mass / boundedness criteria met; amplitude criterion fails.
- **E3** (E2 + swap RK4-over-full-RHS to IMEX-CN-on-v_xxx + midpoint-RK2-on-nonlinear): reached T=8 cleanly; v_peak 2.0 → 0.637, mass drift -0.10 %, |max u| = 5.92, |max v| = 2.0. Matches E2 to <0.4 % — confirms intrinsic physics.

## Use of memory (bank citations)

**Positive entries cited / driving:**
- `BKdV-S1` (positive, depth-3 closure): the exact stack Fourier + 2/3-rule + RK4 ran cleanly to T=10 at amplitude up to 3.0; established that our amp=2, T=8 is inside the safe envelope and the right escalation for F1 is to add 2/3 dealias.
- `kb-kdv-IMEX-CN-spectral-pass` (positive): CN denominator |1 − dt/2 · ik^3| ≥ 1 is unconditionally stable for v_xxx — direct license for the E3 time-integrator swap.
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` (positive): IMEX-CN + 2/3 dealias is the validated stack for the Gardner / m=0 reduction; same stack appropriate for full BKdV.
- `BKdV-S2` (positive solver context): "IMEX-CN + midpoint-RK2" is the integrator used by the pilot deep-synthesis study — adopted verbatim.
- `kb-burgers-MUSCL-Godunov-shock-pass` (positive): considered for E3 but NOT adopted because u stayed bounded |max u| < 6.2 in E2 (no bore formed); the bank entry is a contingent recommendation if u develops shocks, which did not happen in this regime.

**Negative entries cited / rejected:**
- `kb-kdv-noDealiasing-aliasing-artifacts` (negative): predicted E1 failure mode (43 % amplitude inflation from quadratic aliasing) — confirmed; informed the D1 single-component fix.
- `BKdV-S1` (negative, no-dealias variant): same prediction at amp 1.5, blew up before t=0.5 — exactly our E1 timing.
- `kb-kdv-IFRK4-blowup` (negative): IF-RK4's exp(ik^3 t) overflows at high k — rejected as an E3 alternative; we used CN instead.
- `kb-kdv-explicit-RK4-stiffness-blowup` (negative): explicit-only treatment of v_xxx fragments the soliton even with tiny dt — informed the E2 → E3 escalation rationale (although our RK4 + dealias did NOT blow up at dt=1e-4 because post-dealias CFL is ~4.94e-4 >> dt).
- `kb-burgers-fwdEuler-centralFD-Gibbs`, `kb-shallowWater-centralFD-fwdEuler-hNegative`, `kb-general-centralFD-hyperbolic-shockFormation` (negative): central FD on hyperbolic terms is forbidden; we used spectral derivatives throughout, so these did not apply but were explicitly rejected in the E1 design.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup`, `kb-gardner-cubicTerm-tightens-nonlinearCFL`, `kb-gardner-nonlinearCFL-amplitude-boundary` (negative): warn that IMEX-CN can fail at amp ≥ 3 from nonlinear-CFL violations; checked that our amp=2 + dt=2.5e-4 gives NL-CFL ≈ 0.08 << 1, so we are safely inside the bound — no violation.
- `kb-gardner-sech2IC-not-exact-soliton`, `BKdV-S5` deep-synthesis (negative): explicit warning that a KdV-shape sech^2 IC will radiate continuously on full BKdV — this is the **dominant signal in our final reasoning**: the IC is not a true solitary wave of the full system, so amplitude decay is expected physics, not a method bug.
- `BKdV-S4` (negative, depth-3): warns Nx=256 may be sub-converged with diagnostics shifting by 30-140 % at Nx=512. Considered for E3 (resolution refinement) but rejected because (a) doubling Nx + rescaling dt would be TWO simultaneous component changes from E2, violating progressive-complexity discipline, and (b) the IMEX-CN swap was higher-priority per the bank's positive entries. A future Stage-2 follow-up could re-run E3 at Nx=512 / dt=1e-4 to test convergence of the radiation-decay rate.
- `kb-general-massConservation-insufficient-diagnostic` (negative): mass alone is insufficient — informed our F2/F3 explicitly reporting peak count and peak amplitude alongside mass.
- `kb-general-finiteness-not-accuracy` (negative): all-finite is not correctness — F2/F3 explicitly flag the v_peak amplitude as failing target despite finiteness and mass conservation.

## Final self-assessment

I do not believe `pred_results/T_A.npy` fully satisfies the phenomenon target as stated. Diagnostic readouts at T = 8:

- mass(v) drift: **-0.0957 %** (target < 8 %) — **PASS** by ~80×
- |max u|: **5.92** (target < 15) — **PASS**
- |max v|: **0.637** (target < 15) — **PASS**
- single dominant peak: **YES** with prominence ≥ 0.3 (one peak located at x ≈ -9.84) — **PASS**
- amplitude ≥ 0.5 · 2.0 = 1.0: **0.637 < 1.0** — **FAIL** (32 % retention vs 50 % required)

Three of four sub-criteria are satisfied. The amplitude shortfall is **convergent across two independent time integrators** (explicit RK4 in E2 and IMEX-CN + midpoint-RK2 in E3 agree to <0.4 %) and is **consistent with the bank's documented physics**: the prescribed IC (sech^2 in v with u = 0.5 v² + 0.2 v) sits OFF the m = 0 Gardner-reduction manifold by 0.2 v, and the m=0 manifold itself is not invariant under full BKdV for sech^2 ICs (BKdV-S5 depth-3 synthesised diagnosis). The IC is therefore not a true solitary wave of the full coupled system — it radiates continuously, the radiation propagates leftward (the dominant peak migrates to x ≈ -9.84), and 32 % retention at T = 8 is a physically reasonable outcome.

`useful_self_assessment` is set to `false` because the strict amplitude criterion is missed; but the run is numerically clean and trustworthy, and a follow-up at Nx = 512 (within Stage-2's progressive-complexity rules — would need an additional iteration) would test whether the radiation rate is still resolution-dependent or already converged.
