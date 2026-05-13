You are in round 3 of an autoresearch iteration on a hard PDE problem. Round 1 and round 2 both failed. This is your last attempt.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_C/PosOnly/round3
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_C/PosOnly/round3/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_C/PosOnly/round3/reasoning.md (under 500 words: Synthesis of prior failures / Method / Use of bank / Final risks)

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
> # Reasoning: T_C Burgers Bore + KdV Soliton

## Method

**Spatial discretization:** Fourier pseudospectral on the periodic domain [-15, 15] with Nx=256. All spatial derivatives (u_x, v_x, v_xx, v_xxx) are computed via FFT multiplication by ik or ik^3. 2/3 dealiasing is applied to nonlinear products 

candidate.py (first 800 chars):
```python
"""
T_C: Burgers bore interacting with a KdV soliton
Coupled Burgers-swept-KdV system:
  u_t + 3 u u_x = -dx(3v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -dx(u v)

Domain: x in [-15, 15], Nx=256, T=8.0
Method: Fourier pseudospectral + IMEX-Crank-Nicolson
  - dispersive (v_xxx) term handled implicitly (CN)
  - all nonlinear and coupling terms handled explicitly
  - Burgers component (3 u u_x) treated explicitly via spectral differentiation
"""

import numpy as np
import os

# Grid
L = 30.0  # domain length [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers
k = 2 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)
ik = 1j * k
ik3 = 1j * k**3

# Initial conditions
u = 1.5 * (1 - np.tanh(x / 0.5)) / 2.0
v = 1.5 / np.cosh(x + 8)**2

# Time stepping
T = 8.0
dt = 0.0005
N
```

Outcome: NaN/Inf in output (numerical blow-up)
Diagnostics: {"all_finite": false, "n_nan": 3584, "useful": false}


### Round 2 attempt
Approach (excerpt from reasoning.md):
> # Round-2 Reasoning

## Method

The round-2 solver uses a split-operator approach rather than a single uniform pseudospectral explicit scheme:

- **u (Burgers bore):** MUSCL-van Leer reconstruction + Godunov exact Riemann flux for the `-3 u u_x` hyperbolic term, which is TVD and handles the bore sho

candidate.py (first 800 chars):
```python
"""
T_C: Burgers bore interacting with a KdV soliton (Round 2)
Coupled Burgers-swept-KdV system:
  u_t + 3 u u_x = -dx(3v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -dx(u v)

Domain: x in [-15, 15], Nx=256, T=8.0
Method: Split operator approach
  - u: MUSCL-van Leer + Godunov flux for the 3u u_x term (TVD, handles bore)
    coupling term -dx(3v^2 + v_xx) added spectrally
  - v: IMEX-Crank-Nicolson spectral: CN on v_xxx (stiff), explicit on nonlinear
    coupling term -dx(u v) handled explicitly
  - dt chosen conservatively (CFL ~ 0.3 for Burgers, small enough for KdV)
"""

import numpy as np
import os

# Grid
L = 30.0  # domain length [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx_grid = L / Nx

# Wavenumbers
k = 2 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
ik3 =
```

Outcome: NaN/Inf in output (numerical blow-up)
Diagnostics: {"all_finite": false, "n_nan": 3072, "useful": false}


# Synthesis directive
Identify the COMMON FAILURE PATTERN between round 1 and round 2. Do not repeat either approach. If both used variants of explicit time integration, switch to implicit. If both used spectral with same dt, change the dt by an order of magnitude OR change the discretization. If both crashed on the nonlinear term, lower the IC amplitude or change variables.

## Memory: positive-knowledge bank (10 entries)

### kb-burgers-MUSCL-Godunov-shock-pass  (positive, domain=burgers)
  method: MUSCL-van Leer + Godunov + forward Euler
  claim: MUSCL with van Leer limiter + Godunov exact Riemann flux + forward Euler at CFL=0.45 achieves L1 error ~0.003 for Burgers shock at T=0.5, well inside the 0.10 acceptance band.
  applicability: For the Burgers component of coupled Burgers-swept-KdV, MUSCL+Godunov is a proven baseline for bore (shock) propagation. Use it as the default spatial scheme when a sharp bore must interact with a KdV soliton; its TVD property prevents Gibbs contamination in the Burgers sector.

### kb-burgers-Godunov-preShock-smooth  (positive, domain=burgers)
  method: Godunov upwind (exact Riemann for Burgers)
  claim: First-order Godunov upwind (exact Riemann) at adaptive CFL=0.8 correctly reproduces the smooth pre-shock Burgers profile at T=0.1: amplitude_range=2.00, single local maximum, max_jump=0.053 — consistent with a slightly steepened sine.
  applicability: For the early-time Burgers component (before bore forms) in Burgers-swept-KdV coupled problems, even first-order Godunov is sufficient. This establishes a lower-cost option for initialization or short-time baseline runs where the bore has not yet formed.

### kb-kdv-IMEX-CN-spectral-pass  (positive, domain=kdv)
  method: IMEX-Crank-Nicolson spectral (Fourier + CN-dispersion + explicit-nonlinear)
  claim: IMEX-spectral (Fourier pseudospectral + Crank-Nicolson on v_xxx + explicit nonlinear, dt=0.0005, Nt=4000) successfully propagates a KdV single soliton to T=2: peak at x=3.05, amplitude=2.03, mass=4.000 — all within specification.
  applicability: IMEX-CN is the recommended baseline for the KdV/swept-KdV component of coupled problems. The CN denominator (1 - dt/2 * ik^3) has magnitude >=1 so it is unconditionally stable for the dispersive stiffness — no exponential overflow. Transfer to coupled Burgers-swept-KdV: handle the swept dispersive term with CN and the Burgers-like coupling explicitly.

### kb-kdv-smallAmplitude-dispersiveRegime  (positive, domain=kdv)
  method: IMEX-spectral integrating-factor RK4
  claim: IMEX-spectral integrating-factor RK4 remains stable for amplitude-0.1 KdV IC, correctly reproducing the linear-dispersive regime: peak amplitude decays from 0.1 to ~0.052, 8 local maxima consistent with a dispersive wave train, no blow-up.
  applicability: In coupled Burgers-swept-KdV: small-amplitude KdV components (after energy exchange with the Burgers bore) will not form stable solitons — they disperse. This sets a threshold: soliton formation in the KdV/swept-KdV sector requires sufficient amplitude. Use this as a diagnostic: if post-interaction KdV amplitudes are O(0.1) or less, expect dispersive radiation rather than soliton trains.

### kb-shallowWater-LaxFriedrichs-stable-smeared  (positive, domain=shallow_water)
  method: Global Lax-Friedrichs flux + explicit Euler
  claim: Global Lax-Friedrichs flux with explicit Euler at CFL=0.4 solves the shallow water dam-break stably: h stays positive (h_min=1.452), mass conserved (mass_h=300.0), no NaN/Inf, max_jump=0.064 (smeared but bounded).
  applicability: Lax-Friedrichs is a reliable failsafe for shallow-water or shallow-water-like components in coupled problems when robustness is paramount and sharp shock resolution is not required. In coupled Burgers-swept-KdV experiments, LxF can serve as a stability baseline for validating more accurate schemes (HLL, MUSCL), but should not be the production scheme where bore sharpness matters for the soliton interaction measurement.

### kb-shallowWater-HLL-dam-break-pass  (positive, domain=shallow_water)
  method: HLL Riemann solver + explicit Euler
  claim: HLL (Harten-Lax-van Leer) Riemann solver with explicit Euler at CFL=0.4 solves the standard shallow water dam-break accurately: h_min=1.452, h_negative=false, mass conserved (mass_h=300.0), max_jump=0.090, all-finite.
  applicability: HLL is the recommended Riemann solver for any hyperbolic component in a coupled Burgers-swept-KdV system when the solution may include near-dry or variable-depth regions. Its positivity-preservation and entropy compliance make it safer than Roe for robustness, and it resolves shocks more sharply than Lax-Friedrichs.

### kb-kdv-spectral-solitonAmplitude-conservation  (positive, domain=kdv)
  method: IMEX-CN spectral and IMEX-IF RK4 spectral
  claim: Fourier pseudospectral IMEX methods (IMEX-CN and IMEX-IF RK4) both conserve KdV soliton amplitude within ~2% and mass within <1% over T=2 when correctly implemented with stable time stepping, even without dealiasing (IMEX-CN case).
  applicability: Spectral IMEX methods are the preferred discretization for tracking soliton amplitude and phase in the KdV/swept-KdV sector of coupled problems. For Gaussian decomposition into a soliton train, the mass and amplitude conservation properties of these methods ensure that decomposition coefficients remain meaningful over multi-soliton propagation times.

### kb-general-firstOrder-Godunov-preShock-baseline  (positive, domain=general)
  method: First-order Godunov (exact Riemann) / Godunov flux as MUSCL base
  claim: First-order Godunov (exact Riemann flux) at adaptive CFL is a reliable, low-cost baseline for hyperbolic conservation laws in smooth or pre-shock regimes: demonstrated for Burgers T=0.1 (A2) with correct smooth profile, and as component of MUSCL scheme for Burgers T=0.5 pilot.
  applicability: For coupled Burgers-swept-KdV: use Godunov flux as the foundation for the Burgers operator at any time horizon. Before shock formation, first-order Godunov alone suffices; after shock formation, upgrade to MUSCL+Godunov. The entropy-consistent Godunov flux ensures no spurious entropy violations in the bore region during soliton interaction.

### kb-gardner-G2-IMEX-CN-dealiased-stableRadiation  (positive, domain=gardner)
  method: IMEX-Crank-Nicolson spectral with 2/3 dealiasing
  claim: IMEX-CN spectral with 2/3 dealiasing (CN on v_xxx, explicit on 6vv_x + (3/2)v^2 v_x, dt=0.0005) is numerically stable for Gardner at IC amplitude 1.5 over T=2: all-finite, mass=3.000 conserved. However, the KdV-style sech^2 IC is NOT a true Gardner soliton — the wave radiates and amplitude decays to 0.612, peak migrates to x=-3.52, 13 local maxima (substantial radiation).
  applicability: IMEX-CN spectral with 2/3 dealiasing is the recommended stable method for the Gardner component of Burgers-swept-KdV (m=0 reduction). However, correctness depends critically on using a proper Gardner soliton IC, not a KdV sech^2 IC. For soliton-stability and Gaussian decomposition tasks, always use the Gardner soliton parametrization; KdV ICs at the same amplitude will produce spurious radiation trains that contaminate any bore-soliton interaction measurement.

### kb-gardner-KdV-method-transfer-moderate-amplitude  (positive, domain=gardner)
  method: IMEX-Crank-Nicolson spectral with 2/3 dealiasing (positive transfer); IFRK4 (negative transfer)
  claim: IMEX-CN spectral with 2/3 dealiasing — the method validated on KdV (kb-kdv-IMEX-CN-spectral-pass, amp 2.0, dt=0.0005) — transfers cleanly to Gardner at moderate amplitudes in the range [1, 2]: G2 (amp 1.5, dt=0.0005) is all-finite with mass conserved, confirming numerical stability. By contrast, IFRK4 (kb-kdv-IFRK4-blowup) does NOT transfer: it blows up on KdV itself, making it doubly unsuitable for Gardner where the cubic term adds an additional explicit-stiffness channel.
  applicability: For the Gardner-reduction (m=0) leg of Burgers-swept-KdV: adopt IMEX-CN spectral + 2/3 dealiasing as the baseline method, transferring directly from the validated KdV solver. No re-engineering of the dispersive (v_xxx) treatment is needed; only the nonlinear stage must be extended to include the cubic term 6vv_x + (3/2)v^2 v_x. Do NOT attempt to port IFRK4 to Gardner: it failed even on the simpler KdV equation and the Gardner cubic nonlinearity would only worsen the overflow in exp(ik^3 t) or tighten the stability constraint further. For amplitude > 2, this positive transfer no longer holds (see kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup); re-evaluate dt before any amplitude increase.


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
