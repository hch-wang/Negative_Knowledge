#!/usr/bin/env python3
"""Dispatch one sub-agent via the Anthropic API.

Replaces the Claude Code Agent tool used during the original §3
experiment. Reviewer needs:

  - ANTHROPIC_API_KEY env var set
  - `anthropic` python SDK installed (`pip install anthropic`)

Each dispatch reads a single sandbox's prompt.md and runs a sub-agent
constrained to:
  - Read a fixed allowlist of files
  - Write exactly the output files declared in the prompt
  - No Bash, no Edit, no other tools

CLI:
  python dispatch_subagent.py SANDBOX_DIR \\
         --model {sonnet | haiku} \\
         --output-files candidate.py reasoning.md \\
         --read-allowlist prompt.md nk.json

Or for curators:
  python dispatch_subagent.py CURATOR_SANDBOX \\
         --model sonnet \\
         --output-files /path/to/output_nk.json \\
         --read-allowlist prompt.md /abs/path/to/round1/candidate.py ...

Writes a `dispatch_record.json` next to the sandbox capturing the full
I/O for audit (mirrors the schema in logs/curator_audit/).
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import time
from typing import Any

try:
    import anthropic
except ImportError:
    sys.exit("missing `anthropic` SDK; pip install anthropic")


MODEL_ALIASES = {
    "sonnet": "claude-sonnet-4-5",
    "haiku": "claude-haiku-4-5",
    "opus": "claude-opus-4-5",
}

READ_TOOL = {
    "name": "Read",
    "description": "Read a file from disk and return its contents.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string",
                          "description": "Absolute path to the file to read."}
        },
        "required": ["file_path"],
    },
}

WRITE_TOOL = {
    "name": "Write",
    "description": "Write content to a file. Overwrites if it exists.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string",
                          "description": "Absolute path to write to."},
            "content": {"type": "string",
                        "description": "Full content to write."},
        },
        "required": ["file_path", "content"],
    },
}


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
    }


def run_subagent(
    prompt: str,
    model: str,
    read_allowlist: set[str],
    write_allowlist: set[str],
    max_iterations: int = 30,
) -> dict:
    """Run a tool-using sub-agent with constrained Read/Write.

    Returns a dict with:
      tokens_in, tokens_out, total_tokens, tool_uses, duration_sec,
      stop_reason, return_message, intermediate_tool_calls
    """
    client = anthropic.Anthropic()
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    total_in = 0
    total_out = 0
    tool_uses = 0
    intermediate: list[dict] = []
    return_message = ""
    t0 = time.time()

    for _ in range(max_iterations):
        response = client.messages.create(
            model=model,
            max_tokens=8000,
            tools=[READ_TOOL, WRITE_TOOL],
            messages=messages,
        )
        total_in += response.usage.input_tokens
        total_out += response.usage.output_tokens

        # Append assistant turn
        messages.append({"role": "assistant", "content": [
            b.model_dump() for b in response.content
        ]})

        if response.stop_reason != "tool_use":
            # extract final text
            return_message = "".join(
                b.text for b in response.content if b.type == "text"
            )
            break

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_uses += 1
            if block.name == "Read":
                fp = block.input["file_path"]
                if fp not in read_allowlist:
                    content = (
                        f"Error: {fp} not in Read allowlist. "
                        f"Allowed: {sorted(read_allowlist)}"
                    )
                    is_error = True
                elif not pathlib.Path(fp).exists():
                    content = f"Error: {fp} does not exist"
                    is_error = True
                else:
                    content = pathlib.Path(fp).read_text(errors="replace")
                    is_error = False
                intermediate.append({
                    "tool": "Read", "file_path": fp,
                    "result_chars": len(content), "error": is_error,
                })
            elif block.name == "Write":
                fp = block.input["file_path"]
                payload = block.input["content"]
                if fp not in write_allowlist:
                    content = (
                        f"Error: {fp} not in Write allowlist. "
                        f"Allowed: {sorted(write_allowlist)}"
                    )
                    is_error = True
                else:
                    pathlib.Path(fp).parent.mkdir(parents=True, exist_ok=True)
                    pathlib.Path(fp).write_text(payload)
                    content = f"File written: {fp} ({len(payload)} chars)"
                    is_error = False
                intermediate.append({
                    "tool": "Write", "file_path": fp,
                    "wrote_chars": len(payload), "error": is_error,
                })
            else:
                content = f"Error: unknown tool {block.name}"
                is_error = True
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": content,
                **({"is_error": True} if is_error else {}),
            })
        messages.append({"role": "user", "content": tool_results})
    else:
        return_message = (
            f"<<<dispatcher: max_iterations={max_iterations} exceeded>>>"
        )

    return {
        "model": model,
        "tokens_in": total_in,
        "tokens_out": total_out,
        "total_tokens": total_in + total_out,
        "tool_uses": tool_uses,
        "duration_sec": round(time.time() - t0, 2),
        "stop_reason": response.stop_reason,
        "return_message": return_message,
        "intermediate_tool_calls": intermediate,
    }


def main():
    ap = argparse.ArgumentParser(
        description="Dispatch one sub-agent against a sandbox prompt."
    )
    ap.add_argument("sandbox", type=pathlib.Path,
                    help="Sandbox directory containing prompt.md.")
    ap.add_argument("--model", default="sonnet",
                    choices=list(MODEL_ALIASES),
                    help="Model alias (sonnet | haiku | opus).")
    ap.add_argument("--read-allowlist", nargs="*", default=[],
                    help="Absolute paths the agent is allowed to Read "
                         "(prompt.md is added automatically).")
    ap.add_argument("--output-files", nargs="+", required=True,
                    help="Absolute paths the agent must Write.")
    ap.add_argument("--record-out", type=pathlib.Path, default=None,
                    help="Path to write the dispatch_record.json "
                         "(default: <sandbox>/dispatch_record.json).")
    args = ap.parse_args()

    sandbox = args.sandbox.resolve()
    prompt_path = sandbox / "prompt.md"
    if not prompt_path.exists():
        sys.exit(f"missing prompt.md in {sandbox}")
    prompt = prompt_path.read_text()

    read_allowlist = set(str(pathlib.Path(p).resolve())
                         for p in args.read_allowlist)
    read_allowlist.add(str(prompt_path))
    write_allowlist = set(str(pathlib.Path(p).resolve())
                          for p in args.output_files)

    model_full = MODEL_ALIASES[args.model]
    print(f"dispatching {args.model} ({model_full}) on {sandbox.name}")
    print(f"  read allowlist: {len(read_allowlist)} files")
    print(f"  write allowlist: {len(write_allowlist)} files")

    record = run_subagent(prompt, model_full, read_allowlist, write_allowlist)

    # Snapshot inputs (post-resolution: just the prompt and what the agent
    # was permitted to read).
    record["sandbox"] = str(sandbox)
    record["dispatched_at_utc"] = dt.datetime.now(dt.UTC).isoformat()
    record["read_allowlist_count"] = len(read_allowlist)
    record["write_allowlist"] = sorted(write_allowlist)

    # Snapshot what got written
    record["outputs"] = {}
    for fp in args.output_files:
        record["outputs"][pathlib.Path(fp).name] = _file_snapshot(
            pathlib.Path(fp)
        )

    record_out = args.record_out or (sandbox / "dispatch_record.json")
    record_out.write_text(json.dumps(record, indent=2))
    print(f"  done. tokens={record['total_tokens']} "
          f"tool_uses={record['tool_uses']} "
          f"duration={record['duration_sec']}s "
          f"stop={record['stop_reason']}")
    print(f"  record: {record_out}")


if __name__ == "__main__":
    main()
