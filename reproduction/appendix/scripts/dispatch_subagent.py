#!/usr/bin/env python3
"""Dispatch a single Research-Graph sub-agent against the Anthropic API.

This is a clean-room reimplementation of the Agent-tool dispatch used in
the original appendix experiment (which ran inside Claude Code). The
original sub-agents had Read / Write / Bash tools; this script exposes
the same three tools via the Anthropic SDK's tool-use loop.

Reviewers will see a near-identical session trajectory but byte-exact
reproduction is not guaranteed (LLM nondeterminism).

Usage:
  python scripts/dispatch_subagent.py --task T_C --cond NLS
  python scripts/dispatch_subagent.py --task T_C --cond NLS --model claude-sonnet-4-6 --max-turns 30

Requires:
  ANTHROPIC_API_KEY env var, anthropic SDK (pip install anthropic).
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _paths import CONDITIONS, TASKS, cell_dir, PY_VENV


SYSTEM_PROMPT = """You are an autonomous Research-Graph researcher dispatched on a single B-NLS task.
Read your sandbox's prompt.md to get the full protocol (Q/E/F/D node schema,
progressive-complexity discipline, condition-specific bank). Follow it strictly.

You have three tools: read_file, write_file, bash. Use Write (full file rewrites)
rather than Edit. Use bash only to execute candidate.py and quick diagnostics.

At session end, the working directory must contain candidate.py, reasoning.md,
research_state.jsonl, session_log.md, and pred_results/<task_id>.npy. After
all required files exist, output a one-paragraph plain-text summary and stop."""


TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read a file by absolute path. Returns the file contents.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write text content to a file (overwrites existing). Returns 'OK' or an error.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "bash",
        "description": "Run a bash command in the sandbox working directory. 120 s timeout.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
]


def tool_read_file(path, sandbox_root):
    p = pathlib.Path(path).resolve()
    if not p.exists():
        return f"ERROR: file not found: {p}"
    try:
        return p.read_text()
    except Exception as e:
        return f"ERROR: {e}"


def tool_write_file(path, content, sandbox_root):
    p = pathlib.Path(path).resolve()
    if not str(p).startswith(str(sandbox_root.resolve())):
        return f"ERROR: write outside sandbox forbidden: {p}"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return "OK"


def tool_bash(command, sandbox_root):
    try:
        r = subprocess.run(command, shell=True, cwd=str(sandbox_root), capture_output=True,
                           text=True, timeout=120)
        return (f"exit_code={r.returncode}\n--- stdout ---\n{r.stdout[-4000:]}\n"
                f"--- stderr ---\n{r.stderr[-4000:]}")
    except subprocess.TimeoutExpired:
        return "ERROR: timeout 120 s"
    except Exception as e:
        return f"ERROR: {e}"


def dispatch(task, cond, model="claude-sonnet-4-6", max_turns=40):
    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic SDK not installed. `pip install anthropic`.", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: set ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    sandbox = cell_dir(task, cond)
    prompt_path = sandbox / "prompt.md"
    if not prompt_path.exists():
        print(f"ERROR: {prompt_path} not found. Run build_sandboxes.py first.", file=sys.stderr)
        sys.exit(1)
    user_prompt = (
        f"Your sandbox is {sandbox}.\nRead {prompt_path} first, then follow it.\n"
        f"The Python interpreter for candidate.py is `{PY_VENV}`."
    )

    messages = [{"role": "user", "content": user_prompt}]
    for turn in range(max_turns):
        resp = client.messages.create(
            model=model, max_tokens=4096, system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS, messages=messages,
        )
        # echo any text blocks
        for block in resp.content:
            if block.type == "text" and block.text.strip():
                print(f"[{turn}] {block.text[:500]}")

        if resp.stop_reason == "end_turn":
            print(f"\n[end_turn after {turn+1} turns]")
            break

        # process any tool_use blocks
        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        if not tool_uses:
            print(f"\n[no tool_use and not end_turn; stopping]")
            break
        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for tu in tool_uses:
            name = tu.name; args = tu.input
            if name == "read_file":
                out = tool_read_file(args["path"], sandbox)
            elif name == "write_file":
                out = tool_write_file(args["path"], args["content"], sandbox)
            elif name == "bash":
                out = tool_bash(args["command"], sandbox)
            else:
                out = f"ERROR: unknown tool {name}"
            tool_results.append({"type": "tool_result", "tool_use_id": tu.id, "content": out[:8000]})
        messages.append({"role": "user", "content": tool_results})
    else:
        print(f"[reached max_turns={max_turns}]")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=TASKS, required=True)
    p.add_argument("--cond", choices=CONDITIONS, required=True)
    p.add_argument("--model", default="claude-sonnet-4-6")
    p.add_argument("--max-turns", type=int, default=40)
    args = p.parse_args()
    dispatch(args.task, args.cond, args.model, args.max_turns)


if __name__ == "__main__":
    main()
