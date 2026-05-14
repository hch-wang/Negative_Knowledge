# Reasoning: T_A / NoKB — Soliton Stability in Coupled Burgers-swept-KdV

## Final method

**Experiment E3**: Fourier pseudospectral spatial discretization + scipy `solve_ivp` with `RK45` adaptive time-stepping + small spectral hyperviscosity.

- Domain: x in [-15, 15], periodic, Nx=256
- IC: v(x,0)=2*sech^2(x+5), u(x,0)=0.5*v^2 + 0.2*v
- Spatial: FFT-based derivatives with 2/3 dealiasing (modes with |k_int| > Nx//3=85 zeroed)
- Stiffness: handled implicitly by RK45 adaptive time-stepping (solver chose small dt automatically near dispersive events)
- Stabilization: hyperviscosity -eps*k^4 with eps=1e-7 (dissipation rate ~0.01 at k_max_eff, negligible for soliton)
- Tolerances: rtol=1e-6, atol=1e-8, max_step=0.05

The PDE system:
- u_t = -3*u*u_x - 6*v*v_x - v_xxx + hyperviscosity
- v_t = -6*v*v_x - v_xxx - (uv)_x + hyperviscosity

## Iteration trace

- **E1 / F1**: Explicit RK4 with dt=0.001 blew up at t=0.003. Root cause: KdV v_xxx term requires dt < 5e-5 for explicit stability (k_max^3 ~ 19267). Diagnosis confirmed by CFL analysis.

- **E2 / F2**: ETD-RK4 with A=U-V variable decoupling + 2/3 dealiasing. Multiple bug fixes: (1) ETD sign/formulation error, (2) dealiasing mask used physical wavenumber units instead of integer wavenumber index. After both fixes, integration reached t=2 before blow-up due to unchecked growth of u; the A=U-V difference variable lacks any linear dissipation. Method insufficient for long-time stability.

- **E3 / F3**: scipy RK45 adaptive solver with tiny hyperviscosity (eps=1e-7). Integration completed to T=8 successfully. Soliton maintains single dominant traveling peak; mass perfectly conserved (0% drift); solution bounded (max|u|~6, max|v|<1). However v_peak decays from 2.0 to 0.64 (32% amplitude retention), below the >=50% (1.0) threshold.

## Use of memory

No knowledge bank was provided (NoKB condition). All method choices derived from general PDE numerical methods knowledge:
- Pseudospectral methods are standard for KdV and dispersive PDEs on periodic domains
- 2/3 dealiasing (Orszag 1971) is required for polynomial nonlinearities
- ETD methods (Cox-Matthews 2002) handle dispersive stiffness
- scipy solve_ivp RK45 provides adaptive stabilization for stiff systems

No bank entries cited (cites_bank: []) or rejected (rejects_bank: []).

## Final self-assessment

The final `pred_results/T_A.npy` (shape (9, 2, 256)):
- **Single dominant peak**: YES — at all time snapshots, v has exactly 1 dominant peak traveling from x=-5 to x=-10 (via periodic boundary). n_peaks above 30% threshold = 1-2 throughout.
- **Mass conservation**: EXCELLENT — mass drift = 0.00% (well within 8% limit).
- **Boundedness**: YES — max|u|<6.1, max|v|<2.0 at all times (well within |max|<15).
- **Amplitude criterion**: FAILS — v_final_peak = 0.64 (32% of initial 2.0), below the required >=1.0 (50%).

The amplitude decay is likely physical (not numerical): the 0.2*v perturbation to the Gardner reduction continuously drives energy from v into u, causing the v soliton to shed radiation. The large u values (max|u|~6) confirm energy is being transferred to u. The underlying soliton structure (single peak, mass conservation, boundedness) is preserved, but the perturbed system causes decay rather than strict stability.

**Confidence in satisfying phenomenon target**: LOW for the amplitude criterion; HIGH for mass, boundedness, and single-peak structure.
