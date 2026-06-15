# Session log: T_A / NegOnly

iter 1: Fourier pseudospectral + classical RK4, NO dealiasing, dt=2e-4 -> aliasing blow-up at t=0.004 (step 20), exactly matching BKdV-S1 deep-synthesis signature.
iter 2: Add 2/3-rule dealiasing on all quadratic products; keep RK4, dt=2e-4 -> still blows up at t=0.006 (step 30) due to amplitude-tightened explicit nonlinear CFL at A=2 vs BKdV-S1's A=1.5 envelope.
iter 3: Halve dt to 1e-4 (only single-component change), keep dealiased Fourier+RK4 -> clean run T=8 in 26 s, mass_v drift 0.00%, single dominant peak preserved at every snapshot, peak amp decays 2.0->0.64 (matches BKdV-S7 prediction of fragmentation radiation for off-Gardner-manifold sech^2 IC).
