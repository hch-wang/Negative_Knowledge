# T_B / NegOnly — Reasoning

## Final method (E2)

**Solver:** Fourier pseudospectral spatial discretization with explicit RK4 in time and 2/3-rule dealiasing applied to all nonlinear products before differentiation.

**Discretization details**
- Periodic domain x in [-15, 15], Nx = 256, dx ~ 0.117
- Wavenumbers k = 2*pi*fftfreq(Nx, d=L/Nx); dealias mask zeroes |k_index| > N/3
- v_x, v_xxx via spectral derivative on raw v
- (u^2)_x, (v^2)_x, (u v)_x via spectral derivative on the dealiased FFT of the product
- RHS:
  - u_t = -1.5 (u^2)_x - 3 (v^2)_x - v_xxx     (= -3 u u_x - 6 v v_x - v_xxx)
  - v_t = -3 (v^2)_x - v_xxx - (u v)_x
- Time integrator: classical 4-stage RK4, dt = 2e-5 (300,000 steps total)
- 7 snapshots saved (t = 0, 1, 2, 3, 4, 5, 6); output shape (7, 2, 256)

**Why this is the final method.** Progressive-complexity discipline was followed strictly: E1 was the simplest spectral + explicit RK4 baseline; F1 pinpointed aliasing of nonlinear products as the failure mode; E2 added exactly one component (2/3-rule dealiasing) and that single upgrade was sufficient.

## Iteration trace

- **E1 (baseline)**: Fourier spectral derivatives + explicit RK4, NO dealiasing, dt = 2e-5. Linear v_xxx stability budget (dt < 1.45e-4) and the bare nonlinear CFL estimate both looked safe a priori.
  - **F1**: NaN/Inf at step 19,402 (t = 0.388). Overflow originated in the explicit nonlinear products u*v and v*v (RuntimeWarning seen in the run log). At amp = 4 the cubic-style v^2 v_x term aliases beyond Nyquist on the 256-mode grid; the aliased high-k energy is amplified at each RK4 stage, blowing through the bare CFL estimate. Classified `negative`, useful = false.
- **E2 (single-component upgrade)**: same method + 2/3-rule dealiasing on (u*u, v*v, u*v) before spectral differentiation. dt and Nx unchanged.
  - **F2**: all finite to T = 6, mass(v) drift = 0.000%, 10 well-separated peaks with amplitudes 0.85-1.70, min peak spacing 1.52. Phenomenon target (>= 2 peaks at >= 0.8, mass drift < 8%) met with comfortable margin. Classified `positive`, useful = true. Stopped early per protocol.

## Use of memory (negative bank)

**Bank entries that shaped E1 (rejection / pitfall flags)**
- `kb-burgers-fwdEuler-centralFD-Gibbs`, `kb-general-centralFD-hyperbolic-shockFormation`: discouraged central FD on the advective term. Chose Fourier spectral derivatives instead.
- `kb-kdv-explicit-RK4-stiffness-blowup`, `kb-gardner-G1-explicitRK4-finiteFrag`: warned that explicit RK4 on the dispersive term fragments or blows up. The discipline still required running it as the baseline; F1 confirmed the bottleneck is the nonlinear (aliasing) part, not the linear dispersive part — an important debugging payoff.
- `kb-kdv-IFRK4-blowup`: discouraged jumping to integrating-factor RK4 as a "more clever" baseline; reinforced that the right E1 is a plain RK4.

**Bank entries that shaped E2 (escalation direction)**
- `kb-kdv-noDealiasing-aliasing-artifacts`, `kb-gardner-G3-noDealiasing-cubicAliasing`: both negative entries directly pinpoint missing 2/3 dealiasing as a known failure mode of spectral methods on KdV / Gardner-type nonlinearities; reading the F1 diagnostics through this lens identified dealiasing as the single component to add.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup`, `kb-gardner-nonlinearCFL-amplitude-boundary`: warned that the nonlinear CFL is amplitude-sensitive (amp 1.5 -> 3 tightens it ~2.5x). At amp = 4 the situation is worse, so I confirmed numerically that with dealiasing the effective k_max drops to N/3 * 2pi/L = 17.87 and the nonlinear CFL at dt = 2e-5 becomes 0.017, safely below the empirical threshold the bank suggests (~ O(0.3)).

**Bank entries considered but not driving choices**
- `kb-burgers-LaxFriedrichs-longTime-dissipation`, `kb-burgers-LaxFriedrichs-periodic-longTime-contamination`, `kb-shallowWater-LaxFriedrichs-overdiffusion`: Lax-Friedrichs was never a candidate; entries noted only to confirm spectral over LxF.
- `kb-shallowWater-centralFD-fwdEuler-hNegative`, `kb-shallowWater-dryBed-naiveClip-hu-singular`: shallow-water-specific dry-bed concerns; the IC has v > 0 everywhere and v stays bounded (no near-zero amplitude singularity), so not directly applicable.
- `kb-gardner-sech2IC-not-exact-soliton`, `kb-kdv-amplitude-threshold-soliton`: relate to using wrong IC shape or sub-threshold amplitude; not relevant here since the task IC is a Gaussian (intentional decomposition) and amp = 4 is well above the threshold.
- `kb-gardner-GardnerIsM0-coupledSystemInstability`: reminds that the full coupled system is at least as stiff as its Gardner reduction. Encouraged conservative dt choice; consistent with dt = 2e-5.
- `kb-general-finiteness-not-accuracy`, `kb-general-massConservation-insufficient-diagnostic`: drove the diagnostic checklist (peak count + amplitude + position + mass, not just finiteness or mass alone). This is why F2 reports all four.

**No positive bank was available** (NegOnly condition). All decisions were either method elimination from negative bank or direct PDE-class reasoning.

## Final self-assessment

I believe `pred_results/T_B.npy` satisfies the phenomenon target.

**Numerical diagnostics (from F2 / E2 execution)**
- Output shape: (7, 2, 256) — 7 snapshots at t = 0, 1, 2, 3, 4, 5, 6 ; channels (u, v).
- `all_finite = True` for every snapshot (no NaN/Inf anywhere).
- mass(v): initial 10.6347, final 10.6347, drift 0.000 % (target < 8 %).
- v_final: 10 peaks above 0.8, heights {1.70, 1.24, 1.54, 1.04, 1.59, 0.85, 1.46, 1.17, 1.07, 1.58}, x positions {-12.66, -7.38, -3.52, -1.29, 2.81, 5.16, 7.27, 10.08, 11.60, 13.36}.
- Min peak spacing 1.52 (~ 13 grid points) — well-separated and well-resolved.
- u_final range [-2.77, 3.58] — coupling has driven u from zero into solitary structure consistent with the swept-KdV / Gardner regime.

**Caveats**
- 10 peaks is many more than the minimum 2 required. With dealiasing on, the count is physical rather than aliasing-spurious (kb-kdv-noDealiasing-aliasing-artifacts and kb-gardner-G3-noDealiasing-cubicAliasing produced 4 and 11 spurious peaks respectively at amp ~ 1.5 / 2; here we are at amp 4 where the IC has roughly 4x the action, naturally supporting more solitons under inverse-scattering theory).
- The wave-train wraps the periodic domain at T = 6 (peaks span x ~ -12.7 to 13.4, near domain edges). kb-burgers-LaxFriedrichs-periodic-longTime-contamination warns that long-time periodic-domain runs can suffer recirculation contamination. At T = 6 with characteristic speed ~ O(amp) ~ 4, the domain-traversal time is ~ L/c = 30/4 ~ 7.5, so we are still under one full traversal time — the wrapping is borderline but the peaks remain individually identifiable.
- Mass conservation to machine precision is a property of the spectral method on conservation laws and is not by itself a correctness proof, per kb-general-massConservation-insufficient-diagnostic. The combined check (peak count + amplitude + spacing + mass) is what supports the positive self-assessment.
