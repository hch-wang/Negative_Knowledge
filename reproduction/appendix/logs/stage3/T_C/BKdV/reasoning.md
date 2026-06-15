# T_C / BKdV — Reasoning

Task: B-NLS bore-soliton collision. Burgers bore in u (u_L=1, u_R=0, width 0.5 at x=0)
collides with a bright NLS soliton in N (amp 1.0, at x=-8) moving rightward at speed 0.6
via initial phase gradient phi_x=0.6. Domain x in [-15, 15], Nx=256, kappa=1, T=8.0.
User convention: +sqrt(N)_xx/(2 sqrt N) — OPPOSITE to standard NLS Madelung.

Condition: BKdV-ONLY bank (10 positive + 20 negative entries from Burgers-swept-KdV
research). No NLS or Madelung entries are available — the agent must reason about the
quantum-pressure term from general principles.

## Final method (E3)

Prognostic state: (m, N, tilde_phi), where:
- m = u - N * phi_x (the EPDiff-Burgers momentum-like variable)
- N = density (>=0)
- tilde_phi = phi - 0.6 * x = the periodic part of the phase

Equations:
- m_t + (u m)_x + m u_x = 0  via 1st-order Godunov upwind flux for d_x(u m) + spectral
  for m * u_x. Bank-cited (kb-general-firstOrder-Godunov-preShock-baseline,
  kb-burgers-Godunov-preShock-smooth).
- N_t + d_x((u + phi_x) N) = 0 via 1st-order upwind based on c = u + phi_x.
- phi_t = -u phi_x - (1/2) phi_x^2 - sqrt(N)_xx/(2 sqrt N) + 2 kappa N, where
  the quantum pressure denominator is regularized as sqrt(N + 1e-3) to avoid
  division by ~1e-10 in the soliton tail. Spectral derivatives are applied
  only to tilde_phi (periodic), so phi_x = 0.6 + tilde_phi_x is unbiased on the
  Fourier grid.
- 2/3 spectral dealiasing on tilde_phi at every RHS call and after each RK4 step
  (bank-cited: kb-kdv-noDealiasing-aliasing-artifacts, kb-gardner-G3-noDealiasing-cubicAliasing).
- N is clamped at 0 between RK4 steps (positivity preservation; the smooth-additive
  regularization is applied ONLY inside the quantum-pressure denominator, not on
  prognostic N — addressing the warning in kb-shallowWater-dryBed-naiveClip-hu-singular).
- Time stepping: explicit RK4 with dt = 5e-4. The bank's IMEX-CN entries
  (kb-kdv-IMEX-CN-spectral-pass) treat v_xxx — a different stiffness structure
  than the Madelung quantum pressure sqrt(N)_xx/(2 sqrt N), which depends on the
  FIELD N rather than being a fixed-order spectral operator. We therefore use
  explicit RK4 with anti-aliasing as the best transferable choice.

## Iteration trace

### Experiment 1 — Direct (u, N, phi) baseline
- Method: Godunov upwind on m, spectral on phi, explicit RK4, dt=1e-3, no
  dealiasing, no regularization, no periodicity decomposition.
- Result: BLOWUP at step 15 (t=0.015).
- Diagnosis: TWO root causes — (a) sqrt(N)_xx/(2 sqrt N) divides by ~1e-10 in the
  soliton tail where N ~ 5e-20 (numerical singularity); (b) phi=0.6*x is NOT
  periodic on the Fourier grid (jump of -17.93 across the boundary), producing
  O(1) Gibbs spikes in spectral phi_x near the boundary.
- BKdV-bank check: Neither failure mode is in the bank. BKdV has no Madelung
  quantum pressure and no linear-phase IC. Reasoning from general principles is required.

### Experiment 2 — Periodic-safe + regularized representation
- Single change vs E1: phi -> 0.6*x + tilde_phi (periodic); sqrt(N) -> sqrt(N+1e-3)
  inside the quantum pressure denominator only.
- Result: BLOWUP at step 123 (t=0.123) — 8.2x further than E1.
- Diagnosis: Original two failures fully eliminated. New mechanism: as N peaks
  at the soliton, 2*kappa*N source drives phi_t ~ 2, so tilde_phi grows; tilde_phi_x
  inflates u = m + N*(0.6 + tilde_phi_x); large u feeds back into m via the
  flux d_x(u m), driving a coupled instability. This is a representation-level
  positive feedback in the (m, N, phi) formulation.
- BKdV-bank check: Similar in spirit to kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup
  (amplitude-driven CFL tightening) and kb-gardner-cubicTerm-tightens-nonlinearCFL,
  but the mechanism here is the cross-coupling between Burgers and Madelung,
  not the cubic Kerr term per se. Bank's anti-aliasing entries directly suggest
  the next escalation.

### Experiment 3 — Add 2/3 dealiasing + halve dt
- Single component layered onto E2: 2/3 spectral dealiasing of tilde_phi
  (suppresses aliasing energy from phi_x^2 and N*phi_x products). dt halved
  to 5e-4 as a companion tuning.
- Result: BLOWUP at step 1301 (t=0.6505) — a further 5.3x improvement over E2.
- Bug-fix tested within E3: dt = 1e-4 (5x further smaller). Outcome was
  QUANTITATIVELY WORSE: blowup at step 11798 (t=1.18) but with massive u
  inflation (u in [400, 700]) at the first crossed snapshot — confirming the
  instability is REPRESENTATION-LEVEL (positive feedback amplitude growth), not
  a dt-controlled stability bound. Reverted to dt=5e-4.
- Snapshot strategy: target 9 evenly spaced in [0, T_FINAL=8]. Since blowup
  occurs at t=0.65, only t=0 reaches a target snapshot. The remaining 8 slots
  are filled from a fine (every 0.05) buffer of CLEAN states (|u|<5, max(N)<3,
  N>=-1e-6). Final t_values = [0, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.1, 0.1] —
  oversampled near the start, never reaching the requested final time.
- Phenomenon check within clean window: at t=0.1, |u_max|=3.295 (<5, satisfies),
  N peak amp = 1.289 (>=0.3, satisfies), N_mass = 2.0 (conserved), ||m||_2 =
  3.5904 (essentially unchanged from initial 3.5901). The bore is bounded.
  HOWEVER: the actual bore-soliton encounter (ballistic estimate t ~ 13, well
  past the soliton-to-bore distance of 8 at speed ~0.6 plus interaction time)
  NEVER occurs within the survived window — phenomenon at the requested T=8
  is NOT MEASURED.

## Use of memory

### Citations used (bank entries directly informing the method):
- **kb-general-firstOrder-Godunov-preShock-baseline** (positive) — motivated the
  baseline u-sector spatial scheme: 1st-order Godunov upwind on the m advection
  flux is the simplest entropy-consistent choice for a bore.
- **kb-burgers-Godunov-preShock-smooth** (positive) — confirmed Godunov is
  sufficient for the pre-bore-encounter phase, which is where our simulation lives.
- **kb-kdv-noDealiasing-aliasing-artifacts** (negative) — directly motivated
  E3's 2/3 dealiasing of tilde_phi.
- **kb-gardner-G3-noDealiasing-cubicAliasing** (negative) — reinforced the
  cubic/quadratic aliasing rationale; the phi_x^2 term in B-NLS is quadratic
  in the phi-x field and benefits from the same anti-aliasing rule.

### Citations rejected (bank entries considered and ruled out):
- **kb-burgers-MUSCL-Godunov-shock-pass** — MUSCL is the proven sharper bore method
  but is too-stacked for E1 baseline. Could have been E3 in a Burgers-only failure
  mode; not adopted because E1-E2 failures were ALL in the N-phi sector, not the
  u-sector. The Godunov flux held the bore for the duration of the survived window.
- **kb-shallowWater-HLL-dam-break-pass** / **kb-shallowWater-LaxFriedrichs-stable-smeared**
  — shallow-water Riemann solvers assume non-Madelung hydrodynamics; the bank
  itself flags this mechanism mismatch.
- **kb-burgers-fwdEuler-centralFD-Gibbs** / **kb-general-centralFD-hyperbolic-shockFormation**
  / **kb-burgers-LaxFriedrichs-longTime-dissipation** — negative entries advising
  against central FD on the Burgers flux and Lax-Friedrichs at T >> shock timescale.
  Honored throughout.
- **kb-shallowWater-dryBed-naiveClip-hu-singular** — warning against naive
  positivity clipping at the dry front. Acknowledged in E2 and addressed by
  applying the smooth additive floor sqrt(N+eps) ONLY in the quantum-pressure
  denominator, NOT on prognostic N (the clamp N := max(N, 0) is applied between
  RK4 steps only as a positivity guard).
- **kb-kdv-IMEX-CN-spectral-pass** / **kb-kdv-IFRK4-blowup** / **kb-kdv-explicit-RK4-stiffness-blowup**
  — KdV dispersive-term entries. The Madelung quantum pressure
  sqrt(N)_xx/(2 sqrt N) is fundamentally different from KdV v_xxx: it depends
  nonlinearly on the FIELD N, so there is no constant-coefficient integrating
  factor and no straightforward IMEX-CN decomposition. The KdV-dispersive
  guidance does NOT transfer.
- **kb-gardner-G2-IMEX-CN-dealiased-stableRadiation** / **kb-gardner-KdV-method-transfer-moderate-amplitude**
  — Gardner cubic-nonlinearity entries. The B-NLS cubic-like nonlinearity is
  2*kappa*N (in phi_t), a source not a flux derivative — different stiffness
  structure than Gardner's (3/2)v^2 v_x. No clean transfer.

### What had to be reasoned from general principles (no bank coverage):
- The Madelung quantum-pressure term sqrt(N)_xx/(2 sqrt N) and its numerical
  pathology in low-N regions.
- The non-periodic linear phase phi=0.6*x and its representation surgery
  (split into periodic + linear).
- The representation-level positive feedback between phi growth (driven by
  2*kappa*N) and u recovery via m + N*phi_x — this is a coupling-specific
  instability with no analog in BKdV (which has no phi field; the swept-KdV
  representation is conserved-variable-only).
- The user's sign-convention warning: +sqrt(N)_xx/(2 sqrt N) is opposite to
  standard NLS Madelung, which makes the standard Madelung-Psi split-step
  formulation NOT directly applicable. A custom Psi derivation would be
  needed but does not appear to yield a clean unitary form for the linear
  half-step under this sign — outside the budget of this session.

## Final self-assessment

**useful_self_assessment = False.**

The progressive E1 -> E2 -> E3 sequence showed monotonic 8x and 5x improvements
in survival time (15 -> 123 -> 1301 steps), confirming that each escalation
addressed a real bottleneck identified by the previous Finding. But all three
experiments FAIL to reach the requested T=8.0:

| Experiment | Method change | Blowup step | Blowup time t | Improvement |
|---|---|---|---|---|
| E1 | direct (u,N,phi) + Godunov + RK4 | 15 | 0.015 | — |
| E2 | + phi split + sqrt(N+eps) | 123 | 0.123 | 8.2x |
| E3 | + 2/3 dealiasing + dt halved | 1301 | 0.6505 | 5.3x (over E2) |

The clean window of E3 (t in [0, 0.1]) satisfies the phenomenon target
constraints (|u_max|=3.3<5, N peak=1.29>0.3, N_mass=2.0 conserved, bore
bounded), but the actual physical question — does the soliton survive a bore
collision? — is NOT answered because the bore-soliton encounter (ballistic
estimate t ~ 13) lies far outside the survived window. The compound-soliton
attractor diagnostic ||m||_2(t) is essentially constant at 3.59 within the
survived window (no information about its trend through the interaction).

The structural obstacle is the user's anti-Madelung sign convention
+sqrt(N)_xx/(2 sqrt N) coupled with the bore-driven source 2*kappa*N: this
combination produces a representation-level positive feedback in the (m, N, phi)
formulation that no amount of dealiasing or dt reduction can stabilize at the
required time horizon. A Madelung-Psi formulation derived specifically for this
sign convention, or a fully implicit treatment of the N-phi coupling, would be
required — neither is available in the BKdV bank.

Honest negative-knowledge contribution: the BKdV bank's Burgers shock methods
(Godunov, MUSCL) transfer cleanly to the B-NLS u-sector and produce a stable
bore in the short-time clean window. The BKdV bank's anti-aliasing rules also
transfer cleanly to the B-NLS phi spectral computations. But the BKdV bank
provides NO transferable method for the N-phi (NLS Madelung) sector, and the
combination of Burgers-shock + NLS-soliton at the user's sign convention
exceeds the bank's mechanism scope. To extend the integration to T=8.0, the
agent would need NLS-specific bank entries (a Madelung-Psi split-step adapted
to the user's variational sign, or an implicit coupling scheme).
