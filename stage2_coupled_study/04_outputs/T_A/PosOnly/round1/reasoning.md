# Reasoning: T_A Soliton Stability in Coupled Burgers-swept-KdV

## Method

**Spatial discretization:** Fourier pseudospectral on all spatial derivatives with 2/3-rule dealiasing. This gives spectral accuracy for smooth soliton fields and eliminates aliasing errors from the quadratic and cubic nonlinearities.

**Time integration:**
- **v equation (KdV/swept-KdV sector):** IMEX-Crank-Nicolson. The stiff dispersive term `v_xxx` is treated implicitly via CN, which yields an unconditionally stable denominator `1 + (dt/2)(ik)^3` with magnitude >= 1 — no exponential overflow. All nonlinear and coupling terms `[-6vv_x - ∂_x(uv)]` are handled explicitly at the current time step.
- **u equation (Burgers sector):** Forward Euler in time with pseudospectral spatial discretization. The u equation has no dispersive stiffness; the dominant constraint is the CFL condition from the nonlinear wave speed ~3u. With dt=0.0005 and max amplitudes ~O(2), the effective CFL is safe.
- **Time step:** dt = 0.0005, consistent with validated settings from the memory bank for KdV at amplitude 2.

This hybrid IMEX-CN spectral approach is appropriate because: (1) it resolves the sech^2 soliton shape spectrally without numerical diffusion; (2) the CN treatment prevents dispersive blow-up; (3) 2/3 dealiasing suppresses aliasing from the coupling products `uv` and `3v^2`.

## Use of Memory

**Adopted:**
- `kb-kdv-IMEX-CN-spectral-pass`: Directly adopted. IMEX-CN spectral with dt=0.0005 is proven for KdV soliton amplitude=2, T=2 on exactly this domain/grid. Transferred to the v equation.
- `kb-kdv-spectral-solitonAmplitude-conservation`: Confirms spectral IMEX methods conserve KdV soliton amplitude ~2% and mass ~1%, validating the scheme choice for the soliton stability criterion.
- `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` and `kb-gardner-KdV-method-transfer-moderate-amplitude`: Confirm IMEX-CN + 2/3 dealiasing is stable for Gardner (the m=0 reduction of this system) at amplitude 1.5–2. The coupled system is a perturbation of Gardner, so stability should transfer. Also warns that KdV-style sech^2 IC on Gardner radiates — relevant here since our IC perturbs the Gardner reduction by 0.2v, so some radiation is expected but the dominant soliton should persist.

**Rejected:**
- `kb-burgers-MUSCL-Godunov-shock-pass` and `kb-burgers-Godunov-preShock-smooth`: The u equation has no sharp shock expected (smooth IC, coupling to a soliton, not a Riemann problem). A spectral method is more appropriate than finite-volume Godunov here; MUSCL adds complexity without benefit for smooth profiles.
- `kb-shallowWater-LaxFriedrichs-stable-smeared` and `kb-shallowWater-HLL-dam-break-pass`: Shallow water methods — not applicable to this dispersive PDE system.
- `kb-kdv-smallAmplitude-dispersiveRegime`: Not applicable; our amplitude is 2.0, well above the small-amplitude dispersive regime.

## Risks

1. **u equation stability:** Forward Euler for u with spectral derivatives has no implicit damping. If u develops steep gradients due to the `3uu_x` nonlinearity (Burgers-like shock formation), the CFL constraint tightens. At dt=0.0005 the scheme may become marginally stable or blow up if u grows beyond ~O(5).

2. **Coupling-induced radiation:** The IC is perturbed from the Gardner m=0 reduction by 0.2v. This perturbation drives radiation in both u and v sectors via the coupling terms. Excessive radiation could cause the dominant soliton amplitude to drop below the 0.5 * 2.0 = 1.0 threshold required by eval, although the memory bank (kb-gardner) suggests the dominant peak survives at amplitude ~0.6 even with radiation.

3. **Mass drift:** The forward Euler step for u is not a conservation-form update. It may introduce small mass errors in u that feed back into v via the coupling term ∂_x(uv), potentially causing slow mass drift in v beyond the allowed 8%.

4. **Phase velocity mismatch:** The coupled system's effective soliton speed differs from the pure KdV value due to the u-coupling. The soliton may travel faster or slower than expected, possibly leaving the periodic domain window in an unexpected state at T=8. With domain length 30 and soliton speed ~4cs (estimated), the soliton travels ~32 units — wrapping once around the periodic domain — which is manageable but could cause interference with any radiation trailing behind.
