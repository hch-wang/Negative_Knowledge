# Session log: T_C / NegOnly

iter 1: E1 baseline (Fourier pseudospectral + explicit RK4, dt=1e-4, no dealiasing) blew up to all-NaN at t=0.56 via overflow in nonlinear products. Decision D1: upgrade ONE component -> IMEX-CN treating v_xxx implicitly.
iter 2: E2 (Fourier pseudospectral + IMEX-CN, dt=1e-3, no dealiasing) again blew up to all-NaN at t=0.78 in nonlinear products -- v_xxx stiffness was NOT the binding constraint, ALIASING is. Decision D2: layer ONE more component -> add 2/3 dealiasing rule.
iter 3: E3 (Fourier pseudospectral + IMEX-CN + 2/3 dealiasing, dt=1e-3) lasted to t=1.47 (1.9x further than E2); snapshot at t=1 is physically valid (max|u|=3.13, max v=0.82), then NaN from shock formation in u. Iteration cap exhausted; D3: narrow_claim, the unresolved residual issue is the spectral treatment of the shock-forming Burgers u-flux (would need upwind/MUSCL or spectral filter as the next single-component upgrade).
