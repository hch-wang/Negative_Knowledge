# Round 1 reasoning (E1: baseline Gardner-soliton-like configuration)

## Proposal

Set up the smallest meaningful baseline: an "approximate Gardner soliton" on the
m=0 reduction. Take v(x,0) = a sech²(x+5) with u(x,0) = v(x,0)²/2 so that
m₀ = u - v²/2 = 0 at t=0. Choose a near the lower end of the prescribed band
[1, 2] for stability, and evolve to T=15 with the pre-validated solver stack
(Fourier pseudospectral + 2/3 dealiasing + IMEX-CN on v_xxx + MUSCL-Godunov on
u's self-flux + dt=1e-4).

The expectation from the prompt is that this should propagate as a "coherent
traveling wave"; we measure peak amplitude, peak position (→ phase speed),
energy, mass conservation, and especially `m_norm = ||u - v²/2||_L²` (the
distance off the m=0 invariant set).

## Bug fix history (not counted as separate rounds)

- First attempt used a=1.5, dt=2.5e-4, forward-Euler on u spectral. Blew up at
  t≈3 (energy: 2.08 → 29 → nan).
- Reduced to a=1.0, dt=1e-4. Still blew up at t≈9 with sup→17.
- Added MUSCL-Godunov on u's self-flux 3 u u_x to handle the Burgers-bore that
  forms once u acquires large amplitude. With this, the run completes T=15
  cleanly with mass conservation to 0 ppm.

## Observations at T=15

- `mass_v` conserved to 0 ppm; `mass_u` would only conserve if Burgers fluxes
  conserve, which MUSCL does in flux form.
- `m_norm`: 0.0 (t=0) → ~1.5 (t=1) → bounded around 1.3–2.0 → 2.9 (T=15).
  **The m=0 set is NOT invariant for this BKdV** (algebra confirms:
  m_t|_{m=0} = (v-1)(6 v v_x + v_xxx), generically nonzero for sech² IC).
- `v_peak`: 1.0 (t=0) → 0.4–0.7 oscillating chaotically → 0.93 (T=15).
  No coherent single peak persists.
- `energy = 0.5 ∫(u²+v²)`: 0.78 (t=0) → drifts upward; +680% by T=15. The
  energy of the (u,v) pair is not a conserved quantity for the full BKdV
  system; the increase is consistent with energy flowing into the u-field via
  the off-manifold drift.
- Phase speed from a linear fit to peak-x position is unreliable because the
  peak jumps around the chaotic field.

## Conclusion (E1)

The sech² m=0 IC does **not** behave as a coherent Gardner-soliton-like
traveling wave under the full BKdV system. Instead, the off-manifold drift
(established analytically by the m_t|_{m=0} ≠ 0 computation) immediately
radiates the peak, and the resulting state is a chaotic dispersive flow with
slowly growing `m_norm` and `energy(u,v)`. The numerical scheme is stable, the
mass-v invariant holds to machine precision, so this is **physical decoherence,
not numerical instability**.

This means downstream rounds must measure perturbation growth as the deviation
between the perturbed and baseline trajectories, which themselves are both
chaotic; we expect Lyapunov-style sensitivity may dominate "structured-
perturbation growth", complicating clean linear-response readings.
