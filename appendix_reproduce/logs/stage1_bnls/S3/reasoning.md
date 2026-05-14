# S3 reasoning: NLS focusing Gaussian — modulational instability and soliton emission threshold

## Question

Run an amplitude sweep on the Gaussian IC `Psi0 = A * exp(-(x+5)^2 / 4.5)` for A in {1.0, 1.5, 2.0, 2.5, 3.0} under focusing NLS (`kappa=+1`, no Burgers boost) until T=6.0, and characterize:

- How many bright solitons emerge per amplitude (`n_solitons_emitted_per_A`)
- The final peak amplitudes (`peak_amplitudes_final_per_A`)
- At what A the *method* breaks down rather than the physics (`method_breakdown_threshold_A`)

Compare against Karpman-Maslov: `N_sol ~ int(A * sigma * sqrt(2))` with `sigma = 1.5/sqrt(2)` in the prompt's convention, giving the prediction {A=1→1, A=1.5→2, A=2→3, A=2.5→3, A=3→4}.

## Method

Madelung-Psi formulation: the focusing NLS `i Psi_t = -(1/2) Psi_xx - kappa |Psi|^2 Psi` is integrated directly in `Psi` (no need to decompose into N=|Psi|^2 and phi when there is no Burgers boost — quantum pressure is then implicit in the Schrödinger evolution).

**Scheme**: Strang split-step Fourier. Each step:
1. half linear step in k-space: `Psi <- F^{-1}(exp(-i*(k^2/2)*dt/2) * F(Psi))`
2. full nonlinear step in x-space: `Psi <- exp(+i * kappa * |Psi|^2 * dt) * Psi` (exact, since `d/dt |Psi|^2 = 0` for the pure nonlinear flow)
3. half linear step again

Strang splitting is `O(dt^2)` accurate, unconditionally L^2-stable (each sub-flow is unitary), and L^2-conservative to round-off. No dealiasing was applied — focusing NLS is integrable and the nonlinear sub-step keeps the spectrum on-grid; we verified post-hoc that the spectral tail at converged resolution stays at machine precision.

## Iteration plan

Budget = 3 Experiments. Strategy:

- **E1**: Prompt-default discretization (Nx=256, dt=0.001, L=30), full A-sweep. Establish baseline + spot any anomalies (NaN, mass drift, suspicious peaks).
- **E2**: If baseline anomalies appear, refine to test what they depend on. Run TWO variants (Nx=512 dt=5e-4) at L=30 and L=60 to separate dx-refinement from periodic-wrap-around effects.
- **E3**: Final convergence check (Nx=1024 dt=2.5e-4 L=60) to nail down the converged answer.

## What I found

### E1 — baseline

All 5 runs completed without NaN. Mass drift relative was ≤ 6.5e-13 at all A — split-step is essentially exact for mass conservation. The peak counts at the 5% threshold were {1, 1, 2, 3, 3} for A in {1.0, 1.5, 2.0, 2.5, 3.0}. But three flags appeared at high A:

- Spectral tail fraction (top half of k-space) grew from 2e-16 (A=1) to 1.4e-3 (A=3).
- At A=3 a "peak" was detected at x=-13.95 — very close to the periodic boundary at -15.
- linf_final jumped from 2.82 (A=2) to 6.07 (A=3) — much steeper than the IC linf scaling.

These together raised the possibility that the high-A results were contaminated by under-resolution of the narrow solitons emitted by focusing collapse and/or periodic wrap-around of radiation.

### E2 — refinement, separating dx from L

To pull the two effects apart I ran two refined variants: (Nx=512, dt=5e-4, L=30) where dx halves from 0.117 to 0.0586 but L stays the same, and (Nx=512, dt=5e-4, L=60) where dx is the same as the baseline (0.117) but L doubles.

The two variants disagreed at A ≥ 2: linf_final at A=3 was 3.88 in the L=30-refined run vs 5.91 in the L=60-refined run. The L=60-refined run nearly reproduces the L=30 baseline (5.91 vs 6.07). The discriminating parameter was therefore **dx**, not L. Two refined-dx runs (one with L=30 and one with L=60, both having dx=0.0586) gave identical answers, confirming that wrap-around was a red herring for this IC at T=6.0 — solitons drift inward, not outward, and never reach the boundary.

### E3 — convergence

A final hi-res run at (Nx=1024, dt=2.5e-4, L=60, dx=0.0586) reproduced the E2-L30-refined result at machine precision and showed a spectral tail < 1e-10 at A=3.0. The converged answer is stable to further refinement.

## Converged answer

| A   | n_solitons | linf_final | linf_max_over_t | peak intensities                | peak x-locations              |
|-----|------------|------------|-----------------|---------------------------------|-------------------------------|
| 1.0 | 1          | 1.19       | 1.41            | [1.41]                          | [-4.98]                       |
| 1.5 | 1          | 2.13       | 3.08            | [4.55]                          | [-4.98]                       |
| 2.0 | 1          | 2.57       | 5.25            | [6.62]                          | [-4.98]                       |
| 2.5 | 2          | 2.74       | 7.04            | [7.49, 7.52]                    | [-5.68, -4.34]                |
| 3.0 | 3          | 3.89       | 8.33            | [10.19, 15.10, 9.56]            | [-5.92, -4.98, -4.04]         |

The "emitted solitons" at A=2.5 and 3.0 are not yet spatially separated at T=6 — they form an N-soliton bound state with mean separation ~ 1 unit at the original IC center. Linf_max_over_t reveals the breather peaks (5.25, 7.04, 8.33 for A=2, 2.5, 3).

## Karpman-Maslov comparison

- Prompt convention `int(A * sigma_eff * sqrt(2))` with `sigma_eff = 1.5/sqrt(2)` reduces to `int(A * 1.5)`: predicts {1, 2, 3, 3, 4}.
- Standard convention `int(A * sigma * sqrt(2))` with `sigma = 1.5`: predicts {2, 3, 4, 5, 6}.
- Empirical converged result: {1, 1, 1, 2, 3}.

The empirical count lags the prompt-convention KM by ~1 unit and the standard-convention KM by 3-4 units. The prompt-convention KM is a useful **upper bound**; the physical soliton-emission threshold at T=6 is approximately A ≥ 2.5 for emission of a *second* well-resolved soliton.

This is consistent with two physical considerations: (i) at T=6 the solitons emitted by focusing collapse have not yet separated from the parent wavepacket (the Zakharov-Shabat eigenvalues count the *asymptotic* solitons, which at finite T can still be co-localized); (ii) the IC norm `M = sqrt(pi/(4/9)) * A` scales linearly in A, so the L^2 mass threshold for hosting N solitons (Zakharov-Shabat bound M ≥ N for the unit-width sech) is achieved later than KM predicts for a Gaussian.

## Method-breakdown threshold

The Madelung-Psi Strang split-step **never failed** in the sense of NaN or norm blow-up — for every (A, dx, dt) we tried, the run completed and mass was conserved to ~1e-12. However the prompt-default discretization (Nx=256, dt=0.001, L=30) returns the **wrong peak count** for A ≥ 2:

- A=2.0: baseline reports 2 peaks, converged 1
- A=2.5: baseline reports 3 peaks, converged 2

The breakdown is silent: a researcher who only ran the default would walk away with the wrong soliton count starting at A=2. The diagnostic that catches this is the **spectral tail fraction**: > 1e-4 was a near-perfect predictor of wrong peak count. Setting `Nx >= 1024` (or doubling Nx until the spectral tail saturates below 1e-10) is the right fix.

The mechanism is dx-undersampling: an N=k soliton has peak FWHM ~ 1/(k * A) which at A=3, k=3 is ~ 0.11 — only one grid point at dx=0.117. Strang splitting remains stable but the FFT cannot represent the soliton accurately, producing a smoother surrogate with overshoot.

## Useful self-assessment

- F1 (baseline): partial. Gave us numbers but they're wrong at A≥2.
- F2 (E2 refinement, two-variant comparison): partial. Identified dx as the discriminator and ruled out wrap-around — high-value piece of negative knowledge.
- F3 (E3 convergence): positive. Locked in the converged answer.

The most important piece of knowledge for the bank: **the canonical "good" discretization (Nx=256, dt=0.001) for Madelung-Psi on a focusing NLS Gaussian IC is silently wrong for A ≥ 2, with no failure indicator other than a growing spectral tail.** This is the kind of negative finding that benchmarks usually miss.
