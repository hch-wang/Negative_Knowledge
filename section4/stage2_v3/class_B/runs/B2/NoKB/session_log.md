# Session log: B2 / NoKB

- Round 1 (E1): 5x5 coarse grid (u_L in {0.2,0.4,0.6,0.8,1.0}, A in {0.2,0.5,1.0,1.5,2.0}), T=12, dt=1e-4, nu=5e-2. 25 runs in 545 s. Found two qualitative regimes; n_peaks DECREASES with increasing u_L at fixed A (opposite of "bore destroys").
- Round 2 (E2): u_L=0 baseline (5 runs) + finer A grid at u_L=1.0 (6 runs), same solver. 11 runs in 218 s. Baseline showed sech^2 IC fissions intrinsically for A>=0.5. Bore SUPPRESSES this fission; boundary at u_L=1.0 bracketed to A in (1.0, 1.2).
- Round 3 (E3): Sharpness sweep at u_L=1.0 in A in {0.90, 1.00, 1.05, 1.10, 1.15}; long-T arm (u_L=1.0, A=1.0, T=24); dt-half arm (u_L=1.0, A=1.10, dt=5e-5); reflection probe (u_L=2.0, A=0.2). 8 runs in 156 s. Boundary sharp at Δ A <= 0.05; dt-converged to 4 sig figs; "transmission" is a delayed-fission TRANSIENT (T=12: 1 peak, T=24: 2 peaks); no reflection observed.
