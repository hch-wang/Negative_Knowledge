# Round-3 Reasoning: T_C Burgers Bore + KdV Soliton

## Pattern from r1+r2

Both round 1 and round 2 blew up with NaN/Inf. The common failure pattern is **explicit treatment of the stiff dispersive and coupling terms at insufficient temporal resolution**. Round 1 used a fully pseudospectral explicit scheme with dt=0.0005 and attempted 2/3 dealiasing — the Fourier representation of the sharp bore generates large high-k modes, and the explicit nonlinear cross-terms `-dx(3v^2 + v_xx)` and `-dx(u v)` are not properly stabilized. Round 2 switched to MUSCL+Godunov for the Burgers bore and IMEX-CN for v, but the coupling terms between the two fields were not handled carefully enough — specifically the explicit `-dx(u v)` in the v equation and the `-dx(3v^2 + v_xx)` in the u equation can create a feedback loop when u has a bore discontinuity and v has a sharp soliton peak.

## New Method

Round 3 makes three key changes:

1. **Smaller dt (0.0001 vs 0.0005)**: A 5x reduction in timestep to stabilize the explicit coupling terms. The cross-coupling involves products of u (bore, max ~1.5) and v (soliton, max ~1.5), which are moderate-amplitude but their spectral derivatives can be large.

2. **Godunov flux for u with conservative form**: The Burgers equation `u_t + 3u u_x = src` is rewritten in conservative form `u_t + d/dx(3/2 u^2) = src` and solved with entropy-satisfying Godunov flux. This is the validated approach from `kb-burgers-MUSCL-Godunov-shock-pass` and `kb-general-firstOrder-Godunov-preShock-baseline` — it handles the bore (shock) without Gibbs oscillations that would corrupt the coupling terms.

3. **Full IMEX-CN for v with proper CN on v_xxx**: The dispersive v_xxx term is treated with Crank-Nicolson (unconditionally stable since |cn_denom| >= 1 for all k), while the nonlinear and coupling terms are explicit. This is the approach validated in `kb-kdv-IMEX-CN-spectral-pass` and `kb-gardner-KdV-method-transfer-moderate-amplitude` — it directly transfers to the coupled system.

## Use of Bank

- **kb-burgers-MUSCL-Godunov-shock-pass**: Confirms MUSCL+Godunov is the right baseline for the Burgers bore component. Round 3 uses first-order Godunov (simpler, more stable) rather than MUSCL.
- **kb-general-firstOrder-Godunov-preShock-baseline**: Confirms that first-order Godunov at adaptive CFL is sufficient for the bore propagation up to interaction time.
- **kb-kdv-IMEX-CN-spectral-pass**: The IMEX-CN method (CN on v_xxx, explicit nonlinear) is validated for standalone KdV soliton propagation at amplitude 2.0. This transfers directly to the v component here.
- **kb-gardner-KdV-method-transfer-moderate-amplitude**: IMEX-CN with 2/3 dealiasing transfers stably to Gardner (similar structure to the swept-KdV term here) at amplitude 1.5 with dt=0.0005. Round 3 uses the same CN structure but with a 2x smaller dt.
- **kb-kdv-spectral-solitonAmplitude-conservation**: Spectral IMEX methods conserve soliton amplitude within ~2% — this underpins the expectation that v_peak >= 0.5 is achievable after the bore-soliton interaction.

## Final Risks

1. **Coupling feedback at bore-soliton contact**: When the soliton (x ~ -8, moving right) hits the bore (centered at x=0), the coupling term `-dx(u v)` becomes large. The small dt should handle this, but if dt=0.0001 is still too large, the interaction region could produce spikes. The safety clamp (|u|, |v| <= 10) acts as a last-resort limiter.
2. **Operator splitting error**: Treating u and v updates independently (no predictor-corrector) introduces a first-order splitting error. For the long interaction time T=8, this could lead to modest phase errors in the soliton position but should not cause blow-up.
3. **Soliton survival threshold**: The soliton amplitude post-interaction may fall below 0.5 if the bore absorbs too much energy. The knowledge bank entry `kb-kdv-smallAmplitude-dispersiveRegime` warns that amplitudes ~0.1 disperse away. If the interaction is strongly dissipative for v, the target v_peak >= 0.5 may not be met — but this would be a physical result, not a numerical failure.
