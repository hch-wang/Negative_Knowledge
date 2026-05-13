You are studying a real coupled PDE system. This is round 2 of an autoresearch iteration. Round 1 failed.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round2
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round2/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round2/reasoning.md (under 500 words: Approach / Method / Risks / Use of r1 finding / Use of bank)

# Sub-task T_A: Soliton stability in coupled Burgers-swept-KdV

Take a sech^2 soliton IC for v with u initially close to (but not exactly) v^2/2, propagate the coupled system long-time, and study whether the soliton structure survives.

## PDE — Coupled Burgers-swept-KdV system (Holm et al. 2025)

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = 1, ν = 1. On periodic domain x ∈ [-15, 15], Nx = 256.


## Initial condition
v(x, 0) = 2 * sech^2(x + 5)
u(x, 0) = 0.5 * v(x, 0)^2 + 0.2 * v(x, 0)
  (Note: u != v^2/2 exactly, so we are perturbed from the m=0 Gardner reduction by 0.2 v.)

## Final time
T = 8.0

## Required output
Save to: `pred_results/T_A.npy`
Output shape: shape (n_snapshots, 2, 256) where dim-1 channels are (u, v); save at least 5 snapshots evenly spaced from t=0 to t=T_final. The LAST snapshot is what eval focuses on but having time-series is useful for diagnostics.
IMPORTANT: include at least 5 snapshots so eval can measure conservation over time.

## Phenomenon target (this is the eval criterion)
Final v(x, T) should still contain a single dominant peak with amplitude >= 0.5 of the initial 2.0. mass(v) should drift < 8%. Both u and v should stay bounded (|max| < 15).

There is NO closed-form reference solution. Eval checks (deterministically): finiteness, mass conservation of v, peak count via scipy.signal.find_peaks, amplitude check, boundedness.

## Memory: your own round-1 attempt's finding record

You ALREADY attempted this task once. Here is what happened:

### Round-1 candidate's method (your previous approach)
## Method

### Round-1 candidate.py (first 1500 chars)
```python
"""
Coupled Burgers-swept-KdV soliton stability simulation.
PDE:
  u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx (u v)

Spatial: pseudo-spectral (FFT) on periodic domain x in [-15, 15], Nx=256
Time:    RK4 with adaptive sub-stepping, dt=1e-3
"""

import numpy as np
import os

# Domain
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]

# Wavenumbers for spectral derivatives
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)

# Dealiasing mask (2/3 rule)
k_max = np.max(np.abs(k))
dealias = np.abs(k) <= (2.0 / 3.0) * k_max


def spectral_deriv(f, order=1):
    """Compute d^order f / dx^order using FFT."""
    fh = np.fft.fft(f)
    fh *= dealias
    return np.real(np.fft.ifft((1j * k) ** order * fh))


def rhs(u, v):
    """Compute time derivatives for u and v."""
    # Spectral derivatives
    u_x = spectral_deriv(u, 1)
    v_x = spectral_deriv(v, 1)
    v_xx = spectral_deriv(v, 2)
    v_xxx = spectral_deriv(v, 3)

    # u_t = -3 u u_x - d/dx(3 v^2 + v_xx)
    #      = -3 u u_x - 6 v v_x - v_xxx
    u_t = -3.0 * u * u_x - 6.0 * v * v_x - v_xxx

    # v_t = -6 v v_x - v_xxx - d/dx(u v)
    #      = -6 v v_x - v_xxx - u_x v - u v_x
    v_t = -6.0 * v * v_x - v_xxx - u_x * v - u * v_x

    return u_t, v_t


def rk4_step(u, v, dt):
    """One RK4 step."""
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * 
```

### Round-1 outcome
Output contains NaN/Inf (numerical blow-up). All 256 values invalid.

### Round-1 exec.log tail
```
  u_t = -3.0 * u * u_x - 6.0 * v * v_x - v_xxx
${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round1/candidate.py:45: RuntimeWarning: invalid value encountered in subtract
  u_t = -3.0 * u * u_x - 6.0 * v * v_x - v_xxx
${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round1/candidate.py:49: RuntimeWarning: overflow encountered in multiply
  v_t = -6.0 * v * v_x - v_xxx - u_x * v - u * v_x
${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round1/candidate.py:49: RuntimeWarning: invalid value encountered in subtract
  v_t = -6.0 * v * v_x - v_xxx - u_x * v - u * v_x
${VENV}/lib/python3.14/site-packages/numpy/fft/_pocketfft.py:101: RuntimeWarning: invalid value encountered in fft
  return ufunc(a, fct, axes=[(axis,), (), (axis,)], out=out)

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
5. The script must save the output at `pred_results/T_A.npy` with the correct shape.
6. After the two writes, return ONE short sentence describing your numerical scheme.
