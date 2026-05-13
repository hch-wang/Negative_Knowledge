You are studying a real coupled PDE system. Your job: write a Python script that numerically solves the system from the specified initial condition for the specified final time, save the (u, v) field at multiple snapshots, and write a reasoning note describing your method, your use of any provided memory, and the risks.

Working directory: ${PROJECT_ROOT}/stage2/runs/T_B/PosOnly/round1
You will make EXACTLY TWO Write calls:
1) ${PROJECT_ROOT}/stage2/runs/T_B/PosOnly/round1/candidate.py
2) ${PROJECT_ROOT}/stage2/runs/T_B/PosOnly/round1/reasoning.md (under 500 words: Approach / Numerical method / Risks / Use of memory)

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

## Memory: positive-knowledge bank (10 entries)

Below are positive findings from prior component-PDE stress tests on Burgers, KdV, Shallow Water, and Gardner equations. These describe methods that WORKED in their tested regimes. They do NOT cover failure modes.

Each entry has: id, kind, domain, claim (or method+regime), evidence, applicability to coupled Burgers-swept-KdV.

### kb-burgers-MUSCL-Godunov-shock-pass  (positive, domain=burgers)
  method: MUSCL-van Leer + Godunov + forward Euler
  claim: MUSCL with van Leer limiter + Godunov exact Riemann flux + forward Euler at CFL=0.45 achieves L1 error ~0.003 for Burgers shock at T=0.5, well inside the 0.10 acceptance band.
  regime: inviscid Burgers, u0=-sin(pi*x), T=0.5 (post-shock), Nx=200, periodic
  applicability: For the Burgers component of coupled Burgers-swept-KdV, MUSCL+Godunov is a proven baseline for bore (shock) propagation. Use it as the default spatial scheme when a sharp bore must interact with a KdV soliton; its TVD property prevents Gibbs contamination in the Burgers sector.

### kb-burgers-Godunov-preShock-smooth  (positive, domain=burgers)
  method: Godunov upwind (exact Riemann for Burgers)
  claim: First-order Godunov upwind (exact Riemann) at adaptive CFL=0.8 correctly reproduces the smooth pre-shock Burgers profile at T=0.1: amplitude_range=2.00, single local maximum, max_jump=0.053 — consistent with a slightly steepened sine.
  regime: inviscid Burgers, u0=-sin(pi*x), T=0.1 (pre-shock, before t*=0.318), Nx=200
  applicability: For the early-time Burgers component (before bore forms) in Burgers-swept-KdV coupled problems, even first-order Godunov is sufficient. This establishes a lower-cost option for initialization or short-time baseline runs where the bore has not yet formed.

### kb-kdv-IMEX-CN-spectral-pass  (positive, domain=kdv)
  method: IMEX-Crank-Nicolson spectral (Fourier + CN-dispersion + explicit-nonlinear)
  claim: IMEX-spectral (Fourier pseudospectral + Crank-Nicolson on v_xxx + explicit nonlinear, dt=0.0005, Nt=4000) successfully propagates a KdV single soliton to T=2: peak at x=3.05, amplitude=2.03, mass=4.000 — all within specification.
  regime: KdV v0=2 sech^2(x+5), T=2.0, Nx=256, domain [-15,15]
  applicability: IMEX-CN is the recommended baseline for the KdV/swept-KdV component of coupled problems. The CN denominator (1 - dt/2 * ik^3) has magnitude >=1 so it is unconditionally stable for the dispersive stiffness — no exponential overflow. Transfer to coupled Burgers-swept-KdV: handle the swept dispersive term with CN and the Burgers-like coupling explicitly.

### kb-kdv-smallAmplitude-dispersiveRegime  (positive, domain=kdv)
  method: IMEX-spectral integrating-factor RK4
  claim: IMEX-spectral integrating-factor RK4 remains stable for amplitude-0.1 KdV IC, correctly reproducing the linear-dispersive regime: peak amplitude decays from 0.1 to ~0.052, 8 local maxima consistent with a dispersive wave train, no blow-up.
  regime: KdV v0=0.1 sech^2(x+5) (very small amplitude), T=2.0, Nx=256
  applicability: In coupled Burgers-swept-KdV: small-amplitude KdV components (after energy exchange with the Burgers bore) will not form stable solitons — they disperse. This sets a threshold: soliton formation in the KdV/swept-KdV sector requires sufficient amplitude. Use this as a diagnostic: if post-interaction KdV amplitudes are O(0.1) or less, expect dispersive radiation rather than soliton trains.

### kb-shallowWater-LaxFriedrichs-stable-smeared  (positive, domain=shallow_water)
  method: Global Lax-Friedrichs flux + explicit Euler
  claim: Global Lax-Friedrichs flux with explicit Euler at CFL=0.4 solves the shallow water dam-break stably: h stays positive (h_min=1.452), mass conserved (mass_h=300.0), no NaN/Inf, max_jump=0.064 (smeared but bounded).
  regime: Shallow water dam-break h=[2,1], u=0, T=0.4, Nx=200, g=1
  applicability: Lax-Friedrichs is a reliable failsafe for shallow-water or shallow-water-like components in coupled problems when robustness is paramount and sharp shock resolution is not required. In coupled Burgers-swept-KdV experiments, LxF can serve as a stability baseline for validating more accurate schemes (HLL, MUSCL), but should not be the production scheme where bore sharpness matters for the soliton interaction measurement.

### kb-shallowWater-HLL-dam-break-pass  (positive, domain=shallow_water)
  method: HLL Riemann solver + explicit Euler
  claim: HLL (Harten-Lax-van Leer) Riemann solver with explicit Euler at CFL=0.4 solves the standard shallow water dam-break accurately: h_min=1.452, h_negative=false, mass conserved (mass_h=300.0), max_jump=0.090, all-finite.
  regime: Shallow water dam-break h=[2,1], u=0, T=0.4, Nx=200, g=1, periodic
  applicability: HLL is the recommended Riemann solver for any hyperbolic component in a coupled Burgers-swept-KdV system when the solution may include near-dry or variable-depth regions. Its positivity-preservation and entropy compliance make it safer than Roe for robustness, and it resolves shocks more sharply than Lax-Friedrichs.

### kb-kdv-spectral-solitonAmplitude-conservation  (positive, domain=kdv)
  method: IMEX-CN spectral and IMEX-IF RK4 spectral
  claim: Fourier pseudospectral IMEX methods (IMEX-CN and IMEX-IF RK4) both conserve KdV soliton amplitude within ~2% and mass within <1% over T=2 when correctly implemented with stable time stepping, even without dealiasing (IMEX-CN case).
  regime: KdV v0=2 sech^2(x+5), T=2.0, Nx=256, domain [-15,15]
  applicability: Spectral IMEX methods are the preferred discretization for tracking soliton amplitude and phase in the KdV/swept-KdV sector of coupled problems. For Gaussian decomposition into a soliton train, the mass and amplitude conservation properties of these methods ensure that decomposition coefficients remain meaningful over multi-soliton propagation times.

### kb-general-firstOrder-Godunov-preShock-baseline  (positive, domain=general)
  method: First-order Godunov (exact Riemann) / Godunov flux as MUSCL base
  claim: First-order Godunov (exact Riemann flux) at adaptive CFL is a reliable, low-cost baseline for hyperbolic conservation laws in smooth or pre-shock regimes: demonstrated for Burgers T=0.1 (A2) with correct smooth profile, and as component of MUSCL scheme for Burgers T=0.5 pilot.
  regime: Burgers pre-shock (T<t*=0.318) and post-shock with MUSCL upgrade, Nx=200, periodic
  applicability: For coupled Burgers-swept-KdV: use Godunov flux as the foundation for the Burgers operator at any time horizon. Before shock formation, first-order Godunov alone suffices; after shock formation, upgrade to MUSCL+Godunov. The entropy-consistent Godunov flux ensures no spurious entropy violations in the bore region during soliton interaction.

### kb-gardner-G2-IMEX-CN-dealiased-stableRadiation  (positive, domain=gardner)
  method: IMEX-Crank-Nicolson spectral with 2/3 dealiasing
  claim: IMEX-CN spectral with 2/3 dealiasing (CN on v_xxx, explicit on 6vv_x + (3/2)v^2 v_x, dt=0.0005) is numerically stable for Gardner at IC amplitude 1.5 over T=2: all-finite, mass=3.000 conserved. However, the KdV-style sech^2 IC is NOT a true Gardner soliton — the wave radiates and amplitude decays to 0.612, peak migrates to x=-3.52, 13 local maxima (substantial radiation).
  regime: Gardner v0=1.5 sech^2(x+5), T=2.0, Nx=256, domain [-15,15], periodic
  applicability: IMEX-CN spectral with 2/3 dealiasing is the recommended stable method for the Gardner component of Burgers-swept-KdV (m=0 reduction). However, correctness depends critically on using a proper Gardner soliton IC, not a KdV sech^2 IC. For soliton-stability and Gaussian decomposition tasks, always use the Gardner soliton parametrization; KdV ICs at the same amplitude will produce spurious radiation trains that contaminate any bore-soliton interaction measurement.

### kb-gardner-KdV-method-transfer-moderate-amplitude  (positive, domain=gardner)
  method: IMEX-Crank-Nicolson spectral with 2/3 dealiasing (positive transfer); IFRK4 (negative transfer)
  claim: IMEX-CN spectral with 2/3 dealiasing — the method validated on KdV (kb-kdv-IMEX-CN-spectral-pass, amp 2.0, dt=0.0005) — transfers cleanly to Gardner at moderate amplitudes in the range [1, 2]: G2 (amp 1.5, dt=0.0005) is all-finite with mass conserved, confirming numerical stability. By contrast, IFRK4 (kb-kdv-IFRK4-blowup) does NOT transfer: it blows up on KdV itself, making it doubly unsuitable for Gardner where the cubic term adds an additional explicit-stiffness channel.
  regime: Gardner v0 = A sech^2(x+5), amp in [1,2], T=2.0, Nx=256, domain [-15,15], periodic
  applicability: For the Gardner-reduction (m=0) leg of Burgers-swept-KdV: adopt IMEX-CN spectral + 2/3 dealiasing as the baseline method, transferring directly from the validated KdV solver. No re-engineering of the dispersive (v_xxx) treatment is needed; only the nonlinear stage must be extended to include the cubic term 6vv_x + (3/2)v^2 v_x. Do NOT attempt to port IFRK4 to Gardner: it failed even on the simpler KdV equation and the Gardner cubic nonlinearity would only worsen the overflow in exp(ik^3 t) or tighten the stability constraint further. For amplitude > 2, this positive transfer no longer holds (see kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup); re-evaluate dt before any amplitude increase.


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
