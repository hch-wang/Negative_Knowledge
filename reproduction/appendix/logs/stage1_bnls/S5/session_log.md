# Session log: S5

- iter 1 (Q1 init): registered stress question -- does Strang-splitting B-NLS preserve Mcs?
- iter 2 (E1 plan): chose Method A (on-manifold Madelung-Psi Strang split, u := Im(conj Psi Psi_x)), Method B (decoupled Strang, upwind-Burgers + Madelung NLS, no boost), Method C (decoupled Lie).
- iter 3 (E1 run, first pass): hit two bugs. (i) m diagnostic used np.angle(psi) for phi then took dx of it -- branch-cut spikes inflated ||m|| to ~37 spuriously. (ii) Method B+C with spectral RK4 + small hyperviscosity blew up to NaN at the Burgers shock.
- iter 4 (E1 fix): switched m diagnostic to phix := Im(conj Psi Psi_x)/|Psi|^2; switched u-Burgers to conservative upwind (Engquist-Osher flux, 4 sub-steps per dt). Clean run.
- iter 5 (E1 results): A: ||m||_2 ~ 8e-14 (machine precision, on-Mcs by construction). B,C: ||m||_2 grows linearly to 0.21 over T=6. Decoupled splitting drifts off Mcs.
- iter 6 (E2 plan): test Lie-vs-Strang ordering inside Method A, sweep dt to {0.0005, 0.001, 0.005} for A, and add Method D (fully coupled RK4 on (u,N,phi)) with QP regularization 1e-8.
- iter 7 (E2 run): A-Strang & A-Lie both at 1e-13 (ordering moot on-Mcs). A_dt0.005 keeps Mcs but mass/energy/peak go wrong (kinetic propagator aliases). Method D diverges at step 3 (QP stiffness).
- iter 8 (write-up): finalize knowledge_findings.json + reasoning.md.
