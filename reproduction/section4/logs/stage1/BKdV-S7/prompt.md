You are an autonomous researcher conducting a Stage-1 **stress-test research program** on the coupled Burgers-swept-KdV (BKdV) system.

# Program: BKdV-S7 — Gardner-stable but BKdV-unstable IC

## Research question

The Gardner equation v_t + 6 v v_x + (3/2) v² v_x + v_xxx = 0 arises as the m = 0 reduction of BKdV (substituting u = v²/2 into BKdV's v-equation yields exactly Gardner). The naive expectation is therefore: **whatever IC is stable in Gardner should remain stable in BKdV** if we initialize u₀ = v₀²/2 (i.e., m₀ ≡ 0).

**Find an IC that confirms this naive expectation is WRONG: stable in Gardner-only evolution, but unstable in the full BKdV when initialized at m₀ = 0.** Characterize the breakdown mechanism — is m₀ = 0 not preserved? Is some specific mode amplified by the BKdV coupling? What's the timescale?

## Why this matters

The Gardner equation has well-known stable soliton solutions: there exist combinations of (amplitude, width, speed) where a `sech² + tanh²` profile propagates as a coherent soliton. Researchers studying BKdV often assume that on the m = 0 manifold, BKdV "is" Gardner and inherits Gardner's stability. **This is empirically false** because m = 0 is not a dynamically invariant manifold of BKdV (BKdV-S5 already established this algebraically). The current program targets a quantitative version: take a Gardner-soliton-like IC, evolve it in both equations, demonstrate that Gardner-stable IC becomes BKdV-unstable, and isolate the mechanism.

This produces TWO bank entries:
- **Positive**: "Gardner equation has stable sech² propagation at moderate amplitude over T_test for parameters [A, σ]"
- **Negative**: "Gardner-stable IC ≠ BKdV-stable. Setting u = v²/2 in BKdV with such a Gardner-stable v IC does NOT yield stable BKdV evolution; instead m drifts, coupling amplifies specific modes, and the v amplitude decays / loses coherence by T ~ T_breakdown."

The negative entry must include the BKdV-S5 connection (m=0 not invariant identity) but also quantify the *amplitude* of the breakdown for this specific IC.

## Suggested round structure

You will need to implement TWO solvers in candidate.py: one for Gardner alone (1 evolution equation), one for full BKdV (2 coupled equations). Use the same Fourier pseudospectral + 2/3 dealiasing + RK4 stack for both. Keep all numerical parameters (Nx, dt, dealiasing rule) IDENTICAL across the two solvers so the comparison is clean.

The IC for this program (FIXED across rounds):
- v(x, 0) = A · sech²(x + 5) with A = 1.5
- For Gardner: just v IC
- For BKdV: v IC same, plus u(x, 0) = v(x, 0)² / 2 (sets m₀ = 0 exactly)
- Periodic on x ∈ [−15, 15], Nx = 256
- T_test = 10.0 (long enough to see drift)

- **E1**: Run Gardner-only with the chosen IC. Verify it is stable (single coherent peak, amplitude preserved, m_drift not applicable since Gardner doesn't have m). Document Gardner end-state diagnostics. This is the **positive baseline**.

- **E2**: Run BKdV with the matching IC (u₀ = v₀²/2). Document ‖m‖_L2(t) trajectory, v_max(t), u_max(t), and where the BKdV solution diverges from the Gardner solution (compute the L² distance between BKdV's v and Gardner's v over time). This is the **negative finding**.

- **E3**: Either (a) repeat at different A to find the threshold where BKdV-instability sets in, OR (b) probe the mechanism by tracking which spectral modes of m first grow — if it's k-selective, that connects to BKdV-S5's finding.

## What to put in `hypothesis.md`

Key fields in synthesis:
1. **Gardner stability claim**: "Gardner equation at IC `v = A sech²` with A=1.5 propagates stably to T=10; soliton retains XX% of initial amplitude, single coherent peak."
2. **BKdV breakdown claim**: "Same IC + u₀ = v₀²/2 in BKdV: ‖m‖_L2 grows from 0 to YY by t = ZZ; v_max(T) = WW (substantially below Gardner's preserved value); k-selective amplification observed at modes [list]."
3. **Mechanism**: cite the BKdV-S5 identity `m_t|_{m=0} = (v−1)(6 v v_x + v_xxx)` and quantify the integral / sign / spatial structure of m_t at t=0 for our chosen IC.
4. **Implication for downstream Class B**: "Class B B1 (compound soliton mechanism) cannot rely on Gardner stability arguments; the local compound soliton in BKdV does not simply 'restore' Gardner stability."

## Standard protocol

- 3 rounds, Q/E/F/D nodes in research_state.jsonl
- Each round writes round<n>/{candidate.py, exec.log, reasoning.md}
- Final outputs: research_state.jsonl, hypothesis.md, session_log.md
- Every Finding includes `is_trivial: bool` (E1 Gardner-stable will be `is_trivial: false` — it provides the positive baseline; trivial would be "Gardner at amp=0 is stable" which is empty content)
- Working directory: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S7`
- Python: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python`
- Tools: Read, Write, Bash

## PDE recap

BKdV:
```
u_t + 3 u u_x = -∂_x (3 v² + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

Gardner (m=0 reduction; derive directly from substituting u = v²/2 into BKdV's v-equation; verify that the resulting equation on v is consistent with BKdV's u-equation):

After substitution: u_x = v v_x, uv = v³/2, ∂_x(uv) = (3/2) v² v_x. So BKdV's v-equation becomes:
```
v_t + 6 v v_x + (3/2) v² v_x + v_xxx = 0     (Gardner-like, with cubic coefficient 3/2)
```

This is what your Gardner-only solver should evolve.
