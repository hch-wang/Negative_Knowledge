# BKdV-S3 session log

- **Round 1 (E1) — IC family scan @ A=0.8.** 5 ICs (G_gauss, S_sech2,
  N_noise, P2_twopulse, K_sin). Result: smooth-localized ICs (G, S, P2)
  stay coherent (npeaks ≤ 2, fracL_v ≥ 0.996); broadband ICs (N_noise,
  K_sin) blow up by t < 10. P2 passes strict heuristic. F1 informative,
  `is_trivial=false`.
- **Round 2 (E2) — Amplitude sweep on sech² (single coherent family).**
  A ∈ {0.1, …, 1.2}, T=12. Result: structural coherence universal at all
  A (npeaks=1, fracL_v ≥ 0.99). Strict vmax≥0.5 only met for A ≥ 1.0
  (convention, not physics). Lock_corr peaks at A ≈ 0.4 (lock ≈ 0.79),
  indicating a coherent-compound sweet spot at intermediate amplitudes.
  No amplitude threshold for coherence inside the localized family.
  F2 partial, `is_trivial=false`.
- **Round 3 (E3) — Noise-level σ sweep on sech²(A=0.6) seed.**
  σ ∈ {0.00, …, 0.80}, T=12. Result: SOFT phase boundary. fracL_v slides
  monotonically 0.999 → 0.545; lock_corr robust to σ ≈ 0.20 then drops by
  σ=0.60. σ_c ≈ 0.30-0.40 (lock criterion) / ≈ 0.60 (fracL criterion).
  None blew up. Also: peak-count metric is artifact-sensitive
  (jumps from 1 → 10+ at any σ>0), so it is not a reliable coherence
  indicator under noisy ICs — a useful negative finding for the curator.
  F3 partial, `is_trivial=false`.
- **Decision D3:** stop_useful. Programme complete with 3 rounds, 1
  partial-positive (E1), 2 partial (E2, E3), 0 trivial flags.
