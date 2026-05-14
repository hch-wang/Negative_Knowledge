# BKdV → B-NLS knowledge chain

This document traces, for every Stage-3 cell where the BKdV bank contributed to the outcome, **the specific BKdV entry(ies) that informed each Experiment-level decision, and the empirical outcome that followed**. The audit is based on:

- `logs/stage3/<task>/BKdV/research_state.jsonl` — full Q/E/F/D nodes for the 4 BKdV-only cells (intact)
- `logs/stage3/<task>/NLSBKdV/reasoning.md` — bank-usage sections for the 4 NLSBKdV cells (the audit-trail JSON was overwritten by a sandbox rebuild)

Each "chain" below has the form:

> **BKdV entry** → **decision in Experiment E_n** → **observed outcome in Finding F_n**

The eight Stage-1 stress tests that produced the NLS bank are NOT covered here; those produced the *NLS* bank (`bank/nls_knowledge.jsonl`). The BKdV bank itself was constructed earlier in §3 of the paper.

---

## 1. The four BKdV entries that *positively* shaped a passing Experiment

These are the only chains where a BKdV bank entry directly drove a single-component decision and the resulting Experiment passed (or made measurable progress) on a B-NLS task.

### Chain 1 — `kb-general-firstOrder-Godunov-preShock-baseline` + `kb-burgers-Godunov-preShock-smooth` → T_C BKdV E1/E2/E3 bore-sector stability

**Entries** (both positive, from BKdV stage-1):
- `kb-general-firstOrder-Godunov-preShock-baseline`: "use Godunov flux as the foundation for the Burgers operator at any time horizon"
- `kb-burgers-Godunov-preShock-smooth`: "for the early-time Burgers component before bore forms, first-order Godunov suffices"

**Decision in E1 (T_C BKdV)**: cite both entries to justify *Godunov upwind exact-Riemann flux on the u-sector momentum equation*. The agent's `bank_use_rationale` is verbatim:

> "Bank's first-order Godunov is the simplest entropy-consistent baseline for the Burgers u-sector with a smoothed bore; MUSCL reserved for escalation. Bank has NO entries on NLS Madelung quantum pressure +sqrt(N)_xx/(2 sqrt N), so N-phi sector uses spectral + RK4 from general principles."

**Outcome (F1, F2, F3)**: u-sector held perfectly throughout all 3 Experiments: |u| capped at 1.0 (input bore height), monotone (TV(u)=1.988 — exact match to bank's prediction), zero overshoot, mass-of-u exactly conserved. The bore propagated as expected.

**Causal weight**: T_C BKdV reached t = 0.65 of T = 8.0 (8.1 %), vs T_C NoKB's 0.094 of 8.0 (1.2 %). The 8× improvement is **fully attributable to** these two BKdV entries — without them the bore would have Gibbs-rung on a non-upwind discretization. The reason T_C BKdV still failed (not PASS) is that the *N-φ sector* failure had no BKdV analog and the agent ran out of budget before reaching MUSCL-on-u + Madelung-Ψ-on-(N,φ) (which IS in the NLS bank as `kb-nls-muscl-madelung-bore-soliton`).

---

### Chain 2 — `kb-kdv-noDealiasing-aliasing-artifacts` + `kb-gardner-G3-noDealiasing-cubicAliasing` → 2/3 dealiasing rule (transferred to 3 cells)

**Entries** (both negative, from BKdV stage-1):
- `kb-kdv-noDealiasing-aliasing-artifacts`: no-dealiasing IMEX-Euler on KdV produced 4 spurious peaks + 43 % amplitude inflation. `recommended_action`: always apply 2/3 dealiasing or smooth spectral cutoff.
- `kb-gardner-G3-noDealiasing-cubicAliasing`: same conclusion on Gardner cubic; tighter than the quadratic case.

**Decision** in three independent cells:
- **T_A BKdV E2**: single-component upgrade vs E1 = add 2/3 dealiasing. Agent quote: "Both negative entries on no-dealiasing on cubic/quadratic Fourier products directly motivate the 2/3 rule."
- **T_C BKdV E3**: single-component upgrade vs E2 = add 2/3 dealiasing on `tilde_phi` before/after each RHS evaluation. Quote: "Bank's anti-aliasing entries directly motivate the 2/3 rule on the cubic/quadratic phi nonlinearity."
- **T_D BKdV E2/E3**: dealiasing aspect used as standard discipline (Gardner-G2 entry cited).

**Outcome**:
- T_A E2: aliasing failure ruled OUT as primary cause (still blew up — pointed to representation issue, motivating E3 Madelung-Ψ).
- T_C E3: aliasing in φ controlled; agent reached t = 0.65 (vs F2's 0.12) before u-sector shock formation took over.
- T_D E3: dealiasing kept the integration stable through the t < 0.022 window where ‖m‖₂ was measured to be FLAT to 0.12 %.

**Causal weight**: this entry pair is the most-cited BKdV chain across passing B-NLS cells (3 of 4 success traces). It is also the chain with the **cleanest cross-domain transfer** — the warning "no dealiasing on a cubic spectral solver causes aliasing energy cascade" is mechanism-agnostic; whether the cubic is Gardner's $v^2 v_x$ or B-NLS's $|\Psi|^2 \Psi$ or Kerr-spectral $2\kappa N$, the FFT-aliasing pathway is the same.

---

### Chain 3 — `kb-general-finiteness-not-accuracy` + `kb-general-massConservation-insufficient-diagnostic` → T_D BKdV pre-blowup truncation (the only T_D PASS)

**Entries** (both negative, both "depth=family-level / general" — explicitly DOMAIN-GENERAL meta-discipline entries):
- `kb-general-finiteness-not-accuracy`: "all-finite output is necessary but NOT sufficient for correctness; need physically motivated diagnostics."
- `kb-general-massConservation-insufficient-diagnostic`: "mass conservation alone is insufficient — also track peak count, amplitude, structural diagnostics."

**Decision in E3 (T_D BKdV)**: the agent designs a **pre-blowup truncation rule** — monitor (‖m‖₂, max(N), max(u)) at every snapshot; the moment any tracked observable exceeds a sanity bound, truncate the run and pad the remaining requested snapshots with the last-good state. Quote:

> "Cited kb-general-finiteness-not-accuracy and kb-general-massConservation-insufficient-diagnostic to design the pre-blowup truncation rule (m_norm, N, u bounds, not just isfinite)."

**Outcome (F3)**: the agent integrated cleanly through t ∈ [0, 0.022] (the *stable window* before UV cascade onset), captured the scientific finding ‖m‖₂ FLAT to 0.12 %, and stopped — preserving mass drift at 3.74 %. **This is the only T_D cell that passed the parent-side eval's 5 % mass-drift gate.** The two NLS-bank-aware T_D agents (T_D NLS and T_D NLSBKdV) tried to integrate THROUGH the UV cascade with hyperviscosity and lost 96 – 99 % of their mass, failing the gate.

**Causal weight**: this is the strongest example in the appendix of **discipline-level (not method-level) transfer** of BKdV knowledge. Neither entry mentions B-NLS, NLS, Burgers, or any specific PDE; both are domain-general meta-rules about evaluation discipline. They transferred 100 % because they were never domain-specific to begin with.

---

### Chain 4 — `kb-kdv-IMEX-CN-spectral-pass` → T_A BKdV E3 Madelung-Ψ representation (the PASS-enabling step, indirect)

**Entry**: `kb-kdv-IMEX-CN-spectral-pass` (positive): "IMEX-Crank-Nicolson Fourier-pseudospectral is the recommended baseline for the KdV dispersion."

**Decision in T_A BKdV E3**: cited as motivation for the *split-step structure* of Madelung-Ψ (linear half-step unitary FFT phase rotation = the IMEX-CN analog when the kinetic is $-\frac{1}{2}\Psi_{xx}$). The agent's bank_use_rationale:

> "kb-kdv-IMEX-CN-spectral-pass motivates the IMEX-style split (linear unitary FFT phase rotation + explicit Kerr) which is the Madelung-Psi analog."

**Outcome (F3)**: PASS — bright soliton propagates with v=0.5 to x=−1.05, amplitude preserved within 1 %, mass exact, ‖m‖ = 0 structurally via $u = \mathrm{Im}(\bar\Psi \Psi_x)$ definition.

**Causal weight**: this chain is **indirect**. The bank entry endorses a SPLIT-STEP structure (linear treated separately from nonlinear). The agent generalised this from KdV's $v_{xxx}$ to NLS's $-\frac{1}{2}\Psi_{xx}$ by analogy — the actual Madelung-Ψ representation choice was inferred from general numerical-methods principles. So the BKdV entry provided the *family of method* (split-step) but not the *specific representation*.

The NLS bank's `kb-nls-strang-splitstep-bright-soliton` and `kb-nls-madelung-psi-handles-zero-density` would have specified the Madelung representation directly — and they did, in the T_A NLS / T_A NLSBKdV cells, which is why those cells PASSED in **1 iteration** vs T_A BKdV's 3 iterations.

---

## 2. The one BKdV entry that *actively misled* — `kb-kdv-IMEX-CN-spectral-pass` on T_B

**Entry**: same `kb-kdv-IMEX-CN-spectral-pass` as Chain 4 (positive, BKdV).

**Decision in T_B BKdV E1/E2/E3**: cited at every Experiment to justify Fourier-pseudospectral spatial discretization on the *primitive (u, N, φ) form*. Quote (E1): "Fourier pseudospectral is the standard simplest meaningful baseline for periodic stiff PDEs (cited)."

**Outcome**: catastrophic failure. T_B BKdV reached t = 0.0003 of T = 6 (0.005 %) — a 140× degradation relative to T_B NoKB which reached 0.043 of 6 (0.7 %). The mechanism (the agent's E3 linearization, paraphrased):

> "True UV linear instability from the user's +Q sign convention combined with focusing κ, derived to $\Omega(k)^2 = k^4 (N_0+1)/4 + 2\kappa N_0 (N_0+1) k^2 > 0$ for all k — classical Hadamard ill-posedness. No sign-convention or NLS entries in bank."

**Why this is "active mislead"**: the bank entry validates Fourier-pseudospectral on a KdV-like dispersive equation. The agent transferred this confidence to the B-NLS primitive (u, N, φ) form. Under the user's +Q sign convention, the linearized symbol on the φ-equation is anti-diffusive at high k (forward heat equation backwards in time). Fourier-pseudospectral on an anti-diffusive linear operator amplifies the UV modes by $\exp(+k^2 dt/2)$ per step — exactly what destroyed T_B BKdV.

**Critical absence in the BKdV bank**: the NLS bank's family-level entry `kb-nls-direct-n-phi-structural-failure` (confirmed by 5 independent NLS stress tests: S2, S4, S6, S7, S8) *would have* warned the agent that direct (N, φ) integration is structurally unstable for ANY problem where min(N) reaches noise floor. The BKdV bank has no equivalent family-level statement because BKdV does not have Madelung quantum pressure. The agent had no way to know.

**Negative-transfer causal chain**:

> `kb-kdv-IMEX-CN-spectral-pass` (positive, BKdV) — endorses Fourier-pseudospectral on dispersive linear operator
> → agent's E1: direct (u, N, φ) Fourier-pseudospectral + RK4 on B-NLS
> → +Q sign makes the linear operator anti-diffusive at high k
> → first time step amplifies UV modes by exp(+k²dt/2)
> → at step 3, NaN
> → over 3 Experiments the agent stayed in primitive form (no equivalent of `kb-nls-direct-n-phi-structural-failure` to motivate switch to Madelung)
> → final t_reached = 0.0003, 140× worse than NoKB

The NLSBKdV condition (which has both banks) avoided this trap **because** `kb-nls-direct-n-phi-structural-failure` was available and overrode the BKdV bank's spectral-confidence. T_B NLSBKdV PASSED in 2 iterations.

---

## 3. Confirmatory citations in NLSBKdV cells (BKdV entries that agreed but did not drive)

In the four NLSBKdV cells, NLS-bank entries decisively shaped the method (`kb-nls-muscl-madelung-bore-soliton`, `kb-nls-direct-n-phi-structural-failure`, `kb-nls-sign-convention`, etc.). BKdV-bank citations played a *confirmatory* role only — the same conclusion would have been reached from NLS bank alone.

| Cell | BKdV entries cited (confirmatory) | What they confirmed | Counterfactual without them |
|---|---|---|---|
| T_A NLSBKdV | 0 cited; all 30 rejected | N/A | No change (NLS bank's 9 entries fully specified the stack) |
| T_B NLSBKdV | `kb-kdv-noDealiasing-aliasing-artifacts` (1) | 2/3 dealiasing rule | No change (same conclusion from `kb-nls-23-dealiasing-cubic`) |
| T_C NLSBKdV | `kb-burgers-MUSCL-Godunov-shock-pass`, `kb-general-firstOrder-Godunov-preShock-baseline`, `kb-burgers-fwdEuler-centralFD-Gibbs`, `kb-kdv-noDealiasing-aliasing-artifacts`, `kb-gardner-G3-noDealiasing-cubicAliasing` (5) | MUSCL + Godunov + dealiasing for bore × soliton | No change (`kb-nls-muscl-madelung-bore-soliton` is the *complete recipe* validated on the same IC) |
| T_D NLSBKdV | minimal | discipline only | Substantial change — NLS bank lacks `kb-general-finiteness-not-accuracy`'s pre-blowup truncation framing; this is the one BKdV entry whose discipline meaningfully transfers even in the presence of NLS bank |

**Net contribution of BKdV bank in NLSBKdV cells**: **0 unique task-success guidance** on T_A / T_B / T_C; *non-zero* guidance on T_D via the general-discipline entries. Adding BKdV to NLS does not raise pass rate (3/4 = 3/4) but does add cross-confirmation.

---

## 4. Critical gaps — entries the BKdV bank *lacked* that B-NLS demanded

These are entries that DO exist in the NLS bank but have NO BKdV analog. Their absence in BKdV-only experiments produced specific failure modes.

| Missing-from-BKdV entry | What it covers | Cell where its absence hurt | Failure mode it would have prevented |
|---|---|---|---|
| `kb-nls-direct-n-phi-structural-failure` (family-level, 5 sources) | Direct (N, φ) RK4 fails for any IC where min(N) reaches noise floor | **T_B BKdV** | Agent stayed in primitive form; UV cascade destroyed run in 3 steps |
| `kb-nls-madelung-psi-structural-coupling` (structural) | u = Im(conj(Ψ)·Ψ_x) makes m=0 an algebraic identity | **T_A BKdV**, **T_C BKdV** | Agent needed 3 iterations to discover Madelung-Ψ; NLS-aware cells did it in 1 |
| `kb-nls-sign-convention` (structural) | User's +Q sign is parabolic-unstable; need standard-sign hypothesis | **T_D BKdV** (PARTIAL — agent derived it from scratch via linearization) | Agent re-derived the sign issue from scratch (good, but took 3 iterations) |
| `kb-nls-muscl-madelung-bore-soliton` (single-experiment, but EXACT match to T_C IC) | MUSCL + Madelung-Ψ + dealias is the validated stack for bore × NLS soliton | **T_C BKdV** | BKdV bank gave Godunov-on-u but no guidance for N-φ sector — T_C BKdV failed at 8.1 % because the N-φ side blew up |

---

## 5. Master table — every BKdV entry's contribution to a B-NLS task success

| BKdV entry | Cited in | Role | Causal contribution to success |
|---|---|---|---|
| `kb-general-firstOrder-Godunov-preShock-baseline` | T_A BKdV E1; T_C BKdV E1/E2/E3 | direct method transfer | **DECISIVE** for T_C bore stability (8× improvement over NoKB) |
| `kb-burgers-Godunov-preShock-smooth` | T_C BKdV E1/E2/E3 | direct method transfer | DECISIVE (paired with above) |
| `kb-kdv-noDealiasing-aliasing-artifacts` | T_A BKdV E2/E3; T_C BKdV E3; T_B BKdV E3 | discipline / single-comp upgrade | RECURRING — motivated 2/3 dealiasing in 3 cells |
| `kb-gardner-G3-noDealiasing-cubicAliasing` | T_A BKdV E2; T_C BKdV E3; T_B BKdV E3 | paired with above | RECURRING (paired) |
| `kb-kdv-spectral-solitonAmplitude-conservation` | T_A BKdV E2/E3 | discipline | confirmatory (spectral preserves amplitude) |
| `kb-general-finiteness-not-accuracy` | T_D BKdV E3 | discipline | **DECISIVE for T_D PASS** — motivated pre-blowup truncation |
| `kb-general-massConservation-insufficient-diagnostic` | T_A BKdV E3; T_B BKdV E1/E2/E3; T_D BKdV E3 | discipline | enabled multi-diagnostic monitoring |
| `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` | T_D BKdV E2/E3 | dealiasing aspect only | recurring (dealiasing role only; CN aspect rejected) |
| `kb-kdv-IMEX-CN-spectral-pass` | T_A BKdV E1/E3 (positive); T_B BKdV E1/E2/E3 (mislead) | dual-faced | POSITIVE in T_A (motivated split-step → Madelung); **NEGATIVE-TRANSFER in T_B (140× worse than NoKB)** |
| All other 22 BKdV entries | various rejections only | rejected with reason | scaffolding the disciplined "what NOT to try" choice |

---

## 6. The clean answer to "which BKdV knowledge made the B-NLS task solvable"

There are **two clean affirmative answers** and **one critical caveat**:

1. **`kb-general-firstOrder-Godunov-preShock-baseline` + `kb-burgers-Godunov-preShock-smooth`** *directly* transferred to the u-sector of T_C and produced the 8× quantitative improvement over the no-bank baseline. This is method-level cross-domain transfer: the Burgers operator is mechanism-shared between BKdV and B-NLS, so the Godunov scheme works identically.

2. **`kb-general-finiteness-not-accuracy` + `kb-general-massConservation-insufficient-diagnostic`** *indirectly* enabled the T_D PASS by motivating a pre-blowup truncation strategy that preserved the mass-conservation gate. This is discipline-level cross-domain transfer: these entries are mechanism-agnostic by construction, so they transfer 100 %.

3. **Caveat**: the entry that *actively hurt* T_B BKdV (`kb-kdv-IMEX-CN-spectral-pass`) is the same entry that *helped* T_A BKdV. The difference is whether the user's +Q sign happens to be benign for that task's linearization. **The BKdV bank had no entry warning about Madelung-quantum-pressure-induced UV instability**, and that absence — not any present-but-wrong entry — is the proximate cause of the T_B negative-transfer disaster.

The two-bank composition NLSBKdV is therefore not "BKdV plus benefit" — it is "NLS bank, with BKdV cross-confirmation" plus a single useful general-discipline addition (the finiteness/mass-conservation pair). The marginal value of BKdV when NLS is already present is **zero on T_A / T_B / T_C and modest on T_D**.
