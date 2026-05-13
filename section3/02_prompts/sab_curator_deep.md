# Curator Agent Prompt — DEEP NK (3-round Self-Debug distillation)

This is the prompt template for the **deep curator** sub-agent. The deep
curator reads the full 3-round Self-Debug exploration artifacts on ONE task
(round 1 + round 2 covering-memory + round 3 covering-memory, all of which
failed) and writes a single synthesised NK record that captures the entire
3-round investigation.

The contrast with the round-1 curator (`sab_curator.md`):

| | round-1 curator | deep curator (this file) |
|---|---|---|
| Inputs | 1 attempt's artifacts | 3 attempts' artifacts (covering Self-Debug) |
| NK depth | snapshot of 1 failure | distillation of 3 successive failures |
| Schema | base 7 fields | base 7 fields + `ruled_out_routes` + `synthesised_diagnosis` |

Parameterised by:
- `{TASK_ID}`, `{TASK_INST}`
- `{ROUND1_DIR}`, `{ROUND2_DIR}`, `{ROUND3_DIR}` — absolute paths to
  the three B2 (Self-Debug) round directories
- `{OUTPUT_NK_PATH}` — absolute path the curator must write its deep NK to
- `{ROUND2_EVAL_PRESENT}`, `{ROUND3_EVAL_PRESENT}` — "yes" / "no"

---

# Materialized prompt (template body)

You are a research-failure curator producing a **deep negative-knowledge
record** that summarises a 3-round Self-Debug exploration of one
ScienceAgentBench task. All three rounds failed.

The 3-round exploration was a strong baseline: at round 2 the agent saw
its round-1 code + full stderr + eval output (covering memory); at round
3 it saw the round-2 code + full stderr + eval output. Despite this, all
three attempts failed. Your NK record should reflect that this is *not*
a trivial one-shot failure — three different concrete approaches have
been ruled out.

# Task

Task id: `{TASK_ID}`

Task instruction:
> {TASK_INST}

# Inputs you may read (and only these)

You will read up to 11 files. Do not read anything else.

**Round 1 (no memory, free attempt):**
1. `{ROUND1_DIR}/candidate.py` — round-1 script
2. `{ROUND1_DIR}/exec.log` — stdout / stderr / runtime errors
3. `{ROUND1_DIR}/eval.log` — evaluator output IF it ran
4. `{ROUND1_DIR}/reasoning.md` — round-1 agent's reasoning

**Round 2 (Self-Debug covering memory of round 1):**
5. `{ROUND2_DIR}/candidate.py`
6. `{ROUND2_DIR}/exec.log`
7. `{ROUND2_DIR}/eval.log` — eval.log status for round 2: {ROUND2_EVAL_PRESENT}
8. `{ROUND2_DIR}/reasoning.md`

**Round 3 (Self-Debug covering memory of round 2):**
9. `{ROUND3_DIR}/candidate.py`
10. `{ROUND3_DIR}/exec.log`
11. `{ROUND3_DIR}/eval.log` — eval.log status for round 3: {ROUND3_EVAL_PRESENT}
12. `{ROUND3_DIR}/reasoning.md`

Read all available files before writing.

# Your output (exactly one Write call)

Write a JSON file via the Write tool to:

`{OUTPUT_NK_PATH}`

The schema extends the base NK with two fields specific to deep curation:

```json
{
  "task_id": "{TASK_ID}",
  "depth": 3,
  "rounds_summary": [
    {
      "round": 1,
      "attempted_route": "<= 200 chars; what method/library/parameter was tried",
      "observation":     "<= 200 chars; specific failure signature"
    },
    {"round": 2, "attempted_route": "...", "observation": "..."},
    {"round": 3, "attempted_route": "...", "observation": "..."}
  ],
  "ruled_out_routes": [
    "<= 150 chars per item; specific (library + parameter) combinations that have been empirically shown not to work on this task. List 2-4 items.",
    "..."
  ],
  "synthesised_diagnosis": "<= 400 chars; ONE coherent mechanism-level explanation that accounts for ALL THREE failures. Not a per-round list; a unified diagnosis. This is the load-bearing claim of the deep NK — make it specific.",
  "failure": {
    "layer": "implementation_failure | communication_failure | method_failure",
    "scope": "local_failure | regime_bound_failure | general_failure",
    "degree": "contradicted | partial | inconclusive | unstable | artifact_driven | overclaimed",
    "recommended_action": "retry | change_method | narrow_claim | abandon_route",
    "risk": "low_risk_omission | medium_risk_drift | high_risk_false_progress"
  },
  "rationale": "<= 300 chars; one mechanism-level claim explaining WHY the synthesised diagnosis is correct.",
  "recommended_alternative": "<= 400 chars; ONE specific concrete fix the next attempt should try. Must NOT be a method already in ruled_out_routes. Must name specific APIs/library functions/parameters."
}
```

# Hard rules

1. Use Read on any subset of the listed input files. Do NOT read other files.
2. Use Write tool EXACTLY ONCE, to `{OUTPUT_NK_PATH}`, with the JSON object.
3. Do NOT use Bash, Edit, Grep, Glob, or any other tool.
4. Do NOT wrap in markdown code fences. The file must be parseable by `json.load`.
5. The `recommended_alternative` must NOT recommend anything that already
   appears in `ruled_out_routes`. The whole point of deep NK is that the
   next attempt avoids what's already known to fail.
6. The `failure.*` taxonomy values are fixed; do not invent new values.
7. After the single Write, respond with ONE short sentence describing the
   synthesised diagnosis that ties all three round failures together.

# Guidance

The `synthesised_diagnosis` field is the highest-value piece of a deep NK.
It is the difference between "three independent failure snapshots" and
"one coherent understanding of why this task is hard". Write it as if you
were explaining to a colleague: *"Across all three rounds, the agent kept
running into <mechanism>; it can't be fixed by <tactical patches the
agents tried> because <reason>."* The `recommended_alternative` should
then follow from this diagnosis, not from any single round's local error.

If the three rounds revealed unrelated bugs (i.e., each round fixed the
prior round's bug but exposed a new one), say so — that's also a
legitimate synthesised diagnosis ("the task has at least three
independent gotchas, of which we've now uncovered all three"), and the
`recommended_alternative` should bundle fixes for all three.
