# Session log: B1 / NoKB

- R0 (setup): Read prompt + meta. Defined 5 candidate hypotheses (H_A Gardner-template,
  H_B Burgers shock fixed-point, H_C dissipative cleanup, H_D (v-1) sign-flip, H_E
  viscosity artifact). Two more emerged from data: H_F (v-pulse + trailing u-wake) and
  H_G (sub-Gardner speed). Smoke-tested solver (smoke.py, T=2). Code uses Fourier
  pseudospectral + 2/3-dealiasing + RK4 + dt=1e-4 + ν_u=5e-2.

- R1 / E1: Single Gaussian IC A=1.5, σ=1.2, u=v²/2 (m≡0 at t=0), T=20, ν=5e-2.
  Result: m at peak grows to +1.0 then stabilises +0.1 to +0.5; ratio u/(v²/2)|_peak ≈ 2-9;
  u-peak shifted right of v-peak by Δx growing 0.2→1.0; speed ≈1 (vs Gardner ≈3).
  Findings F1: simplistic "u≈v²/2 inside support" claim falsified at high amplitude.
  Decision D1: discriminate H_D vs H_F by varying amplitude (low + sech²).

- R2 / E2: Three runs T=10 in parallel — LO (Gauss A=0.6), HI (Gauss A=1.5), GARDNER_LO
  (sech² A=0.6). All u=v²/2 at t=0. Result: ALL THREE show m_peak grow positive (+0.5 at
  t=10 for LO and GARDNER_LO; +0.15 for HI). The u-wake offset Δx grows in all three.
  (v-1) factor alone does NOT make m=0 attractive — F2 falsifies H_D as a quantitative
  mechanism. The compound state is universally a (v-pulse + u-wake) pair, IC-shape
  independent. Decision D2: viscosity ablation + speed comparison + multipulse basin.

- R3 / E3: Four runs T=8 — LO ν=5e-2, LO ν=0, HI ν=5e-2, multipulse ν=5e-2. Results:
  (a) ν ablation: ν=0 case keeps growing u-peak (1.59) without any m→0 effect; same
  qualitative compound forms. H_E falsified. (b) Speed: measured/Gardner = 0.30-0.53
  across all four runs. H_A falsified, H_G supported. (c) Basin: sign-mixed multipulse
  also relaxes to a single-compound state (positive lobe forms v-peak; negative disperses).
  F3 closes the inquiry: H_F + H_G is the best mechanism, with the compound being a
  bound (v-pulse + trailing u-shock-wake) NOT a Gardner soliton.

- Wrap-up: hypothesis.md (best hypothesis = H_F + H_G; H_A, H_B, H_D, H_E falsified by
  numerical evidence); research_state.jsonl with Q1, H_set, E1/F1/D1, E2/F2/D2, E3/F3/D3;
  candidate.py = E3 code; evidence/{E1,E2,E3}/ saved.
