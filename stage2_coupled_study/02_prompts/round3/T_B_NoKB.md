You are in round 3 of an autoresearch iteration on a hard PDE problem. Round 1 and round 2 both failed. This is your last attempt.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round3
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round3/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_B/NoKB/round3/reasoning.md (under 500 words: Synthesis of prior failures / Method / Use of bank / Final risks)

# Sub-task T_B: Gaussian wave packet -> soliton train decomposition

Initialize v as a localized Gaussian wave packet in v (u=0 initially) and check whether the dispersive coupling decomposes it into a train of solitons (a hallmark of KdV-type integrable inverse scattering).

## PDE — Coupled Burgers-swept-KdV system

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```
γ = ν = 1. Periodic x ∈ [-15, 15], Nx = 256.


## Initial condition
v(x, 0) = 4 * exp(-((x + 5)^2) / 2.25)   (Gaussian, amplitude 4, width sigma=1.5)
u(x, 0) = 0

## Final time
T = 6.0

## Output
Save to: `pred_results/T_B.npy`
Output shape: shape (n_snapshots, 2, 256) where dim-1 channels are (u, v); save at least 5 snapshots. Eval focuses on final snapshot.
IMPORTANT: save at least 5 snapshots so mass conservation can be measured over time.

## Phenomenon target
Final v should contain >= 2 well-separated peaks each with amplitude >= 0.8 (soliton train). mass(v) drift < 8%.

## Your prior failed attempts

### Round 1 attempt
Approach (excerpt from reasoning.md):
> # Reasoning Note — T_B: Gaussian Soliton Train Decomposition

## Method

**Spatial discretization:** Pseudo-spectral (Fourier) method on the periodic domain x in [-15, 15] with Nx=256 grid points. All spatial derivatives (first, second, third) are computed in Fourier space via multiplication by (ik)

candidate.py (first 800 chars):
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
 
```

Outcome: NaN/Inf in output (numerical blow-up)
Diagnostics: {"all_finite": false, "n_nan": 512, "useful": false}


### Round 2 attempt
Approach (excerpt from reasoning.md):
> # Reasoning — T_B Round 2

## Method

Pseudospectral spatial discretization (256 Fourier modes) with 2/3-rule dealiasing to suppress aliasing-driven blow-up, combined with scipy `solve_ivp` (RK45) for adaptive time-stepping with rtol=1e-6, atol=1e-8, max_step=0.01.  All nonlinear products are dealia

candidate.py (first 800 chars):
```python
"""
T_B Round 2: Gaussian wave packet -> soliton train decomposition
Coupled Burgers-swept-KdV system on periodic domain x in [-15, 15]

u_t + 3 u u_x = -d/dx(3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -d/dx(u v)

Round 1 blew up due to insufficient time-step control.
Round 2 fixes: adaptive RK45 via scipy.integrate.solve_ivp + 2/3 dealiasing.
"""

import numpy as np
import os
from scipy.integrate import solve_ivp

# Grid
Nx = 256
L = 30.0  # total domain length [-15, 15]
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for spectral differentiation
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi

# 2/3 dealiasing mask
k_max = np.max(np.abs(k))
dealias = np.abs(k) <= (2.0 / 3.0) * k_max

def deriv_spectral(f_hat):
    """Compute d/dx f from its hat, return in physical space."""
 
```

Outcome: finite but did not satisfy phenomenon: non-finite or unbounded
Diagnostics: {"all_finite": true, "mass_v0": 10.634723105433096, "mass_vT": 10.63472310543309, "mass_drift_rel": 5.011010127267179e-16, "u_max": 59.40796253001846, "v_max": 4.437344291969205, "bounded": false, "useful": false}


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
