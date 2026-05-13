You are studying a real coupled PDE system. Your job: write a Python script that numerically solves the system from the specified initial condition for the specified final time, save the (u, v) field at multiple snapshots, and write a reasoning note describing your method, your use of any provided memory, and the risks.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round1
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round1/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round1/reasoning.md (under 500 words: Approach / Numerical method / Risks / Use of memory)

# Sub-task T_B: Gaussian wave packet -> soliton train decomposition

Initialize v as a localized Gaussian wave packet in v (u=0 initially) and check whether the dispersive coupling decomposes it into a train of solitons (a hallmark of KdV-type integrable inverse scattering).

## PDE — Coupled Burgers-swept-KdV system (Holm et al. 2025)

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = 1, ν = 1 (both coupling/dispersion coefficients normalized to 1). On periodic domain x ∈ [-15, 15], Nx = 256 grid points.

In the special reduction `m := u - v^2/2 = 0`, the system reduces to a Gardner equation `v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0`.


## Initial condition
v(x, 0) = 4 * exp(-((x + 5)^2) / 2.25)   (Gaussian, amplitude 4, width sigma=1.5)
u(x, 0) = 0

## Final time
T = 6.0

## Required output
Save to: `pred_results/T_B.npy`
Output shape: shape (n_snapshots, 2, 256) where dim-1 channels are (u, v); save at least 5 snapshots. Eval focuses on final snapshot.

## Phenomenon target (this is the eval criterion)
Final v should contain >= 2 well-separated peaks each with amplitude >= 0.8 (soliton train). mass(v) drift < 8%.

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
5. The script must save the output at `pred_results/T_B.npy` with the correct shape.
6. After the two writes, return ONE short sentence describing your numerical scheme.
