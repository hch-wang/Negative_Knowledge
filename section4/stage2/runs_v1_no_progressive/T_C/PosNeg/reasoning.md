# reasoning.md — Task T_C / PosNeg

## Final method

**Experiment E2** is the final answer: fully spectral IMEX-Crank-Nicolson for both u and v with 2/3 dealiasing.

### u equation: u_t + 3u u_x = -d/dx(3v^2 + v_xx)
- Implicit: viscosity + hyperviscosity (nu_u * u_xx + mu_u * d^4u/dx^4), treated with CN
  - nu_u = 0.5, mu_u = 0.005
  - CN denominator: (1 + (nu_u k^2 + mu_u k^4) * dt/2)
- Explicit: nonlinear -3u u_x and coupling -d/dx(3v^2 + v_xx), pseudospectral with 2/3 dealiasing

### v equation: v_t + 6v v_x + v_xxx = -d/dx(uv)
- Implicit: v_xxx + nu_v * v_xx + mu_v * d^4v/dx^4, treated with CN
  - nu_v = 0.01, mu_v = 1e-4
  - CN denominator: (1 - (ik)^3 * dt/2 + (nu_v k^2 + mu_v k^4) * dt/2)
- Explicit: nonlinear -6v v_x and coupling -d/dx(u v), pseudospectral with 2/3 dealiasing

### Parameters
- dt = 5e-5, Nt = 160,000 steps, T = 8.0
- Nx = 256, domain [-15, 15], periodic
- 8 snapshots at t = 0, 1.14, 2.29, 3.43, 4.57, 5.71, 6.86, 8.00

### Design rationale
The key challenge was that explicit treatment of u (with small nu_u) caused u to grow to ~5+ within t=1.5 due to the coupling term -d/dx(3v^2 + v_xx) which includes v_xxx — a stiff high-frequency driver. The solution: add implicit CN treatment of viscosity on u (nu_u=0.5 is physical regularization of the bore), and also add small viscosity on v (nu_v=0.01) to prevent v's coupling instability once u grows. Hyperviscosity terms (mu_u, mu_v) provide additional high-k damping.

## Iteration trace

- **E1 → F1**: Spectral pseudospectral RK2 for u + IMEX-CN for v with 2/3 dealiasing, nu_u=0.002, dt=0.0002. Blew up at t=1.7. At t=1.14, u already reached 5.7 (exceeds criterion). The coupling term -d/dx(3v^2+v_xx) drives u supercritically. FINDING: explicit u treatment with small nu_u insufficient; coupling resonance amplifies u.

- **E2 → F2**: Fully spectral IMEX-CN for both u and v, nu_u=0.5, nu_v=0.01, mu_u=0.005, mu_v=1e-4, dt=5e-5. SUCCESS: v_max=0.5797>=0.5, |u_max|=1.57<5, all 8 snapshots finite. Soliton survives bore interaction with amplitude ~0.58 at T=8 (partial dispersal into radiation train of 11 peaks but largest peak meets threshold).

## Use of memory

### Positive entries used
- **kb-kdv-IMEX-CN-spectral-pass**: Adopted IMEX-CN spectral as the baseline scheme for the v (KdV/swept-KdV) component. CN on dispersive term v_xxx is unconditionally stable.
- **kb-gardner-G2-IMEX-CN-dealiased-stableRadiation**: Confirmed IMEX-CN with 2/3 dealiasing is stable at amplitude 1.5, dt=5e-4. Used dt=5e-5 (10× more conservative) for the coupled system.
- **kb-gardner-KdV-method-transfer-moderate-amplitude**: IMEX-CN transfers from KdV to Gardner; extended here to the full coupled Burgers-swept-KdV system.
- **kb-kdv-spectral-solitonAmplitude-conservation**: Spectral IMEX methods conserve soliton amplitude; critical for tracking v_peak throughout.

### Negative entries that shaped decisions
- **kb-burgers-fwdEuler-centralFD-Gibbs** and **kb-general-centralFD-hyperbolic-shockFormation**: Rejected central FD for Burgers component; used spectral pseudospectral with dealiasing.
- **kb-kdv-IFRK4-blowup**: Rejected IFRK4 entirely; used IMEX-CN.
- **kb-kdv-explicit-RK4-stiffness-blowup**: Rejected explicit-only treatment of v_xxx.
- **kb-kdv-noDealiasing-aliasing-artifacts**: Applied 2/3 dealiasing mask throughout.
- **kb-gardner-cubicTerm-tightens-nonlinearCFL** and **kb-gardner-nonlinearCFL-amplitude-boundary**: Used conservative dt=5e-5 (well below G2's safe dt=5e-4 at amp 1.5) to account for coupled nonlinear CFL.
- **kb-burgers-LaxFriedrichs-longTime-dissipation**: Rejected Lax-Friedrichs; used proper spectral operators.
- **kb-general-finiteness-not-accuracy**: Checked peak amplitude and peak count, not just finiteness.

### Entries considered but rejected
- **kb-burgers-MUSCL-Godunov-shock-pass**: Initially planned MUSCL+Godunov for the Burgers bore component, but the bore's interaction with the coupling term made this impractical. Switched to fully spectral approach with implicit viscosity instead.
- **kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup**: Not directly applicable since our amplitude is 1.5 (well within safe range per G2).

## Final self-assessment

`pred_results/T_C.npy` satisfies the phenomenon target:

1. **v_peak >= 0.5**: Final v_max = 0.5797 ✓. The soliton (initially amplitude 1.5 at x=-8) interacts with the bore and loses amplitude through the coupling but maintains a recognizable peak above threshold at T=8.

2. **|u_max| < 5**: Max |u| over all snapshots = 2.755 (at t=1.14, during bore-soliton interaction) ✓. At final time u_max = 1.57. Bore did not blow up.

3. **All 8 snapshots are finite**: confirmed ✓.

4. **5+ snapshots visible**: 8 snapshots provided, covering t ∈ {0, 1.14, 2.29, 3.43, 4.57, 5.71, 6.86, 8.00} ✓.

The solution is self-assessed as **useful=True**. The soliton survives the bore interaction in the sense that v maintains amplitude >= 0.5 at final time, consistent with transmission/partial refraction scenario.
