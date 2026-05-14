# Session log: S1 (NLS focusing bright soliton -- Madelung-Psi split-step validation)

System: i*Psi_t + (1/2)*Psi_xx + kappa*|Psi|^2*Psi = 0, kappa=+1, u=0.
IC: Psi(x,0) = sqrt(2) * sech(sqrt(2)*(x+5)) * exp(i*0.25*x). T=8.0. Domain [-15,15].

| iter | node | method                      | params                                          | outcome  | key diagnostic                                                                 |
|------|------|-----------------------------|-------------------------------------------------|----------|--------------------------------------------------------------------------------|
| 1    | E1   | Strang split-step Fourier   | dt in {0.01,0.001,0.0001}, Nx in {128,256,512}  | pass     | dt=0.001/Nx=256: |dM|/M=5.17e-13, |dE|/|E|=2.93e-12, relL2=5.68e-6, 0.15s wall |
| 1    | E1   | Lie (1st-order) split-step  | dt in {0.01,0.001,0.0001}, Nx=256               | partial  | Mass conserved (norm-preserving) but energy and shape error O(dt) (1st order)  |
| 1    | E1   | ETD-RK1 (exp-Euler)         | dt in {0.01,0.001,0.0001}, Nx=256               | fail     | NOT mass-conserving: |dM|/M = 0.14 @ dt=0.01, 1e-3 @ dt=0.0001 (cubic in dt-1) |
| 2    | E2   | Strang failure-boundary probe | Nx in {32,64,96,128}, dt in {0.5,0.1,...,0.01} | partial  | Nx=32 always fails (dx > soliton width); dt=0.5 fails at all Nx; mass still ok |
