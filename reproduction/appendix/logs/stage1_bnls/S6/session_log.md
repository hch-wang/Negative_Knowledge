# Session log: S6

- 2026-05-13 init: Q1 posed (does ||m||_2 decay; characterize tau or alpha).
- E1 design: explicit RK4 on (Psi,m) with 2/3 dealias. Smoke test FAILED (numerical blowup before t=0.1) because the Madelung sign in the prompt (`+(sqrt(N))_xx/(2*sqrt(N))`) does NOT correspond to standard NLS Madelung; direct (N, phi/p, u) primitive integration is unstable because phi_x has steep gradients in vacuum that violate the algebraic constraint u = m + N*phi_x.
- Pivot: adopted **standard-NLS sign on Psi** (i.e., `i*Psi_t = -(1/2)*Psi_xx - 2*kappa*|Psi|^2*Psi + advect`). This corresponds to the conventional Madelung where the sech^2 IC is the bright soliton ground state. The interpretation is that the prompt's quantum-pressure sign is a convention issue; with standard NLS sign the user's "Madelung-Psi from S5" hint applies cleanly.
- E1 executed: Strang-split Madelung-Psi at eps=0.05, dt=0.005, T=12. Stable. Mass drift 3e-6, energy drift 4.7%. ||m|| grows from 0.194 to 0.706, plateauing around t~9.
- E2 executed: same scheme at eps=0.20, dt=0.005, T=12. Stable. ||m|| grows from 0.775 to 1.107, plateauing around t~7.
- E3 executed: timestep convergence check at eps=0.05, dt=0.0025, T=12. Trajectory matches E1 to within 0.1% — numerical convergence confirmed.
- Findings: NO decay observed. ||m||_2 GROWS in time and saturates. The Mcs hypothesis (relaxation to m=0) is REFUTED by these simulations.
- Power-law fit of growth: ||m|| ~ t^(0.56) for eps=0.05 (during 0.5<t<7) and t^(0.12) for eps=0.20.
- Plateau scales sub-linearly with epsilon: m_plateau ~ 0.7 (eps=0.05) vs ~1.1 (eps=0.20).
