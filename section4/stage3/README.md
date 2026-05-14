# Section 4 — Stage 3: B-NLS transfer test

## What this stage is

Take the **same Research-Graph framework and the same 30-entry stage1 knowledge bank** that were used on BKdV in stage 2, and apply them to a **structurally related but mechanistically different** system: the Burgers-NLS (B-NLS) system from variational (Hamilton's-principle) formulation. See `physics/bnls_equations.md` for the coordinate-form derivation.

This is a deliberate **transfer test** for the bank: stage1 was built from stress-tests on Burgers / KdV / Gardner / shallow-water. B-NLS shares the Burgers part (so MUSCL/Godunov / shock-capturing entries should transfer) but introduces a genuinely new ingredient — the **NLS quantum pressure** $\frac{(\sqrt{N})_{xx}}{2\sqrt{N}}$ and its singularity at $N \to 0$ — that no bank entry directly addresses.

## Why we built this stage

Three reasons, in order of importance:

1. **The user's primary research observation**: in B-NLS the system appears to relax toward a "compound-soliton manifold" $\mathcal{M}_{cs} := \{m = u - N\phi_x = 0\}$. Mechanism unknown. Task T_D is designed to investigate this directly — it is a *research-grade*, no-oracle-answer task.

2. **Stage 2 lessons**: stage 2 v2 showed that on BKdV the bank-vs-no-bank gap shrinks to about *one iteration of efficiency* under progressive-complexity discipline, because the BKdV tasks are well-trodden and a single round of execution recovers most of what the bank tells you. We want to test whether a system with one *genuinely new component* (quantum pressure) restores a measurable bank-vs-no-bank gap, because the bank entries no longer cover the central failure mode.

3. **Bank transferability** is itself a paper-relevant variable. Knowledge produced from one PDE family that fails to transfer to a related family is evidence that the schema is *too instance-specific*; knowledge that transfers cleanly is evidence the abstraction level is right.

## What stage 3 inherits from stage 2

| Component | Stage 2 (BKdV) | Stage 3 (B-NLS) |
|---|---|---|
| Research-Graph protocol (Q/E/F/D nodes, ≤3 Experiments per session) | Yes | **Yes** (will reuse template) |
| Progressive-complexity discipline (E1 = baseline, single-component upgrades) | Yes (v2) | **Yes** (carry forward) |
| 4 conditions: NoKB / PosOnly / NegOnly / PosNeg | Yes | **Yes** |
| Knowledge bank | Stage 1 (30 entries: 10 pos + 20 neg, all BKdV-family) | **Same bank** (transfer test) |
| Phenomenon-based deterministic eval | Yes | Yes for T_A/T_B/T_C, partly for T_D |
| Iteration budget | 3 Experiments | **Same for T_A/T_B/T_C**; T_D may need more (TBD) |

## What stage 3 differs from stage 2

| Component | Stage 2 | Stage 3 |
|---|---|---|
| System | Burgers-swept-KdV | Burgers-NLS |
| Variables per cell | 2 (u, v) | 3 (u, N, phi) |
| New failure mode in bank? | No, all covered | **Yes**: quantum pressure $(\sqrt{N})_{xx}/(2\sqrt{N})$, $N \to 0$ singularity |
| Task list | T_A, T_B, T_C | T_A, T_B, T_C, **T_D** (compound-soliton mechanism) |
| Has "research-grade no-oracle" task? | No (all phenomenon-target) | Yes (T_D) |

## The four tasks

See `tasks/definitions.json` for full IC and phenomenon-target specs.

| Task | Analogous to | Compound-soliton manifold | Phenomenon |
|---|---|---|---|
| **T_A** | BKdV T_A | starts on $\mathcal{M}_{cs}$ | bright soliton stability test; if system stays near $\mathcal{M}_{cs}$, attractor confirmed |
| **T_B** | BKdV T_B | starts on $\mathcal{M}_{cs}$ | Gaussian -> soliton emission (focusing NLS MI) |
| **T_C** | BKdV T_C | starts **off** $\mathcal{M}_{cs}$ | bore × soliton, watch $\|m\|(t)$ during interaction |
| **T_D** | (new) | starts at $\mathcal{M}_{cs} + \epsilon \cdot \text{perturbation}$ | characterize relaxation rate to $\mathcal{M}_{cs}$ — **the user's research question** |

## Why the bank is expected to give differentiated signal here

In stage 2 v2, the BKdV failure modes (aliasing, dispersive stiffness, Burgers shock, amplitude CFL) were all *already in the bank* — so once a baseline E1 was forced and its failure was observed, the next single-component upgrade was visible from the F1 diagnostic alone, without needing the bank. The bank only saved one round of iteration on T_C (PosOnly directly cited `kb-burgers-MUSCL-Godunov-shock-pass`).

In B-NLS:
- The **Burgers and aliasing failure modes** are still in the bank (transfer should work for E1/E2 on `u`-sector failures).
- **Quantum pressure failures** are *not* in the bank. The diagnostic signature when $\sqrt{N}_{xx}/\sqrt{N}$ blows up is unique (small holes in $N$ amplify rapidly into infinite quantum pressure; $\phi_t$ diverges). Without prior knowledge of this failure mode, agents may take 2-3 iterations just to recognize it.

→ The bank-vs-no-bank gap should be *larger* on B-NLS than on BKdV — **but only on the dimensions the bank covers**. The quantum-pressure axis is a genuine novelty test. This separates two paper-relevant claims:
  - "structured knowledge accelerates research on familiar physics" (testable on T_A, T_B, T_C — Burgers-sector failures dominate)
  - "structured knowledge gives less help on novel physics" (testable on T_D — quantum-pressure failures dominate)

## Status

- [x] Skeleton created
- [x] B-NLS equations documented in `physics/bnls_equations.md`
- [x] Tasks defined in `tasks/definitions.json`
- [x] Bank symlinked from stage1 (transfer test)
- [ ] Prompt template adapted from stage2 (TBD — keep progressive-complexity discipline; add explicit B-NLS variable list)
- [ ] `scripts/build_stage3.py` (TBD — adapt from `stage2/scripts/build_v2.py`)
- [ ] Parent-side `eval/phenomenon_checks_bnls.py` (TBD — design for 3-channel output)
- [ ] Dispatch 16 sub-agents (4 tasks × 4 conditions) — pending user approval

## Open questions for the user before dispatch

1. **T_D as research-grade no-oracle task**: should T_D get an extended iteration budget (e.g. 6 rounds instead of 3) to enable epsilon-sweep + decay-rate characterization? Or keep parity with T_A/T_B/T_C at 3 rounds?

2. **Should T_D be run on all 4 conditions** (NoKB / PosOnly / NegOnly / PosNeg) like T_A-T_C, or only on PosNeg (best-case condition) since it's research-grade rather than benchmark-style?

3. **Quantum-pressure-specific bank entries**: option to expand stage1 bank with 2-3 *new* entries about quantum pressure / $N \to 0$ singularity from this stage's experiment trace — turning stage 3 into both a transfer test AND a bank-augmentation run. This would test the "deep negative knowledge" idea (a path-level failure summarized after multiple-iteration learning).

4. **Numerical baseline**: do we test pure-Fourier baseline (will fail at $\sqrt{N}_{xx}/\sqrt{N}$), or directly suggest Madelung-$\Psi$ baseline (complex-valued, sidesteps the singularity)? Choice frames the discipline differently — pure-Fourier exposes more failure modes (better for research signal); Madelung is the "real" answer (better engineering).
