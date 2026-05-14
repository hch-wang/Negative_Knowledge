# Session log: T_D / NoKB

## Init
- Task: T_D Compound-soliton attractor relaxation under off-M_cs perturbation.
- Condition: NoKB (general PDE knowledge only).
- Budget: 3 iterations.
- IC: same N, phi as T_A (A=1.5, x0=-5, phi=0.5 x), u(x,0)=0.5*N(x,0)+eps*cos(2 pi x/L).
- Looked up T_A NoKB baseline (Fourier pseudospectral + RK4, dt=1e-3 on direct (u,N,phi)) — T_A blew up by t~8 (|u|max ~1e16, N peak ~5e8). This tells me direct (u,N,phi) with RK4 is structurally fragile; need to be alert at E1.
- Decided to follow progressive-complexity: E1 = direct (u,N,phi) Fourier-RK4 with small dt; observe failure mode.

## Plan
- E1: direct (u,N,phi) Fourier pseudospectral + explicit RK4 with dt=5e-4 (already tighter than T_A's 1e-3 because T=12 is longer and the system is known fragile); single eps=0.1 trial; 25 snapshots. Goal: see whether simple RK4 survives or blows up, and at what time.
- E2: depending on E1 — if blow-up, add 2/3 dealiasing OR switch to Madelung-Psi OR cut dt 5x.
- E3: refine on E2 to either harvest a clean tau (epsilon sweep) or narrow the claim.
