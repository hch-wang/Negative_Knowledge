#!/usr/bin/env python3
"""Consolidate every solver sub-agent dispatch into one JSON file.

For each of the 220 solver dispatches captured in
section3/04_outputs/solver_tokens.csv, this script reads the
on-disk sandbox artifacts (prompt, candidate.py, reasoning.md,
exec.log, eval.log, result.json, NK file(s)) and writes a single
JSON record at:

  section3/04_outputs/dispatches/solver/task_<id>__<cell>.json

The schema mirrors the curator-audit records at
04_outputs/curator_audit/, so a single reproduction script can
read both archives uniformly.

Each record captures:
- task_id, cell, model_dir, model_choice
- dispatch metadata (agent_id, return_message, tokens,
  tool_uses, duration_ms)
- inputs: prompt + the NK file(s) the agent was allowed to Read
- outputs: candidate.py + reasoning.md (with sha256 + bytes)
- execution: exec.log + eval.log + result.json (exit_code,
  eval_status, eval_score, eval_msg)

What is NOT captured (Claude Code Agent-tool design constraint):
the sub-agent's intermediate tool calls and reasoning between
tool calls. The sub-agent runs in an isolated context; only the
deliberate outputs (written files + return message) cross the
boundary back to the parent.
"""
from __future__ import annotations
import csv
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


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


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


# Map cell -> list of NK filenames the agent was allowed to Read
NK_FILES_BY_CELL = {
    "round1":          [],
    "round2_B0":       [],
    "round2_NKR":      ["nk.json"],
    "round2_B2":       [],   # B2 reads prior code/log, no NK
    "round2_B3":       [],   # B3 reads failure_record + team_memory, complex
    "round3_NKR":      ["nk_r1.json", "nk_r2.json"],
    "round3_B2":       [],
    "round3_B3":       [],
    "deepNKR_sonnet":  ["deep_nk.json"],
    "deepNKR_haiku":   ["deep_nk.json"],
}


def build_solver_record(row: dict) -> dict:
    task_id = row["task_id"]
    cell = row["cell"]
    model_dir = row["model_dir"]
    sandbox = PILOT / f"runs/task_{task_id}/{model_dir}/v3/{cell}"

    inputs = {
        "prompt": _file_snapshot(sandbox / "prompt.md"),
    }
    for nk_name in NK_FILES_BY_CELL.get(cell, []):
        key = nk_name.replace(".json", "")
        inputs[f"nk_{key}" if not key.startswith("nk") else key] = (
            _file_snapshot(sandbox / nk_name)
        )

    outputs = {
        "candidate": _file_snapshot(sandbox / "candidate.py"),
        "reasoning": _file_snapshot(sandbox / "reasoning.md"),
    }

    execution = {
        "exec_log": _file_snapshot(sandbox / "exec.log"),
        "eval_log": _file_snapshot(sandbox / "eval.log"),
        "result_json": _file_snapshot(sandbox / "result.json"),
    }
    # Parse result.json for the headline outcome
    if (sandbox / "result.json").exists():
        try:
            r = json.load(open(sandbox / "result.json"))
            execution["exit_code"] = r.get("exit_code")
            execution["eval_status"] = r.get("eval_status")
            execution["eval_score"] = r.get("eval_score")
            execution["eval_msg"] = r.get("eval_msg")
            execution["output_exists"] = r.get("output_exists")
        except Exception:
            pass

    dispatch = {
        "tool_use_id": row.get("tool_use_id"),
        "agent_id": row.get("agent_id"),
        "return_message": row.get("return_message"),
        "model_choice": row.get("model_choice"),
        "tokens": int(row["tokens"]) if row.get("tokens") else None,
        "tool_uses": int(row["tool_uses_count"]) if row.get("tool_uses_count") else None,
        "duration_ms": int(row["duration_ms"]) if row.get("duration_ms") else None,
    }

    return {
        "schema_version": "section3.dispatch.solver.v1",
        "role": "solver",
        "task_id": task_id,
        "cell": cell,
        "model_dir": model_dir,
        "consolidated_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "dispatch": dispatch,
        "inputs": inputs,
        "outputs": outputs,
        "execution": execution,
    }


def main():
    tokens_csv = SECTION3 / "04_outputs/solver_tokens.csv"
    if not tokens_csv.exists():
        raise SystemExit(f"missing {tokens_csv}; run extract_solver_tokens.py first")

    out_dir = SECTION3 / "04_outputs/dispatches/solver"
    out_dir.mkdir(parents=True, exist_ok=True)

    n = 0
    for row in csv.DictReader(open(tokens_csv)):
        rec = build_solver_record(row)
        # File naming: task_<id>__<cell>.json (cell name encodes model_dir
        # for deepNKR_sonnet vs deepNKR_haiku, but for sonnet_4.6 cells we
        # need to differentiate from haiku_4.5 too).
        if row["model_dir"] != "sonnet_4.6":
            fname = f"task_{row['task_id']}__{row['cell']}__{row['model_dir']}.json"
        else:
            fname = f"task_{row['task_id']}__{row['cell']}.json"
        (out_dir / fname).write_text(json.dumps(rec, indent=2))
        n += 1

    print(f"wrote {n} solver dispatch records to {out_dir.relative_to(SECTION3)}")
    # Quick size summary
    total = sum(p.stat().st_size for p in out_dir.glob("*.json"))
    print(f"archive size: {total/1024:.1f} KB")


if __name__ == "__main__":
    main()
