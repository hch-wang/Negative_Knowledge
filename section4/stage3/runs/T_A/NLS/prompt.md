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
- `pred_results/T_A.npy` — final numerical output, shape per task spec

# Step-by-step protocol

## At session start
1. Read task spec, IC, T_final, phenomenon target below
2. **Read the knowledge bank** (if condition is non-NoKB):
   - For NLS-only: `cat /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/bank/nls_knowledge.jsonl`
   - For NLS+BKdV: `cat /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_bnls/bank/nls_knowledge.jsonl` AND `cat (not provided)` AND `cat (not provided)`
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
3. **Execute**: `cd /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage3/runs/T_A/NLS && /Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python candidate.py`
4. **Inspect output**: stdout, stderr, pred_results. Run quick diagnostics with `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python -c "..."`
5. **Append Finding** F<n>
6. **(Optional) Append Decision** D<n>

# Task spec — T_A: Bright NLS soliton stability in the Burgers frame (compound-soliton attractor test)

Initialize with an exact bright NLS soliton (Madelung form) and check whether the soliton structure survives long-time propagation in the coupled Burgers-NLS system. The IC has u = N*phi_x exactly (on the compound-soliton manifold M_cs); generic methods that introduce numerical noise off M_cs let us measure whether the system relaxes back to M_cs (attractor) or drifts away (marginal).

## Initial condition
kappa = 1 (focusing). Bright soliton ansatz at v=0.5 boost: A=1.5. N(x,0) = A^2 * sech^2(A*(x+5)). phi(x,0) = 0.5*x  (so phi_x = 0.5 everywhere). u(x,0) = N(x,0) * phi_x(x,0) = 0.5 * N(x,0). [This sits on M_cs at t=0; m(x,0) = u - N*phi_x = 0.]

## Final time
T = 8.0

## Output requirements
Save to: `pred_results/T_A.npy` (relative to working directory)
Output shape: shape (n_snapshots, 3, 256), channels are (u, N, phi). Save at least 5 evenly-spaced snapshots from t=0 to T_final. The last snapshot is the eval target; the time series enables diagnostics of m(t) = u - N*phi_x relaxation.
**Save at least 5 snapshots** so eval can measure conservation over time.

## Phenomenon target
Final N(x, T) should still contain a single dominant peak with amplitude >= 0.5 of the initial 2.25 (A^2). Mass M = integral(N dx) should drift < 5%. Both u, N, phi stay bounded (|u|, |N|, |phi| < 25). The momentum m = u - N*phi_x should remain small (||m||_2 / ||N*phi_x||_2 < 0.2) — the system stays near the compound-soliton manifold.

## Domain
x in [-15.0, 15.0], Nx = 256, kappa = 1.0

# Working directory and tools

Working directory: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage3/runs/T_A/NLS`
- `pred_results/` already exists
- Python interpreter: /Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python

Tools allowed: Read, Write, Bash
Tools NOT allowed: Edit (use Write), Grep/Glob, network, package installs

# Memory (condition-dependent)

## Memory: NLS-specific knowledge bank (21 entries)

Curated from 8 B-NLS stress tests in stage1_bnls. Mix of positive (recommended methods) and negative (warned-against routes) entries. The depth field indicates how robustly the finding has been confirmed:
- structural: mathematical identity / algebraic, not a measurement
- family-level: confirmed independently by multiple stress tests
- multi-experiment: needed comparing >=2 method variants in one test
- single-experiment: standard error message — agent could discover this in 1 run

### kb-nls-sign-convention  (negative, domain=B-NLS, depth=structural)
  claim: The user's variational B-NLS derivation has +(sqrt(N))_xx/(2 sqrt(N)) sign in the phi equation, OPPOSITE to the standard NLS Madelung quantum-pressure sign (-). Agents must verify the sign before reusing 'standard' Madelung-Psi results.
  applicability: Any B-NLS subproblem reformulating fluid variables (N, phi) into Psi = sqrt(N) exp(i phi). The mapping i Psi_t = -(1/2) Psi_xx + ... that yields a stable explicit propagator requires the standard NLS sign. Under the user's literal +Q sign the Psi equation is parabolic-unstable.
  evidence: S6 reports: 'The Madelung sign in the prompt's phi equation (+(sqrt(N))_xx/(2 sqrt(N))) does not match standard NLS-Madelung; the simulation here adopts the standard NLS sign assuming the prompt sign is a convention/typo. With the prompt's literal sign, no stable explicit Madelung-Psi formulation exists because Psi cannot satisfy a standard Schrödinger equation.' User has CONFIRMED the variational +sign is the intended convention.
  recommended_action: (i) Always state explicitly which sign convention is in force before invoking Madelung-Psi. (ii) When porting standard-NLS results (S1-S5, S7-S8 and especially S6) to the user's B-NLS sign, treat the transfer as a HYPOTHESIS to be re-verified, not a fact. (iii) If running under the user's literal +sign and a standard Psi propagator is unstable, consider analytic continuation (Wick rotation in dt), implicit time stepping, or fluid-primitive integration with strong regularization (which S6/S7/S8 found unreliable).

### kb-nls-madelung-psi-structural-coupling  (positive, domain=B-NLS-Mcs, depth=structural)
  claim: Defining u := Im(conj(Psi) * Psi_x) makes the Mcs constraint m = u - N * phi_x = 0 an algebraic identity, i.e. a STRUCTURAL property of the representation rather than a numerical invariant to be enforced.
  applicability: Any B-NLS problem where the Mcs surface m=0 must be preserved. Once Psi is the primary state variable and u is reconstructed on demand from j = Im(conj(Psi)*Psi_x), no special integrator is required to keep ||m|| at machine precision.
  evidence: S5 Method A: ||m||_2 stayed at 1e-13 to 1e-17 (machine precision) for the entire T=6 trajectory at every tested dt (5e-4, 1e-3, 5e-3). Both Strang and Lie orderings gave indistinguishable results — Mcs preservation is independent of time-integrator order. Mathematical identity: u - N*phi_x = Im(conj(Psi)*Psi_x) - |Psi|^2 * Im(conj(Psi)*Psi_x)/|Psi|^2 = 0.
  recommended_action: Use Psi = sqrt(N) exp(i phi) as the PRIMARY state variable. Reconstruct u := Im(conj(Psi)*Psi_x) only at snapshot times. Do NOT carry u as an independent integrated variable when the problem requires the Mcs constraint.

### kb-nls-direct-n-phi-structural-failure  (negative, domain=B-NLS, depth=family-level)
  claim: Direct (N, phi) integration with explicit time stepping is STRUCTURALLY unstable for any IC where min(N) approaches O(noise floor), regardless of regularization choice. Five independent stress tests confirm this is a family-level pathology, not a method-tuning problem.
  applicability: Any B-NLS or NLS subproblem with a soliton, vortex, dark-soliton node, or low-density 'hole' — i.e. wherever the soliton tails, nodes, or shock cavities drive N to the grid noise floor. Triggered by the (sqrt(N))_xx / (2 sqrt(N)) quantum-pressure coupling in the phi equation becoming non-Lipschitz at N=0.
  evidence: S2: direct (N,phi) RK4 spectral blows up at step 1 (eps=0) or step 21 (eps=1e-3 + 2/3 dealias), pre-t=0.025 in every case. S4: direct (N,phi) with hard-floor eps in {1e-6, 1e-4, 1e-2} blows up in <60 steps (T<0.04). S6: direct primitive (N, phi_x, u) RK4 with eps=1e-3 + hyperviscosity blows up at t=0.1 even before the bore arrives. S7: all-spectral RK4 on (u,N,phi) blows up at t=0.001; MUSCL on u + spectral on (N,phi) blows up at t=0.006 — same HJ quantum-pressure singularity, proving shock-capturing on u alone is insufficient. S8: direct (N,phi) RK4 fails at t=0.027 (eps=1e-6) and t=0.044 (eps=1e-3) — N drops below 0 by dispersive oscillation, then Q explodes.
  recommended_action: Use Madelung-Psi Strang split-step on Psi = sqrt(N) exp(i phi). The cubic exponential propagator preserves |Psi|^2 >= 0 STRUCTURALLY (unitary), so the quantum-pressure singularity is bypassed at the representation level rather than regularized.

### kb-nls-madelung-psi-handles-zero-density  (positive, domain=B-NLS, depth=family-level)
  claim: Madelung-Psi (Psi = sqrt(N) exp(i phi)) handles N -> 0 natively without ANY explicit regularization, because the singular 1/sqrt(N) coupling in (N, phi) is absorbed by the |Psi|^2 = N identity and the cubic exponential propagator preserves |Psi|^2 >= 0 by unitarity.
  applicability: Bright solitons with vanishing tails (N tails reach 1e-24 numerical zero), dark-soliton density nodes (rho(x=0)=0 exactly), low-density 'holes' (min(N) ~ background ~ 1e-3 of peak), and any other IC where N must be allowed to approach zero.
  evidence: S1/S2: bright soliton with min(N)=3e-24, mass drift 1e-13, no regularization. S4 (anti-periodic basis): dark soliton node preserved to min|Psi|^2 = 2.9e-32, phase jump = pi to 7 digits, mass drift 4e-12 over T=4. S8: low-density problem (min_N0/max_N0 = 1e-3), Madelung-Psi with eps_mad=1e-3 completes T=4 with mass drift 0.09% and Q_max bounded at 1.76e3. Compare: every direct (N,phi) attempt on these same ICs failed in <60 steps.
  recommended_action: When any subproblem allows N to approach zero, switch to Madelung-Psi Strang split-step. Use a small eps_mad ~ noise-floor only if a positive offset is convenient for diagnostics; the unitary propagator itself does not need regularization to handle N=0.

### kb-nls-quantum-pressure-central-failure-mode  (negative, domain=B-NLS, depth=family-level)
  claim: The quantum-pressure term (sqrt(N))_xx / (2 sqrt(N)) in the phi equation is the central NEW failure mode of B-NLS relative to BKdV. Spectral derivatives of sqrt(N) divided by the tail amplitude produce |Q| ~ 1e7 to 1e24 once N is at the noise floor.
  applicability: Every B-NLS subproblem with the (N, phi) Madelung-fluid representation. The pathology is INDEPENDENT of mass conservation (continuity equation is exact in all observations up to the blowup moment), so monitoring only |dM|/M will not detect impending failure.
  evidence: S2: Q_max reaches 6.8e7 at eps=0, 5.2e12 at hard-floor eps=1e-3 (counter-intuitive non-monotonic in eps because the floor injects a non-smooth step into sqrt(N)), 2.2e24 at soft eps + 2/3 dealias. S7: spectral d2x of sqrt(N)/(2 sqrt(N)) overflows to NaN in first RK4 sub-step (N tails ~1e-30). S8: Q_max blows up by 5 orders of magnitude in ~10 dt once N goes negative.
  recommended_action: Bypass Q at the representation level: write the kinetic step as exp(-i k^2 dt / 2) on Psi_k (Fourier diagonal), which absorbs the (sqrt(N))_xx / (2 sqrt(N)) coupling exactly. Never integrate Q explicitly in time.

### kb-nls-strang-splitstep-bright-soliton  (positive, domain=NLS, depth=multi-experiment)
  claim: Strang split-step Fourier on Psi (N(dt/2) - L(dt) - N(dt/2), nonlinear half-step exact pointwise and linear full step exact in Fourier) is the gold-standard primitive for focusing NLS bright solitons: 2nd-order temporal convergence, spectral spatial convergence, mass conservation to machine precision by construction.
  applicability: Focusing 1D NLS / B-NLS Madelung-Psi reduction with bright sech soliton or smooth Gaussian IC; periodic spectral grid; smooth (no nodes, no shocks). Default working point: dt=0.001, Nx=256 on a domain L=30 with peak |Psi|^2 ~ O(1).
  evidence: S1: at dt=0.001/Nx=256, mass drift 5e-13, energy drift 3e-12, relL2 vs exact 5.7e-6 in 0.15 s wall time; clean 2nd-order in dt (relL2 ~ dt^2). S2: same setup conserves mass 1.1e-13 over T=4 on translated bright soliton. S3: same scheme at converged Nx=1024/dt=2.5e-4 gives mass drift 5.8e-12 over T=6, spectral tail 7e-11 at A=3.
  recommended_action: Default to Strang split-step Fourier on Psi for any focusing-NLS subproblem on a smooth IC. Tighten to dt=5e-4 and Nx=512+ for high-amplitude (A>=2) Gaussian ICs (see kb-nls-resolution-soliton-counting).

### kb-nls-antiperiodic-basis-dark-soliton  (positive, domain=B-NLS-dark-soliton, depth=single-experiment)
  claim: For dark-soliton ICs (Psi(-L) = -Psi(L) — anti-periodic at the box boundary), use an anti-periodic Fourier basis via the half-shift trick U = exp(-i pi x / (2L)) * Psi with kinetic wavenumbers shifted to k + pi/(2L). Periodic Fourier on the same IC fails at T<<1 due to a boundary Gibbs jump of size 2.
  applicability: B-NLS / NLS defocusing dark solitons; vortices; any IC with a phase singularity and anti-periodic boundary values at the spectral domain edges. NOT for bright solitons with vanishing tails (which are genuinely periodic).
  evidence: S4: anti-periodic basis (M4) gives min|Psi|^2 = 2.9e-32 at node, phase jump = pi to 7 digits at T=4, mass drift 4e-12. Periodic basis (M1) on the same IC drifts the node to rho(x=0)=4e-3, phase jump drifts to -2.11 rad (off by 1 rad), density-Linf error 0.74 by T=0.01 — FOUR orders of magnitude worse at the same dt/Nx, fixed purely by changing the basis. Crank-Nicolson (M3) with periodic basis fails identically — confirms it is a basis issue, not a time-scheme issue.
  recommended_action: When the IC satisfies Psi(L) != Psi(-L), switch to anti-periodic Fourier (half-shift trick: write Psi = exp(i pi x / (2L)) * U with U periodic; kinetic operator becomes -(1/2)(k + pi/(2L))^2). Avoid direct (N, phi) operator splittings entirely at phase singularities — they blow up at every tested eps in S4.

### kb-nls-muscl-madelung-bore-soliton  (positive, domain=B-NLS-shock, depth=single-experiment)
  claim: For B-NLS bore x soliton interactions, use MUSCL-Godunov SSP-RK3 on u (van-Leer limiter, Godunov flux for f(u)=u^2/2) coupled to Madelung-Psi Strang split on Psi=sqrt(N)exp(i phi). Either piece alone is INSUFFICIENT: spectral on u Gibbs-rings the bore; spectral on (N, phi) hits the quantum-pressure singularity.
  applicability: Any B-NLS subproblem combining a Burgers-like shock or rarefaction in u with a soliton (or any narrow N feature). Requires kappa = +1 (focusing). Cross-validated to T=8 with a u_L=1 / u_R=0 bore + a phi_x=0.6 bright soliton starting at x=-8.
  evidence: S7 Method E2: at Nx=256, dt=5e-4 with 2/3 dealias, |Psi|^2 mass drift 1.5e-7 pre-collision and 7e-5 over the full T=8 run; TV(u)=1.988 with zero overshoot at the bore; soliton transmits through the rarefying bore at t~5.0 with N_max bounded in [0.993, 1.012], single coherent peak. All-spectral RK4 blows up at t=0.001 (HJ singularity). MUSCL-on-u + spectral-on-(N,phi) without Madelung blows up at t=0.006 — same singularity — proving the dual fix is required.
  recommended_action: Apply MUSCL-Godunov on u AND Madelung-Psi Strang split on Psi together. Always include 2/3 dealiasing on the linear FFT step and on |Psi|^2 before the cubic exponential — without dealiasing a modulational-instability cascade triggers near the collision (S7 reports |Psi|^2 mass growing to 8e3 at the collision).

### kb-nls-23-dealiasing-cubic  (positive, domain=NLS, depth=multi-experiment)
  claim: Apply 2/3-rule dealiasing on the cubic nonlinearity |Psi|^2 * Psi (before the pointwise exponential) and on the linear FFT step whenever the problem involves a shock, a low-density region, or a high-amplitude IC. Without dealiasing, cubic-focusing aliasing inflates |Psi|^2 mass by 3 orders of magnitude on bore-soliton collision.
  applicability: B-NLS with shocks, MI-prone IC, or any setting where the high-k tail of |Psi|^2 is non-negligible. Optional for smooth bright solitons on a well-resolved grid (S1/S3 ran without dealiasing successfully when spectral tail < 1e-10).
  evidence: S7: undealiased Strang-Madelung at dt=2e-3 cascades at t=4.4 (|Psi|^2 mass 2 -> 8e3, N_max 1 -> 380); adding 2/3 dealias + dt=5e-4 keeps mass drift below 1e-4 over T=8. S8: 2/3 dealiasing on nonlinear products (u*m, u*phi_x, phi_x^2) was REQUIRED for the Madelung-Psi method to complete T=4. S2/S6 both used 2/3 dealiasing in their best-working setups.
  recommended_action: Set the upper third of Fourier modes to zero on (a) the linear half-step output and (b) the |Psi|^2 array before pointwise nonlinear exponentiation. Negligible cost; required for stability whenever spectral tail energy could grow.

### kb-nls-split-linear-phase  (positive, domain=B-NLS, depth=single-experiment)
  claim: For any spectral method on B-NLS with a non-periodic phase (e.g. an asymptotic flow phi_0 = c*x with c != 0), split phi = c*x + phi_tilde with phi_tilde periodic. Skip this split and spectral derivatives of c*x produce Gibbs oscillations with phi_x range [-17, +8] instead of the constant c=0.1, killing every method for the wrong reason.
  applicability: B-NLS / NLS with an imposed asymptotic phase gradient (Galilean boost), a soliton on a background flow, or any IC where phi tends to a linear function at the box edges. Standard precondition for using FFT.
  evidence: S8 reports: 'Splitting phi = c*x + phi_tilde (periodic) is REQUIRED for any spectral method on this problem — without it spectral derivatives of phi_0=0.1*x produce Gibbs oscillations with phi_x range [-17, +8] instead of constant 0.1, and every method fails immediately for the wrong reason.'
  recommended_action: Always check whether the IC's phase is exactly periodic on [-L, L]. If not, separate the non-periodic linear part c*x analytically and only integrate the periodic remainder spectrally. The same trick applies to Psi via Psi = exp(i c x) * Psi_tilde with Psi_tilde periodic.

### kb-nls-mass-conservation-not-sufficient  (negative, domain=NLS, depth=family-level)
  claim: Mass conservation alone is NOT a sufficient diagnostic of a correct method on NLS / B-NLS. Strang split-step preserves mass to 1e-14 even when the soliton is structurally destroyed by under-resolution OR when the dynamics are completely wrong.
  applicability: Any NLS / B-NLS verification workflow. Especially dangerous because mass conservation is the loudest a posteriori signal an agent has — it gives a confident PASS even when |Psi|_max is off by 50% or the soliton wraps backwards.
  evidence: S1: at Nx=32 the soliton width 1/sqrt(2) < dx=0.94, the peak ends at x=-4.66 (vs gt -3.0) and |Psi|_max collapses to 1.31, but mass is conserved to 1e-14. S3: under-resolved Nx=256/dt=1e-3 over-counts peaks at A>=2 (reports 2/3/3 vs converged 1/2/3) while mass drift stays at 5e-12. S5 Method A at dt=0.005: ||m||_2 stays at 1e-14 (Mcs preservation is structural) yet mass drift 6e-3, energy 100x off, peak wraps backwards.
  recommended_action: Always co-monitor at least: (a) mass drift, (b) energy drift, (c) peak amplitude and position vs ground truth or hi-res reference, (d) spectral tail fraction. Spectral tail > 1e-4 always correlated with wrong physics in S3.

### kb-nls-mcs-not-sufficient  (negative, domain=B-NLS-Mcs, depth=single-experiment)
  claim: ||m||_2 at machine precision is a NECESSARY but NOT SUFFICIENT certificate of a correct B-NLS solution on the Mcs surface — because m=0 is a representational identity under u := Im(conj(Psi)*Psi_x), it stays at machine precision even when the dynamics on Mcs are unstable.
  applicability: Any B-NLS Mcs verification. Reinforces kb-nls-mass-conservation-not-sufficient with the Mcs-specific variant: agents using the Madelung-Psi representation will get ||m|| ~ 1e-14 for free regardless of solution quality.
  evidence: S5 Method A at dt=0.005 (coarse): ||m||_2 stays at 1e-14 (Mcs preservation is structural under the Psi representation) yet mass drifts 6e-3, energy 100x, soliton peak wraps backwards by -6.9 units. Halving dt does not improve Mcs preservation (it is already structural) — it only fixes the dynamics on Mcs.
  recommended_action: Treat ||m|| ~ 0 as 'representation works as intended' rather than 'solution is correct'. Always co-monitor mass, energy, peak amplitude, and peak position against a hi-res reference.

### kb-nls-mcs-not-attractor-standard-sign  (negative, domain=B-NLS-Mcs, depth=single-experiment)
  claim: Under the AGENT-ADOPTED STANDARD-NLS sign convention (-(1/2) Psi_xx), the Mcs surface m=0 is NOT a dynamical attractor of B-NLS for T<=12: ||m||_2 GROWS by factor 1.4-3.6 to a non-zero plateau m_inf ~ eps^0.33, with relaxation timescale tau_relax ~ 2.0. CAVEAT: this finding has NOT been re-verified under the user's intended +sqrt(N)_xx/(2 sqrt(N)) sign — see kb-nls-sign-convention.
  applicability: Any agent investigating B-NLS Mcs-attractor questions. Transfer to the user's sign convention is HYPOTHESIS, not established: under the user's literal sign the standard Madelung-Psi propagator is unstable, so a different numerical method would be required to even test the hypothesis.
  evidence: S6 with epsilon perturbation off Mcs: ||m(t)||_2 grows from 0.1936 to plateau 0.7002 (eps=0.05) or 0.7746 to 1.1066 (eps=0.20), well fit by exponential approach m(t) = m_inf - A*exp(-t/tau_relax), tau_relax=2.16 (eps=0.05) and 1.77 (eps=0.20). Numerical convergence: halving dt changes ||m||(T=12) by 0.14%. Only kappa=+1 (focusing) tested.
  recommended_action: (a) Do NOT cite the S6 plateau values m_inf, tau_relax as fixed B-NLS facts. (b) Before using this finding to argue about Mcs attractor behaviour under the user's variational form, re-run S6 with a numerical scheme compatible with the +sqrt(N)_xx/(2 sqrt(N)) sign (likely implicit time stepping or fluid-primitive with strong regularization). (c) Treat S6's qualitative claim 'Mcs not an attractor under the standard sign' as a constraint on theoretical models; the user's sign may or may not produce attractor behaviour.

### kb-nls-etd-rk1-mass-destruction  (negative, domain=NLS, depth=single-experiment)
  claim: Non-symplectic Eulerian single-step schemes (ETD-RK1, forward Euler, naive RK4 in time on (N, phi)) drift mass LINEARLY in dt on Hamiltonian NLS systems, regardless of nominal order of accuracy.
  applicability: Any NLS or B-NLS subproblem requiring conservation laws. The pathology applies whenever the nonlinear sub-step is integrated forward by an Eulerian correction rather than as a unitary rotation on Psi.
  evidence: S1 Method 3 (ETD-RK1 / exponential Euler on Psi): mass drift |dM|/M = 0.14 (dt=1e-2), 1.1e-2 (dt=1e-3), 1.0e-3 (dt=1e-4) — linear in dt. relL2 vs exact = 1.045 at dt=0.01 (worse than zero solution) and 8.3e-3 at dt=1e-4 (factor 10^4 worse than Strang). At dt=0.01 the field 'looks plausible' (peak amplitude 1.62) but mass is wrong by 14%.
  recommended_action: Always choose a symplectic / unitary time stepper on Psi for NLS. Strang split (S1 Method 1) or higher-order Yoshida composition are the standard choices. Avoid ETD-RK1 / forward Euler / naive RK4 entirely for soliton transport over long T.

### kb-nls-lie-splitting-uneconomical  (negative, domain=NLS, depth=single-experiment)
  claim: Lie splitting (N(dt) - L(dt), asymmetric first-order) on Psi is uneconomical compared to Strang splitting: ~11x larger error per (dt, Nx) at first order, so achieving Strang's accuracy requires ~10x more steps despite Lie being only half the cost per step.
  applicability: NLS / B-NLS split-step Fourier in any sector. EXCEPT: S5 Method A-Lie is indistinguishable from Strang on Mcs initial conditions because the boost sub-flow commutes with kinetic+nonlinear when u is reconstructed from Psi.
  evidence: S1: at dt=0.01/Nx=256, Lie gives relL2=6.1e-3 vs Strang's 5.6e-4 (factor 11). Lie's energy drift O(dt) (2e-4 at dt=1e-2 vs Strang's 4e-8 — 5000x worse). S5: on Mcs IC, A-Lie at dt=1e-3 gives mass drift 1.29e-12 indistinguishable from A-Strang (the boost sub-flow approximately commutes with kinetic+nonlinear when u rides Psi).
  recommended_action: Default to Strang. Lie is acceptable only when (a) sub-flows approximately commute (S5 Mcs case) or (b) extreme prototyping speed matters more than accuracy.

### kb-nls-hard-floor-counterproductive  (negative, domain=B-NLS, depth=single-experiment)
  claim: Hard-floor regularization sqrt(max(N, eps)) is COUNTER-INTUITIVELY WORSE than soft regularization sqrt(N + eps) on spectral methods: it injects a non-analytic step into sqrt(N) at the floor boundary, exciting Gibbs ringing whose amplitude grows with eps. At eps=1e-3, hard-floor Q_max = 5.2e12 vs soft Q_max = 1.3e7 — five orders of magnitude worse.
  applicability: Any attempt to regularize 1/sqrt(N) singularities on a SPECTRAL grid. The hard-floor / soft-floor distinction matters less on a finite-volume or finite-element grid where d/dx is local.
  evidence: S2 with eps_sweep {1e-12, 1e-6, 1e-3} on direct (N,phi) RK4: hard-floor gives non-monotonic Q_max (2.4e11, 2.4e8, 5.2e12 — peaks at the largest eps because flat floor is widest). Soft sqrt(N+eps) gives monotonic improvement (2.4e8, 1.3e7, 3.3e6 as eps increases). S4 corroborates with floor regularization blowing up regardless of eps.
  recommended_action: If a regularization is unavoidable on a spectral grid, use soft sqrt(N + eps). But the larger lesson is that NEITHER hard nor soft regularization rescues direct (N,phi) on spectral grids — switch to Madelung-Psi instead (kb-nls-direct-n-phi-structural-failure).

### kb-nls-karpman-maslov-upper-bound  (negative, domain=NLS, depth=single-experiment)
  claim: Karpman-Maslov soliton-count formula (for a Gaussian IC A*exp(-x^2/(2 sigma^2)) under focusing NLS) is an UPPER BOUND on the operational soliton-emission count, not a sharp predictor. Empirical thresholds for a SECOND soliton lie in A in (2.0, 2.5] and for a THIRD in A in (2.5, 3.0] — about ONE unit above the prompt-convention KM prediction.
  applicability: Focusing NLS (kappa=+1) Gaussian IC; finite T (=6 in S3). For asymptotic-T behavior the Zakharov-Shabat eigenvalue count is sharper, but at finite T solitons remain bound to the parent wavepacket and the operational count lags KM.
  evidence: S3 amplitude sweep at converged Nx=1024/dt=2.5e-4/L=60: A in [1.0, 2.0] yields 1 soliton (KM predicts 1/2/3); A=2.5 yields 2 (KM predicts 3); A=3.0 yields 3 (KM predicts 4). Linf_max scales as ~A^1.5; the N=3 breather at A=3.0 transiently reaches linf=8.33 from initial 3.0.
  recommended_action: Use KM as a sanity-check upper bound but verify empirically at converged resolution. The operational threshold is set by the IC's L^2 norm, not the asymptotic eigenvalue count.

### kb-nls-resolution-soliton-counting  (negative, domain=NLS, depth=single-experiment)
  claim: The prompt-default discretization (Nx=256, dt=1e-3 on L=30, dx=0.117) is QUANTITATIVELY UNRELIABLE for soliton counting at A>=2 on Gaussian ICs: it silently over-counts peaks (reports {2, 3, 3} vs converged {1, 2, 3} for A in {2.0, 2.5, 3.0}) and over-estimates Linf by 26-65%. The method does not blow up; failure is silent and quantitative.
  applicability: Soliton counting / amplitude diagnostics on Gaussian ICs to focusing NLS at finite T. Spectral tail fraction > 1e-4 was always associated with miscounting in S3; use this as an automated under-resolution flag.
  evidence: S3 baseline (Nx=256, dt=1e-3, L=30) reports linf_final={2.82, 4.22, 6.06} at A={2.0, 2.5, 3.0}; converged (Nx=1024, dt=2.5e-4, L=60) reports {2.57, 2.74, 3.88}. Doubling L at fixed dx does NOT clean up the result — the failure is dx-undersampling of the narrow emitted soliton (FWHM ~ 1/A), not periodic wrap-around.
  recommended_action: Use Nx>=1024, dt<=2.5e-4 on L=60 (dx<=0.06) for amplitude sweeps with A in [1, 3]. Always co-report spectral tail fraction; flag any run with tail > 1e-4 as untrustworthy.

### kb-nls-cfl-split-step  (positive, domain=NLS, depth=single-experiment)
  claim: The relevant CFL-like quantity for split-step Fourier on focusing NLS is the linear sub-step phase budget: dt * (pi * Nx / L)^2 <= O(1). Above this threshold dispersion aliases catastrophically (relL2 ~ 1) without producing NaN — the method silently produces a wrong soliton with correct mass.
  applicability: Split-step Fourier on Psi (Strang or Lie) for focusing NLS / B-NLS Madelung-Psi reduction. Practical working rule for B-NLS subproblems with peak |Psi|^2 ~ O(1) on a domain L=30: dt <= 1e-3 with Nx=256, dt <= 2.5e-4 with Nx=512.
  evidence: S1: dt=0.5 destructive at every Nx in {32, 64, 96, 128} (relL2 ~ 0.95) because the linear half-step phase (1/2)(pi Nx/L)^2 dt > 2*pi already aliases dispersion fully. The nonlinear sub-step adds kappa*|Psi|^2_max*dt phase, which at |Psi|^2~2 requires only dt << 1 for accuracy, not stability.
  recommended_action: Before running any split-step Fourier integration, compute the linear-step phase budget pi^2 Nx^2 dt / (2 L^2) and require it <= 1. The nonlinear sub-step is unconditionally stable but require dt <= 1 / max(|Psi|^2) for accuracy.

### kb-nls-energy-drift-vs-mass-drift  (positive, domain=NLS, depth=single-experiment)
  claim: Energy drift is a more sensitive diagnostic than mass drift on NLS: Strang split-step has |dE|/|E| ~ O(dt^4) (4th-order shadow Hamiltonian) so dE catches accuracy degradation much earlier than dM ~ O(machine_eps). Use mass drift to detect catastrophic failures; use energy drift to verify integration order.
  applicability: Any NLS / B-NLS verification with symplectic integrators. The dE ~ dt^4 scaling is specific to symmetric symplectic methods (Strang, Yoshida); non-symplectic schemes have dE ~ dt (S1 ETD-RK1).
  evidence: S1 Strang: at dt=0.01, |dE|/|E| = 4.3e-8; at dt=0.001, 3e-12; at dt=0.0001, 1.7e-11 — drift ~ dt^4 in the accuracy-limited regime, ~ machine_eps at the noise floor. Compare to mass drift: 3e-14 to 8e-12 across the same dt range — i.e. mass is at noise floor everywhere and gives no order signal.
  recommended_action: When verifying convergence order of a new B-NLS integrator, plot |dE|/|E| vs dt on log-log. A clean dt^4 slope confirms symplectic 2nd-order; dt^2 or dt^1 indicates an order loss; growth in time indicates non-symplecticity.

### kb-nls-recommended-default-bnls  (positive, domain=B-NLS, depth=multi-experiment)
  claim: Recommended default scheme for a generic B-NLS subproblem (smooth IC, no shock, finite T <= 10): Strang split-step Fourier on Psi = sqrt(N) exp(i phi), Nx=512-1024 on L=60 (dx<=0.06), dt=2.5e-4 to 1e-3, with 2/3 dealiasing on |Psi|^2 before the cubic exponential. For shocks add MUSCL-Godunov SSP-RK3 on u; for phase singularities switch to anti-periodic basis; for asymptotic non-periodic phase split phi = c*x + phi_tilde.
  applicability: Starting point for any new B-NLS investigation. Specific subproblem flavors should override individual choices (shock -> MUSCL, dark soliton -> anti-periodic, low density -> add eps_mad).
  evidence: S1 (bright soliton): Strang at dt=1e-3/Nx=256 gives relL2 5.7e-6. S3 (Gaussian sweep): Nx=1024/dt=2.5e-4/L=60 needed for converged peak counts. S4 (dark soliton): anti-periodic basis required. S5/S7 (bore/Mcs): MUSCL+Madelung+dealias dual fix. S8 (low density): eps_mad=1e-3 + phi split.
  recommended_action: Start with the default; refine Nx/dt by halving until the diagnostic of interest (peak count, ||m||, mass drift) is stable to within 1%. Always verify by running at Nx=2x, dt=dt/2 and checking the trajectory deviates by < 0.2% in the diagnostic of interest.

