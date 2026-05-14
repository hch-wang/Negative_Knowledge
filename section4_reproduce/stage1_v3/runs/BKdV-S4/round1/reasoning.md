# Round 1 — E1 baseline

## Proposed design
Lay down a single reference run at the prompt-specified BASELINE parameters,
using the PRE-VALIDATED stack (no method iteration this round):

- solver: Fourier pseudospectral + 2/3-dealias on every nonlinear product +
  integrating-factor on v's v_xxx + RK4 on the rest + 8th-order hyperviscous
  tail on u-hat with coefficient ν_h.
- params: dt=5e-4, Nx=256, ν_h=1e-22.
- IC: v0 = 1.5 sech²(x+5), u0 = v0²/2  ⇒ m₀ = u₀ − v₀²/2 ≡ 0
  (a Gardner-manifold IC; this prepares us to detect Gardner-manifold escape).
- T_final = 10.

Diagnostics recorded along the trajectory (every Δt_diag = T/100 = 0.1):
||m||_L2, ||m||_inf, ||u||_L2, ||v||_L2, mass_u, mass_v, energy
E = ½∫(u² + v² + v_x²) dx, lock_corr(u, v²/2), low/high spectral partition
(k < 2 vs k ≥ 2) for u and for v, plus 11 (u(x), v(x)) snapshots.

This baseline is the reference E2 and E3 will diff against. The 5% threshold
specified by the prompt is applied to the *t_end* values of those diagnostics.

## Observations
- Wall: 3.3 s; nsteps=20000; no blow-up.
- ||m||_L2: 0.0 → 2.456 . The Gardner-manifold IC does NOT stay on the manifold;
  m grows quickly. (Consistent with the existing stage-2 finding that the
  Gardner manifold m=0 is NOT attracting under BKdV — but here we are NOT
  testing physics, only logging the trajectory as a numerical reference.)
- ||m||_inf: 0.0 → 3.667.
- lock_corr(u, v²/2): 1.0 → 0.1997  (anti-locking).
- L2_u: 1.076 → 2.489 (more than doubled). L2_v: 1.732 → 0.829 (halved).
  So mass is shifted from v into u over T=10.
- mass_u and mass_v: conserved to 1e-9 . Good (divergence-form is intact).
- E = ½∫(u² + v² + v_x²) dx: 3.279 → 3.547  (drift ≈ +8.2 %).  This is the
  diagnostic most likely to be sensitive to ν_h (hyperviscous u-tail dumps
  energy out of high-k modes) and to Nx (cut-off changes the high-k tail).
- Spectral high-k content (k ≥ 2): for u, eh_u(T)=0.1606, comparable to el_u;
  for v, eh_v(T)=9.6e-5  ≈ zero . So v is genuinely low-pass at T=10 but u has
  developed a high-k component, presumably the sharpened front (u_peak=3.67).
- v_peak collapses 1.5 → 0.55; u_peak grows 1.125 → 3.67. Consistent with
  the "u eats v" picture (m grows by u inflating).

## Conclusion this round
Baseline is well-defined, finite, conservation laws are intact for mass.
End-state values to track in E2/E3 :

  m_l2(T) = 2.456
  m_inf(T) = 3.667
  L2_u(T) = 2.489
  L2_v(T) = 0.829
  lock(T) = 0.1997
  energy(T) = 3.547

Decision: E2 will change ONE numerical parameter — spatial resolution
(Nx 256 → 512) — keeping dt and ν_h fixed. Spatial resolution is the most
likely sensitivity for the sharpened front in u (k_max effectively doubles,
the hyperviscous cut-off moves). Round-3 will then change a *different*
numerical parameter — hyperviscosity coefficient — to disentangle the two.
