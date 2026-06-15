# Session log: S8

- iter 0 (setup): read prompt.md and meta.json. Test = "B-NLS low-density 'hole' — quantum pressure singularity stress test". IC = sech^2(x-5) + 0.001, so min(N0)=1e-3. Goal: characterize when each method fails as N approaches 0.

- iter 1 (debug-discovery, not an E node): first run with naive spectral derivative of phi=0.1*x blew up immediately because phi is not periodic — Gibbs oscillations gave phi_x range [-17, +8] at t=0 instead of constant 0.1. Fixed by splitting phi = 0.1*x + phi_tilde (periodic) and adding 2/3 dealiasing for nonlinear products.

- iter 2 (E1): direct (u, N, phi_tilde) RK4, eps_reg=1e-6. Blew up at t=0.027 with min_N=-1.4, max|Q|=1.08e5. Confirmed the predicted failure: N goes below zero, then 1/sqrt(N+eps) cascades through phi_t -> u_t.

- iter 3 (E2): same scheme, eps_reg=1e-3 (matches initial background). Blew up at t=0.044 with min_N=-1.19, max|Q|=3.66e3. Delayed by 1.6x relative to E1 but still catastrophic. Conclusion: regularization alone cannot save the direct formulation here.

- iter 4 (E3): Madelung-Psi with Strang split-step, psi = sqrt(N + 1e-3) e^{i phi_tilde}. SUCCESS — completes T=4.0 with min_N >= -eps_mad = -1e-3, mass conserved to 0.09% relative drift, max|Q| bounded around 1.7e3 (i.e., transient but does not run away). The structure |psi|^2 = N + eps_mad >= 0 is preserved by construction, so the quantum pressure singularity is dissolved.

- iter 5 (wrap-up): write reasoning.md, knowledge_findings.json. candidate.py contains all three methods so a single run reproduces the comparison.
