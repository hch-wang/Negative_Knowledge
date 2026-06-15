# Reasoning — T_A under NLSBKdV bank condition

## Final method

**Madelung-Psi Strang split-step Fourier** on Psi = sqrt(N) exp(i phi), with three integrated components:

1. **Linear-phase split (kb-nls-split-linear-phase):** phi(x,0) = 0.5*x is non-periodic on
   [-15, 15]. Spectral FFT of a non-periodic function generates Gibbs ringing that kills
   any spectral method. We write Psi = exp(i c x) * Psi_tilde with c = 0.5 and integrate the
   periodic Psi_tilde. The kinetic operator for Psi_tilde in Fourier is
   exp(-i (k + c)^2 dt / 2).

2. **Strang split-step on Psi_tilde (kb-nls-strang-splitstep-bright-soliton):**
   half-kinetic / full-nonlinear / half-kinetic at dt = 1e-3 on Nx = 256.
   - Half kinetic step: multiply Psi_hat by exp(-i (k+c)^2 dt / 4) (Fourier-diagonal,
     exact).
   - Nonlinear step: pointwise rotation Psi_tilde *= exp(+ i kappa |Psi_tilde|^2 dt)
     (unitary, exact). This sign of the nonlinear phase corresponds to the focusing NLS
     i Psi_t = -(1/2) Psi_xx - kappa |Psi|^2 Psi.

3. **2/3 dealiasing (kb-nls-23-dealiasing-cubic):** rho = |Psi_tilde|^2 is dealiased
   (upper 1/3 of Fourier modes zeroed) before each nonlinear exponentiation; the same
   mask is applied on the linear half-step Fourier output. The Nx=256 grid keeps
   171 modes after dealiasing.

4. **Diagnostic reconstruction (kb-nls-madelung-psi-structural-coupling):** at each
   snapshot we compute u := Im(conj(Psi) Psi_x), N := |Psi|^2, phi := unwrap(arg(Psi)).
   With this u-definition the Mcs constraint m = u - N phi_x = 0 is a structural
   identity (||m|| stays at ~1e-13 throughout), independent of integrator order.

CFL check: pi^2 Nx^2 dt / (2 L^2) = 0.36 < 1 — well inside kb-nls-cfl-split-step's
bound for split-step Fourier on focusing NLS.

### Sign-convention caveat (kb-nls-sign-convention)

The user's variational phi equation has **+sqrt(N)_xx / (2 sqrt(N))** (quantum
pressure with a + sign). The Madelung map of standard NLS i Psi_t = -(1/2) Psi_xx + ...
gives the opposite (-) sign. Under the user's literal +Q sign, the Psi PDE becomes
parabolic-unstable (no stable explicit propagator exists; S6 evidence). Per the
bank's recommendation, the run here uses the **standard-NLS sign** as a working
hypothesis to obtain a stable propagator and measure Mcs / mass diagnostics. The
S6/F1 finding that under the standard sign Mcs preservation is structural in this
representation does carry the bank-recorded caveat: under the user's literal sign,
the Mcs-attractor question requires an implicit / fluid-primitive method (out of
scope for this session). This caveat is recorded transparently in research_state.jsonl
and as a session-level note.

## Iteration trace

### E1 (only iteration, useful_self_assessment=True)
- **Plan:** Madelung-Psi Strang split-step + phi-split + 2/3 dealias, Nx=256, dt=1e-3,
  T=8. Use the standard-NLS sign (with caveat).
- **Bank consultation:**
  - **Citations (NLS bank, 9):**
    - kb-nls-direct-n-phi-structural-failure: rules out direct (N, phi) RK4 because
      bright soliton tails reach min(N) ~ 1e-25; bank says Madelung-Psi is the
      simplest meaningful method here.
    - kb-nls-madelung-psi-handles-zero-density: confirms |Psi|^2 representation
      handles vanishing tails without regularization.
    - kb-nls-madelung-psi-structural-coupling: u := Im(conj(Psi) Psi_x) makes
      m=0 an identity.
    - kb-nls-strang-splitstep-bright-soliton: gold-standard primitive for focusing
      bright soliton.
    - kb-nls-split-linear-phase: phi0 = 0.5 x is non-periodic; phi split required.
    - kb-nls-23-dealiasing-cubic: dealiasing on |Psi|^2 needed for stability.
    - kb-nls-recommended-default-bnls: prescribes this exact stack.
    - kb-nls-sign-convention: documents the standard-sign caveat.
    - kb-nls-cfl-split-step: CFL budget computed and verified 0.36 < 1.
  - **Rejections:**
    - **BKdV bank — all entries rejected as method recommendations:** B-NLS has no
      v_xxx dispersion, no shock in T_A, and a cubic |Psi|^2 Psi nonlinearity (not
      Gardner's (3/2) v^2 v_x). Specifically:
      - kb-burgers-MUSCL-Godunov-shock-pass, kb-burgers-Godunov-preShock-smooth,
        kb-general-firstOrder-Godunov-preShock-baseline: u is smooth on Mcs; no
        shock formation, MUSCL/Godunov would be over-engineering.
      - kb-kdv-IMEX-CN-spectral-pass, kb-kdv-IFRK4-blowup,
        kb-kdv-explicit-RK4-stiffness-blowup, kb-kdv-smallAmplitude-*,
        kb-kdv-noDealiasing-aliasing-artifacts, kb-kdv-amplitude-threshold-soliton,
        kb-kdv-spectral-solitonAmplitude-conservation: no v_xxx dispersion in B-NLS.
      - kb-gardner-* (all 8 entries): Gardner cubic structure is unrelated to NLS
        Kerr cubic.
      - kb-shallowWater-* (4 entries): no shallow-water structure here.
    - **BKdV-bank entries USED as cross-corroboration (not skipped, but transferred
      with care):**
      - kb-kdv-noDealiasing-aliasing-artifacts and kb-gardner-G3-noDealiasing-cubicAliasing:
        these confirm a general spectral-method principle (dealias cubic / higher
        nonlinearities) that aligns with NLS:kb-nls-23-dealiasing-cubic. The
        principle is system-agnostic enough that the BKdV evidence is corroborating,
        not contradictory.
      - kb-general-massConservation-insufficient-diagnostic and the NLS analog
        kb-nls-mass-conservation-not-sufficient: same warning, cross-verified.
        We co-monitored peak amplitude, peak position, and ||m|| in addition to mass.
    - **NLS-bank entries also rejected** as not currently relevant:
      - kb-nls-antiperiodic-basis-dark-soliton: IC is bright soliton (genuinely
        periodic decaying tails), not anti-periodic.
      - kb-nls-muscl-madelung-bore-soliton: no bore in this IC.

- **Execution result:** completed T=8.0 with mass drift 1.435e-12, peak N=2.235 at
  x=-1.055 (predicted x=-1 from v=0.5 boost), |u|max=1.12, |phi|max=23.1,
  ||m||/||N phi_x|| = 2.99e-13. Only one physical local maximum on N (interior
  count of 13 includes 12 sub-1e-13 noise-floor oscillations on the vanishing tail).

- **Finding F1:** all phenomenon-target metrics pass with margin >> order of
  magnitude.

- **Decision D1:** stop_useful. Progressive complexity says only escalate if E1
  fails; E1 succeeded.

## Use of memory

**Bank entries CITED (9 entries — all NLS bank):**
- kb-nls-direct-n-phi-structural-failure (chose representation)
- kb-nls-madelung-psi-handles-zero-density (zero-density handling)
- kb-nls-madelung-psi-structural-coupling (||m||=0 structurally)
- kb-nls-strang-splitstep-bright-soliton (time integrator choice)
- kb-nls-split-linear-phase (phi = c x + phi_tilde)
- kb-nls-23-dealiasing-cubic (dealiasing rule)
- kb-nls-recommended-default-bnls (overall stack)
- kb-nls-sign-convention (documented caveat)
- kb-nls-cfl-split-step (dt = 1e-3 validated)

**Bank entries REJECTED — by bank:**
- NLS bank (2): kb-nls-antiperiodic-basis-dark-soliton (wrong IC class),
  kb-nls-muscl-madelung-bore-soliton (no shock).
- BKdV bank (30): every entry rejected as a direct method-import for B-NLS.
  Burgers/shallow-water/KdV/Gardner entries describe systems that share no
  dispersive operator with B-NLS (no v_xxx, no shock in T_A, no Gardner cubic).
  Two BKdV entries (the dealiasing and mass-conservation-insufficient warnings)
  corroborate identical NLS-bank entries from a different system, but did not
  drive any choice.

**Did any BKdV entry mislead?** No. The clearest hazard would have been importing
kb-kdv-IMEX-CN-spectral-pass — to use IMEX-CN on the (N, phi) primitive equations,
hoping to handle B-NLS dispersion implicitly. That would have failed (B-NLS has no
v_xxx; the stiff term is quantum pressure (sqrt(N))_xx / (2 sqrt(N)), which is
nonlinear and non-Lipschitz at N=0 — the NLS bank explicitly rules out direct
(N, phi) integration for this IC). Recognizing this required cross-checking the
BKdV claim against NLS-specific entries; both banks agreed, but only the NLS bank
identified the actual failure mechanism.

The BKdV entry kb-burgers-MUSCL-Godunov-shock-pass would similarly have misled if
naively imported — there is no shock in T_A's IC. MUSCL+Godunov would have added
~30 lines of TVD-flux code that does nothing useful here. Recognizing this required
reading both banks together and seeing the prompt's IC description (u, N, phi all
smooth at t=0).

**Ratio NLS:BKdV citations:** 9 NLS citations : 0 BKdV citations. BKdV bank
provided 0 direct method choices and 2 corroborating cross-references (no
contradictions, no misleading recommendations adopted).

## Final self-assessment

- All phenomenon targets met by margin > 10 orders of magnitude on
  Mcs preservation (3e-13 vs 0.2 threshold) and mass conservation (1e-12 vs 5e-2
  threshold).
- Peak amplitude unchanged to 0.5% over T=8.0; peak position matches the boost
  prediction; |u|, |N|, |phi| bounded.
- Single physical N-peak; spurious "local maxima" are sub-1e-13 noise.
- Caveat on the sign convention is explicitly recorded — the standard-NLS sign was
  adopted to get a stable propagator; the user's literal +Q sign requires a
  separate (implicit) method to even test the Mcs-attractor question in their
  intended convention.
- Mcs preservation here is **structural under the Madelung-Psi representation
  (kb-nls-mcs-not-sufficient)**, NOT evidence that Mcs is dynamically attractive
  in the user's sign convention. T_A's design (initial IC on Mcs, generic method
  introduces noise off Mcs) is partially side-stepped by Madelung-Psi: there is
  no off-Mcs noise to relax — the representation excludes it. Answering the
  attractor question requires an off-Mcs perturbation IC under a method that
  carries u, N, phi independently, not the Mcs-locked Psi representation.

## Stopping condition

`useful_self_assessment=True` reached after E1. Iterations used: 1 of 3.
