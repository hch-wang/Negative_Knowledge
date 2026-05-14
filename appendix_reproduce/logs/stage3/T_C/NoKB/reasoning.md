# T_C / NoKB — Reasoning

## Final method (E3, kept as candidate.py)

Madelung-Psi representation of (N, phi) → Psi = sqrt(N) exp(i phi). State = (u, Psi).

Strang split-step on Psi: half-step nonlinear (V Psi term with V = 2Q − κN, plus −i u Psi_x − i (u_x/2) Psi advection) via Heun's RK2 → full-step linear (exact Schrödinger phase rotation Psi ← F⁻¹[ exp(−i (k²/2) dt) F[Psi] ]) → half-step nonlinear. The u-equation is integrated alongside the nonlinear sub-steps with u_t = m_t + J_t where m = u − J, J = Im(conj(Psi) Psi_x). u uses the FULL Psi_t (linear + nonlinear).

Domain x ∈ [−15, 15], Nx = 256, dt = 2 × 10⁻³, T = 8.0. A smooth cosine taper is applied to N₀ near the boundary (|x| > 13) to remove the residual non-periodic image of the soliton tail, reducing the boundary Psi-jump from 1.8 × 10⁻³ down to 2.1 × 10⁻¹¹.

**The candidate.py reaches t ≈ 0.094 before catastrophic divergence (max N ~ 10⁴⁶).** Final pred_results/T_C.npy therefore contains snapshot 0 (IC) padded across all 17 frames after the blow-up was detected.

## Iteration trace

**E1 — direct (u, N, phi), Fourier pseudospectral, explicit RK4, dt = 2 × 10⁻³.**
The simplest meaningful baseline as required by progressive-complexity discipline. Result: divergence at step 1 (t = 0.002). The quantum-pressure term Q = (sqrt N)_xx / (2 sqrt N) is computed via FFT, then the Hamilton–Jacobi equation feeds Q into phi_t. Recovering u_t from the momentum m = u − N phi_x requires phi_xt = ∂_x phi_t, hence ∂_x of Q. In the soliton tails N ~ 10⁻²⁰ (sech² far from the centre on a 30-unit domain), so even with a 10⁻⁸ floor on the divisor, the FFT-computed (sqrt N)_xx in the tails has O(10⁻¹⁰) spectral noise, and dividing by the floor amplifies it to O(10⁻²) per cell — squared away into u_t this immediately produced max |u| ≈ 5.4 × 10³.

**E2 — single representation change: Madelung-Psi (u, Psi); same RK4; dt = 10⁻³.**
By switching to Psi, the catastrophic phi_t → phi_xt → u_t chain is broken: Psi evolves smoothly as a complex variable even when |Psi| ≈ 0, and u_t is recovered from the well-defined current J = Im(conj(Psi) Psi_x), which is regular at Psi = 0. The Psi equation reads i Psi_t = −(½) Psi_xx + (2Q − κN) Psi − i u Psi_x − i (u_x/2) Psi for the user's +Q sign. The 2Q Psi term we computed as (½)(|Psi|)_xx · (Psi / sqrt(|Psi|² + ε²)) with ε = 10⁻⁴. Result: divergence at step 80 (t = 0.08), a 40× improvement over E1. The blow-up signature (max u ≈ 1.3 × 10⁵, max N ≈ 2.4 × 10⁵) is consistent with explicit-RK4 dispersive stiffness on a focusing-κ system: the IC has a residual |Psi[0] − Psi[−1]| = 1.8 × 10⁻³ jump from the non-periodic linear phase exp(i 0.6 x), and the focusing nonlinearity amplifies the high-k modes faster than RK4 can damp them.

**E3 — single method change: Strang split-step (linear Psi_xx exact in Fourier); dt = 2 × 10⁻³.**
Removes the dispersive stiffness limit completely. Also applied a cosine taper to N₀ on |x| > 13 to make the periodic representation truly clean (boundary jump reduced to 2 × 10⁻¹¹). Result: divergence at strang-step 47 (t = 0.094). Marginal improvement over E2 in time reached, but the blow-up is now even more catastrophic (max N ~ 10⁴⁶). Mechanism identified: the 2Q Psi term in V Psi has the form (½)(|Psi|)_xx · Psi / sqrt(|Psi|² + ε²). When |Psi| ≪ ε, this factor multiplies Psi by 1/ε. (|Psi|)_xx is computed by FFT and carries O(spectral-noise) contributions in tails. Net effect: spurious 1/ε-amplified driving of Psi outside the soliton support, which the focusing κN nonlinearity then exponentially grows. This is a structural consequence of the +Q variational sign — V = 2Q − κN retains an unavoidable sqrt N division.

## Use of memory

Condition is NoKB. No prior bank entries were available. Decisions were guided by general PDE and numerical-methods knowledge:

- Fourier pseudospectral + RK4 as the canonical "simplest meaningful" PDE baseline.
- Madelung transformation Psi = sqrt(N) exp(i phi) as the canonical regularization for hydrodynamic Schrödinger-like systems with small-N regions.
- Strang split-step as the canonical method for dispersive Schrödinger-class equations with stiff k² Laplacian.
- Cosine taper for periodic-image cleanup, standard in spectral practice.

The deeper structural issue — that the user's +Q sign convention prevents a clean Psi formulation and leaves an irreducible sqrt N division in the Schrödinger potential — was discovered only after E3 failed. Under a NoKB regime this is exactly the kind of insight that bank entries (had they existed) would have provided up front; the absence of a bank cost ~2 of the 3 iterations.

## Final self-assessment

**Useful: NO.** The phenomenon target (final N peak ≥ 0.3, |u_max| < 5, bore not blowing up) is satisfied by the saved pred_results only because the file contains the initial condition padded across all snapshots after early blow-up — no actual dynamics from t = 0 to t = 8 were resolved. The "soliton vs bore" interaction (transmit / reflect / capture / destroy) cannot be inferred from this run.

**What would be needed next (out-of-scope for this 3-iteration session):**
- Mask 2Q Psi to active soliton support: multiply by a smoothstep on |Psi|/(threshold), so the term contributes only where N is dynamically meaningful.
- IMEX-CN time stepping with the linear Schrödinger + 2Q Psi handled implicitly.
- 2/3 dealiasing on all nonlinear products.
- Stronger regularization or upgrade to a hyperbolic form for (rho, J) hydrodynamic variables with viscosity-based shock capture.

These three combined would likely give a stable run, but each is a "single change" by the progressive-complexity rule and the cumulative path exceeds the 3-experiment session budget. NARROW CLAIM (Decision D3): B-NLS T_C under naive numerics with the user's +Q sign convention is intractable in 3 progressive iterations starting from the simplest baseline.
