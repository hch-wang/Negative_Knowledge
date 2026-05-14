# Session log: T_C / NLSBKdV

## Initialization
- Two banks read: 21 NLS entries + 30 BKdV entries.
- Task: smoothed Burgers bore (u_L=1, u_R=0, w=0.5) at x=0 colliding with a bright NLS soliton (sech^2 at x=-8, amp 1) moving right via phi_x=0.6. kappa=+1. T_final=8.0.
- Domain: x in [-15, 15], Nx=256 per task spec (even though kb-nls-recommended-default-bnls recommends Nx=512+ on L=60). Honor task spec exactly.

## Bank consultation summary
- **kb-nls-muscl-madelung-bore-soliton** is the directly-applicable NLS bank entry: validated on the SAME IC (u_L=1, u_R=0 bore + phi_x=0.6 bright soliton at x=-8) to T=8 at Nx=256, dt=5e-4 with 2/3 dealias. Recipe: MUSCL-Godunov SSP-RK3 on u + Madelung-Psi Strang split-step on Psi + 2/3 dealias.
- **kb-nls-direct-n-phi-structural-failure**: direct (N, phi) is a dead end -> simplest meaningful baseline at E1 must already use Madelung-Psi.
- **kb-nls-split-linear-phase**: REQUIRED. phi_0=0.6*x is non-periodic; split phi = 0.6*x + phi_tilde with phi_tilde periodic. Equivalently Psi = exp(i*0.6*x)*Psi_tilde with Psi_tilde periodic.
- **kb-nls-sign-convention**: user's literal +sqrt(N)_xx/(2 sqrt(N)) makes standard Psi propagator unstable. Per (iii) of recommended_action, when standard Madelung-Psi is the only available stable explicit method, we adopt the standard NLS sign convention -(1/2)Psi_xx as a working hypothesis and DECLARE this. Co-monitor diagnostics: mass, energy, ||m||.
- **kb-burgers-MUSCL-Godunov-shock-pass** (BKdV bank): MUSCL+Godunov van-Leer is the right scheme for the bore. CONSISTENT with NLS bank but the NLS bank entry kb-nls-muscl-madelung-bore-soliton already specifies MUSCL+Godunov SSP-RK3 + Madelung-Psi + dealias as the combined fix. The BKdV entry confirms the Burgers half independently but adds no new information about (N, phi).
- **kb-general-firstOrder-Godunov-preShock-baseline** (BKdV bank): first-order Godunov suffices pre-shock. Bore is already a finite-width shock at t=0 here, so MUSCL (not first-order) is needed throughout. The entry is consistent but does not add value over NLS bank's specific advice.
- **kb-nls-cfl-split-step**: dt <= 1e-3 at Nx=256 on L=30 (we have L=30 -> dx=0.117). Will use dt=5e-4 to match kb-nls-muscl-madelung-bore-soliton.
- **kb-nls-mass-conservation-not-sufficient + kb-nls-mcs-not-sufficient**: co-monitor mass, energy proxy, ||m||, N_max, peak position, spectral tail.

## Progressive-complexity plan
- E1: Strang Madelung-Psi + SPECTRAL on u (no MUSCL, no dealias). Expected: bore Gibbs-rings, possible blow-up.
- E2: + MUSCL-Godunov SSP-RK3 on u (single component change).
- E3: + 2/3 dealiasing on |Psi|^2 and linear FFT step (single further change).

## E1 execution
- Spectral SSP-RK3 on u + Strang Madelung-Psi (standard sign).
- Diverged at t=4.8 (step 9600). u_max grew 1.0 -> 1.78 -> 1.56 -> 10 -> NaN.
- Psi half stayed healthy: mass=2.0 exactly, N_max=1.0 throughout.
- Failure mode = bore Gibbs ringing in u (no upwinding) — exactly as predicted by kb-nls-muscl-madelung-bore-soliton.
- F1 useful_self_assessment = False. D1 -> change u-sector to MUSCL-Godunov SSP-RK3.

## E2 execution
- MUSCL-Godunov SSP-RK3 on u (van-Leer limiter, exact Burgers Riemann) + Strang Madelung-Psi.
- Completed T=8 cleanly. Walltime 1.8 s.
- Mass = 2.0000e+00 throughout; |u_max| = 1.0 exactly (zero overshoot); TV(u) = 1.988 (matches kb-nls-muscl-madelung-bore-soliton reported value to 4 sig fig); N_max in [0.9974, 1.0000].
- ||m||_2 MONOTONICALLY DECREASES 3.590 -> 3.428 (4.5% drop over T=8) — compound-soliton attractor signature.
- Soliton peak at T=8 at x=-3.164 (consistent with ballistic travel at speed 0.6 from x=-8: x=-3.2).
- Spectral tails: Psi 1.6e-8, u 9.25e-5 — both under the 1e-4 under-resolution flag.
- All four phenomenon targets PASS. F2 useful_self_assessment = True.
- Proceed to E3 only as verification (bank-canonical full stack).

## E3 execution
- E2 method + 2/3 dealiasing on |Psi|^2 (before nonlinear exp) and on the linear FFT step.
- Completed T=8 cleanly. Walltime 1.7 s.
- All snapshot diagnostics match E2 to 3-4 sig fig.
- E2 vs E3 deviation: u identical; N max relmax 7.1e-5 (rmse 9.4e-6) — well under 0.2% verification tolerance per kb-nls-recommended-default-bnls.
- This confirms E2 was already at numerical convergence; dealiasing is a no-op-quality safety margin here (because the spectral tail in Psi was already 1.6e-8 in E2).
- F3 useful_self_assessment = True. D3 -> stop_useful, declare E3 the final method.

## Final method = E3
- Strang Madelung-Psi on Psi=sqrt(N)*exp(i*phi) (standard-NLS sign, declared hypothesis per kb-nls-sign-convention)
- MUSCL-Godunov SSP-RK3 on u with van-Leer limiter and exact Burgers Riemann flux
- 2/3 dealiasing on |Psi|^2 and the linear FFT step
- Galilean factor exp(i*0.6*x) extracted; integrated Psi_tilde is genuinely periodic
- Nx=256, L=30, dt=5e-4, T=8, n_snapshots=9
- Output saved to pred_results/T_C.npy (shape (9, 3, 256)).

## BKdV bank assessment for this task
- DIRECTLY RELEVANT confirmatory entries: kb-burgers-MUSCL-Godunov-shock-pass, kb-general-firstOrder-Godunov-preShock-baseline, kb-burgers-fwdEuler-centralFD-Gibbs (negative anti-pattern), kb-kdv-noDealiasing-aliasing-artifacts (negative), kb-gardner-G3-noDealiasing-cubicAliasing (negative).
- All five are CONSISTENT with NLS bank guidance and add NO unique information not already in kb-nls-muscl-madelung-bore-soliton.
- Inapplicable entries: KdV IMEX-CN tools (~3 entries), Gardner cubic-CFL family (~6 entries), shallow-water HLL/LxF (~4 entries), Burgers long-time/periodic warnings (~2 entries). Total ~15 entries do not transfer.
- The BKdV bank is REDUNDANT here (does not actively mislead, but adds no value beyond what NLS bank already says). The decisive entry is kb-nls-muscl-madelung-bore-soliton from the NLS bank, which was validated on the SAME IC.

