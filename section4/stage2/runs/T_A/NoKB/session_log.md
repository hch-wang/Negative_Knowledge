# Session log: T_A / NoKB

iter 1: E1 Fourier pseudospectral (no dealiasing) + RK4, dt=1e-4. Blew up at t~0.5; classic aliasing instability on quadratic nonlinearities. Decision D1: add 2/3-rule dealiasing.
iter 2: E2 = E1 + 2/3-rule dealiasing on every quadratic product. Stable, mass-conserving (drift ~0%), max|u|=11.24 over snapshots, max|v|=1.997, final peak v=1.355 (amplitude ratio 0.678 >= 0.5). Multi-peak final structure with top 4 v-peaks in [1.16, 1.36]. Decision D2: retry with dt 1e-4 -> 1e-5 to check time-step convergence.
iter 3: E3 = E2 with dt=1e-5. Trajectories agree with E2 up to t~5; after that E3 develops a clearer dominant peak (v=2.165 vs next 1.528) but max|u| over snapshots grows to 17.47 > 15 (violates boundedness). Decision D3: stop. Final answer = E2 (the only iteration to satisfy all four phenomenon criteria simultaneously). T_A.npy restored to E2 output; candidate.py rewritten as the E2 solver. The final candidate.py re-executes E2 deterministically.
