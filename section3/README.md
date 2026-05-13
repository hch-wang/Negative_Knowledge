# Section 3 — Reproducibility status & run guide

This directory holds the prompts, scripts, NK records, and audit
records behind \cref{sec:evaluation} of the paper.

## Reproducibility status (as of 2026-05-13)

**Honest assessment**: this directory is **archive-quality**, not
**clean-room-reproducible**. Concretely:

| Layer | Status |
|---|---|
| Curator prompts (`02_prompts/`) | ✓ complete and portable |
| Sandbox builders (`03_scripts/build_*.py`) | ✓ work, but use hardcoded absolute paths |
| Audit-record writers (`write_curator_audit*.py`) | ✓ work given on-disk artifacts and `dispatch_log*.jsonl` |
| Dispatch-log writers (`write_dispatch_log*.py`) | ⚠ contain agent-id / return-message constants harvested from one specific Claude Code session |
| Solver-token extractor (`extract_solver_tokens.py`) | ⚠ depends on the Claude Code session JSONL at a hardcoded path |
| Sub-agent dispatcher | ✗ **MISSING.** All 285 sub-agent calls were issued by hand through Claude Code's Agent tool; there is no standalone Python dispatcher checked in. |
| End-to-end runner | ✗ no single script reproduces all stages |

These gaps are tracked as open work in
`00_journal/section3_journal_2026-05-13.md §7`. The artifacts on
disk (NK records, audit records, dispatch logs, results CSVs) are
the authoritative record; the scripts re-build derivative views
from those artifacts.

## What you can re-run today (locally, on dietcoke's machine)

The data flow has four stages. Stages (1) and (4) are scripted;
stage (2) requires sub-agent dispatch (currently manual via
Claude Code); stage (3) requires the sandboxes from stage (2).

### Stage (1) — Build sandboxes
```
python 03_scripts/build_curator_runs.py        # 24 r1 curator sandboxes
python 03_scripts/build_curator_runs_r2.py     # 22 r2 curator sandboxes
python 03_scripts/build_curator_runs_deep.py   # 19 deep curator sandboxes
python 03_scripts/build_nkr.py                 # 24 round2_NKR solver sandboxes
python 03_scripts/build_nkr_r3.py              # 22 round3_NKR solver sandboxes
python 03_scripts/build_deep_nkr.py            # 19+19 deepNKR Sonnet+Haiku
```
Sandboxes are written under
`paper/experiments/pilot_2026-05-10/runs/task_<id>/<model>/v3/<cell>/`
and `04_outputs/curator_runs/`.

Prerequisite: the same pipeline's predecessor cells must already
exist on disk. The pilot's `scripts/build_v3.py`,
`scripts/build_v3_b0.py`, and `scripts/run_v3.py` (lives at
`paper/experiments/pilot_2026-05-10/scripts/`) build and run
round-1, B0, B2, B3, and the multi-round derivatives.

### Stage (2) — Dispatch sub-agents (MANUAL)

For each curator sandbox under `04_outputs/curator_runs/task_<id>{,_r2,_deep}/`,
spawn a Claude Sonnet 4.6 sub-agent with the prompt:

```
Read <abs path to prompt.md> and follow its instructions exactly.
Make exactly one Write call to the JSON path specified in the prompt.
Do not Read files outside the listed inputs.
```

For each solver sandbox (`runs/task_<id>/<model>/v3/<cell>/`),
spawn a Claude sub-agent (Sonnet or Haiku as appropriate) with:

```
Read <abs path to prompt.md> and follow its instructions.
You may Read the nk.json file(s) referenced in the Memory section.
Make exactly two Write calls (candidate.py + reasoning.md).
Do not Read other files. Do not run the script.
```

**Capture per dispatch**: `agent_id`, `return_message`,
`total_tokens`, `tool_uses`, `duration_ms`, `dispatched_at_utc`,
`completed_at_utc`. Append one JSON line to
`04_outputs/dispatch_log{,_r2,_deep}.jsonl`.

The current `write_dispatch_log_r1.py / _r2.py / _deep.py` are
**transcriptions** of the dispatch metadata I captured from the
Claude Code session that produced the original runs; they are
useful as **reference data**, not as a generic dispatcher.

### Stage (3) — Run solver sandboxes
```
python 03_scripts/run_deep_nkr.py
# Pilot's runner for non-NKR cells:
python ../../experiments/pilot_2026-05-10/scripts/run_v3.py
```
The runners execute `python candidate.py` and the eval script in
each sandbox; outputs go to `result.json`, `exec.log`, `eval.log`,
and consolidated CSVs at `paper/experiments/pilot_2026-05-10/`.

### Stage (4) — Build audit records and token tables
```
python 03_scripts/write_curator_audit.py        # r1 audit (needs dispatch_log.jsonl)
python 03_scripts/write_curator_audit_r2.py     # r2 audit (needs dispatch_log_r2.jsonl)
python 03_scripts/write_curator_audit_deep.py   # deep audit (needs dispatch_log_deep.jsonl)
python 03_scripts/extract_solver_tokens.py      # solver tokens (needs Claude Code session JSONL)
```

Outputs:
- `04_outputs/curator_audit/task_<id>{,_r2,_deep}.json` — 65 audit records
- `04_outputs/solver_tokens.csv` — 220 solver dispatch tokens

## What needs to change before public release

1. **Standalone sub-agent dispatcher** (highest priority for paper
   submission). Replace the manual Claude Code Agent tool flow with
   a Python module that calls the Anthropic API directly, captures
   the metadata in the same schema as `dispatch_log_*.jsonl`, and
   handles parallelism. Stage (2) above describes the loop this
   dispatcher must implement.
2. **Path relativization.** All 11 scripts in `03_scripts/` carry
   hardcoded `/Users/dietcoke/...` prefixes for `PILOT`,
   `SECTION3`, `BENCH`. Replace with a `${PROJECT_ROOT}` convention
   resolved from an env var or CLI flag.
3. **Replace `extract_solver_tokens.py`'s session-log dependency.**
   The script currently reads the Claude Code session JSONL at a
   user-specific path. The clean alternative is to have the
   standalone dispatcher write tokens directly into each cell's
   `result.json` at dispatch time.
4. **Mirror pilot scripts.** The end-to-end pipeline depends on
   `paper/experiments/pilot_2026-05-10/scripts/{build_v3.py,
   build_v3_b0.py, run_v3.py}` for non-NKR cells. Copy these in or
   document the cross-directory dependency.
5. **Lock the venv.** Reproduce requires the pilot's `.venv_full`
   (Python 3.13 with torch, tensorflow, deepchem, etc.). The
   pinned `requirements.txt` is at
   `paper/release/environment/requirements.txt`.

## Directory layout

```
section3/
├── 00_journal/
│   └── section3_journal_2026-05-13.md     timeline + open issues + definitions
├── 02_prompts/
│   ├── sab_curator.md                     r1 (depth-1) curator template
│   ├── sab_curator_r2.md                  r2 (depth-1 chain) curator template
│   └── sab_curator_deep.md                deep (depth-3) curator template
├── 03_scripts/
│   ├── build_curator_runs.py              build 24 r1 curator sandboxes
│   ├── build_curator_runs_r2.py           build 22 r2 curator sandboxes
│   ├── build_curator_runs_deep.py         build 19 deep curator sandboxes
│   ├── build_nkr.py                       build NKR r2 solver sandboxes
│   ├── build_nkr_r3.py                    build NKR r3 solver sandboxes
│   ├── build_deep_nkr.py                  build deepNKR Sonnet+Haiku sandboxes
│   ├── write_dispatch_log_r1.py           transcribed r1 dispatch metadata
│   ├── write_dispatch_log_r2.py           transcribed r2 dispatch metadata
│   ├── write_dispatch_log_deep.py         transcribed deep dispatch metadata
│   ├── write_curator_audit.py             r1 audit-record writer
│   ├── write_curator_audit_r2.py          r2 audit-record writer
│   ├── write_curator_audit_deep.py        deep audit-record writer
│   ├── run_deep_nkr.py                    runner for deepNKR cells
│   └── extract_solver_tokens.py           back-fill solver tokens from session log
├── 04_outputs/
│   ├── nk_records/                        65 NK files (24 r1 + 22 r2 + 19 deep)
│   ├── curator_audit/                     65 paired audit records
│   ├── curator_runs/                      per-task curator sandboxes
│   ├── dispatch_log.jsonl                 r1 dispatch metadata (24 lines)
│   ├── dispatch_log_r2.jsonl              r2 dispatch metadata (22 lines)
│   ├── dispatch_log_deep.jsonl            deep dispatch metadata (19 lines)
│   └── solver_tokens.csv                  220 solver dispatch tokens
└── 05_results/                            (empty — final §3 tables held in main.tex)
```
