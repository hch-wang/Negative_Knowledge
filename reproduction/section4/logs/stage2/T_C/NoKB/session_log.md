# Session log: T_C / NoKB

iter 1: E1 = Fourier pseudospectral (no dealiasing) + RK4, dt=1e-4 — NaN before t=1.0 due to aliasing from sharp bore + quadratic/cubic nonlinearities.
iter 2: E2 = E1 + 2/3-rule dealiasing — ran to T=8 (no NaN), v peak ~1.13 (>=0.5 ✓), but u_max grows to 11.48 (target |u|<5 ✗) due to Gibbs ringing as bore steepens into a Burgers shock.
iter 3: E3 = E2 + Hou-Li exp smoothing (alpha=36, p=36) per RK4 step — destabilized late-time, |u|max 28.8 at T=8 (worse than E2). Self-rolled back to E2; re-ran E2 to regenerate pred_results/T_C.npy (same method, counted as E2 iteration per bug-fix clause).
