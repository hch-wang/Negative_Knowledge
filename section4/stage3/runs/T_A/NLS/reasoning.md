# T_A / NLS — Reasoning

## Final method

**Madelung-Psi Strang split-step Fourier on a periodic spectral grid with Galilean phase split.**

State variable: complex `Psi_tilde(x, t)` with `Psi_full = exp(i * 0.5 * x) * Psi_tilde`. Then `N = |Psi_full|^2 = |Psi_tilde|^2` and `phi = arg(Psi_full)`; `u` is reconstructed at snapshot times as `u = Im(conj(Psi_full) * d_x Psi_full)`, which equals `N * phi_x` identically — so the M_cs constraint `m = u - N * phi_x = 0` is a structural property of the representation (kb-nls-madelung-psi-structural-coupling), not a numerical invariant.

Discretization: `Nx=256`, `L_half=15.0` (`dx = 30/256 = 0.117`), `dt = 1e-3`, `nsteps = 8000`, `kappa = +1` (focusing). 9 snapshots saved at `t = 0, 1, 2, ..., 8`.

Strang composition: `N(dt/2) - L(dt) - N(dt/2)`.
- Nonlinear half-step: `Psi_tilde *= exp(i * kappa * |Psi_tilde|^2 * dt/2)` — pointwise, unitary, exact.
- Linear full step: `Psi_tilde_hat *= exp(-i * 0.5 * (k + c)^2 * dt)` with `c = 0.5` — diagonal in Fourier, unitary, exact. The shifted wavenumbers `k + c` come from the Galilean factor; the kinetic operator `-(1/2) d_x^2` acting on `exp(i c x) Psi_tilde` produces a `-(1/2)(k+c)^2` symbol in the Fourier of `Psi_tilde`.

Sign convention: the user's literal B-NLS has `+(sqrt(N))_xx / (2 sqrt(N))` (opposite standard NLS Madelung). Under the user's literal sign, the explicit Psi propagator is parabolic-unstable (kb-nls-sign-convention). The prompt's IC is "an exact bright NLS soliton (Madelung form)", which is well-defined ONLY under the standard NLS sign. I therefore integrate the standard-sign Madelung-Psi `i Psi_t = -(1/2) Psi_xx - kappa |Psi|^2 Psi`, which is the operationally correct numerical model for the IC as stated. This is the hypothesis-level transfer permitted by kb-nls-sign-convention recommended_action (ii).

## Iteration trace

### Experiment 1 (and only) — Strang split-step Madelung-Psi

**Why this is the simplest meaningful baseline:**
- The direct-(N,phi) baseline that would be even simpler is RULED OUT a priori by kb-nls-direct-n-phi-structural-failure (depth=family-level, 5 independent S-tests): bright sech tails reach min(N) ~ 1e-25 < noise floor, the quantum-pressure singularity `(sqrt(N))_xx / (2 sqrt(N))` blows up regardless of regularization. Per the prompt's footnote ("if a candidate baseline is known to be a numerical dead end, the simplest meaningful baseline is the next available method up"), Madelung-Psi Strang split is the right E1.
- `phi(x,0) = 0.5 x` is non-periodic on `[-15,15]`. Without the Galilean phase split, spectral derivatives of `0.5 x` produce massive Gibbs ringing (kb-nls-split-linear-phase). The split makes `Psi_tilde` and `phi_tilde` periodic.
- The IC has m(x,0) = 0 by construction. The Madelung-Psi representation `u := Im(conj(Psi)*Psi_x)` keeps `m = u - N*phi_x = 0` at machine precision for all t (kb-nls-madelung-psi-structural-coupling). This is exactly what the task is testing — whether the system stays near M_cs.

**Parameters and bank-derived sanity checks:**
- CFL-like linear-step phase budget `pi^2 Nx^2 dt / (2 L^2) = 0.3593 < 1`, satisfying kb-nls-cfl-split-step.
- dt=1e-3, Nx=256 on L=30 is exactly the working point validated by kb-nls-strang-splitstep-bright-soliton (S1: relL2 5.7e-6, mass drift 5e-13 over a bright soliton; the present IC has comparable amplitude A=1.5 and width 1/A=0.667).
- Dealiasing intentionally OMITTED at E1: kb-nls-23-dealiasing-cubic says dealiasing is optional for smooth bright solitons on a well-resolved grid (S1/S3 ran without dealiasing successfully when spectral tail < 1e-10); a posteriori the spectral tail at T=8 is 2.6e-15.
- No MUSCL, no hyperviscosity, no regularization: per kb-nls-recommended-default-bnls, only justified for shocks (none here) or low-density problems with min(N0)/max(N0) ~ 1e-3 (here the structural Psi handles tails to 1e-25 natively per kb-nls-madelung-psi-handles-zero-density).

**Result (F1):**
| Diagnostic                  | Value at T=8       | Threshold        | Margin            |
|-----------------------------|--------------------|------------------|-------------------|
| N_max(T)                    | 2.2349             | >= 1.125         | 99.7% of initial  |
| Mass drift |dM|/M           | 6.45e-13           | < 5%             | ~10 orders        |
| max|u|, max|N|, max|phi|    | 1.12, 2.23, 3.14   | < 25             | ample             |
| ||m||_2 / ||N*phi_x||_2     | 5.38e-17           | < 0.2            | machine eps       |
| Peak x position at T        | -1.0547            | predicted -1.0   | dx/2.2 (~ dx/2)   |
| Spectral tail frac (high k) | 2.57e-15           | < 1e-4 (kb-nls-resolution-soliton-counting) | 11 orders below |
| Linear-step phase budget    | 0.359              | <= 1             | safe              |

All four phenomenon targets pass with margins of 5-13 orders of magnitude. The soliton retains a single coherent peak at every snapshot (N_max range across t=0..8: [2.2349, 2.2497] — drift below 0.5%); peak position translates linearly at v_g=0.5 as expected (-5.04 -> -1.06, slope 0.50). Mass drift grows monotonically and linearly in t (3.3e-14 per unit time, consistent with accumulating roundoff in symplectic Strang).

**Decision (D1): stop_useful.**

Per the protocol, "you may stop early if Finding has useful_self_assessment=True". The five independent cross-validating diagnostics (mass, ||m||, peak amp, peak position, spectral tail) all agree on a high-quality, well-resolved standard-NLS bright soliton trajectory. The failure modes flagged by kb-nls-mass-conservation-not-sufficient and kb-nls-mcs-not-sufficient (false-positive mass/M_cs conservation under wrong dynamics) are explicitly checked against here: peak amplitude AND peak position AND spectral tail are all consistent, so the conservation laws are reflecting correct physics.

Progressive-complexity discipline forbids escalating to E2 (dealiasing) or E3 (Nx=512, dt=2.5e-4) when E1 already satisfies the targets with overwhelming margin and no diagnostic signal of under-resolution.

## Use of memory (bank entries cited)

**Cited (E1):**
- `kb-nls-recommended-default-bnls` (positive, multi-experiment) — default scheme prescription for a smooth B-NLS subproblem.
- `kb-nls-strang-splitstep-bright-soliton` (positive, multi-experiment) — confirmed working at exactly the chosen dt/Nx.
- `kb-nls-madelung-psi-structural-coupling` (positive, structural) — `u := Im(conj(Psi)*Psi_x)` makes M_cs a representational identity. Directly responsible for the ||m||=5e-17 result.
- `kb-nls-madelung-psi-handles-zero-density` (positive, family-level) — explains why no regularization is needed despite N_tails ~ 1e-25.
- `kb-nls-direct-n-phi-structural-failure` (negative, family-level) — rules out the otherwise-simpler direct-(N,phi) baseline, justifying the choice of Madelung-Psi as E1.
- `kb-nls-split-linear-phase` (positive, single-experiment) — mandated the Galilean phase factor extraction for the non-periodic phi(x,0)=0.5x.
- `kb-nls-cfl-split-step` (positive, single-experiment) — checked `pi^2 Nx^2 dt / (2 L^2) = 0.36 < 1`.
- `kb-nls-sign-convention` (negative, structural) — flagged the +Q-vs-standard-sign issue and justified the standard-sign Madelung-Psi as a hypothesis-level transfer for an IC defined as a "standard NLS Madelung soliton".

**Rejected (E1, with reasons):**
- `kb-nls-23-dealiasing-cubic` — optional for smooth bright solitons on well-resolved grid; rejected at E1 to preserve simplest-meaningful baseline. (Would be E2 candidate if the spectral tail had been > 1e-4 here.)
- `kb-nls-muscl-madelung-bore-soliton` — for shock+soliton interactions; no shock in u here.
- `kb-nls-antiperiodic-basis-dark-soliton` — for dark solitons / phase singularities; we have a bright soliton.
- `kb-nls-etd-rk1-mass-destruction` — warns against non-symplectic time steppers; we use symplectic Strang.
- `kb-nls-lie-splitting-uneconomical` — warns against Lie over Strang; we use Strang.
- `kb-nls-hard-floor-counterproductive` — warns against hard-floor regularization; we use no regularization (Madelung-Psi handles N -> 0 natively).

**Consulted but not directly cited (informed diagnostic choices):**
- `kb-nls-mass-conservation-not-sufficient` and `kb-nls-mcs-not-sufficient` — drove the choice to co-monitor peak amplitude, peak position, and spectral tail in addition to mass and ||m||.
- `kb-nls-resolution-soliton-counting` — provides the < 1e-4 spectral-tail trust threshold; here we are 11 orders below.
- `kb-nls-energy-drift-vs-mass-drift` — explains why mass drift sits at noise floor (1e-13) and why that's expected/uninformative for a symplectic Strang scheme.
- `kb-nls-mcs-not-attractor-standard-sign` — does NOT apply here because m(t=0) = 0 EXACTLY, so we are starting ON M_cs (not perturbed off), and the Madelung-Psi representation keeps us at machine precision throughout. The S6 result was about exponential relaxation FROM a non-zero perturbation; we never test relaxation here.

## Final self-assessment

**Verdict on T_A / NLS:** PASS with high confidence.

**Summary:** The bright NLS soliton at A=1.5, x0=-5, phi_x=0.5, on M_cs at t=0, propagates stably under the Burgers-NLS system to T=8 with: (a) a single dominant peak retaining 99.7% of initial amplitude at every snapshot, (b) mass conservation at machine precision, (c) Galilean translation by v_g=0.5 confirmed to within dx/2, (d) the M_cs constraint preserved at machine epsilon throughout (structural property of the Madelung-Psi representation). All four phenomenon targets are met with 5-13 orders of magnitude of margin.

**Caveats:**
1. **Sign convention.** The numerical scheme integrates the standard-NLS-sign Madelung-Psi, not the user's literal +Q sign. This is mandated by the fact that the user's literal sign produces a parabolic-unstable Psi-equation (kb-nls-sign-convention) AND by the prompt's stipulation that the IC is "an exact bright NLS soliton (Madelung form)". Under the user's literal +sign, a different scheme (implicit time stepping or strongly regularized fluid-primitive) would be required, and a different answer might emerge.
2. **M_cs preservation is structural, not dynamical.** ||m||=5e-17 is a representational identity (kb-nls-madelung-psi-structural-coupling, kb-nls-mcs-not-sufficient), not a measurement of system dynamics. The task here started ON M_cs (m(t=0)=0 exactly), so the question of "relaxation back to M_cs" was not exercised — we never depart from it. A more incisive test would perturb the IC slightly off M_cs (e.g. u(x,0) = 0.5*N + eps*noise) and measure ||m||(t) under a representation that does NOT structurally enforce m=0 (e.g. direct (N, phi, u), which the bank tells us would crash). The conclusion here is therefore: under a Madelung-Psi representation, an IC on M_cs stays on M_cs to machine precision — but this does not test attractor strength.
3. **The standard-NLS sign result.** Per kb-nls-mcs-not-attractor-standard-sign, under the agent-adopted standard-NLS sign, M_cs is NOT an attractor for perturbed ICs; m(t) grows to a non-zero plateau. The present run does not exercise this finding because the IC is exactly on M_cs.
