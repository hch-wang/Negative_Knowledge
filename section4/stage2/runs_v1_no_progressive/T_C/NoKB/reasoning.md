# Reasoning: T_C / NoKB

## Final method

**Experiment E3**: Explicit pseudo-spectral RK4 with 2/3-rule de-aliasing.

- Domain: x in [-15, 15], Nx=256, periodic BC
- Time step: dt=0.00008 (100,000 steps total for T=8)
- All spatial derivatives computed via FFT: 1st, 2nd, 3rd order
- 2/3 de-aliasing mask applied to each field after every full RK4 step (zeroes top 1/3 of Fourier modes to suppress aliasing errors)
- 9 snapshots at t = 0, 1, 2, 3, 4, 5, 6, 7, 8

PDE solved:
```
u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -d/dx (u v)
```

## Iteration trace

- **E1 / F1**: Explicit RK4, dt=0.0005 — NaN blow-up at t=0.5. The v_xxx term imposes a stability limit of dt < k_max^3^{-1} ~ 0.0001, which dt=0.0005 violated by 5x.
- **E2 / F2**: Integrating Factor RK4 (IFRK4) handling v_xxx, dt=0.001 — still blew up at t=0.5. Root cause: the u-equation coupling term -d/dx(v_xx) also introduces effective k^3 stiffness not handled by the IF acting only on v. Both equations share this stiffness through the nonlinear coupling.
- **E3 / F3**: Explicit RK4, dt=0.00008 (below stability limit), 2/3 de-aliasing — ran stably to T=8. Final v_peak=0.6366, |u_max|=3.6174, no NaN. Phenomenon target met.

## Use of memory

No knowledge bank was provided (NoKB condition). All method choices were driven by general PDE numerics knowledge:
- cites_bank: [] for all experiments
- rejects_bank: [] for all experiments

Key reasoning steps from general knowledge:
1. Spectral stability analysis: for third-order dispersive terms with pseudo-spectral derivatives, the explicit RK4 stability limit scales as dt < C / k_max^3 (C ~ 2 for RK4). With Nx=256, L=30, k_max ~ 26.8, this gives dt < 0.000104.
2. IFRK4 is the standard fix for isolated stiff dispersive terms (e.g., pure KdV) but fails when both equations share cross-coupled stiffness of the same order.
3. Explicit RK4 at dt < stability limit with 2/3 de-aliasing is the conservative but reliable approach for coupled systems where the IF cannot decouple all stiff modes.

## Final self-assessment

The final `pred_results/T_C.npy` satisfies the phenomenon target:

| Criterion | Value | Required | Met |
|---|---|---|---|
| Final v peak amplitude | 0.6366 | >= 0.5 | YES |
| Final \|u\| max | 3.6174 | < 5 | YES |
| No NaN/blow-up | True | True | YES |
| Number of snapshots | 9 | >= 5 | YES |

Physical interpretation: The KdV soliton (initial amplitude 1.5 at x=-8) moves rightward, encounters the Burgers bore (centered at x=0, u_L=1.5, u_R=0) approximately between t=1 and t=3. The soliton transmits through the bore with reduced but surviving amplitude (minimum ~0.57 during transit, recovering to 0.64-0.98 afterward). The bore itself steepens moderately (u_max grows from 1.5 to ~3.6) but remains bounded. This is consistent with a refraction/transmission scenario rather than reflection or destruction.
