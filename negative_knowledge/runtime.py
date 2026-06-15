"""negative_knowledge.runtime — constrained Read/Write sub-agent runtime.

This is the low-level "how": a single-call tool-use loop against the
Anthropic API in which a sub-agent may only Read a fixed allowlist of
files and Write a fixed allowlist of files (no Bash, no Edit, no other
tools). :class:`~negative_knowledge.curator.NKCurator` uses it to let a
curator agent read failure artifacts and write one NK JSON record.

Requirements:
  - ``ANTHROPIC_API_KEY`` in the environment
  - ``pip install anthropic``

The public entry point is :func:`run_subagent`, which returns a dict of
token usage, tool-use count, duration, stop reason, and final message.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import sys
import time
from typing import Any


MODEL_ALIASES = {
    "sonnet": "claude-sonnet-4-6",
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
    try:
        import anthropic
    except ImportError as e:  # lazy: only curation needs the SDK
        raise ImportError(
            "run_subagent requires the anthropic SDK: pip install anthropic"
        ) from e
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


