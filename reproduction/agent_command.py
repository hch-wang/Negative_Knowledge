"""Provider-neutral bridge for optional fresh-agent reproduction runs.

Set ``NK_AGENT_COMMAND`` to an executable command. The command receives one
JSON request on stdin, performs the requested agent run, writes only the
declared output files, and returns a JSON metadata object on stdout.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shlex
import subprocess
import time
from typing import Any, Optional


def resolve_model(name: str) -> str:
    """Resolve a local model alias through ``NK_MODEL_<ALIAS>``."""
    suffix = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()
    return os.environ.get(f"NK_MODEL_{suffix}", name)


def run_subagent(
    prompt: str,
    model: str,
    read_allowlist: set[str],
    write_allowlist: set[str],
    max_iterations: int = 30,
    *,
    enable_bash: bool = False,
    bash_workdir: Optional[str] = None,
    bash_timeout: int = 120,
    system_prompt: Optional[str] = None,
    command: Optional[str] = None,
) -> dict[str, Any]:
    """Run a user-supplied agent command through a stable JSON protocol."""
    configured = command or os.environ.get("NK_AGENT_COMMAND")
    if not configured:
        raise RuntimeError(
            "fresh runs require NK_AGENT_COMMAND; see reproduction/README.md"
        )
    argv = shlex.split(configured)
    if not argv:
        raise RuntimeError("NK_AGENT_COMMAND is empty")

    request = {
        "protocol": "negative-knowledge-agent-command/v1",
        "prompt": prompt,
        "system_prompt": system_prompt,
        "model": resolve_model(model),
        "read_allowlist": sorted(str(pathlib.Path(p).resolve()) for p in read_allowlist),
        "write_allowlist": sorted(str(pathlib.Path(p).resolve()) for p in write_allowlist),
        "max_iterations": max_iterations,
        "capabilities": {
            "read": True,
            "write": True,
            "bash": enable_bash,
            "bash_workdir": bash_workdir,
            "bash_timeout": bash_timeout,
        },
    }
    started = time.monotonic()
    completed = subprocess.run(
        argv,
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
    )
    duration = round(time.monotonic() - started, 3)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            f"NK_AGENT_COMMAND exited with {completed.returncode}: {detail[-2000:]}"
        )

    stdout = completed.stdout.strip()
    if stdout:
        try:
            metadata = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("NK_AGENT_COMMAND stdout must be one JSON object") from exc
        if not isinstance(metadata, dict):
            raise RuntimeError("NK_AGENT_COMMAND stdout must be one JSON object")
    else:
        metadata = {}

    metadata.setdefault("model", request["model"])
    metadata.setdefault("tokens_in", 0)
    metadata.setdefault("tokens_out", 0)
    metadata.setdefault("total_tokens", metadata["tokens_in"] + metadata["tokens_out"])
    metadata.setdefault("tool_uses", 0)
    metadata.setdefault("stop_reason", "completed")
    metadata.setdefault("return_message", "")
    metadata.setdefault("duration_sec", duration)
    metadata.setdefault("stderr", completed.stderr.strip())
    return metadata
