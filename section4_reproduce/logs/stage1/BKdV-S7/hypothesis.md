# BKdV-S7 hypothesis (final synthesis)

## Program research question

The Gardner equation v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0 arises as the
m = 0 reduction of the coupled BKdV system

  u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -∂_x (u v)

via the substitution u = v^2 / 2.  The naive expectation is therefore that an
IC stable in Gardner-only evolution should remain stable in full BKdV when
initialized with u_0 = v_0^2 / 2 (so m_0 ≡ 0). **Find a concrete
counter-example and quantify the breakdown mechanism.**

IC fixed across the program:
- v(x, 0) = A sech^2(x + 5),  A = 1.5
- For BKdV: u(x, 0) = v(x, 0)^2 / 2  (so m_0 = 0 to machine precision)
- Periodic x ∈ [-15, 15], Nx = 256, T = 10
- Numerical stack identical across solvers: Fourier pseudospectral + 2/3
  dealiasing + RK4, dt = 2e-4.

## Two key findings (bank-relevant)

### (a) POSITIVE — Gardner stable reference  (F1, E1, is_trivial: false)

The Gardner equation at A = 1.5 with the IC v_0 = 1.5 sech^2(x + 5)
propagates as a clean coherent single peak over T = 10:

| Diagnostic     | t = 0          | t = 10         | drift        |
|----------------|-----------------|-----------------|---------------|
| mass_v         | +3.0000e+00     | +3.0000e+00     | +0.000000%    |
| L2v (Casimir)  | 1.73205         | 1.73205         | +0.000000%    |
| H (Hamiltonian)| -4.13571        | -4.12794        | +0.188%       |
| v_max          | 1.4977          | 1.4957          | -0.137%       |
| n_peaks        | 1               | 1               | constant      |

The peak wraps the periodic domain at speed c ≈ 3.56. Mass and L2 are
exact, the Gardner Hamiltonian drifts <0.2%. **Stable reference.**

### (b) NEGATIVE — BKdV breakdown of the m = 0 manifold  (F2 + F3, E2 + E3, is_trivial: false)

Under the **same** IC plus u_0 = v_0^2 / 2 in full BKdV:

#### Drift off the m = 0 manifold

‖m(t)‖_L2 grows from 0 immediately:

| t   | ‖m‖_L2  |
|-----|----------|
| 0   | 0        |
| 0.5 | 0.7365   |
| 1.0 | 1.2157   |
| 2.0 | 1.8739   |
| 5.0 | 2.3323   |
| 10  | 2.5498   |

Empirical initial rate ≈ **1.18 per time unit** (m_norm(t = 1) / 1).

The BKdV-S5 algebraic identity
  **m_t |_{m = 0}  =  (v − 1) · (6 v v_x + v_xxx)**
evaluated on our specific IC v_0 = 1.5 sech^2(x + 5) gives a source
S(x) := (v_0 − 1) · (6 v_0 v_0,x + v_0,xxx) with the following diagnostics:

- ‖S‖_L2 = **1.7682 per unit time** (predicted initial growth rate of ‖m‖_L2)
- ‖S‖_Linf = 1.319
- ∫S dx = 0 (signed); ∫|S| dx = 3.665
- spatial support (5% threshold of Linf): **x ∈ [-8.20, -1.76]** — localized
  to the soliton core
- Source decomposition: ‖(v−1)·6 v v_x‖_L2 = 2.39, ‖(v−1)·v_xxx‖_L2 = 1.91
  (quadratic-flux piece slightly larger than dispersive piece, ratio 1.25)

Linear extrapolation ‖m‖_L2(t) ≈ t · ‖S‖_L2 matches observed within **17%
at t = 0.5** (0.736 observed vs 0.884 predicted), then under-saturates as
nonlinear feedback engages (ratio falls to 0.53 by t = 2).

#### v amplitude collapse and dispersive fragmentation

- v_max drops from 1.498 to 0.558: **-62.8% drift**.
- v solution fragments from a single coherent peak (n_peaks = 1) into a
  multi-peaked dispersive train (n_peaks reaches 8 by T = 10).
- u_max climbs from 1.12 to 3.97 — a ~3.5× amplification driven by the
  v² source term in the u equation.

#### L2 distance from Gardner solution

| t   | ‖v_BKdV − v_Gardner‖_L2 |
|-----|--------------------------|
| 0.0 | 0                        |
| 0.5 | 0.1317                   |
| 1.0 | 0.3751                   |
| 2.0 | 0.5837                   |
| 3.0 | 1.1223                   |
| 5.0 | 1.9755                   |
| 10  | 1.8138                   |

By T = 10, the L2 distance to Gardner is **1.81 > ‖v_BKdV‖_L2 = 0.84** —
the BKdV solution is more dissimilar from Gardner than from zero. The
solutions are essentially uncorrelated for t ≥ 2.

#### Spectral mechanism (k-selectivity prediction validated)

The top 5 positive-k Fourier modes of the source S(x) are
**n = 4, 5, 3, 6, 2** (wavenumbers k ≈ 0.4 to 1.3). The top 5 observed
positive-k Fourier modes of m at t = 0.5 are **n = 4, 3, 5, 2, 6** —
identical mode set with slight reordering.

**Cosine similarity** between |m̂(k, t=0.5)|/0.5 and |Ŝ(k)| over positive-k
modes: **0.940** — strong spectral agreement.

Secondary spectral content: dispersive piece (v−1)·v_xxx contributes
high-k modes n ≈ 13–16 (k ≈ 2.7 to 3.4) which also appear in observed m.

#### Amplitude (A) sensitivity

‖S‖_L2 vs A scales in two regimes:
- A ∈ [0.25, 0.75]: log-log slope **0.22** (nearly constant; dispersive
  piece dominates because v ≪ 1 makes (v − 1) ≈ −1).
- A ∈ [1.0, 2.5]: log-log slope **2.49** (between A² and A³; (v − 1)·6 v v_x
  becomes the cubic-Burgers piece once v passes 1 over the soliton core).

At A = 1.5 we are just above the (v − 1) sign-flip threshold; the source is
fully on with both pieces contributing — hence the rapid breakdown.

## Mechanism summary

1. The IC has v_max = 1.5 > 1. The factor (v − 1) is **positive over the
   soliton core**, so the source S = (v − 1)(6 v v_x + v_xxx) is *fully
   turned on* — neither piece is suppressed.
2. m is generated locally at the v_0 peak (x ≈ -5) with spectral mass
   concentrated at intermediate-k modes n = 2–6.
3. Once m ≠ 0, the BKdV coupling −∂_x(u v) in the v-equation differs from
   the Gardner reduction by exactly −∂_x(m v); this term immediately
   amplifies modulation of v at the same k modes, fragmenting the
   coherent peak.
4. The Burgers self-flux 3 u u_x in the u-equation steepens u (u_max
   grows ~3.5×), which feeds further forcing into v.
5. By t ≈ 2 the system is in a multi-peaked dispersive state with no
   coherent traveling wave; m saturates near 2.55 and v_max decays to
   ~0.56 — independent of the Gardner reference.

## Implication for downstream Class B

Class B Conjecture B1 ("compound soliton mechanism on the m = 0 reduction")
**cannot rely on Gardner stability arguments**:

- The Gardner reduction is a kinematic substitution, not a dynamically
  invariant set of BKdV.
- Any compound-soliton construction in BKdV must either (i) build a
  *coherent state of full BKdV* directly (e.g. via relaxation /
  imaginary-time integration on the coupled system) or (ii) work in an
  amplitude regime A < 1 where (v − 1) is uniformly negative and the
  source is dispersively-suppressed (which loses the cubic-Gardner content
  responsible for "Gardner soliton" features in the first place).
- The "u = v²/2 ⇒ BKdV ≡ Gardner" identification is **a one-time
  algebraic coincidence at t = 0, not a dynamical equivalence**.

## Trivial-finding flag

None of F1, F2, F3 are trivial:
- **F1** (Gardner stable at A = 1.5, T = 10): a non-trivial positive
  result with quantified drifts <0.2% and quantified peak speed; not
  reducible to "A = 0 is stable."
- **F2** (BKdV breakdown): quantified ‖m‖_L2 trajectory, v_max collapse,
  L2 distance to Gardner; explicit numerical refutation of the
  Gardner-inheritance hypothesis.
- **F3** (mechanism via BKdV-S5 identity): quantitative match (17% on
  amplitude, cos-sim 0.94 on spectral content) between predicted source
  S(x) and observed m(x, t) at early time; quantifies the integrated
  source, decomposes it into quadratic-flux and dispersive pieces, and
  identifies the A ≈ 1 sign-flip threshold of the (v − 1) factor.

Trivial-finding count: **0**.

## Recommendation for downstream Stage-2

1. Drop the "Gardner soliton on m = 0" framing for BKdV stability work.
2. Build a coherent BKdV state numerically (relaxation on the full
   coupled system) before any perturbation/linear-stability analysis.
3. Sweep A across the (v − 1) sign-flip threshold (A ≈ 1) to find the
   slowest-breakdown regime; below A = 1 the source is dispersive-dominated
   and ~constant in A, suggesting a slower drift may exist but Gardner
   features will be weak.
4. Map the predicted spectral source Ŝ(k) for general IC families (Gaussian,
   bi-soliton, periodic train) to predict which BKdV ICs minimize the
   initial off-manifold forcing.
