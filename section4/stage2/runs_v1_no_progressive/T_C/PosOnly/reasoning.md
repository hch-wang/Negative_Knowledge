# Reasoning: T_C — Burgers bore interacting with a KdV soliton

## Final method

**Experiment E1** is the final answer.

**Method**: Operator-split (Strang) solver on periodic domain x ∈ [-15, 15], Nx=256, T=8.0.

- **u-equation** (Burgers-like sector): MUSCL van Leer limiter + Godunov exact Riemann flux + Forward Euler, CFL = 0.45, with explicit coupling source `-d/dx(3v^2 + v_xx)` evaluated spectrally.
- **v-equation** (swept-KdV sector): IMEX-Crank-Nicolson spectral — Crank-Nicolson on the stiff dispersive term `v_xxx` (in Fourier space: denominator `1 + dt/2 * (ik)^3`, magnitude >= 1, unconditionally stable), explicit on nonlinear `6vv_x` and coupling `-d/dx(uv)`; 2/3 dealiasing applied.
- **Time splitting**: Each global step uses Strang splitting: u(dt/2) → v(dt) → u(dt/2). The CFL constraint from the Burgers sector (s_max = 3|u|_max) controls the actual dt.
- **Snapshots**: 9 evenly-spaced snapshots from t=0 to t=T=8.

## Iteration trace

- **E1 / F1**: MUSCL+Godunov for Burgers bore + IMEX-CN spectral for KdV sector, Strang splitting. Ran to T=8. final v_max=0.5081 >= 0.5 (soliton survived), u_max=1.296 < 5 (bore bounded), mass_v=3.0 conserved, no NaN/Inf. Phenomenon target fully satisfied. Stopped early.

## Use of memory

**Used (positive entries that drove decisions):**

- **kb-burgers-MUSCL-Godunov-shock-pass**: Adopted MUSCL van Leer + Godunov as the spatial scheme for the Burgers component. Its TVD property prevents Gibbs oscillations near the bore, which is critical when the bore is about to interact with the KdV soliton. L1 error ~0.003 proven for Burgers shock — directly applicable.
- **kb-kdv-IMEX-CN-spectral-pass**: Adopted IMEX-CN spectral for the dispersive v-equation. The CN denominator (1 - dt/2 * ik^3) has |magnitude| >= 1, giving unconditional stability for the stiff v_xxx term. Validated on KdV soliton amplitude=2 at T=2.
- **kb-kdv-spectral-solitonAmplitude-conservation**: Confirmed that spectral IMEX methods conserve soliton amplitude within ~2% and mass within <1% — this supports confidence in the v-sector amplitude tracking at T=8.
- **kb-gardner-KdV-method-transfer-moderate-amplitude**: Confirmed that IMEX-CN spectral + 2/3 dealiasing transfers cleanly from KdV to Gardner at amplitude [1,2] — the coupled system with the v-equation having Gardner-like terms benefits from the same scheme. Only the nonlinear stage needs extension to include coupling term d/dx(uv).

**Considered but less directly used:**
- **kb-burgers-Godunov-preShock-smooth**: First-order Godunov considered for early-time Burgers, but MUSCL upgrade was used throughout since the bore is already formed at t=0.
- **kb-gardner-G2-IMEX-CN-dealiased-stableRadiation**: Noted that KdV-style sech^2 IC at amp 1.5 is not a true Gardner soliton and will radiate. In our task, this is expected and acceptable — the phenomenon target only requires final v_max >= 0.5, not exact soliton preservation. The radiation observation gave context for interpreting the amplitude dip during bore interaction (snaps 3-7).
- **kb-kdv-smallAmplitude-dispersiveRegime**: Noted amplitude threshold ~0.1 for dispersive spreading. Our soliton maintains >> 0.1 throughout, so dispersive collapse was not a concern here.

**Rejected entries (no matching applicability):**
- **kb-shallowWater-LaxFriedrichs-stable-smeared**: LxF not used because bore sharpness matters for measuring the soliton-bore interaction; MUSCL+Godunov is superior here.
- **kb-shallowWater-HLL-dam-break-pass**: HLL for shallow water — not directly applicable to Burgers equation.

## Final self-assessment

**I believe `pred_results/T_C.npy` satisfies the phenomenon target.**

Numerical diagnostics from E1:

| Check | Value | Required | Pass? |
|-------|-------|----------|-------|
| final v_max (soliton peak) | 0.5081 | >= 0.5 | YES |
| final u_max (bore bound) | 1.2956 | < 5 | YES |
| NaN/Inf anywhere | False | False | YES |
| Output shape | (9, 2, 256) | (>=5, 2, 256) | YES |
| mass_v conserved | 3.000 | — | stable |

The simulation captures the bore-soliton encounter: the v-soliton (initial amp 1.5 at x=-8) moves rightward and interacts with the Burgers bore (centered at x=0, descending step u_L=1.5, u_R=0). During interaction (snapshots 3-7, t ≈ 3–7), the soliton amplitude dips to ~0.42 as it penetrates or scatters off the bore. By T=8, the soliton has partially re-emerged with peak amplitude 0.5081, satisfying the survival criterion. The bore u remains bounded [0.22, 1.30] throughout — no blowup.
