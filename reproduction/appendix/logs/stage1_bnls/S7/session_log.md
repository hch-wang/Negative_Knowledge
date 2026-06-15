# Session log: S7

- iter 1 (E1, all-spectral RK4): BLEW UP at t = 0.001 (one step). HJ quantum-pressure term (sqrt N)_xx / (2 sqrt N) overflows at the soliton tails where N ~ 1e-20. Bore in u also shows 0.26% Gibbs overshoot in the first sub-step, but the dominant failure is the HJ singularity. Confirmed prediction.
- iter 2 (E2, MUSCL u + Madelung-Psi): PASSES T = 8.0. u_max = 1.0 exactly, TV(u) = 1.988 (no Gibbs), N_max in [0.99, 1.01] throughout, |Psi|^2 mass drift = 1.5e-7 pre-collision and 7e-5 over the full run, single coherent soliton transmits across the rarefying bore. Collision time t = 5.0 (soliton crosses x=0). Bore foot at x = 3.98 at T = 8.0; soliton at x = 4.80.
- iter 3 (E3, MUSCL u + spectral (N, phi)): BLEW UP at t = 0.006. Same HJ singularity as E1, despite MUSCL+Godunov on u holding the bore monotone. Proves both cures are needed: MUSCL on u for the shock AND Madelung on Psi for the quantum-pressure singularity.
- Wrote knowledge_findings.json, reasoning.md, candidate.py = E2. Done.
