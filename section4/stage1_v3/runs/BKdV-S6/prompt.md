You are an autonomous researcher conducting a Stage-1 **stress-test research program** on the coupled Burgers-swept-KdV (BKdV) system. Each program is a 3-round Research-Graph exploration whose **traces** are downstream input to NK curators.

# Program: BKdV-S6 — Burgers-side stability under coupling

## Research question

**Under the standard pre-validated stack (Fourier pseudospectral + 2/3-rule dealiasing + classical RK4) with NO explicit viscosity / hyperviscosity on u, does the u-equation remain bounded for moderately-amplitude initial conditions that stress the Burgers self-flux?** If the answer is "no", what minimum level of explicit u-side dissipation is needed to restore boundedness without distorting the v sector?

## Why this matters

The Burgers equation u_t + 3 u u_x = 0 (which is what u-equation reduces to when v ≡ 0) is known to develop shocks from smooth initial conditions in finite time. In the coupled BKdV system, u also has source forcing from v² coupling, which can drive u-steepening even when u starts at zero. 2/3-rule dealiasing prevents nonlinear products from aliasing back into resolved modes, but it does NOT regularize a developing shock — shocks have intrinsic high-k content that dealiasing alone cannot dissipate.

If a research agent attempts this with pre-validated stack and no u-viscosity, they may see Gibbs-like oscillations growing in u near regions of strong u-gradient. The lesson: **explicit u-side dissipation (small linear viscosity ν u_xx or hyperviscosity −ν_h k^(2p) u) is mandatory for any IC that develops a strong u-gradient (bore, shock, or coupling-driven steepening).**

## Suggested round structure (you may adjust within progressive-complexity discipline)

The IC for this program (FIXED across rounds):
- v(x, 0) = 1.5 · sech²(x + 5)   (moderate-amplitude KdV-like seed)
- u(x, 0) = 1.5 · (1 − tanh(x / 0.5)) / 2  (smoothed bore: u_L = 1.5 → u_R = 0)
- Periodic on x ∈ [−15, 15], Nx = 256, T = 6.0

This IC has BOTH a Burgers-bore-like u (smoothed step) AND a v soliton. As they propagate and interact, u develops shock-like gradients.

- **E1 (mandatory baseline)**: Standard pre-validated stack with NO u-viscosity:
  - Fourier pseudospectral spatial derivatives (all)
  - 2/3-rule dealiasing on every nonlinear product (v², uv, u·u_x, v·v_x)
  - Classical explicit RK4
  - dt = 1e-4 (within stability boundary at this Nx)
  - **NO viscosity, NO hyperviscosity, NO filter on u**
  
  Expected: u develops Gibbs at the bore and grows beyond physical bound. Document where/when u becomes unbounded (e.g. |u|_max(t) trajectory). This is the negative finding.

- **E2 (single-component upgrade)**: Add a SMALL linear viscosity ε · u_xx to the u equation only, with ε = 1e-4. Keep everything else identical to E1. Does this help? Quantify how much u_max is reduced.

- **E3 (single-component upgrade)**: Based on F2, either increase ε (if E2 was insufficient) or switch to hyperviscosity (−ν_h k^8 with ν_h ~ 1e-22 to 1e-20 as suggested by BKdV-S4's safe envelope). Document the minimum dissipation needed to keep u bounded.

## What to put in `hypothesis.md`

In the synthesis section, your `recommended` (or `Recommendation for downstream Stage-2 tasks`) section should specifically say:

> "For ICs that introduce strong u-gradients (bores, large v amplitudes that drive u via v² coupling), the pre-validated stack alone is INSUFFICIENT — explicit u-side dissipation is required. Suggested levels: ν ~ X for linear viscosity, or ν_h ~ Y for k^8 hyperviscosity. Without it, u_max grows by factor Z over T = 6."

The negative finding should be explicit: pre-validated stack without u-viscosity is unsafe for any BKdV simulation with bore-like or large-amplitude u-forcing IC.

## Same standard protocol applies

- 3 rounds via Research Graph (Q/E/F/D nodes in research_state.jsonl)
- Each round writes round<n>/{candidate.py, exec.log, reasoning.md}
- Final outputs: research_state.jsonl, hypothesis.md, session_log.md
- Every Finding node must include `is_trivial: bool`
- Working directory: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S6`
- Python: `/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/.venv/bin/python`
- Tools: Read, Write, Bash

## PDE recap

```
u_t + 3 u u_x = -∂_x (3 v² + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = ν = 1, on periodic x ∈ [−15, 15], Nx = 256.
