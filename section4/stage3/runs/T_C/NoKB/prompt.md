You are an autonomous researcher operating inside the **Research Graph framework** on the **Burgers-NLS (B-NLS)** coupled system.

# The B-NLS system (user's variational convention — note sign on quantum pressure)

Three coupled PDEs on periodic domain x in [-15, 15], Nx grid points.

```
m_t + (u*m)_x + m*u_x = 0,          m := u - N*phi_x                                          (momentum / EPDiff-Burgers)
N_t + d_x((u + phi_x) * N) = 0                                                                (continuity for N)
phi_t + u*phi_x + (1/2)*phi_x^2 + (sqrt(N))_xx / (2*sqrt(N)) - 2*kappa*N = 0                  (Hamilton-Jacobi)
```

**IMPORTANT — sign convention**: The +sqrt(N)_xx/(2 sqrt(N)) sign is the user's variational form; it is OPPOSITE to the standard NLS Madelung convention. Methods imported directly from standard NLS literature may not apply without sign adaptation. (This is recorded in bank entry kb-nls-sign-convention if your condition gives you the NLS bank.)

State variables: u (real, Burgers velocity), N (real >= 0, density), phi (real, phase).

Compound-soliton manifold: Mcs := {m = u - N*phi_x = 0}.

kappa = +1 (focusing) for all tasks in this stage.

# Research Graph framework

Append-only `research_state.jsonl` in working directory; four node types:
- **Question (Q)**: research question of this task
- **Experiment (E)**: a concrete (IC, method, parameters, T) tuple
- **Finding (F)**: outcome of an experiment (diagnostics + interpretation)
- **Decision (D)**: retry / change_method / narrow_claim / abandon_route / stop_useful

Edges: Q → motivates → E → produces → F → informs → D → motivates → E (next)

# Session protocol — exactly 3 Experiments allowed per session

**"Loop 3 times" (binding):**
- ONE iteration = ONE Experiment node + execution + Finding node
- An iteration is COUNTED when you execute candidate.py via Bash
- Bug-fixes (typos) that re-run SAME method count as SAME iteration
- You may consume up to **3 iterations**
- You may **stop early** if Finding has useful_self_assessment=True

# Progressive-complexity discipline (NON-NEGOTIABLE)

Each Experiment is the *smallest meaningful escalation* over the previous one:

1. **Experiment 1 must be the simplest meaningful method** for B-NLS:
   - Spatial: Fourier pseudospectral on (u, N, phi) — but BEWARE: if `kb-nls-direct-n-phi-structural-failure` applies, direct (N, phi) integration is known unstable; the simplest meaningful method may be Madelung-Psi from the start. **Choose what is simplest while still PHYSICALLY meaningful.** If a candidate baseline is known to be a numerical dead end (e.g. direct (N, phi) for a problem with min(N) small), the "simplest meaningful" baseline is the next available method up.
   - Time: explicit RK4 or split-step Lie
   - NO operator splitting BEYOND a single split (e.g. linear vs nonlinear in Psi-form is one split, allowed)
   - NO dealiasing, NO MUSCL, NO hyperviscosity at E1
   - Even if bank says E1 will fail, you MUST run it first to observe failure mode

2. **Experiment 2 (if E1 fails) changes AT MOST ONE major component over E1**:
   - explicit RK4 → IMEX-CN or Strang split-step (one of these, not both)
   - no dealiasing → 2/3 rule (only this single change)
   - direct (N, phi) → Madelung-Psi (single representation change)
   - same method, but reduce dt by 5-10x

3. **Experiment 3 layers ONE more component on E2**.

4. **Bank's role**:
   - If your condition has a bank, scan it at proposal stage. Bank entries inform WHICH single component to upgrade NEXT given the F1 diagnostic.
   - The bank is for **escalation direction**, NOT for skipping straight to a complex stack.
   - You may NOT directly adopt a fully-stacked complex method as E1 even if bank endorses it.

# Required output files at session end

Working directory MUST contain:
- `candidate.py` — final solver (your best Experiment)
- `reasoning.md` — sections: Final method / Iteration trace / Use of memory / Final self-assessment
- `research_state.jsonl` — Q + ≤3 E + ≤3 F + Decision nodes
- `session_log.md` — chronological log
- `pred_results/T_C.npy` — final numerical output, shape per task spec

# Step-by-step protocol

## At session start
1. Read task spec, IC, T_final, phenomenon target below
2. **Read the knowledge bank** (if condition is non-NoKB):
   - For NLS-only: `cat (none)`
   - For NLS+BKdV: `cat (none)` AND `cat (none)` AND `cat (none)`
   - For NoKB: skip
3. Initialize research_state.jsonl with Question Q1
4. Plan E1 — under progressive-complexity discipline

## For each iteration (max 3)
1. **Propose Experiment** with explicit bank consultation:
   - Append to research_state.jsonl:
   ```
   {{"node_type": "Experiment", "id": "E<n>", "ic": "...", "method": "...", "params": {{...}}, "T": <T>, "motivated_by": "Q1 or D<n-1>", "cites_bank": ["<id>"], "rejects_bank": ["<id>"], "bank_use_rationale": "<one sentence>", "ts": <ts>}}
   ```
   - If NoKB: cites_bank and rejects_bank are empty []
   - Otherwise MANDATORY: for each upgrade, cite which bank entry informed your choice, and which entries you rejected (and why)
2. **Write candidate.py** — full rewrite via Write tool
3. **Execute**: `cd /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage3/runs/T_C/NoKB && /Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python candidate.py`
4. **Inspect output**: stdout, stderr, pred_results. Run quick diagnostics with `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python -c "..."`
5. **Append Finding** F<n>
6. **(Optional) Append Decision** D<n>

# Task spec — T_C: Burgers bore in u colliding with a bright NLS soliton in N

Initialize u as a smoothed Burgers bore (descending step), N as a bright NLS soliton placed to the bore's left moving rightward (via initial phase gradient), and phi consistent. Watch the interaction: does the soliton transmit (refract through bore), reflect, get captured, or destroyed? Direct analog of BKdV T_C, now with NLS-Madelung dispersion replacing KdV linear dispersion.

## Initial condition
kappa = 1 (focusing). u(x,0) = 1.0 * (1 - tanh(x/0.5))/2 (bore: u_L=1.0, u_R=0, width 0.5 centered at 0). N(x,0) = 1.0 * sech^2(x + 8) (bright soliton, amplitude 1.0, at x=-8). phi(x,0) = 0.6*x (so phi_x = 0.6, the soliton moves right at speed ~0.6). [m(x,0) = u - N*phi_x is NOT zero — generic off-M_cs IC.]

## Final time
T = 8.0

## Output requirements
Save to: `pred_results/T_C.npy` (relative to working directory)
Output shape: shape (n_snapshots, 3, 256). Save 5+ snapshots so the bore-soliton encounter (~t=8 to 14) is visible.
**Save at least 5 snapshots** so eval can measure conservation over time.

## Phenomenon target
Final N should still contain a recognizable peak with amplitude >= 0.3 (soliton survives some interaction). u should stay bounded (|u_max| < 5). Bore should not have blown up. Bonus: compute ||m||_2(t) and observe whether it decreases through the interaction (compound-soliton attractor signature).

## Domain
x in [-15.0, 15.0], Nx = 256, kappa = 1.0

# Working directory and tools

Working directory: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage3/runs/T_C/NoKB`
- `pred_results/` already exists
- Python interpreter: /Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python

Tools allowed: Read, Write, Bash
Tools NOT allowed: Edit (use Write), Grep/Glob, network, package installs

# Memory (condition-dependent)

## Memory: no knowledge bank.

You have no prior knowledge bank. Use general PDE / numerical-methods knowledge.

