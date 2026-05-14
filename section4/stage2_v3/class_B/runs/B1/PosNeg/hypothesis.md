# B1 / PosNeg — Compound-soliton formation mechanism + basin + Gardner relation

## Best current mechanism hypothesis

**Mechanism.** From smooth-localized initial data with v-amplitude in a moderate range, BKdV evolution relaxes the (u, v) pair toward a coherent compound structure inside the v-peak support in which u and v² are **linearly correlated** but **not** related by the naive Gardner-reduction u = v²/2. Operationally, after a transient of O(2-4) time units, an in-peak linear fit u = α(t) · v²/2 + β(t) attains R² ≈ 0.94 for sech² seeds and R² ≈ 0.60-0.67 for Gaussian / two-pulse seeds, with the slope α drifting from 0 at t=0 up to α ≈ 10-13 by T=10 — far from the value α=1 the m=0 reduction would predict. The mechanism that drives this relaxation is the **u-equation's source term −∂ₓ(3v² + v_xx)**: starting from u₀=0, the Burgers-side u is *generated* by the v² and v_xx gradients of the seed, and the system's three forces — Burgers steepening (3uuₓ), KdV dispersion (vₓₓₓ), and the bilinear cross-coupling −∂ₓ(uv) — pull (u, v) into a *quasi-stationary* local profile that approximates the traveling-wave branch U₋(V; c) = [(c+V) − √(c² − 4cV + V²)] / 3 derived from the steady-frame integrals of BKdV. This TW branch satisfies U ~ V (linear, not quadratic) at small V — which is why the empirical α = du/d(v²/2) is large and grows as V shrinks. The compound is then a *local* relaxation toward this TW branch, embedded in O(0.15-0.20) radiative noise that contaminates the global picture.

**Basin of attraction (amplitude × shape product).** The basin in the sech² family is bounded both **below** (A ≲ 0.4: dispersion dominates, no lock forms — lock_max=0.56 at A=0.3) and **above** (A ≳ 1.5: the BKdV-S5 source S = (v−1)(6vvₓ + vₓₓₓ) shatters the compound; at A=2.0 the compound forms transiently with lock_max=0.91 but then decoheres to lock_T=0.16). It is also bounded on the **spectral-shape** axis: broadband ICs (cosine modes at A=0.4) reach only R²=0.09, never developing the in-peak lock. The basin is similarly disrupted by **pre-existing Burgers bores** in u: forcing u₀ = 0.6·(1-tanh(x/0.5))/2 alongside sech² v collapses lock_T to 0.17 even though the bore is well-resolved (per BKdV-S6 with ν=5e-2). So the basin consists of: amplitude A in roughly [0.4, 1.5] (single-pulse), **smooth-localized** v shape, and **small-gradient** u initialization. The two boundaries are physically distinct — the lower one is dispersive (linear KdV regime per kb-kdv-smallAmplitude-dispersiveRegime), the upper one is nonlinear shattering through the BKdV-S5 identity.

**Gardner relation.** The local compound is **NOT** a Gardner soliton, and is not equivalent to one in any meaningful asymptotic sense over the timescale we observe (T=10). Directly co-evolving v under the Gardner equation v_t + 6vvₓ + (3/2)v²vₓ + vₓₓₓ = 0 from the same sech² initial seed gives v_max,Gardner(T) = 0.85 (preserved as a clean Gardner soliton) while v_max,BKdV(T) = 0.36 (compound has decayed); ||v_BKdV − v_Gardner||_L² = 1.11 at T=10, exceeding ||v_BKdV||_L² itself; phase speed c_BKdV = 1.45 vs c_Gardner = 1.93. The **only** sense in which a Gardner-like equation is *locally* approximate is that, IF one substituted u → α · v²/2 inside −∂ₓ(uv), the v-equation would reduce to a Gardner-like equation with cubic coefficient 3α/2 (i.e., α=1 recovers Gardner; observed α ≈ 12 gives an effective cubic 8× stronger than Gardner). But this substitution is **not** what BKdV is doing: u carries radiation outside the peak, the linear fit is imperfect, and the TW branch U₋(V; c) has u ~ V (linear) at the peak edge, not u ~ V². The Gardner-reduction reading of the prompt's anchoring is therefore a useful symbolic limit (it correctly identifies the cubic structure of the v-flux), not a description of the actual local profile.

## Supporting evidence (from your experiments)

- **From E1 / F1:**
  - sech²(x+5) A=1.0 IC: lock_corr(u, v²/2) climbs from 0 to 0.97 by T=10, with linear-fit slope α=12.3, intercept β=−0.04, R²=0.94. m_rms inside peak = 0.257 (i.e., m=0 is *not* a meaningful approximation in-peak). Phase speed c=1.45.
  - Gaussian A=1.0 IC: lock=0.82 (max 0.96), α=13.8, R²=0.67, c=1.39 — same mechanism with rougher initial spectral content gives broader compound, similar speed.
  - Gaussian A=0.2 (sub-threshold) IC: lock=0.23, centroid drifts only +0.08/unit-t — no compound forms; consistent with kb-kdv-smallAmplitude-dispersiveRegime and kb-kdv-amplitude-threshold-soliton.
  - Two-pulse IC (sech² at x=−5 and x=+2 with amplitudes 1.0, 0.8): lock=0.78, R²=0.61, the two pulses partially merge but with a smaller compound slope α=3.5 — the basin tolerates multi-pulse seeds but the resulting compound has weaker lock.

- **From E2 / F2:**
  - **Gardner companion test** (E2a): identical v₀, parallel BKdV vs Gardner. v_Gardner stays at amplitude 0.85, v_BKdV decays to 0.36. ||v_BKdV − v_Gardner||_L² = 1.11 > ||v_BKdV||_L² = 0.84. Phase speeds 1.45 (BKdV) vs 1.93 (Gardner). Both are stable and finite — the divergence is physical, not numerical.
  - **Broadband basin test** (E2b): v₀ = 0.4·(cos(2πx/L) + 0.5·cos(4πx/L)), u₀=0. lock_T=0.30, α=2.86, R²=0.087, phase speed −0.19 (essentially stationary). No coherent compound forms. (We kept A=0.4 below the BKdV-S3 broadband blow-up wall at A=0.8, so the result reflects basin geometry, not numerical failure.)
  - **Bore-u basin test** (E2c): u₀ = 0.6·(1−tanh(x/0.5))/2 paired with sech² v₀. With ν=5e-2 the run is well-behaved (no Gibbs), but in-peak lock collapses to R²=0.03 at T=10. The bore disrupts compound formation, supporting the H_basin_bore branch.

- **From E3 / F3:**
  - **Algebraic-ansatz residual ranking** (in-peak RMS at t=10, sech² A=1.0 IC):
    1. linear-rescaled `u = α v²/2 + β`: RMS=0.054, R²=0.94 (best empirical fit)
    2. **TW full quadratic branch `U₋(V; c)`: RMS=0.115, R²=0.73**
    3. TW small-V linear leading `u ≈ V − V²/(6c)`: RMS=0.144, R²=0.58
    4. **m=0 ansatz `u = v²/2`: RMS=0.257 (effectively R² ≈ 0 — falsified)**
  - The TW branch outperforms its small-V linearization, confirming it captures *real* nonlinear structure; but the empirical linear fit (a phenomenological summary, not a TW) still beats both, indicating the t=10 state is a **slowly-modulated relaxation toward** rather than a pure traveling wave.
  - **Amplitude sweep** (T=10, sech² seed, u₀=0):
    | A    | lock_max | lock_T | α_T  | R²_T |
    |------|----------|--------|------|------|
    | 0.3  | 0.56     | 0.48   | 10.1 | 0.23 |
    | 0.6  | 0.90     | 0.82   | 10.5 | 0.67 |
    | 1.0  | 0.97     | 0.97   | 12.3 | 0.94 |
    | 1.5  | 0.93     | 0.78   | 7.7  | 0.60 |
    | 2.0  | 0.91     | 0.16   | 0.59 | 0.02 |
  - Compound forms at all A ≥ 0.3 (transient lock visible), but only A in [0.6, 1.5] holds the compound to T=10 with R²≥0.6. At A=2.0 the compound forms transiently (lock_max=0.91 around t=2-4) and then **shatters** (lock_T=0.16, R²_T=0.024) — exactly the BKdV-S5 (v−1) shattering predicted analytically.

## Hypotheses considered and falsified / weakened (or shown trivial)

- **H_α (m=0 ansatz / Gardner reduction is the local structure):** *falsified* by E1/E3a. The strict slope-1 fit gives RMS=0.257 in-peak versus 0.054 for the rescaled linear fit; in-peak m_rms is comparable to out-of-peak m_rms, refuting the picture "m=0 inside, m≠0 outside." This corroborates BKdV-S5/S7 deep entries quantitatively.

- **H_γ (global Gardner equivalence):** *falsified* by E2a. Direct co-evolution of Gardner from the same v₀ gives ||v_BKdV − v_Gardner||_L² = 1.11 at T=10 with different amplitudes (0.36 vs 0.85) and different phase speeds (1.45 vs 1.93). The compound is fundamentally not a Gardner soliton over the observed timescale.

- **H_basin_amplitude_only (compound forms at all positive amplitudes):** *falsified* by sub-threshold E1 IC-C and amplitude sweep E3b. Below A ≈ 0.3-0.4 dispersion dominates; above A ≈ 1.5 the compound forms transiently but shatters by T=10.

- **H_basin_shape_indifferent (any IC shape works):** *falsified* by E2b broadband cosine IC (R²=0.09) and E2c bore-u IC (R²=0.03). The basin requires a smooth localized seed in v and small-gradient u; broadband or shock-driven ICs do not produce a compound.

- **H_β_TW (compound is exactly a BKdV traveling wave U₋(V; c)):** *weakened*. The TW branch is the best **physically motivated** ansatz (R²=0.73), but a *phenomenological* linear-rescaled fit beats it (R²=0.94 with RMS=0.054 vs 0.115). Interpretation: at T=10 the structure has relaxed *toward* but not yet onto the TW; coexisting radiation and slow modulation leave O(0.1) residual that the TW ansatz alone does not capture.

- **H_radiation_lock (the lock is artifact of single-pulse concentration, not a true compound):** *partially weakened*. The two-pulse IC-D still locks (R²=0.61), and the lock improves over time (lock₀=0, lock_T=0.78) — the lock is a real relaxation process, not just an IC artifact. But the *value* of α and the R² depend on IC shape, so the lock is not a universal one-parameter object.

- **H_trivial_solver_artifact (the compound is just numerical viscosity ν on u smoothing things):** *weakened*. ν=5e-2 acts on u only, and at the late time the centroid drift c=1.45 is consistent across all three sech² snapshots and is not sensitive to whether u₀=0 (E1 sech²) or u₀=bore (E2c bore) — the latter has the *same* ν but no lock, so ν alone cannot explain the lock. Per BKdV-S6 deep, ν=5e-2 is the minimum necessary for Burgers self-flux stability and is not a strong dissipation knob in our regime (TV(u) trajectories are not over-smoothed).

## Open questions / what 1 more experiment would test

A 4th round would do the following to sharpen the TW-relaxation picture:

1. **Construct a true BKdV traveling wave by Petviashvili iteration on the (U, V) ODE system** (recommended_alternative from BKdV-S5 deep). The steady-frame equations are (Eu) −cU + (3/2)U² + 3V² + V_xx = 0 and (Ev) −cV + 3V² + V_xx + UV = 0, which together yield (3/2)U² − U(c+V) + cV = 0 (the algebraic constraint we tested) plus V_xx = V(c − 3V − U), a 2nd-order ODE for V(x) once U is eliminated via the constraint. Numerically iterate to a fixed-point compound profile (U_∞, V_∞)(x; c), then run the full BKdV from this exact IC at the *same* c as the relaxed E1 state. Predicted result: the resulting compound profile preserves α and lock with negligible relaxation transient and reaches R²_TW ≈ 1 — falsifying H_β_TW if it doesn't.

2. **Distinguish slow modulation from radiation noise** by running E1 to T=20 with twice as many snapshots and checking whether α(t), c(t), and R²(t) are *constants* or *secularly drifting*. If α drifts log-linearly, the compound is genuinely modulating; if α plateaus, it's a stable attractor with bounded radiation.

3. **Map the upper basin boundary at A∈{1.7, 1.8, 1.9, 2.0} with finer resolution** to determine whether the shattering at A=2 is a hard bifurcation (sudden lock collapse around some critical A_c) or a soft soliton-amplitude-scale transition that just plays out faster at larger A.
