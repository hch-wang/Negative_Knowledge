You are studying a real coupled PDE system. This is round 2 of an autoresearch iteration. Round 1 failed.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round2
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round2/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round2/reasoning.md (under 500 words: Approach / Method / Risks / Use of r1 finding / Use of bank)

# Sub-task T_B: Gaussian wave packet -> soliton train decomposition

Initialize v as a localized Gaussian wave packet in v (u=0 initially) and check whether the dispersive coupling decomposes it into a train of solitons (a hallmark of KdV-type integrable inverse scattering).

## PDE — Coupled Burgers-swept-KdV system (Holm et al. 2025)

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = 1, ν = 1. On periodic domain x ∈ [-15, 15], Nx = 256.


## Initial condition
v(x, 0) = 4 * exp(-((x + 5)^2) / 2.25)   (Gaussian, amplitude 4, width sigma=1.5)
u(x, 0) = 0

## Final time
T = 6.0

## Required output
Save to: `pred_results/T_B.npy`
Output shape: shape (n_snapshots, 2, 256) where dim-1 channels are (u, v); save at least 5 snapshots. Eval focuses on final snapshot.
IMPORTANT: include at least 5 snapshots so eval can measure conservation over time.

## Phenomenon target (this is the eval criterion)
Final v should contain >= 2 well-separated peaks each with amplitude >= 0.8 (soliton train). mass(v) drift < 8%.

There is NO closed-form reference solution. Eval checks (deterministically): finiteness, mass conservation of v, peak count via scipy.signal.find_peaks, amplitude check, boundedness.

## Memory: your own round-1 attempt's finding record

You ALREADY attempted this task once. Here is what happened:

### Round-1 candidate's method (your previous approach)
## Method

### Round-1 candidate.py (first 1500 chars)
```python
"""
T_B: Gaussian wave packet -> soliton train decomposition
Coupled Burgers-swept-KdV system on periodic domain x in [-15, 15]

u_t + 3 u u_x = -d/dx(3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -d/dx(u v)
"""

import numpy as np
import os

# Grid
Nx = 256
L = 30.0  # total domain length [-15, 15]
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for spectral differentiation
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi

# Initial conditions
v = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u = np.zeros(Nx)

# Final time and snapshots
T = 6.0
n_snapshots = 7
t_snapshots = np.linspace(0, T, n_snapshots)

# Storage
snapshots = []

def deriv_spectral(f, k):
    """Compute d/dx f using spectral method."""
    return np.real(np.fft.ifft(1j * k * np.fft.fft(f)))

def deriv3_spectral(f, k):
    """Compute d^3/dx^3 f using spectral method."""
    return np.real(np.fft.ifft(-1j * k**3 * np.fft.fft(f)))

def rhs(u, v, k):
    """Compute RHS of the coupled system."""
    # u equation: u_t = -3 u u_x - d/dx(3 v^2 + v_xx)
    u_x = deriv_spectral(u, k)
    v_xx = deriv_spectral(deriv_spectral(v, k), k)
    rhs_inner = 3.0 * v**2 + v_xx
    drhs_inner_dx = deriv_spectral(rhs_inner, k)
    du_dt = -3.0 * u * u_x - drhs_inner_dx

    # v equation: v_t = -6 v v_x - v_xxx - d/dx(u v)
    v_x = deriv_spectral(v, k)
    v_xxx = deriv3_spectral(v, k)
    uv = u * v
    duv_dx = deriv_spectral(uv, k)
    dv_dt = -6.0 * v * v_x - v_xxx - duv_dx

    return du_dt, dv_dt

def rk4_step(u, v, k, dt
```

### Round-1 outcome
Output contains NaN/Inf (numerical blow-up). All 256 values invalid.

### Round-1 exec.log tail
```
  return ufunc(a, fct, axes=[(axis,), (), (axis,)], out=out)
${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round1/candidate.py:35: RuntimeWarning: invalid value encountered in multiply
  return np.real(np.fft.ifft(1j * k * np.fft.fft(f)))
${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round1/candidate.py:48: RuntimeWarning: overflow encountered in multiply
  du_dt = -3.0 * u * u_x - drhs_inner_dx
${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round1/candidate.py:53: RuntimeWarning: overflow encountered in multiply
  uv = u * v
${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round1/candidate.py:55: RuntimeWarning: overflow encountered in multiply
  dv_dt = -6.0 * v * v_x - v_xxx - duv_dx

```

### Round-2 task
Address what failed. If your previous method was numerically unstable, change it. If it produced wrong-shape output, fix the shape. If it produced wrong-phenomenon output, change parameters or method to recover the target phenomenon. Do NOT repeat the exact same approach.


## Memory: no knowledge bank provided

You have no prior knowledge bank for this problem family.


## Reasoning note structure
Write reasoning.md with these sections:
- **Method**: what changed vs round 1 and why
- **Use of r1 finding**: explicitly describe what went wrong in r1 and how the new method addresses it
- **Use of bank**: (if memory section is non-empty) explicitly cite which bank entries influenced your new choices by `id`
- **Risks**: 2-3 specific things that could still go wrong

## Hard constraints
1. Use Write tool EXACTLY TWICE.
2. Only numpy, scipy, matplotlib are available.
3. Script must run as `python candidate.py` from the working directory.
4. No Read of any file other than this prompt. No Bash. No Edit.
5. The script must save the output at `pred_results/T_B.npy` with the correct shape.
6. After the two writes, return ONE short sentence describing your numerical scheme.
