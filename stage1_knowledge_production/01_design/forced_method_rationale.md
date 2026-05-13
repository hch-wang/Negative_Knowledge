# Why force agents to use basic methods?

Sub-agents asked "solve a PDE" naturally choose advanced methods (TVD-Godunov, IMEX-spectral). That produces only positive ✓ knowledge.

To populate negative ✗ knowledge, we explicitly forbid advanced methods in prompts. The 14 stress tests are designed so that:

- 6 of them (A1, A4, A5, A7, A8, G1, G3) force **methods known to be inappropriate** for the PDE in question → produces negative entries about what fails and why
- 4 of them (A2, A3, A6, G4) force **edge-case parameter regimes** → produces negative entries about parameter-regime failures
- 4 of them (A8, A10, G2, G4) allow **good methods** but at boundary regimes → some positive, some negative

The full forced constraints per test are in each `<id>/meta.json`.

Without these forced constraints, Stage 1 would produce ~10 positive entries and zero negative entries — and the Stage 2 PosNeg condition would degenerate into PosOnly.
