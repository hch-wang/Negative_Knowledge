# T_C / NLS — reasoning

## Final method (E3)

**MUSCL-Godunov SSP-RK3 on u + Madelung-Psi Strang split-step on Psi_tilde + 2/3 dealiasing + phi-split** — the full validated S7 stack from `kb-nls-muscl-madelung-bore-soliton`.

Specifically:

- **u (Burgers velocity)**: finite-volume cell averages, van-Leer-limited MUSCL
  reconstruction at faces, Godunov flux for the inviscid Burgers flux
  `f(u) = u^2/2`. Time: SSP-RK3 (Shu-Osher) at `dt = 5e-4`.
- **Psi = sqrt(N) * exp(i * phi)**: spectral on Psi_tilde, with the boost split
  `Psi = exp(i * c * x) * Psi_tilde` (`c = phi_x = 0.6`) so Psi_tilde is
  periodic. Strang split-step:
  - Nonlinear half: `Psi <- exp(i * kappa * dealias(|Psi|^2) * dt/2) * Psi`
  - Linear full step in Fourier: multiply each `Psi_tilde_k` by
    `exp(-i * (k + c)^2 * dt / 2)`, then apply the 2/3 mask.
  - Nonlinear half again.
- **Sign convention**: standard NLS sign `i Psi_t = -(1/2) Psi_xx - kappa |Psi|^2 Psi`
  is adopted because under the user's literal `+(sqrt(N))_xx / (2 sqrt(N))` sign
  the Psi propagator is parabolic-unstable (`kb-nls-sign-convention`).
- **Outer coupling**: Strang-like composition over `dt`:
  `[u SSP-RK3 dt/2] - [Psi Strang dt] - [u SSP-RK3 dt/2]`.
- **2/3 dealiasing** applied on (a) the linear-step output `Psi_tilde_k` and
  (b) the `|Psi|^2` array before the cubic exponential.
- **Grid**: `Nx = 256`, `L = 30`, `dx = 0.117`, `T = 8`, 17 snapshots.

## Iteration trace

### E1 — simplest meaningful baseline (executed)

Spectral RK4 on the m-equation `m_t + (u*m)_x + m*u_x = 0` + Madelung-Psi Strang on
Psi_tilde + phi-split. No MUSCL, no dealiasing. `dt = 1e-3`.

Result: ran to T=8 without blow-up; soliton intact (peak 0.999, speed 0.60); mass
exact. **Failure mode**: spectral on u Gibbs-rings the bore — `u` oscillates between
-0.19 and 1.32 with `TV(u) = 23.9` (vs initial 1.0); spectral high-1/3 energy ratio
0.006 (>> 1e-4 ringing flag from `kb-nls-mass-conservation-not-sufficient`).
`||m||_2` essentially flat (3.59 → 3.61, slight non-monotone wiggle) — the
ringing dominates over the physical compound-soliton attractor signal.

This precisely matches the failure mode flagged in `kb-nls-muscl-madelung-bore-soliton`:
"spectral on u Gibbs-rings the bore".

### E2 — single-component escalation: MUSCL on u

Replace spectral on u with MUSCL-Godunov SSP-RK3 (Burgers flux `u^2/2`, van-Leer
limiter). Keep Madelung-Psi Strang on Psi_tilde, still no dealiasing. `dt = 5e-4`.

Result: u stays clean monotone in [0, 1] with `TV(u) = 2.0`. Mass to 2e-6. Soliton
intact (peak 0.999, speed 0.60, x = -8.03 → -3.22 over T=8).
**`||m||_2` monotonically DECREASES 3.58 → 3.42 (-4.5%)** — the compound-soliton
attractor signature finally emerges once spectral noise is removed. u high-1/3 ratio
1.4e-4 (borderline at the bank's empirical 1e-4 flag).

Phenomenon target met. Marked `useful_self_assessment = True` but chose to do one
final escalation to tighten confidence.

### E3 — single-component escalation: add 2/3 dealiasing

E2 + 2/3 dealias mask on the linear half-step Psi_tilde and on `|Psi|^2` before the
cubic exponential. All other components unchanged.

Result: nominally identical macroscopic quantities to E2 (mass 1.999998, `||m||_2`
monotone 3.58 → 3.42, soliton peak 0.999 at x=-3.22), but spectral cleanliness
greatly improved — N high-1/3 ratio drops from 2.4e-9 to 3.4e-11 (70x), NLS energy
E = 0.0267 conserved to 4-digit precision across all 17 snapshots. This is the
predicted behaviour from `kb-nls-23-dealiasing-cubic`: with dealiasing, no MI cascade
is admitted by the cubic-focusing nonlinearity.

Stop with E3.

## Use of memory

Bank entries cited at experiment-proposal time:

| Bank entry | Role |
|---|---|
| `kb-nls-direct-n-phi-structural-failure` | Ruled out direct (N, phi) integration as E1 candidate — drove E1 to start at Madelung-Psi |
| `kb-nls-madelung-psi-structural-coupling` | Justified using Psi as primary state variable |
| `kb-nls-madelung-psi-handles-zero-density` | Confirmed Madelung-Psi handles soliton tails (N -> 1e-9) without regularization |
| `kb-nls-strang-splitstep-bright-soliton` | Strang split-step chosen as the Psi propagator (gold-standard for focusing NLS) |
| `kb-nls-split-linear-phase` | REQUIRED. Used `Psi = exp(i * 0.6 * x) * Psi_tilde` split throughout — without it spectral derivatives of `phi_0 = 0.6*x` would Gibbs-ring at the box edges |
| `kb-nls-sign-convention` | Adopted standard NLS sign (-(1/2) Psi_xx) as a hypothesis; user has acknowledged the +sign is parabolic-unstable so standard sign is the working choice |
| `kb-nls-mass-conservation-not-sufficient` / `kb-nls-mcs-not-sufficient` | Drove co-monitoring of energy, spectral tails, peak position — not just mass and `||m||` |
| `kb-nls-muscl-madelung-bore-soliton` | Direct match for THIS IC. Selected as the E2 / E3 target. S7 cross-validated the exact same setup at T=8 with similar diagnostics. |
| `kb-nls-23-dealiasing-cubic` | Drove E3's single-component upgrade. Required for clean spectral tails on the cubic source |
| `kb-nls-cfl-split-step` | Set `dt = 5e-4` on Nx=256, L=30 — within the bank's CFL prescription |
| `kb-nls-energy-drift-vs-mass-drift` | Drove adding NLS energy as a co-monitor at E3 |

Bank entries explicitly rejected at E1:
- `kb-nls-muscl-madelung-bore-soliton` rejected at E1 — too complex for the simplest-baseline rule; deferred to E2.
- `kb-nls-23-dealiasing-cubic` rejected at E1 and E2 — single-component escalation, only added at E3.

The bank was used strictly for **escalation direction** (which single component to upgrade next), not for skipping straight to the validated complex stack. Progressive-complexity discipline preserved.

## Final self-assessment

**Pass.** All phenomenon targets met:

- N peak at T=8: **0.999 >> 0.3** (required)
- |u_max| at T=8: **1.000 << 5** (required)
- Bore stable: monotone in [0, 1], TV = 2.0
- Compound-soliton attractor bonus: **||m||_2 monotonically DECREASES** 3.5819 → 3.4200 (-4.52%) over T=8

Physical interpretation: the bright soliton survives intact during the approach phase
(centered at x=-3.22 at T=8) while the bore stays stationary near x=0. The
collision proper (peak overlap) is at t ~ 13 — beyond the requested T=8 window —
but the **leading edge of the soliton has already entered the bore region**
(soliton tail extends ~3 units, so by T=8 the front edge is at x~0). The
monotone decrease of `||m||_2` toward the Mcs surface during this approach phase
is exactly the BKdV T_C analog phenomenology, recovered with NLS-Madelung
dispersion in place of KdV linear dispersion.

**Caveats** (for downstream consumers):

- The sign-convention transfer from standard NLS (`-(1/2) Psi_xx`) to the user's
  literal variational `+(sqrt(N))_xx / (2 sqrt(N))` is a HYPOTHESIS per
  `kb-nls-sign-convention`. To re-verify under the user's literal sign would
  require implicit time stepping on Psi — not attempted in this session.
- `||m||_2 ~ machine_precision` is NOT a sufficient certificate of solution
  correctness (`kb-nls-mcs-not-sufficient`); here `||m||_2 ~ 3.5` because the
  IC is generically off-Mcs, and the decrease is the meaningful signal.
- The collision proper happens at t ~ 13, beyond the requested T=8.
  Within the requested window, the experiment captures only the approach phase.

## Files

- `candidate.py` — E3 final solver
- `pred_results/T_C.npy` — shape `(17, 3, 256)`, channels (u, N, phi=full phase)
- `E1_diag.json`, `E2_diag.json`, `E3_diag.json` — per-iteration scalar diagnostics
- `research_state.jsonl` — append-only research-graph (Q, 3xE, 3xF, 3xD)
- `session_log.md` — chronological log
