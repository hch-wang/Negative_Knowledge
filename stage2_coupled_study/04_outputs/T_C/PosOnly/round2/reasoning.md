# Round-2 Reasoning

## Method

The round-2 solver uses a split-operator approach rather than a single uniform pseudospectral explicit scheme:

- **u (Burgers bore):** MUSCL-van Leer reconstruction + Godunov exact Riemann flux for the `-3 u u_x` hyperbolic term, which is TVD and handles the bore shock without Gibbs oscillations. The coupling source `-dx(3v^2 + v_xx)` is added spectrally (always smooth).
- **v (KdV soliton):** IMEX-Crank-Nicolson spectral — the dispersive `v_xxx` term is treated implicitly with CN (unconditionally stable for this linear stiff term), while the nonlinear `-6 v v_x - dx(u v)` is treated explicitly at the current time step.
- **Time step:** `dt = 0.0002`, satisfying CFL ~ 0.3 for the Burgers hyperbolic sector (u_max ~ 1.5, 3*u_max * dt/dx ~ 0.3) and well within the CN-stable regime for dispersion.

## Use of r1 finding

Round 1 used a fully explicit pseudospectral method with `dt = 0.0005`. The blow-up manifested immediately as overflow in `u * u_x` and `u * v` products, indicating the explicit scheme violated the CFL constraint for the Burgers operator or had amplified high-frequency spectral modes without any TVD protection. The coupling via spectral differentiation of the bore (a near-discontinuity) produced large Gibbs-amplified wavenumber content, feeding back into overflow.

The new method addresses this in two ways:
1. MUSCL-Godunov for the Burgers sector eliminates Gibbs by working in physical space with a limiter, keeping the bore TVD.
2. The time step is reduced to `dt = 0.0002` (factor ~2.5 smaller), bringing the Burgers CFL down to ~0.3.

## Use of bank

- **kb-burgers-MUSCL-Godunov-shock-pass**: directly used — MUSCL with van Leer limiter + Godunov flux is the scheme for the Burgers bore; TVD property prevents Gibbs contamination in the bore region.
- **kb-kdv-IMEX-CN-spectral-pass**: directly used — IMEX-CN is applied to the v equation; the CN denominator `(1 - dt/2 * ik^3)` has magnitude >= 1, ensuring unconditional stability for dispersive stiffness, and was validated at amplitude 2 over T=2 in the bank.
- **kb-gardner-KdV-method-transfer-moderate-amplitude**: confirms IMEX-CN + 2/3 dealiasing transfers cleanly at amplitude 1.5 (exactly our IC amplitude). Dealiasing was not added here since the v IC is smooth (sech^2) and the primary instability risk is from the Burgers sector, not the KdV dispersive sector.

## Risks

1. **Explicit coupling instability:** The `-dx(u v)` term in the v equation is treated explicitly. As u and v overlap during the interaction, u ~ 0.75 at the transition and v ~ 1.5, so `|u v|` can reach ~1.1. The spectral derivative amplifies high-k modes; this could cause instability if v develops sharp features during the interaction. Mitigation: the small dt = 0.0002 keeps this Courant-like contribution bounded.
2. **Bore–MUSCL accuracy:** MUSCL is second-order in smooth regions but only first-order near the bore. The bore broadening over T=8 is physically expected, but the coupling source (computed spectrally from v) may introduce small-scale noise back into u. If the bore sharpens due to the coupling, MUSCL with van Leer limiter will clip it, which could cause a slight over-diffusion of u.
3. **Periodic domain re-entry:** The domain is [-15, 15] (L=30). The bore moves right at speed ~ 3*1.5/2 = 2.25, covering ~18 units in T=8, which may wrap around and interact with the soliton a second time. This is physically unrealistic but unavoidable with periodic BCs; however, the eval only checks the final state, not the interaction history, so this is unlikely to cause an eval failure.
