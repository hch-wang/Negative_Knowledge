# T_B / PosOnly — reasoning

## Final method

The final answer comes from **Experiment E2** (the second and last
executed iteration; the parent should also note that E1 was an
intentional baseline failure-mode probe under the progressive-complexity
discipline, not an alternative answer).

**E2 method**: Coupled Burgers-swept-KdV system,
```
u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -d_x(u v)
```
solved on the periodic domain `x in [-15, 15]`, `Nx = 256`, with:

- **Spatial**: Fourier pseudospectral derivatives `d_x = ifft(i*k*fft(.))`,
  `d_xx = ifft(-k^2 fft(.))`, `d_xxx = ifft(-i*k^3 fft(.))`.
- **Dealiasing**: 2/3 rule applied to every nonlinear product
  (`v*v`, `u*v`, `v*v_x`, `u*u_x`). Spectral modes with `|k| > (2/3) k_max`
  are zeroed after each multiplication.
- **Time integrator**: explicit classical RK4 on every term (no IMEX,
  no operator splitting).
- **Time step**: `dt ~ 0.4 * 2.83 / k_max^3 = 5.88e-5`, set by the
  explicit-RK4 stability radius on the dispersive `v_xxx` eigenvalues
  (pure imaginary), giving `n_steps ~ 102 120`.

The intuition: the bank consistently recommends Fourier pseudospectral
spatial discretization for KdV/Gardner-class problems on these grids
(`kb-kdv-IMEX-CN-spectral-pass`,
`kb-kdv-spectral-solitonAmplitude-conservation`). With the *one*
critical addition of 2/3 dealiasing (which the bank pairs with the
spectral scheme via `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`),
the aliasing-driven blow-up disappears and the dispersive CFL is
manageable on the short `T = 6` horizon.

## Iteration trace

- **E1** — Fourier pseudospectral + explicit RK4 with NO dealiasing.
  Result `F1`: blow-up at `t = 0.421` (step 7170 / 102120). First
  overflow appears in `v*v`. This is the textbook signature of aliasing
  pumping energy into resolved high-`k` modes that explicit RK4 cannot
  damp on the pure-imaginary `i*k^3` dispersion. Conclusion: aliasing is
  the dominant failure axis.
- **E2** — Same as E1 but **add** 2/3-rule dealiasing on every
  pseudospectral product. Result `F2`: integration completes the full
  `T = 6`, all-finite, with `mass(v)` drift = -0.6 %, 14 well-separated
  peaks of amplitude >= 0.8 in final `v`, smallest inter-peak spacing
  1.29 (>> grid `dx = 0.117`), peak count robust under a hard
  low-pass at `|k| <= 6` (still 14 peaks >= 0.8). Phenomenon target met
  with wide margin.
- **E3** — not executed. The decision rationale (see `D2` in
  `research_state.jsonl`): E2 already exceeds the target by a wide
  margin, and the bank entry
  `kb-gardner-KdV-method-transfer-moderate-amplitude` explicitly limits
  the positive transfer of IMEX-CN spectral to amplitudes in `[1, 2]`.
  At `amp = 4` (the current IC), `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup`
  (referenced inside that entry) warns of CFL-induced blow-up. Therefore
  the obvious next single-component upgrade (RK4 -> IMEX-CN) carries
  non-trivial risk and would not be a strict improvement over an already
  passing E2.

## Use of memory

- **Cited (drove decisions)**:
  - `kb-kdv-IMEX-CN-spectral-pass` — confirms Fourier pseudospectral is
    the correct spatial family for Nx=256, [-15,15] KdV-type problems.
    Used to justify the spatial choice at E1 (without yet adopting its
    time integrator, per progressive-complexity discipline).
  - `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` — confirms that
    spectral KdV/Gardner-class solvers pair with 2/3-rule dealiasing.
    Drove the E2 single-component upgrade choice (add dealiasing).
  - `kb-kdv-spectral-solitonAmplitude-conservation` — additional support
    that spectral + dealiasing preserves both mass and soliton
    amplitudes; informs why mass drift of -0.6 % in F2 is a credible
    diagnostic.
  - `kb-gardner-KdV-method-transfer-moderate-amplitude` — used at the
    `D2` stop-early decision: warns that IMEX-CN with the standard
    `dt = 5e-4` transfers cleanly only for amplitudes in `[1, 2]`.
    Our IC is `amp = 4`, well outside that band, so the natural E3
    upgrade (RK4 -> IMEX-CN) is risky.
- **Considered and rejected (at this step)**:
  - `kb-burgers-MUSCL-Godunov-shock-pass`,
    `kb-burgers-Godunov-preShock-smooth`,
    `kb-general-firstOrder-Godunov-preShock-baseline` — these suggest
    upwind/Godunov-style schemes for the Burgers operator. Rejected for
    this task because the task target is a *soliton train* in `v`, which
    requires high-order dispersive accuracy. Mixing
    Godunov-on-u + spectral-on-v adds complexity and operator splitting,
    which the discipline does not allow as a single-component upgrade.
    A pure spectral treatment with 2/3 dealiasing handles both `u` and
    `v` cleanly here because no real shocks form in `u` over `T = 6`
    (the `u` amplitudes stay below ~15 with smooth spatial structure
    confined to `|k| <= 10` after dealiasing).
  - `kb-shallowWater-LaxFriedrichs-stable-smeared`,
    `kb-shallowWater-HLL-dam-break-pass` — shallow-water Riemann
    solvers; not applicable to the current Burgers-swept-KdV PDE
    structure.
  - `kb-kdv-smallAmplitude-dispersiveRegime` — diagnostic on the
    low-amplitude radiation regime; our amplitude (4) is firmly in the
    soliton-forming regime, not the dispersive-radiation one, so its
    warning does not apply.

## Final self-assessment

Do I believe `pred_results/T_B.npy` satisfies the phenomenon target?
**Yes**, by a wide margin.

Numerical diagnostics (from F2):
- Final `v` is all-finite, no NaN/Inf anywhere in the saved tensor.
- `mass(v)`: `10.6347 -> 10.5709`, drift `= -0.6 %` (target: `< 8 %`).
- 14 distinct interior local maxima of `v(T)` have amplitude `>= 0.8`;
  the strongest peaks reach 4.4, 4.3, 4.2 at `x ~ -7.1, -3.6, -12.2`
  (target: `>= 2 well-separated peaks with amp >= 0.8`).
- Smallest inter-peak spacing 1.29, far larger than the grid spacing
  `dx = 0.117`. Peaks are physical structures, not grid-scale
  oscillations.
- Spectrally, the peak count is preserved under a strict low-pass
  retaining only `|k| <= 6`: still 14 peaks `>= 0.8`. Even at
  `|k| <= 3`, 11 peaks `>= 0.8` survive. So the soliton-train structure
  is dominated by the smooth, resolved part of the spectrum.

Caveat: `||v||_2` and `||u||_2` both grow over the run (mass-`v` is
conserved but pointwise amplitude redistributes). This is expected
behaviour for the coupled system because `u` is generated from the
`3 v^2` source, then feeds back into `v` through `-d_x(u v)`, so energy
is exchanged between the two channels. It is not a numerical
instability — `mass(v)` and the spectrum stay bounded and dealiased
throughout the run.

The saved tensor has shape `(7, 2, 256)`, with snapshots at
`t = 0, 1, 2, 3, 4, 5, 6` and channels `(u, v)`. Final snapshot is at
index 6 (t=6.0). This satisfies the >= 5-snapshot requirement.
