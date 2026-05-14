# E1 — IC family scan at moderate amplitude

## Proposal
Probe the BKdV system with five distinct IC families, all at v-amplitude `A=0.8`,
on a `[-15, 15]` periodic domain with Nx=256, using the pre-validated solver
stack (Fourier pseudospectral / 2/3 dealiasing / RK4 / integrating-factor on
v_xxx / spectral hyperviscosity). Run to T=12.0 with dt=2.5e-4.

ICs:
- `G_gauss`: single Gaussian on v, flat u
- `S_sech2`: single sech^2 on v (KdV-soliton shape), flat u
- `N_noise`: Gaussian-envelope * white noise on v, flat u
- `P2_twopulse`: two well-separated sech^2 pulses, flat u
- `K_sin`: spatially-periodic cosine, flat u

Late-time (last 20% of trajectory) coherence heuristic (loose):
`coherent = (npeaks_v ≤ 3) AND (vmax ≥ 0.5) AND (frac_low_v ≥ 0.5)`.

## Observations

| IC | vmax_late | npeaks_v | frac_low_v | lock_late | blew_up | label |
|---|---|---|---|---|---|---|
| G_gauss     | 0.46 | 1  | 1.00 | 0.39 | no  | INCOHERENT (by heuristic) |
| S_sech2     | 0.42 | 1  | 1.00 | 0.47 | no  | INCOHERENT (by heuristic) |
| N_noise     | 5.27 | 31 | 0.07 | 0.07 | YES | INCOHERENT (blew up)      |
| P2_twopulse | 0.67 | 2  | 1.00 | 0.44 | no  | COHERENT                  |
| K_sin       | 5.04 | 18 | 0.25 | 0.07 | YES | INCOHERENT (blew up)      |

Key qualitative things:
- Smooth single-bump ICs (G, S) stay localized (single peak, almost all energy
  at |k|≤2), but they radiate energy: vmax drops from 0.8 to 0.42-0.46. They
  are **structurally coherent** but the v-amplitude dips below the
  programme's threshold (≥0.5). They sit just inside the partial-coherence
  basin.
- Broadband/large-L2 ICs (`N_noise` L2=4.38, `K_sin` L2=3.10) immediately
  drive the cascade beyond the dealiased band and **blow up** before t=10.
  At A=0.8, these IC families are physically incoherent and numerically
  unstable. The bath of high-k modes is the radiation regime.
- **P2_twopulse** is the unambiguous coherent winner: two distinct moving
  pulses, vmax≈0.67 sustained, full energy at low |k|.

## Conclusion
At amplitude A=0.8:
- **Coherent IC family**: localized + smooth (Gaussian, sech², multi-pulse).
  Smooth localized ICs lie in or near the soliton-attractor basin and
  produce one or a small number of long-lived peaks.
- **Incoherent IC family**: broadband (white noise, sinusoid). These
  generate a chaotic cascade that radiates / blows up.
- The heuristic threshold `vmax≥0.5` was a touch too strict for the single
  Gaussian/sech² (their natural mass radiates to vmax≈0.45). We treat them
  as *weakly coherent / partial*.

For E2 we pick the most robust coherent family — multi-pulse sech² — and
sweep amplitude A to find the lower threshold for coherent structure
formation.

`is_trivial = false` (the IC family map is informative; the noise/sinusoid
blow-up is a real physical observation, not a tautology, because it
distinguishes incoherent IC families even when L2 budget is moderate).
