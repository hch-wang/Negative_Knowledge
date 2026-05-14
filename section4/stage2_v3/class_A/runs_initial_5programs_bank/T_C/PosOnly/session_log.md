# Session log: T_C / PosOnly

iter 1: E1 Fourier pseudospectral + RK4 baseline (NO dealiasing) — diverged at step 16 (t=0.0032) due to aliasing overflow on quadratic nonlinear products of bore+soliton.
iter 2: E2 = E1 + 2/3-rule dealiasing on every nonlinear product (single-component upgrade per BKdV-S1). Ran to T=8 cleanly, perfect mass conservation, v target met (peak 1.50), but sup|u|=18.38 violates |u_max|<5 — Gibbs ringing from the periodic-boundary discontinuity of the smoothed-bore IC and from the physical Burgers shock at the bore center.
iter 3: E3 = E2 + Hou-Li smooth exponential filter sigma=exp(-36*eta^16) (single-component upgrade per kb-burgers-MUSCL-Godunov-shock-pass shock-capturing direction). Both phenomenon targets MET: final v peak = 0.666 (>=0.5), final sup|u| = 2.88 (<5), perfect mass conservation. STOP_USEFUL.
