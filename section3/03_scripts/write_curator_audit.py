#!/usr/bin/env python3
"""Materialise the curator-agent audit records.

This is run by the orchestrator (parent agent) AFTER all curator sub-agents
have returned. It produces, for each task, a self-contained audit file at:

  section3/04_outputs/curator_audit/task_<id>.json

The audit file captures every piece of input the curator was given, every
piece of output it produced, plus the dispatch metadata — enough that a
reader can reproduce / verify the curator's reasoning without re-running it.

Dispatch metadata is read from `section3/04_outputs/dispatch_log.jsonl`,
one JSON-line per dispatched curator with these fields:
  - task_id
  - agent_id
  - return_message       (the curator agent's final reply text)
  - tokens               (total_tokens reported by the runtime)
  - tool_uses            (count)
  - duration_ms
  - dispatched_at_utc    (ISO 8601)
  - completed_at_utc     (ISO 8601)

The orchestrator writes that log as it dispatches. This script reads it and
joins against the on-disk artifacts.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import pathlib

SECTION3 = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/Negative_Knowledge/section3"
)
PILOT = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/experiments/pilot_2026-05-10"
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _file_snapshot(path: pathlib.Path) -> dict:
    """Capture a file's full content + size + hash for the audit."""
    if not path.exists():
        return {"path": str(path), "missing": True}
    raw = path.read_text(errors="replace")
    return {
        "path": str(path),
        "bytes": len(raw.encode("utf-8")),
        "sha256": _sha256(raw),
        "content": raw,
    }


def build_audit_for_task(tid: str, dispatch_rec: dict) -> dict:
    """Assemble one task's audit record by reading on-disk artifacts."""
    round1_dir = PILOT / f"runs/task_{tid}/sonnet_4.6/v3/round1"
    curator_dir = SECTION3 / f"04_outputs/curator_runs/task_{tid}"
    nk_path = SECTION3 / f"04_outputs/nk_records/task_{tid}.json"

    inputs = {
        "prompt": _file_snapshot(curator_dir / "prompt.md"),
        "round1_candidate": _file_snapshot(round1_dir / "candidate.py"),
        "round1_exec_log": _file_snapshot(round1_dir / "exec.log"),
        "round1_eval_log": _file_snapshot(round1_dir / "eval.log"),
        "round1_reasoning": _file_snapshot(round1_dir / "reasoning.md"),
    }

    # The curator's output: the NK file it wrote
    if nk_path.exists():
        nk_raw = nk_path.read_text()
        try:
            nk_parsed = json.loads(nk_raw)
            nk_parse_ok = True
        except Exception as e:
            nk_parsed = {"_parse_error": str(e), "_raw": nk_raw[:1000]}
            nk_parse_ok = False
        nk_block = {
            "path": str(nk_path),
            "bytes": len(nk_raw.encode("utf-8")),
            "sha256": _sha256(nk_raw),
            "parses_as_json": nk_parse_ok,
            "content": nk_parsed,
        }
    else:
        nk_block = {"path": str(nk_path), "missing": True}

    audit = {
        "schema_version": "section3.curator_audit.v1",
        "task_id": tid,
        "audit_written_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "curator_model": "claude-sonnet-4.6",
        "dispatch": dispatch_rec,
        "inputs": inputs,
        "output_nk": nk_block,
    }
    return audit


def main():
    dispatch_log = SECTION3 / "04_outputs/dispatch_log.jsonl"
    audit_dir = SECTION3 / "04_outputs/curator_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    if not dispatch_log.exists():
        raise SystemExit(f"missing {dispatch_log}; orchestrator must write it "
                         "before audit can be materialised")

    seen = set()
    n = 0
    for line in dispatch_log.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        tid = rec["task_id"]
        if tid in seen:
            print(f"  skip duplicate dispatch record for task_{tid}")
            continue
        seen.add(tid)
        audit = build_audit_for_task(tid, rec)
        out = audit_dir / f"task_{tid}.json"
        out.write_text(json.dumps(audit, indent=2))
        print(f"  wrote {out.relative_to(SECTION3)}  "
              f"(inputs+output {sum(v.get('bytes', 0) for v in audit['inputs'].values()) + audit['output_nk'].get('bytes', 0)} B)")
        n += 1

    print(f"\nwrote {n} curator audit records to {audit_dir.relative_to(SECTION3)}")


if __name__ == "__main__":
    main()
