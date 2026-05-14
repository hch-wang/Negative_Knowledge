# BKdV-S2 session log

- Round 1 (E1): Long-time baseline T=20 with v0=1.5 sech²(x+5), u0=0 using pre-validated stack (Fourier + 2/3 dealias + IMEX-CN on -v_xxx + midpoint RK2). Tracked all 5 candidate functionals. Found C1, C2 conserved to ~1e-15; C3 drifts and oscillates; C4 grows 119%; C5 grows 724%. C1 conservation is ambiguous because u0=0 — need IC change in r2.

- Round 2 (E2): Single-component escalation — changed ONLY the IC to a smooth multi-mode periodic state with nonzero means (mean_u=0.15, mean_v=0.10). Confirmed C1=4.5 conserved to 1.6e-14 (structural, not zero-stuck). C2 still conserved. C3, C4, C5 all drift even more (C4 grows 16×, C5 grows 34×). The proposed C4 "kinetic-like energy" is structurally not the BKdV invariant — confirmed by hand-IBP showing a non-vanishing cubic remainder.

- Round 3 (E3): Numerical artifact control — three configs (dt=5e-4/N=256, dt=1e-4/N=256, dt=2.5e-4/N=512), same E1 IC, T=5. dt-only comparison (A vs B at fixed Nx=256) gives drift ratios of 1.002, 0.992, 0.996 for C3, C4, C5 → inferred numerical order p≈0, i.e. drift is dt-invariant and therefore physical. C1, C2 stay at FFT round-off across all configs. Verdict locked: 2 trivial structural conservations + 3 physical non-conservations + 0 hits on the "near-conserved slowly drifting" category.

- Decision D3: stop_useful. Candidate set exhausted; results written to research_state.jsonl and hypothesis.md.
