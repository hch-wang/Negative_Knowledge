# Class B Mechanism-Inquiry Judge: 8-cell Comprehensive Evaluation

You are evaluating 8 research outputs from a study on the coupled Burgers-swept-KdV (BKdV) PDE system. 2 mechanism-inquiry tasks (B1, B2) × 4 knowledge-bank conditions (NoKB / PosOnly / NegOnly / PosNeg) = 8 cells. Each cell ran 3 rounds of Research Graph protocol. Your job is to evaluate **correctness, rigor, and value** of each cell's hypothesis.md, then produce a **cross-condition meta-analysis** of what the experiment as a whole reveals.

# Task definitions

**B1**: Why does BKdV relax locally to a compound-soliton structure from generic ICs? What is the basin of attraction? How does it relate to the Gardner soliton (the m=0 algebraic reduction, where m = u − v²/2)?

**B2**: In bore-soliton interaction (smoothed Burgers bore on u + sech² soliton on v), what distinct outcome regimes exist? Where are the phase boundaries? Are transitions sharp or smooth?

# Independent physics "oracles" you may use as ground truth

These are established BKdV facts (algebraic or from converged independent stage-1 simulations):

1. **m=0 manifold algebraic identity**: m_t|_{m=0} = (v−1)(6 v v_x + v_xxx). Therefore m=0 is NOT a dynamically invariant set of BKdV — only an algebraic identity.

2. **BKdV-S7 quantitative breakdown**: For IC v = 1.5 sech²(x+5) + u = v²/2 (so m₀=0 exactly), full BKdV evolution over T=10 gives v_max decay -62.8% (1.498 → 0.558); ‖m‖_L₂ grows from 0 to 2.55; n_peaks 1 → 8; cos-similarity 0.94 between predicted vs observed spectral modes of m amplification.

3. **BKdV-S6 numerical fact**: For IC with bore-like u-gradient on u, the spectral+dealias+RK4 stack WITHOUT explicit u-viscosity produces Gibbs growth (u_max 1.5→3.4 over T=6, TV inflation 42×). Minimum viscosity for stability: ν_linear ≈ 1e-2, comfortable default ν = 5e-2.

4. **BKdV-S3 basin geometry**: Smooth-localized ICs (Gaussian, sech², multi-pulse) produce coherent compound structures; broadband ICs (white noise, sinusoidal) produce high-k cascade blow-up beyond 2/3 dealias band.

# Files to read

For each of the 8 cells `{B1, B2} × {NoKB, PosOnly, NegOnly, PosNeg}`:

- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/{task}/{cond}/hypothesis.md`
- `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/runs/{task}/{cond}/research_state.jsonl`

You may also Read evidence files if needed for spot checks, but the main deliverable is reading hypothesis.md (the agent's synthesis) + research_state.jsonl (the trace).

# Output format

Write a single Markdown file via Write tool to:
`/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2_v3/class_B/judge_report.md`

Structure the output as:

```
# Class B Judge Report — 8-cell Comprehensive Evaluation

## Per-cell evaluation (rubric below; 8 cells in 2 tables)

### B1 — Compound soliton mechanism

| Cell | Mech. quality (0-3) | Empirical rigor (0-3) | Substantive contrib (0-3) | Bank use quality (0-3) | Honest limitations (0-3) | Total /15 | Verdict |
|---|---|---|---|---|---|---|---|

[short 2-3 sentence justification per cell after the table]

### B2 — Bore-soliton phase diagram

[same structure]

## Cross-cell consistency check

For each task (B1, B2), do the 4 cells agree on the *qualitative* mechanism / phase structure? Where do they DISAGREE and is the disagreement methodological or substantive?

## Physics correctness check (oracle comparison)

For each cell, indicate whether its central claims:
1. Confirmed by the 4 oracle facts above (✓)
2. Contradicted by oracle (✗)
3. Beyond oracle — agent's own quantitative claim, judge as "plausible / overclaimed / suspicious"

## Bank value analysis

Comparing bank-aware (PosOnly, NegOnly, PosNeg) vs NoKB cells:
- Did bank entries help reach correct mechanism faster / more rigorously?
- Did the bank's deep entries (BKdV-S5, S6, S7) specifically anchor any findings?
- Was the bank misleading anywhere?

## Most valuable finding across all 8 cells

What single new physics insight emerged that was NOT in the prompt's physics anchoring?

## Concerns / overclaims to flag

Identify any cell that makes a claim its evidence doesn't support, or that is internally inconsistent.

## Recommendation for the paper

What story does this 8-cell run tell? What should the paper claim and what should it temper?
```

# Rubric definitions

- **Mechanism quality (0-3)**: 0 = vague/handwave, 1 = single hypothesis, 2 = multiple distinguishable hypotheses with discrimination plan, 3 = multiple hypotheses + rigorous discrimination + quantitative refinement
- **Empirical rigor (0-3)**: 0 = no ablation, 1 = single experiment, 2 = ≥1 ablation or convergence check, 3 = multiple ablations (numerical/physical/parameter) + clean ablation logic
- **Substantive contribution (0-3)**: 0 = trivial/wrong, 1 = re-states prompt, 2 = partial new insight, 3 = quantitatively novel finding that goes beyond prompt anchoring
- **Bank use quality (0-3)**: (skip for NoKB — give NA). 0 = ignored bank, 1 = citation theater, 2 = bank shaped one decision, 3 = bank entries quantitatively shaped multiple decisions with explicit rationale
- **Honest limitations (0-3)**: 0 = overclaims, 1 = brief mention, 2 = explicit limitations section, 3 = limitations + proposed falsification path

Be candid and specific. This is a research evaluation, not a participation award. Cells that ran cleanly but produced trivial findings should score lower than cells that produced rigorous negative results. Cells that overclaimed should be called out.
