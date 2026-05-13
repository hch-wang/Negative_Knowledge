#!/usr/bin/env python3
"""Materialise round-2 curator-agent audit records.

Same shape as write_curator_audit.py but for the round-2 curator pass:
- inputs are the round-2 NKR artifacts + the round-1 NK (which the round-2
  curator was given as context).
- output is the round-2 NK file at nk_records/task_<id>_r2.json.
- dispatch metadata read from dispatch_log_r2.jsonl.
- audit written to curator_audit/task_<id>_r2.json.
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
    r2_dir = PILOT / f"runs/task_{tid}/sonnet_4.6/v3/round2_NKR"
    curator_dir = SECTION3 / f"04_outputs/curator_runs/task_{tid}_r2"
    r1_nk_path = SECTION3 / f"04_outputs/nk_records/task_{tid}.json"
    r2_nk_path = SECTION3 / f"04_outputs/nk_records/task_{tid}_r2.json"

    inputs = {
        "prompt": _file_snapshot(curator_dir / "prompt.md"),
        "round1_nk": _file_snapshot(r1_nk_path),
        "round2_candidate": _file_snapshot(r2_dir / "candidate.py"),
        "round2_exec_log": _file_snapshot(r2_dir / "exec.log"),
        "round2_eval_log": _file_snapshot(r2_dir / "eval.log"),
        "round2_reasoning": _file_snapshot(r2_dir / "reasoning.md"),
    }

    if r2_nk_path.exists():
        nk_raw = r2_nk_path.read_text()
        try:
            nk_parsed = json.loads(nk_raw)
            nk_parse_ok = True
        except Exception as e:
            nk_parsed = {"_parse_error": str(e), "_raw": nk_raw[:1000]}
            nk_parse_ok = False
        nk_block = {
            "path": str(r2_nk_path),
            "bytes": len(nk_raw.encode("utf-8")),
            "sha256": _sha256(nk_raw),
            "parses_as_json": nk_parse_ok,
            "content": nk_parsed,
        }
    else:
        nk_block = {"path": str(r2_nk_path), "missing": True}

    audit = {
        "schema_version": "section3.curator_audit.v1",
        "task_id": tid,
        "round": 2,
        "audit_written_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "curator_model": "claude-sonnet-4.6",
        "dispatch": dispatch_rec,
        "inputs": inputs,
        "output_nk": nk_block,
    }
    return audit


def main():
    dispatch_log = SECTION3 / "04_outputs/dispatch_log_r2.jsonl"
    audit_dir = SECTION3 / "04_outputs/curator_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    if not dispatch_log.exists():
        raise SystemExit(f"missing {dispatch_log}")

    seen = set()
    n = 0
    for line in dispatch_log.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        tid = rec["task_id"]
        if tid in seen:
            continue
        seen.add(tid)
        audit = build_audit_for_task(tid, rec)
        out = audit_dir / f"task_{tid}_r2.json"
        out.write_text(json.dumps(audit, indent=2))
        total_b = sum(v.get('bytes', 0) for v in audit['inputs'].values()) + audit['output_nk'].get('bytes', 0)
        print(f"  wrote {out.relative_to(SECTION3)}  ({total_b} B)")
        n += 1

    print(f"\nwrote {n} round-2 curator audit records")


if __name__ == "__main__":
    main()
