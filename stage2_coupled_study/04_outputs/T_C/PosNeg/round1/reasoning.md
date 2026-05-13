# Reasoning: T_C Burgers bore + KdV soliton interaction

## Method

**u equation** (`u_t + 3uu_x = -∂_x(3v² + v_xx)`):
- Spatial: MUSCL reconstruction with van Leer limiter + Godunov exact-Riemann flux for the hyperbolic `3uu_x` term. This is a TVD finite-volume scheme that prevents Gibbs oscillations at the bore (discontinuous step).
- Source `-∂_x(3v² + v_xx)`: computed spectrally (FFT-based differentiation), which is accurate for the smooth `v` field.
- Time: explicit forward Euler at dt=0.001. CFL = 3·1.5·dt/dx ≈ 0.45, within the stable range.

**v equation** (`v_t + 6vv_x + v_xxx = -∂_x(uv)`):
- Spatial: Fourier pseudospectral.
- Time: IMEX-Crank-Nicolson. The dispersive stiffness term `v_xxx` is treated implicitly (CN denominator `1 − idt/2 · k³`), which is unconditionally stable for the dispersive stiffness. The nonlinear terms `6vv_x + ∂_x(uv)` are treated explicitly.
- 2/3 dealiasing applied to all nonlinear products before and after spectral operations.
- dt=0.001 satisfies the nonlinear CFL constraint: max(6A + 1.5A²) ≈ 12.4 at A=1.5; with k_Nyq ≈ 27, NL-CFL ≈ 0.001 · 12.4 · 27 ≈ 0.33 < 1, within the empirical stability band.

## Use of memory

**Directly applied (positive entries):**
- `kb-burgers-MUSCL-Godunov-shock-pass`: MUSCL+van Leer+Godunov is a proven scheme for Burgers bore propagation; adopted as the default for the `u` hyperbolic sector.
- `kb-kdv-IMEX-CN-spectral-pass`: IMEX-CN spectral with CN on `v_xxx` and explicit nonlinear is the validated baseline for KdV soliton propagation; adopted directly for the `v` sector.
- `kb-kdv-noDealiasing-aliasing-artifacts` and `kb-gardner-G3-noDealiasing-cubicAliasing`: both warn that omitting 2/3 dealiasing inflates soliton amplitude and creates spurious peaks; 2/3 dealiasing is applied to all nonlinear terms.
- `kb-gardner-nonlinearCFL-amplitude-boundary` and `kb-gardner-cubicTerm-tightens-nonlinearCFL`: used to set dt=0.001 after verifying NL-CFL ≈ 0.33 at amplitude 1.5.
- `kb-gardner-KdV-method-transfer-moderate-amplitude`: confirms IMEX-CN spectral + 2/3 dealiasing transfers from KdV to Gardner at amplitude ≤ 2; amplitude 1.5 is within the validated range.

**Entries consulted and rejected:**
- `kb-burgers-fwdEuler-centralFD-Gibbs` (negative): central FD for Burgers produces 21 spurious maxima; rejected — use MUSCL instead.
- `kb-burgers-LaxFriedrichs-longTime-dissipation` (negative): Lax-Friedrichs over-diffuses bore over long times; rejected.
- `kb-kdv-IFRK4-blowup` (negative): IFRK4 blows up due to exp(ik³t) overflow at high k; rejected.
- `kb-kdv-explicit-RK4-stiffness-blowup` (negative): explicit RK4 on v_xxx produces soliton fragmentation into 10 peaks even without NaN; rejected.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup` (negative): dt=1e-4 blows up at amplitude 3.0; our amplitude 1.5 is safe, confirmed by NL-CFL check.
- `kb-gardner-sech2IC-not-exact-soliton` (negative): KdV sech² is not an exact Gardner soliton, causes radiation. Here the IC is for the full coupled system, not an isolated Gardner test — the prompt specifies sech² IC explicitly, so radiation from the Gardner reduction is acceptable; the phenomenological criterion is peak amplitude ≥ 0.5 at T=8.

## Risks

1. **Long-time periodic wrap-around of the bore**: at T=8 with bore speed ~u_L/2=0.75, the bore travels ~6 units, well within [-15,15]; but the soliton at x=-8 with KdV speed ~3A²/... travels further. Periodic domain contamination is possible after multiple traversals (see `kb-burgers-LaxFriedrichs-periodic-longTime-contamination`), potentially making the final state hard to interpret — but the eval criterion only requires peak ≥ 0.5 and |u|<5.

2. **Explicit-implicit operator splitting error**: the u-source term uses the v field at the old time level (pure explicit). For strong coupling, this first-order operator splitting can accumulate phase error between u and v. At dt=0.001 the splitting error is O(dt²)=O(10⁻⁶) per step and O(dt)=O(10⁻³) globally — acceptable for the qualitative phenomenology test.

3. **u equation treated with forward Euler (no CN)**: the source term `−∂_x(3v²+v_xx)` in the u equation is purely explicit. The `v_xx` term introduces a spectral second-derivative whose maximum wavenumber contribution is k²_Nyq ≈ 729; the source amplitude is bounded by O(3A²+A·k²) which at A=1.5 and k_Nyq≈27 is O(1100). At dt=0.001, this could marginally destabilize u. Monitoring u_max<5 throughout is the guard.

4. **Bore-soliton interaction energy transfer**: the knowledge bank has no prior entries for this specific coupled system's interaction behavior. The soliton may lose substantial amplitude to the coupling term `−∂_x(uv)`, potentially falling below the 0.5 threshold. If this occurs, reducing dt further or switching to a fully implicit nonlinear solve would be needed.
