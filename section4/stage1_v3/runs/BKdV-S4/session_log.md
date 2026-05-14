# BKdV-S4 session log

Program: numerical-resolution sensitivity (dt, Nx, ν_h).

| round | E_id | change vs baseline | result | trivial? |
|-------|------|--------------------|--------|----------|
| 1     | E1   | none (baseline dt=5e-4, Nx=256, ν_h=1e-22) | wall=3.3 s, no blow-up. End: m_l2=2.456, lock=0.200, L2_u=2.489, L2_v=0.829, energy=3.547 (+8.2 % drift from 3.279). | n/a (baseline) |
| 2     | E2   | Nx 256→512 (three sub-runs) | E2a (ν_h=1e-22 fixed): blow-up t=0.002 from explicit-HV stability. E2b (ν_h rescaled, dt=5e-4): blow-up t=0.097 from u-eq dispersion CFL. E2c (ν_h rescaled, dt=1e-4): stable; ALL diagnostics shift far beyond 5 %: m_l2 −33 %, lock +139 %, energy −51 %, u_peak −39 %. Nx 256 baseline is sub-converged. | no |
| 3     | E3   | ν_h sweep at Nx=256, dt=5e-4 (four sub-runs incl. dt-trivial check) | E3a (ν_h=1e-18, dt=5e-4): blow-up t=0.003 (same mechanism as E2a — trivial re-finding). E3b (ν_h=1e-26, dt=5e-4): stable; max shift 11.7 %, most under 2 % → ν_h ROBUST in weak direction. E3c (ν_h=1e-18, dt=1e-5): stable; energy −71 %, m_l2 −51 %, lock +277 % → ν_h SENSITIVE in strong direction. E3d (ν_h=1e-22, dt=1e-4): stable; max shift 13.2 % (eh_u), most under 5 % → dt mostly-trivial as prompt anticipated. | F3a trivial; F3d (partial-trivial) |
