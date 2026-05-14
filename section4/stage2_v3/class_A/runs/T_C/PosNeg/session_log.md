# Session log: T_C / PosNeg

iter 1: E1 baseline (Fourier+2/3+RK4, no u-viscosity) — ran to T=8 cleanly; mass exactly conserved; but bore-driven Gibbs gave TV(u) 165x inflation, u_max=3.4 (bounded), v_max_final=0.448 (just below 0.5 phenomenon threshold); soliton fragmented into 6 peaks. Confirms BKdV-S6 r1 mode.
iter 2: E2 = E1 + explicit linear viscosity ν*u_xx with ν=5e-2 on u-equation (single-component escalation; BKdV-S6 prescription). Phenomenon target MET: v_max_final=0.506 (>=0.5), u_max_final=1.340 (< 5), TV(u) only 3.3x IC TV (vs 165x in E1), mass exactly conserved. Soliton physically transmits through bore with energy loss; partial recovery from t=4 dip 0.418 to T=8 value 0.506. STOP_USEFUL.
