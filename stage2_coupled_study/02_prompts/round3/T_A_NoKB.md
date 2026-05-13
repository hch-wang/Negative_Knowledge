You are in round 3 of an autoresearch iteration on a hard PDE problem. Round 1 and round 2 both failed. This is your last attempt.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round3
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round3/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_A/NoKB/round3/reasoning.md (under 500 words: Synthesis of prior failures / Method / Use of bank / Final risks)

# Sub-task T_A: Soliton stability in coupled Burgers-swept-KdV

Take a sech^2 soliton IC for v with u initially close to (but not exactly) v^2/2, propagate the coupled system long-time, and study whether the soliton structure survives.

## PDE — Coupled Burgers-swept-KdV system

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```
γ = ν = 1. Periodic x ∈ [-15, 15], Nx = 256.


## Initial condition
v(x, 0) = 2 * sech^2(x + 5)
u(x, 0) = 0.5 * v(x, 0)^2 + 0.2 * v(x, 0)
  (Note: u != v^2/2 exactly, so we are perturbed from the m=0 Gardner reduction by 0.2 v.)

## Final time
T = 8.0

## Output
Save to: `pred_results/T_A.npy`
Output shape: shape (n_snapshots, 2, 256) where dim-1 channels are (u, v); save at least 5 snapshots evenly spaced from t=0 to t=T_final. The LAST snapshot is what eval focuses on but having time-series is useful for diagnostics.
IMPORTANT: save at least 5 snapshots so mass conservation can be measured over time.

## Phenomenon target
Final v(x, T) should still contain a single dominant peak with amplitude >= 0.5 of the initial 2.0. mass(v) should drift < 8%. Both u and v should stay bounded (|max| < 15).

## Your prior failed attempts

### Round 1 attempt
Approach (excerpt from reasoning.md):
> # Reasoning: T_A Coupled Burgers-swept-KdV Soliton Stability

## Method

**Spatial discretization:** Pseudo-spectral method using the Fast Fourier Transform (FFT) on the periodic domain x in [-15, 15] with Nx=256 grid points. All spatial derivatives (u_x, v_x, v_xx, v_xxx) are computed exactly in Fo

candidate.py (first 800 chars):
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
    """Compute ti
```

Outcome: NaN/Inf in output (numerical blow-up)
Diagnostics: {"all_finite": false, "n_nan": 3072, "useful": false}


### Round 2 attempt
Approach (excerpt from reasoning.md):
> # Reasoning — Round 2

## Method

Pseudo-spectral spatial discretisation (Nx=256, periodic, 2/3 de-aliasing) with an **integrating-factor RK4 (IFRK4)** time integrator.

The key change is that the dominant stiff term `v_xxx` is handled analytically via an exponential integrating factor. We work in t

candidate.py (first 800 chars):
```python
"""
Coupled Burgers-swept-KdV soliton stability simulation — Round 2.
PDE:
  u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx (u v)

Round-1 blew up due to stiff high-k modes and no step-size control.
Fix: operator splitting — treat dispersive/stiff linear parts (v_xxx, u_xxx-like)
with an implicit/exact spectral exponential integrator (integrating factor),
and the nonlinear parts with explicit RK4, using a smaller dt=2e-4 for safety.

Alternatively (simpler and robust): use spectral RHS + RK4 with much smaller dt
and aggressive de-aliasing + a mild spectral filter to kill aliasing energy.
"""

import numpy as np
import os

# ---------------------------------------------------------------------------
# Domain
# -----------------------------------------------------------
```

Outcome: finite but did not satisfy phenomenon: amp ratio 0.48 < 0.5
Diagnostics: {"all_finite": true, "mass_v0": 3.9999999926838448, "mass_vT": 3.9999999926838448, "mass_drift_rel": 0.0, "u_max": 5.528529398231534, "v_max": 1.9969513439288096, "bounded": true, "v0_max": 1.9969513439288096, "vT_max": 0.9622033754475846, "amp_ratio": 0.48183616409728947, "n_dominant_peaks_vT": 4, "useful": false}


# Synthesis directive
Identify the COMMON FAILURE PATTERN between round 1 and round 2. Do not repeat either approach. If both used variants of explicit time integration, switch to implicit. If both used spectral with same dt, change the dt by an order of magnitude OR change the discretization. If both crashed on the nonlinear term, lower the IC amplitude or change variables.

## Memory: no knowledge bank.


## Reasoning note structure
- **Pattern from r1+r2**: what's the COMMON THING that failed in both?
- **New method**: what's qualitatively different in r3?
- **Use of bank**: (if non-empty) cite bank entries by `id`
- **Final risks**

## Hard constraints
1. Use Write tool EXACTLY TWICE.
2. Only numpy, scipy, matplotlib.
3. Script runs as `python candidate.py` from working dir.
4. No Read of other files, no Bash, no Edit.
5. After writes, ONE short sentence describing your method.
