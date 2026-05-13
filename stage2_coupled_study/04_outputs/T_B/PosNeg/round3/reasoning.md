# Round-3 Reasoning — T_B: Gaussian wave packet → soliton train

## Pattern from r1+r2

Both prior rounds failed due to the **amplitude-4 nonlinear CFL condition** being violated. Round 1 (IMEX-CN) blew up to NaN — the dt was not small enough to handle the explicit nonlinear terms at amplitude 4. Round 2 (ETD-RK2 with Strang splitting) avoided NaN but produced an unbounded solution (mass drift 18.5×, v_max=49) — the ETD integrating factor correctly handled v_xxx stiffness but the large nonlinear terms in both the v equation (6vv_x at A=4 gives effective speed ~24) and the coupling term d_x(uv) caused explosive growth in the explicit stage.

Common failure pattern: **both methods underestimated the nonlinear CFL constraint at A=4**. Per `kb-gardner-nonlinearCFL-amplitude-boundary`, the effective nonlinear wave speed at A=4 is max|6A| = 24, and the stability constraint scales as dt × 24 × k_Nyquist < O(0.5). With k_Nyquist = π×256/30 ≈ 26.8, this requires dt < 0.5/(24×26.8) ≈ 7.8e-4 for the 6vv_x term alone. The coupling also adds d_x(uv) which grows as u grows.

## New Method

Round 3 uses the same **IMEX-Crank-Nicolson spectral** framework validated in `kb-kdv-IMEX-CN-spectral-pass` and `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`, but with a critical change: **dt = 5e-5**, reduced by ~10× from prior attempts. This is computed from the nonlinear CFL formula: dt = min(5e-5, 0.3 / (48.0 × k_max)), where 48 = max|6A + 1.5A²| at A=4 (from `kb-gardner-cubicTerm-tightens-nonlinearCFL`).

Key differences from prior rounds:
1. **dt = 5e-5** instead of O(5e-4) — satisfies amplitude-4 nonlinear CFL with margin
2. **IMEX-CN on v_xxx** (not ETD-RK2) — per `kb-kdv-IMEX-CN-spectral-pass`, CN denominator has |magnitude| ≥ 1, unconditionally stable for dispersion
3. **2/3 dealiasing** on all nonlinear products — required per `kb-kdv-noDealiasing-aliasing-artifacts` to prevent spurious soliton peaks
4. **Forward Euler for u** — u has no stiff dispersive term; the Burgers-like nonlinearity 3uu_x is handled in spectral space with dealiasing

## Use of Bank

- `kb-kdv-IMEX-CN-spectral-pass`: confirms IMEX-CN is the baseline method for KdV-type dispersive terms
- `kb-gardner-nonlinearCFL-amplitude-boundary`: provides the dt formula dt < C/(max_nonlinear_speed × k_Nyquist); at A=4 with 6v term, max speed = 24, demanding dt ~ O(1e-4) or smaller
- `kb-gardner-cubicTerm-tightens-nonlinearCFL`: at A=4, the combined 6A + 1.5A² = 24 + 24 = 48 sets the nonlinear CFL denominator
- `kb-kdv-noDealiasing-aliasing-artifacts`: dealiasing is essential to avoid spurious soliton peaks in the final count
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup`: confirms that even dt=1e-4 can blow up at amplitude 3 with IMEX-CN explicit nonlinear — at amplitude 4, even smaller dt is needed
- `kb-general-massConservation-insufficient-diagnostic`: mass conservation alone is insufficient; also check peak count and amplitude

## Final Risks

1. **dt=5e-5 may still be marginal** if the coupling term d_x(uv) causes u to grow rapidly and feed back into v. Mitigation: finite check at every step with early-stop fallback.
2. **Forward Euler for u** (no implicit treatment) may allow u to grow without bound via the coupling forcing -d_x(3v²+v_xx). At amplitude 4, d_x(3v²) ~ 3×16×(1/sigma) ~ O(30), which is large. Risk is medium.
3. **Soliton train formation**: A=4 Gaussian on KdV-like equation should decompose into ~2-3 solitons (by IST theory, number ~ floor(A/2) for KdV normalization). With the swept coupling to u, the decomposition may be modified. The phenomenon target (≥2 peaks each ≥0.8) should be achievable if numerical stability holds.
4. **Mass drift target <8%**: IMEX-CN conserves mass well for the v equation since only dispersive CN part is implicit and nonlinear is mass-conserving; forward Euler for u is not mass-conservative for u but v mass should be approximately conserved.
