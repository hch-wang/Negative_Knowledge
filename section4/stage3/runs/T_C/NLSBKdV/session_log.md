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
