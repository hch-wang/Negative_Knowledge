## Program research question
From which IC families does BKdV produce coherent (long-lived localized)
structures, and from which does it produce incoherent radiation? Is there a
phase boundary?

## Key findings
- **Finding 1 (E1):** At moderate v-amplitude A=0.8, IC families partition
  cleanly into (i) smooth-localized — single Gaussian, single sech²,
  two-pulse sech² — which keep one or two peaks with ~99% of energy at
  |k|≤2 and survive T=12 without blow-up; and (ii) broadband — Gaussian
  envelope * white noise, spatial cosine — which spawn an immediate high-k
  cascade beyond the dealiased band and blow up before T=10. The localized
  vs broadband distinction is the dominant separator. P2_twopulse passed
  the strict programme threshold (vmax≥0.5, npeaks≤3, fracL_v≥0.5);
  single G and S sat just inside the partial-coherent regime (vmax
  decayed to ~0.42-0.46).
- **Finding 2 (E2):** Within the sech² family there is NO amplitude
  threshold for coherence: at every sampled A ∈ [0.1, 1.2] the seed
  retains npeaks=1 and fracL_v ≥ 0.99 (radiation halves vmax but the
  structure persists). The strict (vmax≥0.5) threshold is just a
  measurement convention. Lock_corr between u and 0.5 v² is
  **non-monotonic with peak ≈ 0.79 at A ≈ 0.4** — indicating a
  coherent-compound sweet spot at intermediate amplitudes.
- **Finding 3 (E3):** Interpolating between localized and broadband by
  adding noise σ on top of a sech²(A=0.6) seed reveals a **soft phase
  boundary**, not a sharp threshold. The spectral fraction fracL_v slides
  smoothly from 0.999 (σ=0) to 0.545 (σ=0.80). lock_corr is robust up to
  σ≈0.20 then drops sharply by σ=0.60. Working estimate of the boundary:
  σ_c ≈ 0.30-0.40 by lock collapse, ≈ 0.60 by fracL_v dropping below 0.7.
  None of the σ values produced blow-up at this base amplitude, so the
  noise destroys coherence by radiation/spreading rather than by cascade
  to instability.

## Ruled-out routes / paths shown not to work
- **Hypothesis: there is a sharp amplitude threshold for coherence in
  sech² ICs.** Falsified in E2: structural coherence (one peak, ~99% low-k)
  is universal across A ∈ [0.1, 1.2]. The strict (vmax≥0.5) criterion is
  just a calibration of the absolute scale.
- **Hypothesis: the peak-count metric (`npeaks_v`) cleanly identifies
  coherence under noise.** Falsified in E3: as soon as σ > 0, npeaks_v
  jumps from 1 to ≥10 because of small ripples on the tail of the noise
  field, even when 99% of v's energy is still in the soliton core.
  Peak count is sensitive to *noise texture* but blind to *noise energy*.
  Downstream curators should use spectral fractions and lock_corr, not
  peak count, when noise is present in the IC.
- **Hypothesis: the phase boundary between coherent and incoherent
  regimes is a single sharp line.** Falsified in E3: the boundary is a
  soft margin spanning σ ∈ [0.2, 0.6]; different diagnostics put σ_c at
  different positions inside that window. The boundary's location depends
  on the diagnostic chosen.

## Trivial-finding flag
- None. Every Finding (F1, F2, F3) had `is_trivial: false`. The closest
  candidate for trivial would be E2's "structural coherence is universal
  for sech²" — but that fact is non-obvious (it is a real statement that
  the soliton basin extends down to A → 0 in npeaks/spectral terms, which
  is the *opposite* of what one might expect from KdV soliton-amplitude
  selection rules). It is therefore informative, not tautological.

## Recommendation for downstream Stage-2 tasks
Use multi-metric coherence labels (spectral fraction + lock_corr), not
peak count. Treat the boundary as a soft margin σ_c ≈ 0.3-0.4. Broadband
seeds (cosine, white noise) at A≥0.8 hit a separate, hard L2-budget
blow-up wall — keep them out of Stage-2 IC banks.
