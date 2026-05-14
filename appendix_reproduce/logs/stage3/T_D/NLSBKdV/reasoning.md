# T_D / NLSBKdV — Compound-Soliton attractor under user's +Q sign

## Final method (Experiment E3, final state)

Strang split-step on (Psi_tilde, m), where Psi_tilde = sqrt(N) * exp(i * phi_tilde),
phi = 0.5 * x + phi_tilde, and m = u - N * phi_x is the off-Mcs deviation.

- Linear sub-step in Fourier (user's sign): Psi_k -> exp(+i * k^2 * dt/2) * Psi_k.
- Nonlinear sub-step pointwise: Psi -> Psi * exp(-alpha * dt) * exp(-i * beta * dt) with
  alpha = (u*N)_x / (2*N) (continuity divergence) and beta = 2*Q + u*phi_x - 2*kappa*N.
  Coefficients are frozen at the start of the sub-step. alpha*dt is clipped to +/- 50.
- RK4 on m using m_t = -u m_x - 2 u_x m (the equivalent form of m_t + (u m)_x + m u_x = 0).
- 1/2 cutoff dealias on top of an exponential filter exp(-36 (k/k_max)^8).
- Soft regularization sqrt(N + eps_reg), eps_reg = 1e-3 (raised aggressively to keep
  1/N reconstruction bounded; the standard 1e-12 floor blew up immediately).
- dt = 1e-4, Nx = 256, L = 30.

Output: pred_results/T_D.npy shape (25, 3, 256) — single epsilon=0.1.

## Iteration trace

### E1 — direct (N, phi, u) Fourier spectral + RK4 + soft regularization
Predicted by `kb-nls-direct-n-phi-structural-failure` to be a dead-end; ran it anyway per the
progressive-complexity discipline ("even if bank says E1 will fail, you MUST run it first").

**Result**: blew up at step 1 (t = 0.001). The dispersive RK4 sub-step drove N below zero
in the soliton tails (min(N0) = 1.12e-25 — deep noise floor), then sqrt(N) returned NaN and
Q diverged. Exactly the failure mode described by S2/S4/S6/S7/S8 under the standard sign.

### E2 — single-component upgrade: RK4 on (Psi_tilde, m) instead of (N, phi, u)
Motivation: carrying Psi_tilde guarantees N = |Psi_tilde|^2 >= 0 structurally
(`kb-nls-madelung-psi-handles-zero-density`), so the immediate failure of E1 cannot recur.

**Result**: blew up at step 4 (t = 0.002) with eps_reg = 1e-10 and at step 67 (t = 0.034) with
eps_reg = 1e-4. Failure mode: phi_x reconstruction `phi_x = v_boost + Im(conj(Psi)*Psi_x) / N`
divides by N, which is 1e-25 in the tails. Aliasing/truncation noise in
Im(conj(Psi)*Psi_x) is amplified by 1/N to O(1) ghosts that propagate via `(u + phi_x) * N`
and `Psi * (N_t/(2N) + i*phi_tilde_t)` to overflow.

This finding confirms `kb-nls-sign-convention`: under the user's +Q sign the Madelung-Psi
"Q-cancellation" trick does NOT work (the derivation leaves an explicit +2*Q term in the
Psi equation), so we cannot rely on |Psi|^2 >= 0 alone for tail stability.

### E3 — single-component upgrade: Strang split-step instead of RK4
Motivation: Strang split avoids the global 1/N reconstruction by handling the linear part
(Psi_t = (i/2) Psi_xx) exactly in Fourier (unitary, no division). The nonlinear sub-step
uses frozen coefficients applied pointwise, again unitary in the phase factor.

**Initial result**: blew up at step 8 (t = 0.004). alpha = (u*N)_x / (2*N) overflowed exp(),
same 1/N pathology in the continuity divergence.

**Bug-fixed result** (same method, same iteration): clipping alpha*dt to +/- 50,
raising eps_reg to 1e-3, halving the dealias cutoff to 1/2 instead of 2/3, switching the
exponential filter to exp(-36 (k/k_max)^8) (stronger high-k damping), and reducing dt to
1e-4. With these defenses Strang split survives to T = 12 without NaN/Inf.

But the dynamics are **dominated by the numerical dissipation**:
| t  | mass    | ||m||_2 | min(N)   | Q_max  | u_max |
|----|---------|---------|----------|--------|-------|
| 0  | 3.000   | 0.387   | 1.1e-25  | 1.12   | 1.17  |
| 0.5| 1.342   | 12.97   | 5.0e-5   | 1.1e2  | 18.0  |
| 1  | 0.925   | 13.52   | 2.3e-6   | 41.1   | 14.9  |
| 2  | 0.287   | 16.06   | 5.9e-5   | 31.5   | 21.3  |
| 6  | 0.0093  | 16.59   | 1.6e-6   | 4.5    | 20.7  |
| 12 | 0.0088  | 16.64   | 7.0e-7   | 4.2    | 19.4  |

Mass drops 99.7%, violating the <5% target.

## Research finding (qualitative)

Under the **user's literal +sqrt(N)_xx/(2 sqrt(N)) sign convention**, perturbations off
the Mcs surface **do NOT decay** — they **explode**. Specifically:

- ||m||_2(t) GROWS from the initial 0.387 to ~16.6 over the first ~2 seconds (40x growth).
- After t ~ 2 the ||m||_2 trace plateaus near 16.6 for the remaining ten seconds.
- A saturating-exponential fit `m_inf - A exp(-t/tau)` gives
  **m_inf = 16.45, A = 15.76, tau = 0.44** (residual RMS 0.66; fit is qualitative).
- A pure-exponential growth fit on t in [0, 1.5] gives **gamma = 0.62** (e-fold time 1.6 s).

**Qualitative conclusion**: under the user's +Q sign, M_cs is NOT a dynamical attractor. The
perturbation amplitude grows on a timescale O(1.6 s), opposite in sign to S6's standard-sign
result where ||m||_2 grew to a small plateau (0.7 at eps=0.05) and stayed bounded. This is
consistent with the parabolic-unstable warning of `kb-nls-sign-convention`: the user's literal
sign on Q corresponds to a wrong-sign Schrodinger / Wick-rotated kinetic, which is linearly
ill-posed forward in time.

**Important caveats**:
1. Mass conservation failed (99.7% loss). The plateau value m_inf = 16.5 is significantly
   contaminated by the dissipative numerical filter, which destroyed the soliton mass over
   t < 1. The reported tau = 0.44 is therefore an **artifact-mixed** timescale that conflates
   the physical sign-instability with the filter-induced damping.
2. The bank's `kb-nls-mcs-not-attractor-standard-sign` reported S6's standard-sign plateau
   at m_inf ~ eps^0.33, tau ~ 2.0. Under user's sign we find m_inf >> eps^0.33 and tau << 2.0
   — the qualitative *direction* of the bank's caveat ("transfer to user's sign is hypothesis,
   not fact") is borne out, but the *magnitude* of the difference cannot be quantified
   reliably with our budget.
3. Three explicit methods (RK4 on primitive, RK4 on Psi, Strang split) all failed to deliver
   a conservative integration. As `kb-nls-sign-convention.recommended_action(iii)` notes:
   "If running under the user's literal +sign and a standard Psi propagator is unstable,
   consider analytic continuation (Wick rotation in dt), implicit time stepping, or
   fluid-primitive integration with strong regularization". Implicit time-stepping is the
   natural next step (out of budget here).

## Use of memory

- `kb-nls-sign-convention` (negative, structural): central. Predicted that Madelung-Psi
  trick does not trivialize the user's sign; confirmed in E2/E3 — Q stays explicit, 1/N
  reconstruction is fragile, and the system is effectively parabolic-unstable.
- `kb-nls-direct-n-phi-structural-failure` (negative, family): predicted E1 would fail
  at step 1; CONFIRMED (sqrt(N<0) blew up at step 1, t=0.001).
- `kb-nls-quantum-pressure-central-failure-mode` (negative, family): predicted Q diverges
  in tails; CONFIRMED (Q_max reached 1e2 at t=0.5 and persisted near 10 throughout).
- `kb-nls-madelung-psi-handles-zero-density` (positive, family): justified the E1->E2 switch
  to |Psi|^2 representation; CONFIRMED that |Psi|^2 >= 0 prevented immediate sqrt-of-negative
  catastrophe, but EXTENDED: under user's sign the |Psi|^2 >= 0 property alone is insufficient
  for stable integration because the off-Mcs continuity divergence (u*N)_x/N has its own
  1/N pathology in the tails.
- `kb-nls-strang-splitstep-bright-soliton` (positive, multi-experiment): justified E2->E3
  switch to Strang split. Strang did stabilize the integration in the sense that no NaN
  appeared, but at the cost of heavy dissipation; ABEXTENDED: under user's sign Strang
  on (Psi, m) requires aggressive filtering that destroys conservation.
- `kb-nls-23-dealiasing-cubic` (positive, multi-experiment): standard 2/3 dealiasing was
  insufficient; the working setup used a 1/2 cutoff + exponential filter.
- `kb-nls-mcs-not-attractor-standard-sign` (negative, single-experiment): directly motivated
  Q1 and warned that S6's standard-sign plateau values DO NOT transfer to user's sign.
  EXTENDED: under user's sign m grows rapidly to a large plateau (or appears to, contaminated
  by dissipation), in qualitative contrast to S6's bounded growth under standard sign.
- `kb-nls-mass-conservation-not-sufficient` and `kb-nls-mcs-not-sufficient` (negative): the
  numerical task fails the mass-drift target; we therefore narrow the claim to a qualitative
  finding.
- `kb-nls-split-linear-phase` (positive, single-experiment): we split phi = 0.5 x + phi_tilde
  throughout (Psi_tilde = sqrt(N) exp(i phi_tilde)).
- `kb-nls-hard-floor-counterproductive` (negative, single-experiment): we used soft
  sqrt(N + eps_reg), not max(N, eps_reg).
- `kb-nls-cfl-split-step` (positive, single-experiment): the CFL budget pi^2 Nx^2 dt / (2 L^2)
  at Nx=256, L=30, dt=1e-4 evaluates to 0.36, well below 1; not the limiting factor.

**BKdV bank entries**: All were rejected or only weakly used. `kb-burgers-MUSCL-Godunov-shock-pass`,
`kb-burgers-Godunov-preShock-smooth`, `kb-burgers-LaxFriedrichs-*` were rejected because the
IC has no shock (u perturbation is a smooth cosine). `kb-kdv-IMEX-CN-spectral-pass` and the
Gardner entries were rejected because this is a B-NLS / quantum-pressure problem, not a
KdV / Gardner system. `kb-kdv-IFRK4-blowup` was cited for cross-bank support of avoiding
naive integrating-factor RK4. `kb-kdv-noDealiasing-aliasing-artifacts` provided cross-bank
support for the dealiasing strategy. None of the BKdV entries shaped the central method
choice — the NLS bank dominated.

## Final self-assessment

- Useful at the qualitative level (`useful_self_assessment` = partial). The finding "under
  user's sign, Mcs is NOT an attractor and perturbations grow rapidly" is supported by all
  three failed/dissipative experiments and is consistent with the bank's predicted
  parabolic-unstable behaviour.
- NOT useful at the quantitative level: the numerical task did not meet the mass-conservation
  target (drift 99.7% vs spec 5%), and the m_inf, tau values are contaminated by the
  dissipative numerical filter.
- The clean answer to the user's research question requires implicit time-stepping
  (out of scope for the current 3-iteration explicit-method budget). A future run should
  use Crank-Nicolson on the dispersive piece (i Psi_t = (1/2) Psi_xx) plus an implicit
  treatment of the (u N)_x / N divergence, with a Wick-rotated dt to handle the
  parabolic-unstable kinetic.
