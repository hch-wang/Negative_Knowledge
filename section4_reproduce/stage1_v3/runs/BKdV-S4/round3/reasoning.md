# Round 3 — E3 hyperviscosity probe (vary ν_h at Nx=256, dt=5e-4)

## Proposed design
Single-parameter change vs E1: vary ν_h while holding Nx=256 (baseline) and
dt=5e-4 (baseline). This is the DIFFERENT numerical parameter from E2 (which
probed Nx). Four sub-runs to triangulate hyperviscosity sensitivity AND
ground the trivial-flag in data:

- E3a: ν_h ×10⁴ stronger = 1e-18, dt=5e-4. Predicted to blow up (same
  mechanism as E2a: explicit-HV stability bound dt ≲ 2/(ν_h k_max^16) is
  ≈ 2.8e-5 here, well below 5e-4).
- E3b: ν_h ×10⁻⁴ weaker = 1e-26, dt=5e-4. Stability cone huge (dt bound
  ≈ 2.8e3); pure physics probe of "what if hyperviscosity were essentially
  removed".
- E3c: bug-fix rescue of E3a — ν_h=1e-18, dt=1e-5 (inside the strong-HV
  stability cone). Tests the actual physics effect of 10⁴× stronger HV.
- E3d: TRIVIAL-FINDING check the prompt explicitly anticipated — dt
  5e-4 → 1e-4 at baseline (Nx=256, ν_h=1e-22). Grounds the "dt is trivial
  at baseline" flag in data.

## Observations

| sub-run | (Nx, dt, ν_h)           | blew up?    | max |Δ%| vs E1 | dominant effect              |
|---------|-------------------------|-------------|-------------------|------------------------------|
| E3a     | (256, 5e-4, 1e-18)      | t=0.003     | n/a (NaN)         | explicit-HV stability        |
| E3b     | (256, 5e-4, 1e-26)      | stable      | 11.7 %            | small quantitative           |
| E3c     | (256, 1e-5, 1e-18)      | stable      | 277 %             | QUALITATIVE                  |
| E3d     | (256, 1e-4, 1e-22)      | stable      | 13.2 %            | mostly < 5 % (PARTIAL TRIV)  |

Detailed end-state shifts vs E1:

| diagnostic | E1     | E3b Δ% | E3c Δ%  | E3d Δ% |
|------------|-------:|-------:|--------:|-------:|
| m_l2_T     | 2.456  | +0.11  | **−51** |  +3.16 |
| m_inf_T    | 3.667  | −11.7  | **−76** |  −0.33 |
| lock_T     | 0.200  | +1.70  | **+277**|  −0.31 |
| L2_u_T     | 2.489  | +0.15  | **−50** |  +3.20 |
| L2_v_T     | 0.829  | +0.42  | −18.5   |  +3.06 |
| energy_T   | 3.547  | +0.47  | **−71** |  +6.61 |
| u_peak_T   | 3.670  | −11.7  | **−76** |  −0.37 |
| v_peak_T   | 0.545  | +1.40  | −39.3   |  +4.53 |
| eh_u_T     | 0.161  | −0.49  | −97     |  +13.2 |
| eh_v_T     | 9.6e-5 | +6.36  | −92     |  −0.35 |

## Interpretation

**E3b (ν_h weakened to 1e-26)** — at Nx=256, weakening hyperviscosity by
10⁴× barely changes the answer. Most diagnostics within ±2 %, the two that
shift more (m_inf and u_peak, both −11.7 %) reflect that without aggressive
HV the front sharpens slightly more (its peak grows). m_l2 shifts by only
0.11 %. Lock shifts by 1.7 %. Conclusion: at the spatial resolution Nx=256
the truncation IS the regularization — HV at 1e-22 contributes almost
nothing on top, so dropping it 10⁴× is effectively a no-op. This direction
is ROBUST.

**E3c (ν_h strengthened to 1e-18, rescued by dt=1e-5)** — strengthening HV
by 10⁴× DRASTICALLY changes the answer. Energy drops 71 %, m_l2 drops 51 %,
u_peak drops 76 %, eh_u drops 97 %, lock more than triples to 0.752
(strong positive lock, i.e. u and v²/2 become well-aligned). Strong HV is
not a "regularization" anymore — it is actively destroying high-k content
and re-shaping the basin attractor toward a smooth low-amplitude locked
state. This direction is QUALITATIVELY SENSITIVE. Any claim relying on
ν_h being "small enough to be numerical regularization only" must be
verified against this finding.

**E3a (ν_h strengthened, naive at dt=5e-4)** — blows up at step 6 from the
same explicit-RK4 hyperviscous stability mechanism as E2a (just at a
different (Nx, ν_h) corner). Re-confirms: in the pre-validated stack
(ν_h, Nx, dt) are tightly co-constrained. ν_h alone is INADMISSIBLE as a
one-parameter change in the strong-HV direction without rescaling dt.

**E3d (dt 5e-4 → 1e-4 at baseline)** — the trivial-flagged direction.
Result: max shift is +13.2 % (on eh_u, the only diagnostic > 5 %); most
diagnostics shift by 3-6 %. Energy: +6.6 %. m_l2: +3.2 %. Lock: −0.3 %.
So dt is the LEAST sensitive of the three parameters, but the prompt's
"trivial" framing was slightly too strong — dt=5e-4 is NEAR converged but
not fully converged for spectral-tail diagnostics. We classify F3d as
**partial-trivial / mostly-trivial**: the shift is small enough that no
qualitative conclusion changes, but a strict 5 % threshold is failed on
one diagnostic.

## Conclusion this round
Two clear and one nuanced sensitivity result at baseline (Nx=256):

- ν_h weaker than 1e-22: ROBUST (max 11.7 % shift, most diagnostics within
  2 %).
- ν_h stronger than 1e-22 (under bound rescaling): SENSITIVE (qualitative
  shift up to 277 % on lock, energy halved).
- dt finer than 5e-4: PARTIAL-TRIVIAL — mostly < 5 %, one diagnostic up to
  13 %, no qualitative shift. The prompt's anticipated "trivial" framing is
  vindicated for the bulk of diagnostics; eh_u is the partial-failure.

Decision: stop after 3 rounds (the program protocol limit). Synthesize.
