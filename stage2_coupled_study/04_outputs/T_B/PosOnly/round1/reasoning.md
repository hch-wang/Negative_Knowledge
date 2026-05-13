# Reasoning: T_B — Gaussian wave packet -> soliton train decomposition

## Method

**Spatial discretization:** Fourier pseudospectral on the periodic domain x ∈ [-15, 15], Nx = 256. This gives spectral accuracy for smooth solutions and exact evaluation of all derivative operators. A 2/3-rule dealiasing mask is applied to nonlinear products (v·v_x, u·v, v^2, etc.) to suppress aliasing-induced instability.

**Time integration:** IMEX-Crank-Nicolson (IMEX-CN), dt = 0.0005, T = 6.0 (12 000 steps).

- **v equation:** The dispersive term v_xxx is treated implicitly via Crank-Nicolson. In spectral space the CN update reads `v_hat_new = (cn_num * v_hat + dt * rhs_v_hat) / cn_den` where `cn_num = 1 + (dt/2)(ik)^3` and `cn_den = 1 - (dt/2)(ik)^3`. Because `|cn_den| >= 1` for all k, the scheme is unconditionally stable for the dispersive stiffness. All nonlinear and coupling terms (-6vv_x, -∂_x(uv)) are handled explicitly.

- **u equation:** The u PDE has no dispersive term; it is a Burgers-like equation with a forcing from v. A forward Euler step is used for simplicity, which is stable at the chosen dt under the expected smooth-field conditions.

This setup is appropriate for this task because: (a) the primary phenomenon of interest (soliton train formation in v) is governed by KdV-type dispersion which demands a numerically stable, spectrally accurate dispersive integrator; (b) the Gaussian IC is smooth, so pseudospectral methods are ideal; (c) T = 6.0 is long enough for multi-soliton separation, requiring the unconditional stability of IMEX-CN on the dispersive operator.

## Use of memory

**Used:**
- **kb-kdv-IMEX-CN-spectral-pass:** Primary design basis. IMEX-CN spectral (dt=0.0005, Nx=256, domain [-15,15]) proved stable and accurate for KdV soliton propagation to T=2. Directly transferred to the v equation here, extending to T=6.
- **kb-kdv-spectral-solitonAmplitude-conservation:** Confirms that Fourier IMEX methods conserve soliton amplitude (~2%) and mass (<1%), essential for reliably detecting a soliton train at T=6.
- **kb-gardner-KdV-method-transfer-moderate-amplitude:** Validates that IMEX-CN + 2/3 dealiasing transfers cleanly from KdV to equations with additional nonlinearity (Gardner cubic term). The coupling term in v is structurally similar, so this positive transfer supports the choice.
- **kb-gardner-G2-IMEX-CN-dealiased-stableRadiation:** Confirms stability of IMEX-CN + dealiasing at amplitude 1.5; the Gaussian IC here has amplitude 4, which may decompose into multiple solitons of moderate amplitude.

**Rejected:**
- **kb-burgers-MUSCL-Godunov-shock-pass / kb-general-firstOrder-Godunov-preShock-baseline:** Finite-volume Godunov schemes are appropriate for shocked Burgers but not for the dispersive v equation where spectral accuracy is needed to resolve soliton phase and amplitude faithfully.
- **kb-kdv-smallAmplitude-dispersiveRegime:** Amplitude-0.1 KdV disperses without soliton formation. Not directly applicable here (amplitude 4 Gaussian should produce solitons), but used as a reminder that the amplitude must stay above threshold after decomposition.
- **kb-shallowWater-LaxFriedrichs-stable-smeared / kb-shallowWater-HLL-dam-break-pass:** Shallow water solvers; not relevant to this dispersive PDE task.

## Risks

1. **Coupling instability at large amplitude:** The Gaussian has amplitude 4, which can produce strong coupling between u and v via the ∂_x(uv) and ∂_x(3v^2 + v_xx) terms. If the explicit treatment of these coupling terms introduces numerical instability, the solution may blow up. Mitigation: dt = 0.0005 and dealiasing provide a safety margin.

2. **Insufficient peak separation by T=6:** Whether the Gaussian fully decomposes into 2+ well-separated solitons (each amplitude ≥ 0.8) by T=6 depends on the PDE dynamics. The eval criterion is tight; if the KdV-like speed hierarchy is slower in this coupled system than in pure KdV, solitons may not be far enough apart to register as separate peaks.

3. **u-equation Euler instability:** The u-equation uses forward Euler without a dispersive stabilizer. If the coupling forcing from v becomes large (e.g., during fast v soliton formation), u can develop numerical spikes. This could then feed back into v via ∂_x(uv). Monitoring boundedness of u is important.

4. **Aliasing in high-amplitude nonlinear products:** Despite 2/3 dealiasing, the combination of amplitude-4 fields and cubic-like effective nonlinearity (v^2 in the u-forcing, uv in the v-forcing) may generate aliased energy at high wavenumbers, degrading accuracy at late times. Spectral roll-off in the dealiased region serves as a diagnostic.
