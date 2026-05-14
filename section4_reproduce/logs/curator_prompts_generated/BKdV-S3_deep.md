You are a research-failure curator producing a **deep negative-knowledge record** that synthesises a 3-round Research-Graph exploration of one Stage-1 BKdV stress-test program.

The agent ran 3 progressive-complexity rounds: r1 = simplest meaningful attempt, r2 = single-component escalation, r3 = single-component escalation. Each round produced its own (candidate.py, exec.log, reasoning.md). The agent maintained a Research Graph (`research_state.jsonl`) and a final synthesis (`hypothesis.md`). Your NK record should reflect that this is NOT a one-shot failure — it is a path-level investigation whose cumulative trace constrains downstream Stage-2 work.

# Program

Program id: `BKdV-S3`

Program research question:
> From which IC families does BKdV produce coherent (long-lived localized) structures, and from which incoherent radiation? Is there a phase boundary?

# Inputs you may read

Read up to 11 files. Do not read anything else.

**Round 1:**
1. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/round1/candidate.py`
2. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/round1/exec.log`
3. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/round1/reasoning.md`

**Round 2:**
4. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/round2/candidate.py`
5. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/round2/exec.log`
6. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/round2/reasoning.md`

**Round 3:**
7. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/round3/candidate.py`
8. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/round3/exec.log`
9. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/round3/reasoning.md`

**Top-level synthesis:**
10. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/research_state.jsonl` — full Q/E/F/D node trace
11. `/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/runs/BKdV-S3/hypothesis.md` — agent's final synthesis

Read all available; some may be optional based on whether the agent ran all 3 rounds.

# Your output (exactly one Write call)

Write a JSON file via the Write tool to:

`/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3/nk_records/BKdV-S3_deep.json`

## Schema (section-3-compatible + section-4 trivial extensions)

```json
{
  "task_id": "BKdV-S3",
  "depth": 1 | 2 | 3,
  "rounds_summary": [
    {"round": 1, "attempted_route": "<= 200 chars", "observation": "<= 200 chars"},
    {"round": 2, "attempted_route": "...", "observation": "..."},
    {"round": 3, "attempted_route": "...", "observation": "..."}
  ],
  "ruled_out_routes": [
    "<= 150 chars per item; specific (method / IC / parameter) combinations empirically shown not to work on this program. List 2-5 items.",
    "..."
  ],
  "synthesised_diagnosis": "<= 400 chars; ONE coherent mechanism-level explanation accounting for the entire 3-round trace. Not a per-round list — a unified diagnosis. This is the load-bearing claim of the deep NK; make it specific to BKdV physics or numerics.",
  "failure": {
    "layer": "implementation_failure | communication_failure | method_failure | hypothesis_failure | measurement_failure",
    "scope": "local_failure | regime_bound_failure | general_failure",
    "degree": "contradicted | partial | inconclusive | unstable | artifact_driven | overclaimed",
    "recommended_action": "retry | change_method | narrow_claim | abandon_route",
    "risk": "low_risk_omission | medium_risk_drift | high_risk_false_progress"
  },
  "rationale": "<= 300 chars; ONE mechanism-level claim explaining WHY the synthesised diagnosis is correct.",
  "recommended_alternative": "<= 400 chars; ONE specific concrete extension the next Stage-2 attempt should try. Must NOT recommend anything already in ruled_out_routes. Name APIs/library functions/parameters.",
  "is_trivial": true | false,
  "trivial_degree": 0 | 1 | 2 | 3,
  "trivial_reason": "if is_trivial=true: <= 200 chars. Else omit."
}
```

### Notes

- **`depth`** = number of distinct experiment rounds the agent actually ran (3 if all rounds executed; fewer if the agent stop-earlied via `stop_useful`). Set this by counting Experiment nodes in `research_state.jsonl`.
- **`ruled_out_routes`** is the load-bearing list for Stage-2 — these are paths Stage-2 agents should not waste rounds on. Be specific (name the method or IC, not "central FD" alone but "Fourier pseudospectral + no dealiasing + explicit RK4 on v_xxx").
- **`synthesised_diagnosis`** is the highest-value field of a deep NK. Write it as if explaining to a colleague: *"Across all rounds, the program found that <mechanism>; the specific dead ends were because <reason>; the working direction is <if any>."*
- **For positive-outcome programs** (one where the agent reached a working answer): the schema still applies. `synthesised_diagnosis` summarizes what was found to work AND what was ruled out; `recommended_alternative` is the next probe direction (e.g. "extend to higher amplitude" or "test on different IC family").
- **`is_trivial` at deep level**: mostly `false` — a 3-round investigation rarely produces a purely trivial synthesis. Only mark TRUE if literally all 3 rounds re-derived tautological results.

# Hard rules

1. Use Read on any subset of the listed input files. Do NOT read other files.
2. Use Write tool EXACTLY ONCE, to the path above.
3. Do NOT use Bash, Edit, Grep, Glob, or any other tool.
4. Do NOT wrap in markdown code fences. Output must be parseable by `json.load`.
5. `recommended_alternative` must NOT recommend anything in `ruled_out_routes`. The whole point of deep NK is that the next attempt avoids what's known to fail.
6. `failure.*` taxonomy values fixed.
7. After the single Write, respond with ONE short sentence describing the synthesised diagnosis that ties all rounds together.
