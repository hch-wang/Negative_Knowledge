You are studying a real coupled PDE system. This is round 2 of an autoresearch iteration. Round 1 failed.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round2
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round2/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round2/reasoning.md (under 500 words: Approach / Method / Risks / Use of r1 finding / Use of bank)

# Sub-task T_C: Burgers bore interacting with a KdV soliton

Initialize u as a smoothed bore (descending step) and v as a soliton to its left moving rightward. Study what happens when the soliton encounters the bore: does it transmit (refract), reflect, fuse, or get destroyed?

## PDE — Coupled Burgers-swept-KdV system (Holm et al. 2025)

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = 1, ν = 1. On periodic domain x ∈ [-15, 15], Nx = 256.


## Initial condition
u(x, 0) = 1.5 * (1 - tanh(x / 0.5)) / 2     (smoothed bore: u_L = 1.5, u_R = 0, transition centered at 0 with width 0.5)
v(x, 0) = 1.5 * sech^2(x + 8)               (KdV soliton, amplitude 1.5, initially at x = -8, will move right toward bore)

## Final time
T = 8.0

## Required output
Save to: `pred_results/T_C.npy`
Output shape: shape (n_snapshots, 2, 256); save 5+ snapshots so the bore-soliton encounter is visible.
IMPORTANT: include at least 5 snapshots so eval can measure conservation over time.

## Phenomenon target (this is the eval criterion)
Final v should still contain a recognizable peak with amplitude >= 0.5 (soliton survived). u should stay bounded (|u_max| < 5). Bore should not have blown up.

There is NO closed-form reference solution. Eval checks (deterministically): finiteness, mass conservation of v, peak count via scipy.signal.find_peaks, amplitude check, boundedness.

## Memory: your own round-1 attempt's finding record

You ALREADY attempted this task once. Here is what happened:

### Round-1 candidate's method (your previous approach)
## Method

### Round-1 candidate.py (first 1500 chars)
```python
"""
Coupled Burgers-swept-KdV system: bore-soliton interaction
u_t + 3 u u_x = -d/dx(3v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -d/dx(u v)
Periodic domain x in [-15, 15], Nx=256, T=8.0
"""

import numpy as np
from scipy.fft import fft, ifft, fftfreq
import os

# ---- Grid ----
L = 30.0          # domain length
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for spectral differentiation
k = 2 * np.pi / L * fftfreq(Nx, d=1.0/Nx)
# Anti-aliasing: zero out top 1/3 of wavenumbers
k_max = np.max(np.abs(k))
k_alias = 2.0 / 3.0 * k_max
k_dealias = np.where(np.abs(k) <= k_alias, k, 0.0)

# ---- Initial conditions ----
def sech2(x):
    return 1.0 / np.cosh(x)**2

u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 * sech2(x + 8.0)

# ---- Spectral derivatives ----
def deriv(f, order=1):
    """Compute d^order f / dx^order spectrally with dealiasing."""
    fh = fft(f)
    return np.real(ifft((1j * k_dealias)**order * fh))

def rhs(u, v):
    """Compute time derivatives for u and v."""
    # u_t = -3 u u_x - d/dx(3v^2 + v_xx)
    u_x = deriv(u, 1)
    v_x = deriv(v, 1)
    v_xx = deriv(v, 2)

    # RHS for u
    bracket_u = 3.0 * v**2 + v_xx
    u_t = -3.0 * u * u_x - deriv(bracket_u, 1)

    # v_t = -6 v v_x - v_xxx - d/dx(u v)
    v_xxx = deriv(v, 3)
    bracket_v = u * v
    v_t = -6.0 * v * v_x - v_xxx - deriv(bracket_v, 1)

    return u_t, v_t

# ---- Time integration: RK4 ----
T = 8.0
# CFL-based dt: dispersive term v_xxx needs small dt
# Conservative ch
```

### Round-1 outcome
Output contains NaN/Inf (numerical blow-up). All 256 values invalid.

### Round-1 exec.log tail
```
  bracket_u = 3.0 * v**2 + v_xx
${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round1/candidate.py:47: RuntimeWarning: overflow encountered in multiply
  u_t = -3.0 * u * u_x - deriv(bracket_u, 1)
${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round1/candidate.py:36: RuntimeWarning: invalid value encountered in multiply
  return np.real(ifft((1j * k_dealias)**order * fh))
${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round1/candidate.py:51: RuntimeWarning: overflow encountered in multiply
  bracket_v = u * v
${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round1/candidate.py:52: RuntimeWarning: overflow encountered in multiply
  v_t = -6.0 * v * v_x - v_xxx - deriv(bracket_v, 1)

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
5. The script must save the output at `pred_results/T_C.npy` with the correct shape.
6. After the two writes, return ONE short sentence describing your numerical scheme.
