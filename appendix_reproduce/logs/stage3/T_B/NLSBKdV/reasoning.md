# T_B / NLSBKdV — Reasoning

## Final method

Madelung-Psi Strang split-step Fourier on `Psi = sqrt(N) exp(i phi)`, with the
Galilean phase split `phi = c x + phi_tilde` (c = 0.3) baked into a wavenumber
shift `k -> k + c` on the linear half-step.  2/3 dealiasing applied on both
`|Psi|^2` (before the pointwise cubic exponential) and on the linear FFT
output.  Sign convention adopted: STANDARD NLS sign `i Psi_t = -1/2 Psi_xx -
kappa |Psi|^2 Psi` (see "Use of memory" below for caveat).

Resolution: internal grid Nx_int=512 on `x in [-15, 15]` (dx=0.0586), time step
dt=5e-4 (12000 steps to T=6).  Output downsampled to Nx=256 per the task spec.
25 snapshots saved.

Diagnostics on the final output:
- mass drift = -1.44e-11 (relative -1.9e-10)
- spectral tail (90-95% modes) = 6.5e-7
- final-snap peak count with `N>=1.0` = **2** (x=-3.98, N=2.158 and x=-2.46, N=2.156)
- max(N) over the whole trajectory = 13.04 (reached at t=5.0, second focusing
  event of the breather)

## Iteration trace

### E1 — Madelung-Psi Strang, Nx=256, dt=1e-3

Rationale: kb-nls-recommended-default-bnls explicitly recommends Strang
split-step on Psi for smooth focusing-NLS Gaussian IC.  Progressive-complexity
discipline says to start with the simplest meaningful method; because the bank
declares direct (N, phi) integration to be a *family-level* numerical dead end
(kb-nls-direct-n-phi-structural-failure, 5 independent stress tests),
Madelung-Psi is the simplest *meaningful* baseline.  Phase split required by
kb-nls-split-linear-phase because phi_0 = 0.3 x is non-periodic at the box
boundary.

Outcome: ran cleanly to T=6, mass drift -6.4e-6, 2 peaks of amplitude 2.16 at
final time.  But spectral tail energy (90-95% modes) reached 0.16 during the
focusing collapse at t~1.5 and t~5 — far above the 1e-4 threshold flagged
"untrustworthy" by kb-nls-resolution-soliton-counting.  Could not certify the
peak count as converged.

### E2 — Same Madelung-Psi Strang, Nx=512, dt=5e-4

Single grid-refinement upgrade per progressive-complexity discipline.
Nx_int=512 gives dx=0.0586, which exactly matches the dx that S3
(kb-nls-resolution-soliton-counting) declared converged for A in [1, 3]
sweeps on L=60.

Outcome: identical peak structure to E1 (positions agree to 3 decimal places,
amplitudes to 4 decimal places, max(N) over trajectory differs by 0.03).  Mass
drift improved to -1.4e-11.  Spectral tail dropped to 6.5e-7.  Confirmed E1
was a correct answer; E2 is the certified converged version.

Stopped at E2 with useful_self_assessment=True.

## Use of memory

### Cross-check between NLS bank and BKdV bank

I consulted both banks at the proposal stage of E1.  Citation ratio in the
final solver: **10 NLS entries cited, 1 BKdV entry cited** (kb-kdv-no-
Dealiasing-aliasing-artifacts, which agreed with kb-nls-23-dealiasing-cubic on
the dealiasing requirement).  All other 29 BKdV entries were rejected:

- BKdV Burgers-shock methods (kb-burgers-MUSCL-Godunov-shock-pass, kb-burgers-
  Godunov-preShock-smooth, etc.): not applicable.  T_B's u IC is u = 0.3 N, a
  smooth Gaussian-amplitude profile of u; there is no Burgers shock at t=0 and
  none develops because the Burgers coupling here is mediated through Psi, not
  through u directly.
- BKdV KdV-dispersion methods (kb-kdv-IMEX-CN-spectral-pass, kb-kdv-small-
  Amplitude-dispersiveRegime, etc.): not applicable.  NLS kinetic operator is
  -1/2 d_xx, not d_xxx.  IMEX-CN for v_xxx solves a different stiffness problem
  and the resulting recommended dt does not transfer.
- BKdV shallow-water methods (kb-shallowWater-HLL-dam-break-pass, kb-shallow-
  Water-LaxFriedrichs-stable-smeared, etc.): not applicable.  B-NLS has no
  Saint-Venant-like h>=0 structure.
- BKdV Gardner methods (kb-gardner-G2/G3/G4-*, kb-gardner-cubicTerm-tightens-
  nonlinearCFL, etc.): not applicable.  Gardner's cubic 3/2 v^2 v_x is in u
  (real, hyperbolic).  B-NLS's cubic is kappa |Psi|^2 Psi (in the complex
  field), which is unitary and absorbed by Strang exactly.  The Gardner CFL
  tightening does NOT apply because the B-NLS nonlinear step is exact in dt.

### Did the BKdV bank help or mislead?

Help: marginal.  kb-kdv-noDealiasing-aliasing-artifacts independently
corroborated the NLS dealiasing rule, which strengthens the "always 2/3
dealias on a cubic-NLS spectral run" rule, but the same conclusion was
available from kb-nls-23-dealiasing-cubic alone with NLS-specific evidence.

Mislead potential: I had to actively guard against importing the wrong
recommendation.  Gardner amplitude-CFL warnings (kb-gardner-G4-IMEX-CN-amp-
litudeCFL-blowup, kb-gardner-cubicTerm-tightens-nonlinearCFL, kb-gardner-non-
linearCFL-amplitude-boundary) would, if naively transferred, have implied that
the B-NLS amplitude A=2 needs an aggressive dt reduction — which is false,
because the NLS cubic step is exact pointwise via the exponential of i kappa
|Psi|^2 dt and so dt is unconstrained by the cubic.  Sticking to the NLS-
specific kb-nls-cfl-split-step (phase budget pi^2 Nx^2 dt / (2 L^2) <= 1)
gave the correct constraint.

### Sign convention caveat

Per kb-nls-sign-convention, the user's literal sign in the HJ phi equation is
opposite to standard NLS Madelung.  Under the literal sign, the standard Psi
propagator is parabolic-unstable and no usable explicit method exists.  I
adopted the STANDARD-NLS sign convention (-1/2 Psi_xx) per the bank's
hypothesis-transfer warning, and document that result here.  Caveats applicable
to this output identical to those flagged in kb-nls-sign-convention and kb-nls-
mcs-not-attractor-standard-sign.

## Final self-assessment

`useful_self_assessment = True` because:

1. **Phenomenon target met**: 2 peaks at T=6, amplitudes >=1.0, mass drift well
   below 5%.
2. **Convergence verified**: E1 (Nx=256) and E2 (Nx=512) agree on peaks to <0.01%
   in amplitude and 0.000 in position; max(N) over trajectory agrees within
   0.03.
3. **Bank-cited diagnostics are clean**: spectral tail 6.5e-7 (<< 1e-4 flag),
   mass drift 1.4e-11 (machine precision), no NaN, all finite.
4. **Sign-convention caveat documented**: the result is for the standard-NLS
   sign per bank guidance; the literal +sign case would require an
   implicit/Wick-rotated method not yet developed in the bank.

Iterations consumed: 2 of 3.  Stopped early at E2 because E1 and E2 mutually
corroborate the answer and a third refinement would not change the diagnostic
conclusion.

The Burgers boost phi_x = 0.3 here behaves as a pure Galilean translation
under the Madelung-Psi reformulation (absorbed into the k -> k + c wavenumber
shift); it does NOT alter the focusing threshold or the breather period
relative to the un-boosted (c=0) Gaussian.  This is the answer to Q1's
phenomenon question: at A=2, T=6, kappa=+1, the Gaussian sheds 2 peaks of
amplitude 2.16 in a breather cycle, and the Burgers coupling at the chosen
phi_x = 0.3 does not alter the threshold from pure focusing-NLS behaviour.
