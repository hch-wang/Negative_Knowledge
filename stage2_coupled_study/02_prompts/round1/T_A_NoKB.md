You are studying a real coupled PDE system. Your job: write a Python script that numerically solves the system from the specified initial condition for the specified final time, save the (u, v) field at multiple snapshots, and write a reasoning note describing your method, your use of any provided memory, and the risks.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round1
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round1/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round1/reasoning.md (under 500 words: Approach / Numerical method / Risks / Use of memory)

# Sub-task T_A: Soliton stability in coupled Burgers-swept-KdV

Take a sech^2 soliton IC for v with u initially close to (but not exactly) v^2/2, propagate the coupled system long-time, and study whether the soliton structure survives.

## PDE — Coupled Burgers-swept-KdV system (Holm et al. 2025)

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = 1, ν = 1 (both coupling/dispersion coefficients normalized to 1). On periodic domain x ∈ [-15, 15], Nx = 256 grid points.

In the special reduction `m := u - v^2/2 = 0`, the system reduces to a Gardner equation `v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0`.


## Initial condition
v(x, 0) = 2 * sech^2(x + 5)
u(x, 0) = 0.5 * v(x, 0)^2 + 0.2 * v(x, 0)
  (Note: u != v^2/2 exactly, so we are perturbed from the m=0 Gardner reduction by 0.2 v.)

## Final time
T = 8.0

## Required output
Save to: `pred_results/T_A.npy`
Output shape: shape (n_snapshots, 2, 256) where dim-1 channels are (u, v); save at least 5 snapshots evenly spaced from t=0 to t=T_final. The LAST snapshot is what eval focuses on but having time-series is useful for diagnostics.

## Phenomenon target (this is the eval criterion)
Final v(x, T) should still contain a single dominant peak with amplitude >= 0.5 of the initial 2.0. mass(v) should drift < 8%. Both u and v should stay bounded (|max| < 15).

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
5. The script must save the output at `pred_results/T_A.npy` with the correct shape.
6. After the two writes, return ONE short sentence describing your numerical scheme.
