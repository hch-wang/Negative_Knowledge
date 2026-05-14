# Reasoning — T_C / NoKB

## Final method (E3)

**Spatial:** Fourier pseudospectral on x ∈ [-15, 15], Nx = 256 (dx = 0.117), with **2/3-rule dealiasing** on all nonlinear products (u², v², u·v). The mask zeros Fourier modes |k| > (2/3)·kmax = (2/3)·26.81 ≈ 17.87 before back-transforming any product.

**Time:** Integrating-factor RK4 (IF-RK4). The linear dispersive term −v_xxx in the v equation appears in Fourier space as eigenvalue +i k³ on v̂ (purely imaginary, but oscillates with period 1/k³ → very stiff). Substitute ŵ(k,t) = exp(−i k³ t) v̂(k,t); the linear stiffness is removed analytically and ŵ evolves by the nonlinear RHS only. RK4 with dt = 0.002. Nonlinear terms (3 u u_x, 6 v v_x, (uv)_x, plus the non-stiff v_xxx forcing in the u equation) are evaluated explicitly inside RK4.

**Full discrete RHS in Fourier space:**
- û_t = −i k · (1.5 · F[u²]_dealiased + 3 · F[v²]_dealiased + (i k)² v̂)
- ŵ_t = exp(−i k³ t) · ( −i k · (3 · F[v²]_dealiased + F[uv]_dealiased) )

The smoothed-bore IC u(x,0)=1.5·(1−tanh(x/0.5))/2 has a sharp transition near x=0; the soliton IC v(x,0)=1.5 sech²(x+8) is well-resolved.

**Outcome:** Mass exactly conserved (∫u dx, ∫v dx unchanged to ~7 sig figs). |v|max stays ≤ 1.5 throughout the integration. The run is stable until t ≈ 2.34, at which point inviscid-Burgers shock formation on u produces Gibbs oscillations that drive |u|max to ~16 → overflow. The PDE as stated has **no physical viscosity on u**, so Fourier pseudospectral without an additional spectral filter or shock-capturing scheme cannot represent the post-shock bore. The phenomenon target |u_max| < 5 is therefore **not** met across the full [0, T=8] interval; it holds only for t ≲ 1.2.

## Iteration trace

- **E1 (Fourier pseudospectral + explicit RK4, no dealiasing, dt=0.001) → F1**: NaN at step 5 (t=0.005). Root cause = dispersive CFL: required dt ≲ 2.8/k_max³ ≈ 1.5e-4 for v_xxx with explicit RK4. dt=0.001 was 7× too large for the dispersive part. Hyperbolic (Burgers) advection is NOT the limiting factor at this stage.
- **E2 (= E1 + integrating-factor RK4 on the linear v_xxx → removes dispersive stiffness, single-component upgrade) → F2**: NaN at t=0.056 (step 28). Diagnostic with forward-Euler dt=1e-5 showed blowup at t=0.013 even with vanishingly small dt — so the remaining failure is not a time-step CFL issue. It is **aliasing-driven nonlinear instability**: the bore tanh(x/0.5) excites Fourier modes whose nonlinear product u·u_x folds energy back into resolved modes, pumping |u| upward.
- **E3 (= E2 + 2/3-rule dealiasing on all nonlinear products, single-component upgrade) → F3**: Mass exactly conserved; valid snapshots through t=2.0 (|v|max≈1.30, |u|max grows from 1.5 → 2.4 → 3.3 → 11.2 → 16 over t∈[0,2]). Blowup at t=2.336. The remaining failure mode is **genuine inviscid-Burgers shock formation** at the bore front (predicted time t*=1/max(3 u_x)≈0.11, but the smoothed transition delays the steepening to ~t=1). Fourier with 2/3-rule dealiasing has no mechanism to dissipate the Gibbs ringing once a true discontinuity forms — Gibbs oscillations grow in |u|max while mass is conserved exactly.

## Use of memory

No knowledge bank was provided for this condition (NoKB). All design choices were made from general knowledge of PDE numerical methods. Every Experiment node has `cites_bank: []` and `rejects_bank: []`. The progressive-complexity discipline was followed strictly: E1 = simplest baseline (pseudospectral + RK4, no add-ons); E2 = E1 with single change (time integrator → IF-RK4); E3 = E2 with single addition (2/3-rule dealiasing).

## Final self-assessment

**Does pred_results/T_C.npy satisfy the phenomenon target?** Partially.
- ✓ |v_max| at the last valid snapshot (t=2.0) = 1.30 ≥ 0.5 → soliton is recognizable.
- ✗ |u_max| at the last valid snapshot (t=2.0) = 16.04 ≫ 5 → **fails the u-bounded check**.
- The bore IS effectively blown up (Gibbs oscillation, not physical blow-up): mass is exactly conserved but the Fourier representation cannot suppress oscillations around the developing shock.

The file `pred_results/T_C.npy` has shape (17, 2, 256). Snapshots t_idx=0..4 (t=0,0.5,1.0,1.5,2.0) are physically valid; t_idx=5..16 are padded copies of the t=2 snapshot (set when the integrator detected NaN). The parent's phenomenon check at T=8 will see |u_max|=16, failing the bound.

**What was missing (forbidden by 3-iteration budget):** the next single-component upgrade — an exponential / Hou-Li spectral filter on u OR shock-capturing (Godunov/MUSCL) on the u-advection only — would suppress the post-shock Gibbs and let the simulation continue. Reaching the genuine T=8 phenomenon study would have required either E4 (filter) or a re-engineered E3 that combines IF + dealias + filter from the start.

`useful_self_assessment: false` for all three Findings. Returning E3's run as the best-of-three.
