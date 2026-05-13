You are studying a real coupled PDE system. Your job: write a Python script that numerically solves the system from the specified initial condition for the specified final time, save the (u, v) field at multiple snapshots, and write a reasoning note describing your method, your use of any provided memory, and the risks.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round1
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round1/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round1/reasoning.md (under 500 words: Approach / Numerical method / Risks / Use of memory)

# Sub-task T_C: Burgers bore interacting with a KdV soliton

Initialize u as a smoothed bore (descending step) and v as a soliton to its left moving rightward. Study what happens when the soliton encounters the bore: does it transmit (refract), reflect, fuse, or get destroyed?

## PDE — Coupled Burgers-swept-KdV system (Holm et al. 2025)

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = 1, ν = 1 (both coupling/dispersion coefficients normalized to 1). On periodic domain x ∈ [-15, 15], Nx = 256 grid points.

In the special reduction `m := u - v^2/2 = 0`, the system reduces to a Gardner equation `v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0`.


## Initial condition
u(x, 0) = 1.5 * (1 - tanh(x / 0.5)) / 2     (smoothed bore: u_L = 1.5, u_R = 0, transition centered at 0 with width 0.5)
v(x, 0) = 1.5 * sech^2(x + 8)               (KdV soliton, amplitude 1.5, initially at x = -8, will move right toward bore)

## Final time
T = 8.0

## Required output
Save to: `pred_results/T_C.npy`
Output shape: shape (n_snapshots, 2, 256); save 5+ snapshots so the bore-soliton encounter is visible.

## Phenomenon target (this is the eval criterion)
Final v should still contain a recognizable peak with amplitude >= 0.5 (soliton survived). u should stay bounded (|u_max| < 5). Bore should not have blown up.

There is NO closed-form reference solution for this problem. The phenomenon target above is checked deterministically by a fixed eval script using: (a) finiteness, (b) mass conservation of v, (c) peak count of v at final time via scipy.signal.find_peaks, (d) amplitude check, (e) boundedness of u and v.

## Memory: no knowledge bank provided

You have no prior knowledge bank for this problem family. Use your general knowledge of PDE numerical methods.


## Reasoning note structure
Write reasoning.md with these sections:
- **Method**: which numerical schemes you chose for u and v equations (spatial discretization + time integration). Explain why these are appropriate for THIS PDE system specifically.
- **Use of memory**: (if memory section above is non-empty) explicitly cite which bank entries influenced your choices by `id`. Identify entries you considered but REJECTED for this task and why. (If no memory, skip this section.)
- **Risks**: 2-4 specific things that could go wrong with your method on this task.

## Hard constraints
1. Use Write tool EXACTLY TWICE.
2. Only numpy, scipy, matplotlib are available.
3. Script must run as `python candidate.py` from the working directory.
4. No Read of any file other than this prompt. No Bash. No Edit.
5. The script must save the output at `pred_results/T_C.npy` with the correct shape.
6. After the two writes, return ONE short sentence describing your numerical scheme.
