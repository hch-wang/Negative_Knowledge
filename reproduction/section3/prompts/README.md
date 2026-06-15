# Curator prompt variants

The **canonical** curator prompt lives one level up, at
[`../curator_prompt.md`](../curator_prompt.md). It is the most general
form: read $N$ rounds of failed attempts and produce one structured NK
record with cross-round fields.

This directory holds two **documented modifications** of the canonical
template. Each filename names the modification it applies.

## Files in this directory

| File | Modification relative to canonical |
|---|---|
| `curator_prompt__single_round_simpler_schema.md` | restricts input to **1 round** of failure; drops the three cross-round output fields (`rounds_summary`, `ruled_out_routes`, `synthesised_diagnosis`), keeping only the base 6 fields |
| `curator_prompt__chain_with_prior_nk.md` | adds a **prior NK record** to the input alongside one failed round; adds a **`relationship_to_round1`** field to the output |

## Which variant feeds which paper claim

| Variant | Paper claim it produces |
|---|---|
| canonical (top-level) | §3 main result: depth-3 deepNKR Sonnet passes task_072 (1/19 on the hard subset) |
| single-round simpler schema | §3 NKR depth-1 condition (24 r1 NKs, used for round-2 NKR PASS rate 2/24) |
| chain with prior NK | §3 NKR depth-1 chain condition (22 r2 NKs, used for round-3 NKR PASS rate 3/24, and for the **9% NK error rate** finding via `round1_recipe_was_wrong`) |

## Why prompts are first-class

The Python module ([`nk_curator.py`](../nk_curator.py)) validates the
schema after the fact, but the curator agent's behavior — what it
reads, what it summarises, what it commits to — is determined entirely
by the prompt. The audit trail for every NK record is therefore:

1. Read the prompt — what was the curator told to produce?
2. Read the audit record — what input did the curator actually receive?
3. Read the NK record — what did the curator commit to?

A reviewer can verify any NK by tracing this 3-step path.

## Placeholders

Each template substitutes `{KEY}` placeholders at dispatch time:

| Placeholder | Set by | Used in |
|---|---|---|
| `{TASK_ID}` | curator caller | all templates |
| `{TASK_INST}` | curator caller | all templates |
| `{ROUND1_DIR}` | curator caller | canonical, single-round |
| `{ROUND2_DIR}`, `{ROUND3_DIR}` | curator caller | canonical |
| `{ROUND1_NK_PATH}` | curator caller | chain-with-prior-NK |
| `{OUTPUT_NK_PATH}` | curator caller | all templates |
| `{EVAL_LOG_STATUS}` | curator caller (auto-detected) | single-round, chain |
| `{ROUND2_EVAL_PRESENT}`, `{ROUND3_EVAL_PRESENT}` | curator caller (auto-detected) | canonical |

`nk_curator.py` fills these placeholders automatically; reviewers don't
need to manage them by hand.

## Customising the prompt

To run a curator with a modified prompt:

```python
import pathlib
from nk_curator import NKCurator

# Re-point at a custom base_dir (must contain curator_prompt.md
# at top level and prompts/{single_round, chain} variants underneath).
curator = NKCurator(
    model="claude-sonnet-4-5",
    base_dir=pathlib.Path("/path/to/your/custom/templates"),
)
```

Or override one specific template by editing the markdown in place —
the module reloads from disk on each dispatch.

## Versioning

If you change a prompt for an experiment, increment a version comment at
the top of the template (e.g., `<!-- v2 -->`). The curator audit record
captures the exact prompt content (including the version comment) via
SHA-256, so older NK records remain traceable to the prompt version that
produced them.
