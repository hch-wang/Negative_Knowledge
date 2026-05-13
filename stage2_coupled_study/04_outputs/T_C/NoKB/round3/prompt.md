You are in round 3 of an autoresearch iteration on a hard PDE problem. Round 1 and round 2 both failed. This is your last attempt.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round3
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round3/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_C/NoKB/round3/reasoning.md (under 500 words: Synthesis of prior failures / Method / Use of bank / Final risks)

# Sub-task T_C: Burgers bore interacting with a KdV soliton

Initialize u as a smoothed bore (descending step) and v as a soliton to its left moving rightward. Study what happens when the soliton encounters the bore: does it transmit (refract), reflect, fuse, or get destroyed?

## PDE — Coupled Burgers-swept-KdV system

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```
γ = ν = 1. Periodic x ∈ [-15, 15], Nx = 256.


## Initial condition
u(x, 0) = 1.5 * (1 - tanh(x / 0.5)) / 2     (smoothed bore: u_L = 1.5, u_R = 0, transition centered at 0 with width 0.5)
v(x, 0) = 1.5 * sech^2(x + 8)               (KdV soliton, amplitude 1.5, initially at x = -8, will move right toward bore)

## Final time
T = 8.0

## Output
Save to: `pred_results/T_C.npy`
Output shape: shape (n_snapshots, 2, 256); save 5+ snapshots so the bore-soliton encounter is visible.
IMPORTANT: save at least 5 snapshots so mass conservation can be measured over time.

## Phenomenon target
Final v should still contain a recognizable peak with amplitude >= 0.5 (soliton survived). u should stay bounded (|u_max| < 5). Bore should not have blown up.

## Your prior failed attempts

### Round 1 attempt
Approach (excerpt from reasoning.md):
> # Reasoning: T_C Burgers Bore / KdV Soliton Interaction

## Method

**Spatial discretization:** Pseudo-spectral (Fourier) on the periodic domain [-15, 15] with Nx=256 points. All spatial derivatives (first through third order) are computed via FFT with the standard spectral derivative formula d^n/dx

candidate.py (first 800 chars):
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
def deri
```

Outcome: NaN/Inf in output (numerical blow-up)
Diagnostics: {"all_finite": false, "n_nan": 3584, "useful": false}


### Round 2 attempt
Approach (excerpt from reasoning.md):
> # Round 2 Reasoning

## Method

Standard explicit RK4 spectral method with a drastically reduced time step (dt = 1e-4) and 2/3-rule dealiasing. The domain is periodic on [-15, 15] with Nx=256. Spatial derivatives are computed in Fourier space. Ten snapshots are recorded evenly across T=8. A safety c

candidate.py (first 800 chars):
```python
"""
Coupled Burgers-swept-KdV system: bore-soliton interaction (Round 2)
u_t + 3 u u_x = -d/dx(3v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -d/dx(u v)
Periodic domain x in [-15, 15], Nx=256, T=8.0

Round 1 failed due to numerical blow-up (overflow in nonlinear terms).
Round 2 fix: much smaller dt (adaptive CFL), split-step approach with
implicit linear part and explicit nonlinear part, plus amplitude clipping
as a safety valve.
"""

import numpy as np
from scipy.fft import fft, ifft, fftfreq
import os

# ---- Grid ----
L = 30.0
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers for spectral differentiation
k = 2 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)
# Anti-aliasing mask: 2/3 rule
k_max_abs = np.max(np.abs(k))
alias_thresh = 2.0 / 3.0 * k_max_abs
dealias_mask = (n
```

Outcome: finite but did not satisfy phenomenon: u_max 5.00 too large (bore blew up)
Diagnostics: {"all_finite": true, "mass_v0": 2.9999977863409164, "mass_vT": 4.064594622671604, "mass_drift_rel": 0.3548658739609175, "u_max": 5.0, "v_max": 5.0, "bounded": true, "vT_max": 5.0, "vT_min": -5.0, "n_dominant_peaks_vT": 22, "useful": false}


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
