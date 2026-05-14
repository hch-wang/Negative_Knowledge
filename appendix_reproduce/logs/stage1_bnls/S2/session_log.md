# Session log: S2


E1: Run BOTH methods (Madelung-Psi split-step + direct (N,phi) RK4 spectral, eps=0). Result: Madelung mass drift 1.1e-13 (perfect); direct BLEW UP at step 1 (t=0.001) with |Q|=6.8e7 and N reaching 1.6e18. Confirmed: quantum pressure 1/sqrt(N) singularity in soliton tails (min N0 ~ 3e-24) instantly destabilizes spectral RK4.
E2: Direct (N, phi) with hard-floor regularization sqrt(max(N, eps)), eps in {0, 1e-12, 1e-6, 1e-3}. ALL FOUR BLEW UP. eps=1e-3 (largest) had the largest qmax = 5.2e12 because the larger flat floor amplifies spectral artifacts on sqrt(N)'s second derivative. Survived only 1-6 steps out of 4000 needed.
E3: Smooth regularization Nsafe = N+eps at eps in {1e-6, 1e-3, 1e-1} plus a (soft, eps=1e-3, 2/3-rule dealiased) variant. Survival improved monotonically from 2 to 21 steps, but ALL still blew up well before T=4 (4000 steps needed). Smooth is better than hard, dealiasing helps, but the (N, phi) system on a periodic spectral grid is fundamentally unstable for soliton tails — Madelung-Psi is mathematically necessary, not optional.
D3: Stop. Knowledge recorded.
