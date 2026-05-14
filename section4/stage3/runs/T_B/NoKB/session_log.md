# Session log: T_B / NoKB

## Pre-experiment analysis (timestamp: start)
- Task: Gaussian density packet on M_cs; expect bright soliton emission (focusing NLS modulational instability).
- IC: N(x,0) = 2*exp(-(x+5)^2/2.25), phi_x=0.3, u=0.3*N => m=u-N*phi_x=0 (on M_cs).
- M_cs invariance: m_t = -u m_x - 2 m u_x, so m=0 stays invariant.
- User's sign convention: +sqrt(N)_xx / (2 sqrt(N)) -- opposite to standard NLS Madelung.
- Strategy: E1 = simplest baseline = Fourier pseudospectral (u, N, phi) with RK4. Watch for: blow-up at N->0 (since quantum pressure ~ 1/sqrt(N)), aliasing, dt stability.

## E1 plan (no bank)
- Spatial: Fourier pseudospectral on (u, N, phi), Nx=256 on x in [-15,15].
- Time: explicit RK4.
- dt: choose conservative dt = 5e-4 initially (T=6, so 12000 steps).
- Snapshots: 21 (every 0.3s).
- Floor in sqrt(N) to avoid 0/0 (N_floor = 1e-10).
- No dealiasing, no operator splitting, no hyperviscosity.

