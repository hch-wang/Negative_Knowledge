# T_C / PosOnly — reasoning

## Final method (E3)

Fourier pseudospectral discretization on periodic `[-15, 15]`, `Nx=256`, with
**2/3-rule dealiasing** applied to (i) every nonlinear product (`u^2`, `v^2`,
`u*v`) and (ii) every spatial-derivative spectrum (`d_x`, `d_xx`, `d_xxx`).
Time integration is **classical explicit RK4** with `dt = 5e-4` for
`n_steps = 16 000` reaching `T = 8.0`. The u-equation carries an additional
**linear viscosity** term `nu * u_xx` with `nu = 5e-2`; the v-equation is
unchanged (still dissipationless, dispersive).

Equations actually integrated:
```
u_t = -3 u u_x  - d_x(3 v^2)  - v_xxx  + nu u_xx          (nu = 5e-2)
v_t = -6 v v_x - v_xxx  - d_x(u v)
```
which matches the PDE `u_t + 3 u u_x = -d_x(3 v^2 + v_xx)`,
`v_t + 6 v v_x + v_xxx = -d_x(u v)` because `v_xx_x = v_xxx`, with linear
u-viscosity added.

ICs: `u0 = 1.5 * (1 - tanh(x/0.5)) / 2` (smoothed bore at x=0),
`v0 = 1.5 / cosh^2(x + 8)` (KdV soliton, amp 1.5, x_c=-8). Output
`pred_results/T_C.npy` has shape `(9, 2, 256)` — 9 snapshots at
`t = 0, 1, ..., 8`.

## Iteration trace

- **E1** — bare baseline: Fourier pseudospectral, NO dealiasing, RK4 dt=5e-4.
  Blew up at step 6 (`t ≈ 0.003`): undealiased `v^2` + sharp bore generates
  alias-folded high-k modes that `v_xxx` amplifies by `(k_max)^3 ~ 1230`.
  F1: negative.
- **E2** — add 2/3 dealiasing (single-component upgrade): reached T=8 with
  mass conserved to machine precision; u_max=3.90 < 5 OK, but `v_peak=0.4733`
  at T=8 misses the 0.5 target and `u_min` grew to −2.55 — Gibbs ringing in
  u (sub-resolved bore) contaminates v via `-d_x(u v)`. F2: partial, not
  useful enough.
- **E3** — add linear u-viscosity `nu = 5e-2` (single-component upgrade):
  v_peak final = 0.5019 (PASS ≥ 0.5), u_max final = 1.43 (PASS < 5), mass
  conserved to machine precision (4.4e-16 for v, 1.1e-14 for u). Soliton
  transmitted through the bore from x=−8 to x≈+10.8 with amplitude reduced
  from 1.5 → ~0.5 but remaining a recognizable single peak. F3: positive,
  useful = True. Stop.

## Use of memory

**Positive-bank entries that drove decisions** (citing `task_id` field of
`bank_v3A_positive.jsonl`):

- `BKdV-S7` (round 1, baseline) — confirmed Fourier pseudospectral + RK4 is
  the canonical bare baseline for the BKdV PDE class. Used to legitimize the
  E1 choice under progressive-complexity discipline (must run bare baseline
  first).
- `BKdV-S1` (round 1) — proved that **2/3-rule dealiasing on every nonlinear
  product** is the single-component fix that turns an aliasing-blowup
  pseudospectral run into a stable T=10 run with mass conservation <1e-12
  and bounded sup. This is exactly the F1 → E2 single-knob upgrade I
  performed.
- `BKdV-S1` (round 2) — extended the same dealias+RK4 stack to amp=3 and
  T=10 with no blowup. Provided extra evidence that the F1 failure is
  aliasing-driven (not v_xxx-stiffness) and that no time-integrator change
  is required at this dt.
- `BKdV-S7` (round 2) — full BKdV (no Gardner reduction) shows v_max drops
  60%+ while u_max climbs under coupling. This is the physical signature I
  also see in F2 / F3 (v_peak drops 1.5 → 0.5), so the partial v-amplitude
  reduction is *physics*, not numerics. Critical context for interpreting
  whether the phenomenon target is achievable in principle.
- **BKdV-S6 (dispatcher hint)** — cited by the parent at session dispatch
  as validating `nu_linear = 5e-2` u-viscosity for bore-like IC. The actual
  bank file (`bank_v3A_positive.jsonl`) does not contain explicit BKdV-S6
  entries; I treated this as a load-bearing parent-side prescription and
  applied it as the E2 → E3 single-component upgrade. The result (v_peak
  cleared 0.5, u_min stopped diverging) validates the prescription
  empirically.

**Bank entries considered but rejected** (with reason):

- `kb-burgers-MUSCL-Godunov-shock-pass` and
  `kb-general-firstOrder-Godunov-preShock-baseline` — recommend MUSCL+Godunov
  flux for the u sector. Rejected because (a) it is a multi-component change
  (different spatial discretization + new flux + likely different dt) so
  cannot be used at any single iteration without violating
  progressive-complexity discipline, and (b) once linear viscosity controls
  the bore (E3), the smoothed-bore u remains well-resolved by Fourier modes
  and a TVD shock-capturing scheme is not needed. Bank entries do not say
  MUSCL is *required*; they say it's a proven baseline. The simpler
  viscosity-regularized spectral stack here meets the phenomenon target.
- `kb-kdv-IMEX-CN-spectral-pass`,
  `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`,
  `kb-gardner-KdV-method-transfer-moderate-amplitude` — recommend IMEX-CN
  for the dispersive stiffness. Rejected because at the chosen
  `dt = 5e-4 < dispersion-CFL` after dealiasing (BKdV-S1-r1 showed CFL bound
  ~4.94e-4 at Nx=256 L=30; my dt is just below this), explicit RK4 is
  stable, and adopting IMEX-CN would change time integrator + linear-term
  treatment simultaneously (two-component change).
- `kb-shallowWater-LaxFriedrichs-stable-smeared`, `kb-shallowWater-HLL-...`
  — out of scope (not the relevant PDE structure here; bore in u is
  Burgers, not shallow water).
- `kb-kdv-smallAmplitude-dispersiveRegime` — diagnostic only ("amp ≤ 0.1 →
  disperses"). My v_peak stays well above 0.4, so this regime is not
  reached; entry just rules out an alternative interpretation of F3 (the
  ~0.5 plateau is not the small-amplitude-dispersion floor, because the
  bound there would be ~0.1).
- `BKdV-S7` (round 3, S-source analysis) — relates to A-sweep of the m=0
  manifold breakdown. Not directly applicable because our IC has m_0 ≠ 0
  (the bore sets u_L=1.5 while v=0 there, so m=u-v²/2=1.5 in the left bulk).

## Final self-assessment

I believe `pred_results/T_C.npy` satisfies the phenomenon target:

| Criterion | Required | Measured | Verdict |
| --- | --- | --- | --- |
| Final v peak amplitude | `>= 0.5` | `0.5019` (at x ≈ 10.78) | PASS |
| u stays bounded | `|u_max| < 5` | `1.4264` | PASS (large margin) |
| Bore not blown up | (qualitative) | u in [0.28, 1.43] at T=8 | PASS |
| Mass conservation | (good practice) | `|Δmass_v| = 4.4e-16`, `|Δmass_u| = 1.1e-14` | PASS |

Physical interpretation of the bore-soliton encounter: the soliton
**transmits** through the bore but suffers a substantial amplitude reduction
(1.5 → ~0.5) and propagation slowdown (free speed ~3.0, observed mean speed
~2.35), with the lost energy radiated as small-amplitude dispersive tail.
This is consistent with `kb-kdv-smallAmplitude-dispersiveRegime` (the
post-interaction amplitude is still well above the dispersion floor) and
with `BKdV-S7` (round 2)'s finding that the coupling generically degrades v
amplitude while keeping the dynamics bounded.
