# Architecture

`negative_knowledge.py` is a single-file, stateless, data-oriented
module (stdlib only). The shape is *functional core / imperative shell*
with exactly one dependency-injection point at the LLM boundary. It is a
library, not a framework: it never takes over your agent loop, and the
only state it owns is the JSONL bank on disk.

## Layers (top of file to bottom)

| Layer | What lives there | Discipline |
|---|---|---|
| **Contract** | `LAYERS` / `SCOPES` / `DEGREES` / `ACTIONS` / `RISKS`, `FIELDS`, `_PROMPT` | Module-level constants are the single source of truth for the schema. `_PROMPT` must advertise exactly the vocabularies and limits `validate()` enforces (guarded by a test). |
| **Pure core** | `validate(record) -> list[str]` | No IO, no side effects. The one judge of what a record is. |
| **Port** | `curate(backend, *, task_id, task, evidence)` | The LLM is injected as `backend: Callable[[str], str | Mapping]`. The module never imports a model SDK — your client is the adapter. |
| **IO shell** | `append(path, record)` / `load(path)` | The only place that touches the filesystem. Append-only JSONL, one record per line; no locks, no database, no sessions. |

## Data flow

```
failure artifacts ──curate(backend)──▶ dict record ──validate──▶ append() ──▶ bank.jsonl
                                                                                   │
      next agent's prompt ◀── (caller selects / formats) ◀── load() ◀──────────────┘
```

Records are plain dicts / JSON end to end — deliberately not classes —
so they stay serializable, language-neutral, and copy-pasteable.

## Deliberate non-goals

No stateful objects, no retrieval or ranking, no database, no async, no
plugin system, no third-party dependencies. Relevance selection belongs
to the caller (or to the reading agent itself); this module only owns
the data shape and its persistence round-trip.

## Where new things land

- Formatting/selection helpers → pure core, next to `validate()`.
- Error types → value types only (exception classes carrying no state).
- Anything provider-specific → outside this file, behind the `backend`
  callable or the `NK_AGENT_COMMAND` bridge.

A second port with the same philosophy lives in
[`reproduction/agent_command.py`](../reproduction/agent_command.py):
fresh reproduction runs inject an agent runner as an executable speaking
a JSON-over-stdin/stdout protocol (`NK_AGENT_COMMAND`), keeping the
harness provider-neutral too.
