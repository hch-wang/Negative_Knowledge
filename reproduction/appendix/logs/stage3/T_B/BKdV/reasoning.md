# T_B / BKdV reasoning

## Final method

**E3: Direct (u, N, tilde_phi) Fourier pseudospectral + explicit RK4
+ Q-floor regularization (eps_N = 1e-10) + 2/3 dealiasing
+ gauge split phi = 0.3*x + tilde_phi (tilde_phi periodic).**

Parameters: Nx = 256, dt = 1e-4, T = 6.0, kappa = +1 (focusing).
Equations of motion as in task spec, with USER variational sign convention on
the Madelung quantum pressure (+sqrt(N)_xx/(2 sqrt(N)) in phi_t).

The solver BLEW UP at step 4 (t = 0.0004) due to a UV linear instability
analyzed below. The saved `pred_results/T_B.npy` contains the last sane state
(t = 0.0003, essentially the IC) repeated for snapshots 2 through 9. The
phenomenon target (>= 2 well-separated peaks at amp >= 1.0) was NOT achieved.

## Iteration trace

### E1: simplest meaningful (Fourier + RK4 on direct (u, N, phi))

- dt = 2e-4, no dealiasing, no regularization.
- BLEW UP at step 3 (t = 0.0006), overflow in multiply.
- Root cause: N(x, 0) has Gaussian tails ~ 1e-77 at the boundary; the term
  `Q = sqrt(N)_xx / (2*sqrt(N))` contains 1/sqrt(N) ~ 1e38 in those tails,
  producing astronomical phi_t source and immediate divergence.
- Bank coverage: NONE. The BKdV bank explicitly notes the Madelung pressure has
  no analog. The closest cautionary entry was
  `kb-shallowWater-dryBed-naiveClip-hu-singular` (vacuum positivity issues in
  shallow-water context), which is mechanism-related but does not prescribe a
  fix for Madelung pressure.

### E2: regularize the Q operator (Q-floor only, dt halved)

- Same direct (u, N, phi) representation, but `Q = sqrt(max(N, eps_N))_xx /
  (2*sqrt(max(N, eps_N)))` with eps_N = 1e-10. dt cut to 1e-4.
- BLEW UP at step 3 (t = 0.0003), overflow in multiply.
- Q itself was now bounded (|Q|_max ~ 22 at t=0, vs ~ 1e30 unregularized).
  But |phi_x|_max at t=0 was 53 (analytic value 0.3), and |phi_t|_max = 1401.
- Diagnosis: the IC `phi(x,0) = 0.3*x` is NOT periodic on x in [-15, 15]
  (jumps 9.0 between x=15- and x=-15+ via periodicity). Fourier derivatives of
  this non-periodic field produce massive Gibbs ringing at the boundary. The
  resulting huge phi_t blew through the regularized Q.
- Bank coverage: NONE direct. Closest is
  `kb-burgers-LaxFriedrichs-periodic-longTime-contamination` (periodic-domain
  artifacts at long times) — directionally about periodicity but addresses a
  different mechanism.
- Considered: switch to Madelung-Psi (Psi = sqrt(N) * exp(i*phi)). DEAD END
  under the user sign convention — re-derivation showed that the +Q sign in
  phi_t forces an i*Psi_t = +(1/2)*Psi_xx mapping, which gives the WRONG sign
  on the continuity flux (predicts +d_x(phi_x*N) instead of -d_x(phi_x*N)).
  The B-NLS in user convention is NOT in the standard Madelung-NLS form. So
  Psi was not used.

### E3: gauge split + 2/3 dealiasing

- State: (u, N, tilde_phi) with phi = 0.3*x + tilde_phi, tilde_phi periodic.
- 2/3 dealiasing on all nonlinear products and on spectral derivative outputs.
- Q-floor regularization carried over from E2.
- RK4, dt = 1e-4 (same as E2).
- At t=0, RHS magnitudes were now sane (|u_t| ~ 4, |N_t| ~ 1, |tphi_t| ~ 13)
  — the gauge fix solved the boundary-ringing problem.
- BLEW UP at step 4 (t = 0.0004). |u_new|_max = 2.6e6, |N_new|_max = 180
  (vs IC max 2.0). Grid-scale oscillations with period 3*dx = 0.352 visible
  at step 3.
- **Linear stability analysis** explains the failure structurally:
  Linearize around (u, N, phi) = (0, N0, 0) on M_cs.
    `d^2/dt^2(delta_N) = [k^4*(N0+1)/4 + 2*kappa*N0*(N0+1)*k^2] * delta_N`
  For focusing kappa = +1 AND user-convention +Q, the bracket is STRICTLY
  POSITIVE for all k. Linear growth rate:
    `Omega(k) = sqrt(k^4*(N0+1)/4 + 2*kappa*N0*(N0+1)*k^2)`.
  At k_max ~ 18 (after 2/3 dealias) and N0 = 2: `Omega ~ 287 rad/s`.
  This is UV-unbounded (`Omega(k) ~ k^2/2` as k -> infty after dealias). The
  user-convention B-NLS is **ill-posed in the classical Hadamard sense**:
  high-k modes grow without bound and the IVP has no continuous dependence on
  IC. No explicit time scheme can stabilize it; even an exact integrator for
  the linear part would still see exp(Omega(k)*t) growth in unstable modes,
  saturating into grid-scale nonlinear cascade.

- Bug-fix to same iteration: added a sanity threshold (|state|_max < 1e3)
  to terminate before float-overflow, so the saved snapshot is the last sane
  state rather than catastrophic-overflow garbage.

## Use of memory (BKdV bank)

The BKdV bank had 30 entries: 10 positive + 20 negative.

**Citations made (E1, E2, E3):**
- `kb-kdv-IMEX-CN-spectral-pass`: motivated Fourier pseudospectral as the
  baseline spatial scheme. Transferred cleanly at the representation level
  (Fourier basis on periodic domain), though we used explicit RK4 rather than
  IMEX-CN in E1-E3 because the destabilizing operator (Madelung Q) is not the
  same as KdV's v_xxx, so the bank's IMEX-CN recipe is not directly
  applicable.
- `kb-kdv-noDealiasing-aliasing-artifacts` (negative) and
  `kb-gardner-G3-noDealiasing-cubicAliasing` (negative): motivated the 2/3
  dealiasing in E3. Both entries describe the same mechanism (spurious peak
  inflation from undealiased polynomial nonlinearities) and the B-NLS Kerr
  term is polynomial in N = |Psi|^2, so the lesson transfers.
- `kb-general-massConservation-insufficient-diagnostic`: motivated tracking
  peak count, peak amplitude, position separation, and finiteness in addition
  to mass drift. Used in all three experiments' diagnostics.

**Rejections made:**
- `kb-burgers-fwdEuler-centralFD-Gibbs` and
  `kb-general-centralFD-hyperbolic-shockFormation`: bank warns against central
  FD for shock-prone hyperbolic. Rejected as not applicable because Fourier
  derivatives are spectrally exact and the on-M_cs initial u is smooth — no
  classical shock formation at t=0.
- `kb-burgers-MUSCL-Godunov-shock-pass`: rejected at E1 (premature complexity
  per progressive-complexity discipline), reserved for shock-rich regimes
  that did not materialize in any iteration.
- `kb-kdv-IFRK4-blowup`: rejected — no integrating factor in our scheme.
- `kb-gardner-cubicTerm-tightens-nonlinearCFL`: bank quantifies a dt bound
  for v_xxx + cubic nonlinearity (Gardner). Rejected as not transferable: the
  NLS Kerr term has different derivative degree and a fundamentally different
  dispersion than KdV, so the Gardner amplitude-CFL formula doesn't apply.
- `kb-shallowWater-dryBed-naiveClip-hu-singular`: bank warns that clipping
  positivity (e.g. h_max = max(h, 0)) can produce ill-defined u = hu/h. Used
  as a CAUTIONARY guide for E2's Q-floor (we floored INSIDE the singular Q
  operator only, not in the continuity equation, to limit scope of the
  positivity clip).

**Bank coverage of failure modes encountered:**
- E1 Madelung 1/sqrt(N) singularity: NOT covered. Bank explicitly notes
  Madelung pressure has no analog. Reasoned from first principles + the
  prompt's hint about `kb-nls-direct-n-phi-structural-failure` (an NLS-bank
  entry the BKdV-only condition does not have access to).
- E2 non-periodic phi gauge: NOT covered. Reasoned from Fourier-method
  fundamentals.
- E3 UV instability from +Q sign convention: NOT covered. Bank entries on
  aliasing-driven peak inflation (kb-kdv-noDealiasing, kb-gardner-G3) flag a
  RELATED but DIFFERENT mechanism — those are nonlinear-aliasing artifacts
  curable by dealiasing; the +Q UV instability is a LINEAR ill-posedness that
  no amount of dealiasing alone can stabilize. The bank gave a partial
  diagnostic toolkit but no recipe.

## Final self-assessment

**Phenomenon target NOT met.** The saved `pred_results/T_B.npy` contains
mostly the IC repeated. Mass drift is ~0% (because nothing evolved). N peak
count above 1.0 is 1 (the original Gaussian, plus 8 grid-scale ringing peaks
that emerged in steps 2-3 before the run was terminated by the sanity
threshold).

**Useful diagnostic, not a useful solver.** The session demonstrated that
B-NLS in the user's variational sign convention (+Q in phi_t) is linearly
UV-unstable for focusing kappa = +1, and that none of the BKdV bank entries
prescribe a stabilization recipe. To produce a valid T_B solution with this
sign convention, the next iteration (not in budget) would require ONE of:
  (a) A spectral cutoff at low k (e.g. k_cut = 5-10) — but this destroys
      resolution and would not propagate the modulational instability
      faithfully even if it were to run.
  (b) A variational/symplectic integrator preserving the Hamiltonian
      structure of B-NLS, which may have a different stability character
      than the explicit RK4 we tried.
  (c) Re-interpret the sign convention: the prompt notes that the +Q sign
      is OPPOSITE the standard Madelung NLS. If the intended physics is
      focusing-NLS modulational instability, the standard -Q sign would
      give a well-posed system, and the standard NLS bank would apply. The
      BKdV bank, however, would still not help (no NLS-specific entries).
  (d) Damped/dissipative regularization (hyperviscosity) outside
      progressive-complexity rules.

**Conclusion for the negative-knowledge experiment.** Under the BKdV-only
condition, the agent could:
  + Cleanly identify the Fourier-pseudospectral baseline and 2/3 dealiasing
    as transferable bank lessons.
  - NOT prevent the three sequential failure modes (Madelung singularity,
    non-periodic gauge, UV instability) because the bank has no entries on
    Madelung physics or on the user-variational sign convention.
  - NOT achieve the phenomenon target within the 3-iteration budget; the
    diagnostic value of the session is the linear-stability analysis in F3,
    showing the system is ill-posed under +Q with focusing kappa.

The bank GAP that dominated this run is the absence of any
`kb-nls-sign-convention` or `kb-nls-direct-n-phi-structural-failure` entries —
both flagged by the prompt as NLS-bank entries unavailable to this condition.
The BKdV bank's mechanism set (Burgers shocks, KdV dispersive stiffness,
shallow-water dam-breaks) is genuinely orthogonal to the NLS Madelung
pressure that dominates B-NLS dynamics.
