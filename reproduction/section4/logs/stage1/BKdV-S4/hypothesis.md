## Program research question
How sensitive is BKdV long-time behavior to numerical resolution (dt, Nx,
hyperviscosity coefficient ν_h)? Is there a regime where doubling resolution
changes the qualitative answer (vs only quantitative)?

## Key findings

- **F-Nx (E2c):** Spatial resolution is QUALITATIVELY SENSITIVE — doubling
  Nx from 256 to 512 (with ν_h and dt rescaled to keep the solver stable)
  changes every diagnostic by far more than 5 %. End-state energy halves
  (3.55 → 1.74), m_l2 drops by a third (2.46 → 1.65), lock-correlation
  more than doubles (0.20 → 0.48). The E1 baseline at Nx=256 is NOT in the
  converged regime; its quantitative end-state values are numerical
  artifacts of under-resolution.

- **F-νh-weak (E3b):** Hyperviscosity is ROBUST in the weak direction. At
  Nx=256, dropping ν_h by 4 orders of magnitude (1e-22 → 1e-26) shifts 7 of
  10 diagnostics by < 5 % (most under 2 %); the largest shifts (m_inf and
  u_peak at −11.7 %) reflect a slightly sharper front in the no-HV limit.
  At Nx=256 the spectral truncation IS the regularization — ν_h is doing
  essentially no extra work.

- **F-νh-strong (E3c):** Hyperviscosity is QUALITATIVELY SENSITIVE in the
  strong direction. Strengthening ν_h by 10⁴ × (1e-22 → 1e-18, with dt
  reduced to 1e-5 for stability) drops energy by 71 %, m_l2 by 51 %,
  u_peak by 76 %, eh_u by 97 %, and more than TRIPLES the lock-correlation
  (0.20 → 0.75). Strong HV is no longer "regularization"; it actively
  reshapes the basin attractor toward a smooth low-amplitude locked state.
  Any claim relying on ν_h being "small enough to be numerical only" must
  be cross-checked against this finding.

- **F-dt (E3d):** dt is the LEAST sensitive of the three numerical
  parameters at baseline. Halving dt at (Nx=256, ν_h=1e-22) shifts 7 of 10
  diagnostics under 5 %, energy by 6.6 %, eh_u by 13.2 %; no qualitative
  conclusion changes. As the prompt anticipated, dt=5e-4 is near the
  converged regime; the prompt's "trivial" flag is mostly vindicated.

- **F-stack-coupling (E2a/E2b/E3a):** The pre-validated solver stack has
  TWO numerical co-constraints that the prompt's "vary one parameter"
  framing did not account for:
  1. Explicit-RK4 hyperviscous stability: dt ≲ 2/(ν_h k_max^16). Violated
     at (Nx=512, ν_h=1e-22) and at (Nx=256, ν_h=1e-18).
  2. u-equation dispersion CFL through the −ik · v_xx coupling: dt ≲
     2.83/k_max^3. Violated at (Nx=512, dt=5e-4) even after HV rescaling.
  Consequence: "double Nx" or "strengthen ν_h" cannot be one-parameter
  changes — they FORCE dt down too. Naive one-parameter changes BLEW UP at
  steps 4-193 in three separate sub-runs.

## Ruled-out routes / paths shown not to work

- **"Just double Nx" (E2a):** keeping (dt=5e-4, ν_h=1e-22) and only
  doubling the grid violates the explicit-HV stability bound by 10⁵ × ;
  NaN at step 4 (t=0.002). Cannot be a one-parameter change.

- **"Double Nx with HV rescaled to preserve ν_h k_max^16" (E2b):** restores
  the HV bound but exposes a second stability constraint — the explicit
  v_xx → u_t coupling needs dt ≲ 2.83/k_max^3 ≈ 1.8e-5 at Nx=512. dt=5e-4
  violates by 30 ×, blow-up at t=0.097.

- **"Strengthen HV at fixed dt" (E3a):** same stability mechanism as E2a;
  ν_h ↑ 10⁴ × at dt=5e-4 blows up at step 6. The ν_h direction is
  symmetrically coupled to dt through the explicit-HV bound.

- **"E1 Nx=256 baseline as a converged answer":** ruled out by E2c — the
  end-state shifts massively when going to Nx=512, so any downstream BKdV
  conclusion about E1's lock=0.20, energy=3.55, m_l2=2.46 must be treated
  as a (possibly large) numerical artifact, not as physics.

## Trivial-finding flag

- **F3a (is_trivial=true):** ν_h=1e-18 + dt=5e-4 blow-up is a TRIVIAL re-
  finding — same explicit-HV stability mechanism documented in F2 (E2a),
  same blow-up at a different (Nx, ν_h, dt) corner. No new information
  about BKdV physics or sensitivity; only re-confirms the stack's stability
  bound. Closes off "naive one-parameter ν_h change" as an experimental
  route.

- **F3d (is_trivial=true, partial):** dt 5e-4 → 1e-4 at baseline is the
  prompt-anticipated "dt is already near converged" trivial finding. Most
  diagnostics shift < 5 %, no qualitative change. Mildly-non-trivial caveat:
  the spectral-tail eh_u shifts by +13.2 %, so a strict 5 % threshold fails
  on one diagnostic — but no qualitative conclusion moves. The trivial
  framing is vindicated for the bulk of diagnostics.

## Recommendation for downstream Stage-2 tasks
Nx=256 is sub-converged for this IC and T=10; use Nx≥512 with rescaled ν_h≤1.5e-27 and dt≤1e-4. Treat any E1-scale quantitative claim (lock, energy, m_l2) as upper-bound only. ν_h must be ≤ 1e-22 (preferably 1e-26) to avoid actively reshaping physics.
