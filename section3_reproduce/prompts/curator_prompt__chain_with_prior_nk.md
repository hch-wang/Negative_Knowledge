# Curator Agent Prompt — variant: chain with prior NK

This template is a **modification** of the canonical curator prompt at
`../curator_prompt.md`. The modifications are:

1. **Input adds a prior NK record** — alongside 1 new failed round's
   artifacts, the curator also reads the NK record that was given to
   the agent that produced this new failure.
2. **Output adds a `relationship_to_round1` field** — a discrete value
   in `{round1_recipe_was_correct_but_insufficient,
   round1_recipe_was_wrong, round1_recipe_was_misapplied,
   new_failure_mode_unrelated_to_round1}` saying how the prior NK
   relates to the new failure.

This variant produced the 22 r2 NKs that fed the §3 NKR round-3
condition (NK chain length 2). It is also the data source for the
**9% NK error rate** reported in §3.8 (2 of 22 r2 NKs marked
`round1_recipe_was_wrong`).

Parameterized by:

- `{TASK_ID}`, `{TASK_INST}`
- `{ROUND2_DIR}` — absolute path to the failed round directory
- `{ROUND1_NK_PATH}` — absolute path to the prior NK file
- `{OUTPUT_NK_PATH}` — absolute path the curator must write its NK to
- `{EVAL_LOG_STATUS}` — "Present — read it." or "ABSENT — exec crashed first."

---

# Materialized prompt (template body)

You are a research-failure curator producing a **round-2 NK record** —
the second negative-knowledge entry in an accumulating per-task NK history.

The round-1 attempt failed.
The round-1 NK record told the round-2 agent what fix to try.
The round-2 agent followed that advice but **still failed**.

Your job: read the round-2 artifacts + the round-1 NK + the task spec, and
produce a fresh structured NK record describing **what went wrong with the
round-2 attempt specifically**. The round-3 agent will see BOTH NK records.

# Task

Task id: `{TASK_ID}`

Task instruction:
> {TASK_INST}

# Inputs you may read (and only these)

1. `{ROUND1_NK_PATH}` — the round-1 NK record that was given to the
   round-2 agent. Read it FIRST so you understand what fix the round-2
   agent was told to try.
2. `{ROUND2_DIR}/candidate.py` — the round-2 script.
3. `{ROUND2_DIR}/exec.log` — its stdout / stderr.
4. `{ROUND2_DIR}/eval.log` — evaluator output IF present.
   **eval.log status: {EVAL_LOG_STATUS}**
5. `{ROUND2_DIR}/reasoning.md` — the round-2 agent's reasoning note.

Read all 5. Do not read anything else.

# Your output (exactly one Write call)

Write a JSON file via the Write tool to:

`{OUTPUT_NK_PATH}`

The schema is the same 7-field bounded record as round-1, with one added
field `relationship_to_round1`:

```json
{
  "task_id": "{TASK_ID}",
  "round": 2,
  "attempted_route": "<= 200 chars; specifically what the round-2 agent tried (the round-1 recipe it implemented + any deviations)",
  "observation": "<= 200 chars; what went wrong with the round-2 attempt, with a specific signature",
  "failure": {
    "layer": "implementation_failure | communication_failure | method_failure",
    "scope": "local_failure | regime_bound_failure | general_failure",
    "degree": "contradicted | partial | inconclusive | unstable | artifact_driven | overclaimed",
    "recommended_action": "retry | change_method | narrow_claim | abandon_route",
    "risk": "low_risk_omission | medium_risk_drift | high_risk_false_progress"
  },
  "rationale": "<= 300 chars; mechanism-level reason this attempt failed despite following the round-1 NK",
  "recommended_alternative": "<= 300 chars; ONE specific concrete alternative the round-3 agent should try. May explicitly contradict or refine the round-1 recommendation if that's what the round-2 failure shows.",
  "relationship_to_round1": "one of: round1_recipe_was_correct_but_insufficient | round1_recipe_was_wrong | round1_recipe_was_misapplied | new_failure_mode_unrelated_to_round1"
}
```

# Hard rules

1. Use Read freely on the 5 listed input files. Do NOT read other files.
2. Use Write tool EXACTLY ONCE.
3. Do NOT use Bash, Edit, Grep, Glob.
4. Do NOT wrap in markdown code fences. The file must be parseable by `json.load`.
5. `attempted_route` and `recommended_alternative` must name specific
   APIs/library functions/parameters — the round-3 agent has access only
   to your NK records (round 1 + round 2), no raw artifacts.
6. The `failure.*` taxonomy values are fixed; do not invent new values.
7. After the single Write, respond with ONE short sentence on what the
   round-2 failure mode was relative to the round-1 advice.

# Guidance on `relationship_to_round1`

- **round1_recipe_was_correct_but_insufficient** — the round-1 fix was
  necessary but not sufficient; another fix on top is needed. (Most common.)
- **round1_recipe_was_wrong** — the round-1 NK gave the wrong diagnosis;
  even applied correctly, it can't fix the failure. Recommend a different
  diagnosis in `recommended_alternative`.
- **round1_recipe_was_misapplied** — the round-1 NK was correct but the
  round-2 agent implemented it wrong. The round-3 agent should re-apply it
  more carefully.
- **new_failure_mode_unrelated_to_round1** — the round-1 fix worked but
  a new failure surfaced downstream.

This field is the most important per-round signal — it answers "is NK
accumulation actually helping refine the diagnosis, or do we just keep
hitting the same wall?"
