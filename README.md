# Negative Knowledge

Code, prompts, and reproducibility artifacts for the paper:

> **Negative Knowledge as Failure-aware shared memory for AutoResearch**
> ICML 2026 AI4Research Workshop.

A *negative-knowledge record* (NK) is a structured, machine-readable
summary of one or more failed attempts on a task. This repository
contains the schema, the prompt-driven curator that produces NK
records, the Python module that wraps it, and two end-to-end
reproducibility packages — one per paper section.

---

## Six key components of the negative-knowledge framework

Every artifact in this repo is one of these six pieces. Reading them
in this order is the fastest way to understand the codebase.

### 1. The bounded failure schema

The NK record is a JSON object with a fixed shape. Every field draws
from a controlled vocabulary; no field is free text in a way that
would defeat downstream machine consumption. The base form has 6
required fields:

```
task_id, attempted_route, observation,
failure { layer, scope, degree, recommended_action, risk },
rationale, recommended_alternative
```

A **depth-N** extension adds three cross-round fields
(`rounds_summary`, `ruled_out_routes`, `synthesised_diagnosis`)
when the curator reads more than one failed round.

Schema is implemented in
[`section3_reproduce/nk_curator.py`](section3_reproduce/nk_curator.py)
(constants `SCHEMA_BASE_FIELDS`, `SCHEMA_DEEP_EXTRA`, `LAYERS`, …),
with `validate_nk(nk, depth)` returning a list of violations.

### 2. The curator (producer mechanism)

A *curator* is a sub-agent restricted to two tools — `Read` (on a
fixed allowlist of failure artifacts) and `Write` (exactly once, to
a designated NK output path). It does not run code, does not retry
the task, does not see anything outside its allowlist. Its sole job
is `raw failure trace → structured NK JSON`.

Curator behavior is determined entirely by the prompt sent to it.
Three prompt variants live in the repo (see component 3).

### 3. The curator prompts (operational definition of the schema)

The schema is enforced not just by the post-hoc validator but by
what the curator is asked to produce. The canonical prompt and its
two documented modifications are:

| Template | Location | What it produces |
|---|---|---|
| **canonical** | [`section3_reproduce/curator_prompt.md`](section3_reproduce/curator_prompt.md) | depth-N NK from N rounds of failed attempts |
| single-round simpler schema | [`section3_reproduce/prompts/curator_prompt__single_round_simpler_schema.md`](section3_reproduce/prompts/curator_prompt__single_round_simpler_schema.md) | depth-1 NK from one round |
| chain with prior NK | [`section3_reproduce/prompts/curator_prompt__chain_with_prior_nk.md`](section3_reproduce/prompts/curator_prompt__chain_with_prior_nk.md) | depth-1 NK that also reads a prior NK, adds a `relationship_to_round1` field |

Variant filenames name the modification applied to the canonical
template. Reviewers can read the canonical to see the schema
contract; the variants are explicit deltas.

### 4. NKCurator — programmatic API

The Python module
[`section3_reproduce/nk_curator.py`](section3_reproduce/nk_curator.py)
exposes `NKCurator.produce_depth1(...)` and `produce_deep(...)`. It
loads the right prompt template, materialises placeholders, sends the
prompt to the Anthropic API via a tool-use loop (`Read` and `Write`
only), captures token usage and runtime metadata, and validates the
resulting JSON against the schema before returning. This is the
single entry point downstream code uses to produce NK records.

### 5. The audit trail

Every NK record produced in our experiments has a paired audit JSON
that captures:

- the exact prompt sent to the curator (full content + sha256);
- every file the curator was allowed to read (full content + sha256
  + byte count);
- the curator's final return message + token usage + tool-use count
  + UTC dispatch and completion timestamps;
- the NK record itself (full content + sha256 + parse status).

Audit records make every paper claim traceable: prompt → audit
record → NK record → downstream consumer. They are bundled with the
reproduction packages.

### 6. End-to-end reproduction packages

Two directories carry self-contained reviewer kits, one per paper
section:

- **[`section3_reproduce/`](section3_reproduce/)** — within-task NK
  validation on ScienceAgentBench. Bundles the curator module, the
  three prompts, 65 NK records, 65 audit records, 220 solver dispatch
  records, 38 task specs, and an `analyze_results.py` script that
  re-derives every §3 paper claim from the bundled archive in 5
  seconds with no API key needed.

- **[`section4_reproduce/`](section4_reproduce/)** — PDE-case-study
  Stage 1 + Stage 2 snapshot for §4 (Burgers-swept-KdV coupled
  system; AutoResearch loop with 4 memory conditions × 3 sub-tasks).

Each reproduction package has its own `README.md` documenting
verification mode (no API key) and end-to-end mode (Anthropic API
required).

---

## Repository layout

```
Negative_Knowledge/
├── README.md                    this file
├── section3_reproduce/          §3 reviewer kit (within-task NK)
├── section4_reproduce/          §4 reviewer kit (PDE case study)
└── section4/                    §4 full working directory (Stage 1-3 + variants)
```

The `section4/` working directory is preserved alongside the
reviewer-facing `section4_reproduce/` because §4 still has multiple
in-flight stage variants. The internal §3 working dir (with the
original Claude Code Agent-tool dispatch transcripts) is not in this
repo; the reviewer-facing [`section3_reproduce/`](section3_reproduce/)
is the canonical §3 deliverable.

## How to reproduce

Section-specific reproduction guides:

- [`section3_reproduce/README.md`](section3_reproduce/README.md) —
  §3 verification (no API) + single-task end-to-end (~$1)
- [`section4_reproduce/README.md`](section4_reproduce/README.md) —
  §4 PDE case study reproduction

The fastest verification, requiring only Python ≥ 3.10:

```bash
cd section3_reproduce
python analyze_results.py
# expected: 31/31 claims match
```

## Citation

```bibtex
@inproceedings{NegativeKnowledge2026,
  title  = {Negative Knowledge as Failure-aware shared memory for AutoResearch},
  author = {...},
  booktitle = {ICML 2026 AI4Research Workshop},
  year   = {2026},
}
```

ScienceAgentBench: Chen et al., 2024
(https://github.com/OSU-NLP-Group/ScienceAgentBench).
