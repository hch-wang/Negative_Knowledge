# Reasoning: Stress Test A3 — Burgers / Very Long T

## Method as written
I implemented the Lax-Friedrichs finite-difference scheme applied to the inviscid Burgers equation in conservation form (flux F = u²/2) on a periodic domain with Nx=200 grid points and CFL=0.5, integrated to T=10.0. This scheme is stable (satisfies the entropy condition and is consistent) but highly dissipative.

## Predicted vs expected
I agree with the predicted outcome of a decayed N-wave plus periodic boundary recirculation contamination. By T=10.0, which is far beyond the shock formation time (~1/π ≈ 0.32), the initial sine wave has long since formed and the dissipation of Lax-Friedrichs has numerically smeared the shock. The periodic boundary allows the solution to recirculate: the net zero mean of the initial condition is preserved, and the shock/rarefaction structure wraps around the periodic domain repeatedly, producing a contaminated N-wave-like profile. The heavy numerical diffusion of Lax-Friedrichs also progressively damps amplitude over such a long integration, consistent with a decayed N-wave.

## What knowledge this might produce
A future agent solving long-time Burgers integration on periodic domains can learn that highly dissipative schemes like Lax-Friedrichs, while stable, wash out sharp features over long times and are unsuitable when fine shock resolution is needed at large T. It also confirms that periodic recirculation contamination is a genuine artifact of long-time integration, not a scheme artifact — any stable scheme will exhibit it, though dissipative schemes smear the recirculated features more.
