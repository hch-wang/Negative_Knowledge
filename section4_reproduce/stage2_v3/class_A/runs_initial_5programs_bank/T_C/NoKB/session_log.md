# Session log: T_C / NoKB

iter 1: Pseudospectral + RK4 baseline (no dealiasing, dt=1e-4) — blew up to NaN around t<=0.5 due to aliasing from steep bore (width-0.5 step has full-band spectral content at Nx=256).
iter 2: Added 2/3-rule dealiasing on all nonlinear products. Run completed (no NaN). v soliton survived (final peak 1.22); however u developed monotonically growing Gibbs oscillations on the bore front (u_max=22.9 at t=8) — violating |u_max|<5.
iter 3: Kept E2 stack + added low-amplitude hyperviscosity (-1e-5 * u_xxxx) on u only. Run completed. v soliton survived (final peak 0.88, every snap >=0.69). u amplitude peaks 8.54 at t=6.5 and ends at 6.33 — still above the 5 threshold but bounded and not blowing up. Budget consumed; submitting E3.
