# T_B / PosNeg reasoning

## Final method

**E1** is the final answer (early stop after iteration 1, since the baseline already met the phenomenon target).

Full method:
- Spatial: Fourier pseudospectral derivatives on Nx=256 grid over periodic box `x in [-15,15]`, L=30.
- Dealiasing: 2/3-rule mask (`|k_idx| <= Nx/3 = 85`) applied to (a) every spectral derivative used inside nonlinear products and (b) every nonlinear-product FFT (v*v_x, u*v, u*u_x, u*v_x, u_x*v) before transforming back.
- Time stepping: classical explicit 4th-order Runge-Kutta on the FULL RHS, including the dispersive v_xxx term (kept explicit, NOT split off, NOT IMEX).
- dt = 1e-4 (sub-multiple of the BKdV-S1 validated dt=2e-4, halved to absorb the amp=4 nonlinear-CFL tightening predicted by `kb-gardner-nonlinearCFL-amplitude-boundary`).
- T = 6.0; 60000 steps; 13 snapshots saved (t = 0, 0.5, 1.0, ..., 6.0).
- Output `pred_results/T_B.npy` shape `(13, 2, 256)`; final snapshot is at index 12.

PDE algebra (explicit forms used in code):
- `u_t = -3 u u_x - 6 v v_x - v_xxx`   (from `u_t + 3 u u_x = -d/dx (3 v^2 + v_xx) = -6 v v_x - v_xxx`)
- `v_t = -6 v v_x - v_xxx - d/dx (u v)`

## Iteration trace

- **E1 / F1**: Fourier pseudospectral + 2/3 dealias + explicit RK4, Nx=256, dt=1e-4, T=6.0 on the Gaussian IC. Reached T=6.0 cleanly in 14.7s, no NaN, mass_v conserved to <1e-13 (drift ~1e-14 relative), final sup_v=1.88, sup_u=4.87, **10 well-separated peaks (prom>=0.5, dist>=10) all with amplitude >= 0.8** (heights 0.82, 0.95, 1.09, 1.20, 1.30, 1.49, 1.52, 1.65, 1.74, 1.80). Spectral content in the upper dealias band is 6.8e-7 -- well below contamination level. Phenomenon target (>=2 peaks of amp>=0.8 with mass-drift <8%) is decisively met. D1 = stop_useful.

E2 and E3 not executed. Progressive-complexity discipline forbids spending iterations on cosmetic upgrades when the baseline already produces a satisfactory result.

## Use of memory

**Cited (drove method choice):**
- `BKdV-S1` (positive, second entry — Fourier + 2/3-rule + RK4 reached T=10 at amp=3.0, dt=2e-4): single most direct positive precedent for this exact PDE class; confirmed the baseline stack is appropriate for E1 and gave the dt anchor.
- `kb-gardner-nonlinearCFL-amplitude-boundary` (negative, but informative for *parameter* choice rather than method rejection): the `dt * max(6A + 1.5A^2) * k_max < O(1)` rule told me to halve BKdV-S1's dt (2e-4 -> 1e-4) for amp=4. Worth noting: at A=4, the combined coefficient `6*4 + 1.5*16 = 48` is ~3.9x larger than at A=1.5 (`12.4`), so a 2x dt cut is the prudent floor.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup` (negative): warned that even IMEX-CN can blow up at A=3 if dt isn't re-evaluated; reinforced the dt-cut decision.

**Rejected (would have violated progressive-complexity or known dead ends):**
- `kb-burgers-fwdEuler-centralFD-Gibbs`, `kb-general-centralFD-hyperbolic-shockFormation`, `kb-shallowWater-centralFD-fwdEuler-hNegative` -- central FD without upwinding on the Burgers-like u u_x / advective terms produces unbounded Gibbs oscillations. Rejected at E1.
- `kb-kdv-IFRK4-blowup` -- integrating-factor RK4 overflows via `exp(i k^3 t)` at high k. Rejected at E1.
- `kb-kdv-noDealiasing-aliasing-artifacts`, `kb-kdv-explicit-RK4-stiffness-blowup`, `kb-gardner-G1-explicitRK4-finiteFrag`, `kb-gardner-G3-noDealiasing-cubicAliasing` -- families of "spectral without dealias" or "explicit RK4 with too-small dt" failures. All addressed by including the 2/3-rule (which is what BKdV-S1 confirmed makes the explicit-RK4 stack work).
- `kb-burgers-LaxFriedrichs-longTime-dissipation`, `kb-shallowWater-LaxFriedrichs-overdiffusion` -- LxF damps shock amplitude; rejected as an unnecessary upgrade that would *worsen* peak amplitudes.
- `kb-gardner-sech2IC-not-exact-soliton` -- noted but inapplicable: the task IC is a Gaussian, not a sech^2 fit to either KdV or Gardner soliton parametrization; the question is whether the system decomposes that Gaussian, not whether a sech^2 IC propagates cleanly.
- `kb-burgers-MUSCL-Godunov-shock-pass`, `kb-shallowWater-HLL-dam-break-pass` -- positive precedents for MUSCL-Godunov / HLL on the Burgers/hyperbolic component. Considered but *not* adopted at E1 because they would introduce a hybrid spectral/finite-volume scheme (multi-component leap). Would have been the planned E2 escalation if E1 had shown shock-front overshoot on u; sup_u peaked at 4.87 without sign of dealias-band overrun (upper-band energy 6.8e-7), so no escalation was needed.
- `BKdV-S5` deep-synthesis warning about the `m=0` manifold not being invariant: not directly relevant — the task IC has `u_0=0` (so m_0 = -v_0^2/2 != 0 unless v_0 = 0), and the Gaussian-decomposition question doesn't require m=0 to be preserved; it asks whether soliton structures emerge, which they do.
- `kb-general-massConservation-insufficient-diagnostic` and `kb-general-finiteness-not-accuracy` -- I followed this warning: in addition to mass conservation and finiteness I checked (a) peak count and amplitudes with prominence filter, and (b) spectral content near the dealias band.
- `kb-burgers-LaxFriedrichs-periodic-longTime-contamination` -- noted but T=6 with L=30 corresponds to far less than the recirculation timescale for the leading wave-train, so this is not a concern.

## Final self-assessment

**Yes**, `pred_results/T_B.npy` satisfies the phenomenon target.

Numerical diagnostics on the final snapshot (t=6.0):
- Peak count with `(height>=0.8, distance>=10, prominence>=0.5)`: **10 peaks** (target: >=2). PASS.
- Each peak amplitude: min 0.82, max 1.80, distribution `[0.82, 0.95, 1.09, 1.20, 1.30, 1.49, 1.52, 1.65, 1.74, 1.80]`. PASS.
- Mass(v) drift over `[0, T]`: |10.634723105433096 - 10.634723105433116| / 10.6347 = 1.9e-15 (machine precision). Bound is 8%. PASS by 13 orders of magnitude.
- All-finite check: PASS.
- Spectral hygiene: 6.8e-7 of the |k|-spectrum's energy lives within 10% of the dealias cutoff -- confirms the resolution and dealiasing are adequate; the multi-peak structure is physical, not aliasing-induced (rejects the kb-kdv-noDealiasing-aliasing-artifacts / kb-gardner-G3 alternative explanation).
- u-field stayed bounded throughout, peaking at sup_u ~ 4.87 -- no Burgers-shock blow-up; the MUSCL escalation flagged in the bank was not needed.

Interpretation: the amp=4 Gaussian is well above the soliton-formation amplitude threshold (kb-kdv-amplitude-threshold-soliton sets the floor near A>>0.1, and kb-kdv-smallAmplitude-dispersiveRegime confirms small-amplitude components disperse instead). Inverse-scattering for the swept-KdV component is expected to shed multiple solitons from a localized initial bump of this size; the 10-peak structure observed is consistent with that prediction, though some of those peaks likely correspond to a combination of solitons and the trailing dispersive radiation in u-v coupled form.
