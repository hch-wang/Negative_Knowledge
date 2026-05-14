# Burgers-NLS (B-NLS) system: coordinate form

## 1. From Hamilton's principle to PDEs

Source: variational Lagrangian (Holm-type formulation)

$$
\mathcal{L} = \frac{u^2}{2} - N(\phi_t + u\phi_x) - \frac{N}{2}\phi_x^2 - \frac{1}{2}(\partial_x \sqrt{N})^2 + F(N)
$$

with $F(N) = \kappa N^2$, so $F'(N) = 2\kappa N$.

Boosting the lab-frame NLS Hamiltonian $H_{\text{Lab}}$ by the momentum-map coupling $\int u N \phi_x \, dx$ and writing the Lie-Poisson canonical equations, we get three coupled evolution equations for $(u, N, \phi)$ in the Burgers frame:

### 1.1 Momentum (EPDiff-Burgers) equation

Define $m := u - N \phi_x$ (a covector density, transforms like $dx \otimes dx$). Then:

$$
\boxed{\;\partial_t m + (u m)_x + m\, u_x = 0\;}
$$

equivalently $\partial_t m + u m_x + 2 m u_x = 0$.

### 1.2 Continuity equation for the density $N$

$N$ is transported by the velocity $u + \phi_x$ (note: **not** just $u$):

$$
\boxed{\;\partial_t N + \partial_x\big((u + \phi_x)\, N\big) = 0\;}
$$

### 1.3 Hamilton-Jacobi equation for the phase $\phi$

$\phi$ is advected by $u$, with NLS quantum pressure and self-interaction:

$$
\boxed{\;\partial_t \phi + u \phi_x + \frac{1}{2}\phi_x^2 + \frac{(\sqrt{N})_{xx}}{2\sqrt{N}} - 2\kappa N = 0\;}
$$

## 2. Compound-soliton manifold

Define the **compound-soliton constraint manifold**:

$$
\mathcal{M}_{cs} := \{(u, N, \phi) : m = u - N\phi_x = 0\}
$$

On $\mathcal{M}_{cs}$, $u = N \phi_x$ and the momentum equation (1.1) is trivially preserved ($m = 0 \Rightarrow \partial_t m = 0$). The reduced dynamics on $\mathcal{M}_{cs}$ become:

- $N_t + \partial_x((N+1)\, N\, \phi_x) = 0$
- $\phi_t + (N + 1/2)\phi_x^2 + \frac{(\sqrt{N})_{xx}}{2\sqrt{N}} - 2\kappa N = 0$

This is a *boosted* NLS-Madelung system on a hydrodynamic manifold parameterized by $\phi_x$.

**The user's research observation**: generic ICs appear to relax toward $\mathcal{M}_{cs}$ — the system "tends to form Compound Solitons." Mechanism unknown.

## 3. Conserved quantities

- **Mass**: $M = \int N\, dx$, conservation follows directly from (1.2).
- **Energy**: $H = \int \big[\frac{N}{2}\phi_x^2 + \frac{1}{2}(\sqrt{N})_x^2 - F(N) + u N \phi_x\big] dx$
- **Momentum**: $P = \int m\, dx = \int (u - N\phi_x)\, dx$ — conserved by (1.1)? actually $\int m\, dx$ is conserved since $(um)_x + mu_x$ is a divergence-up-to-an-integrable term... need to verify; safe lower bar: $\int N\phi_x dx + \int u \, dx$ stuff.

For phenomenon eval: **mass** is the cleanest invariant.

## 4. Critical numerical challenges (new vs BKdV)

| Challenge | BKdV had it? | B-NLS specific issue |
|---|---|---|
| Aliasing in nonlinear products $u m$, $N\phi_x$, $\phi_x^2$, $N^2$ | Yes (KdV $vv_x$, Gardner $v^2 v_x$) | Same — 2/3 dealiasing should transfer |
| Burgers-type shock formation in $u$ | Yes (T_C) | Same — MUSCL / Godunov on $u$ should transfer |
| Hyperbolic continuity with vanishing density | Partial (shallow water) | **New & central**: $N \to 0$ creates $\frac{(\sqrt{N})_{xx}}{2\sqrt{N}}$ singularity |
| Quantum pressure $\frac{(\sqrt{N})_{xx}}{2\sqrt{N}}$ | **No** | **Genuinely new** — agent cannot directly recall from BKdV bank |
| Energy/mass conservation across long-time integration | Yes | Same |
| Multi-scale coupling: Burgers (hyperbolic) + NLS (dispersive) in 3 variables | Partial (2 vars) | More variables, similar character |

The **quantum pressure term** is the central new failure mode. Direct evaluation:
1. Compute $\sqrt{N}$ point-wise (requires $N \geq 0$ — **a numerical positivity requirement**, not a continuum constraint)
2. Take $\partial_x^2 \sqrt{N}$ (spectral or FD)
3. Divide by $\sqrt{N}$ — singular when $N \to 0$

Equivalent Madelung-transform implementation uses $\Psi = \sqrt{N} e^{i\phi}$ with NLS-like dynamics for $\Psi$ in the boosted frame — likely more stable but introduces complex-valued integration.

## 5. Numerical schemes — first-principles candidates

Spatial discretization:
- Fourier pseudospectral on $u$, $N$, $\phi$ all (simplest, BKdV bank endorses for KdV-like; risky for $u$ on shocks and for $N \to 0$)
- MUSCL/Godunov on $u$, spectral on $N, \phi$ (split, mirrors BKdV T_C compound success)
- All in $\Psi = \sqrt{N} e^{i\phi}$ Madelung form, then recover $(N, \phi, u)$ post-step

Time integration:
- Explicit RK4 (baseline; will fail for stiff quantum pressure)
- IMEX-CN on linear stiff parts (quantum pressure as Laplacian-of-$\sqrt{N}$)
- Strang splitting: linear (quantum pressure) + nonlinear (advection + self-interaction)

BKdV bank gives method names; bank does **not** tell agent how to handle $N \to 0$ singularity or quantum pressure — this is what stage 3 should expose.
