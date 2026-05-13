#!/usr/bin/env python3
"""Extract per-dispatch token usage from the Claude Code conversation log
and join it onto v3 cells.

Source: the JSONL conversation log at
  ~/.claude/projects/.../<session_id>.jsonl

For each Agent tool_use:
  - capture (tool_use_id, prompt, model, description)
  - extract task_id and cell_name from the prompt's file paths

For each tool_result matching that tool_use_id:
  - parse the trailing <usage>total_tokens: N\ntool_uses: K\nduration_ms: D</usage>
  - parse the agentId from the result text
  - parse the return_message (text before the agentId line)

Output:
  - section3/04_outputs/solver_tokens.csv   per-dispatch row with all
    metadata
  - back-write tokens / tool_uses / duration_ms / agent_id / return_message
    into each result.json file under runs/<task>/<model>/v3/<cell>/

After this, results_v3.csv and results_deep_nkr.csv can be regenerated
with the token columns included.
"""
from __future__ import annotations
import csv
import json
import pathlib
import re

CONV_LOG = pathlib.Path(
    "/Users/dietcoke/.claude/projects/"
    "-Users-dietcoke-Documents-Project-00-simulation-software/"
    "9190c1d6-ecb2-4855-ab9f-39782709cf65.jsonl"
)
SECTION3 = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/Negative_Knowledge/section3"
)
PILOT = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/experiments/pilot_2026-05-10"
)

# Path patterns we care about. Anything else is from an earlier experiment.
V3_CELLS = (
    "round1", "round2_B0", "round2_B2", "round2_B3", "round2_NKR",
    "round3_B2", "round3_B3", "round3_NKR",
    "deepNKR_sonnet", "deepNKR_haiku",
)

# Regex for extracting task_id + cell from prompt
PATH_RE = re.compile(
    r"/runs/task_(\d{3})/(sonnet_4\.6|haiku_4\.5|opus_4\.7)"
    r"/v3/([A-Za-z0-9_]+)/"
)

USAGE_RE = re.compile(
    r"<usage>total_tokens:\s*(\d+)\s*\n\s*tool_uses:\s*(\d+)\s*\n"
    r"\s*duration_ms:\s*(\d+)\s*</usage>"
)

AGENT_ID_RE = re.compile(r"agentId:\s*([a-z0-9]+)")


def parse_prompt_for_task_cell(prompt: str):
    """Return (task_id, model, cell) or (None, None, None)."""
    m = PATH_RE.search(prompt)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return None, None, None


def parse_result(text: str):
    """Return (tokens, tool_uses, duration_ms, agent_id, return_message)
    or all None if the text doesn't match expected format."""
    u = USAGE_RE.search(text)
    a = AGENT_ID_RE.search(text)
    if not u:
        return None, None, None, None, None
    tokens = int(u.group(1))
    tool_uses = int(u.group(2))
    duration = int(u.group(3))
    agent_id = a.group(1) if a else None
    # return_message is everything before the agentId line
    if a:
        msg = text[: a.start()].rstrip()
    else:
        msg = text[: u.start()].rstrip()
    # strip a trailing newline that often precedes the agentId line
    return tokens, tool_uses, duration, agent_id, msg


def main():
    # Pass 1: collect all Agent tool_use blocks
    calls = {}  # tool_use_id -> (task, model, cell, description, model_choice)
    for line in open(CONV_LOG):
        try:
            d = json.loads(line)
        except Exception:
            continue
        msg = d.get("message") or {}
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for blk in content:
            if not isinstance(blk, dict):
                continue
            if blk.get("type") == "tool_use" and blk.get("name") == "Agent":
                inp = blk.get("input") or {}
                prompt = inp.get("prompt", "")
                description = inp.get("description", "")
                model_choice = inp.get("model", "")
                task, model_dir, cell = parse_prompt_for_task_cell(prompt)
                tu_id = blk.get("id")
                if tu_id:
                    calls[tu_id] = {
                        "tool_use_id": tu_id,
                        "task_id": task,
                        "model_dir": model_dir,
                        "cell": cell,
                        "description": description,
                        "model_choice": model_choice,
                        "prompt_first_100": prompt[:100],
                    }

    # Pass 2: collect tool_results
    results = {}  # tool_use_id -> {tokens, ...}
    for line in open(CONV_LOG):
        try:
            d = json.loads(line)
        except Exception:
            continue
        msg = d.get("message") or {}
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for blk in content:
            if not isinstance(blk, dict):
                continue
            if blk.get("type") == "tool_result":
                tu_id = blk.get("tool_use_id")
                if not tu_id:
                    continue
                text = blk.get("content")
                if isinstance(text, list):
                    text = "".join(
                        b.get("text", "") for b in text if isinstance(b, dict)
                    )
                if not isinstance(text, str):
                    continue
                toks, tu, dur, aid, ret = parse_result(text)
                if toks is None:
                    continue
                results[tu_id] = {
                    "tokens": toks,
                    "tool_uses_count": tu,
                    "duration_ms": dur,
                    "agent_id": aid,
                    "return_message": ret,
                }

    # Pass 3: join calls + results, filter to v3 cells
    rows = []
    for tu_id, call in calls.items():
        if call["cell"] not in V3_CELLS:
            continue
        r = results.get(tu_id)
        if r is None:
            continue
        row = {**call, **r}
        rows.append(row)

    # Write CSV
    out_csv = SECTION3 / "04_outputs/solver_tokens.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_id", "model_dir", "cell", "description",
        "model_choice", "tokens", "tool_uses_count", "duration_ms",
        "agent_id", "tool_use_id", "return_message",
    ]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote {out_csv}  ({len(rows)} solver dispatches)")

    # Pass 4: back-write into each cell's result.json
    n_back = 0
    for row in rows:
        rj = (PILOT / f"runs/task_{row['task_id']}/{row['model_dir']}"
              f"/v3/{row['cell']}/result.json")
        if not rj.exists():
            continue
        try:
            existing = json.load(open(rj))
        except Exception:
            continue
        existing["solver_tokens"] = row["tokens"]
        existing["solver_tool_uses"] = row["tool_uses_count"]
        existing["solver_duration_ms"] = row["duration_ms"]
        existing["solver_agent_id"] = row["agent_id"]
        rj.write_text(json.dumps(existing, indent=2))
        n_back += 1
    print(f"back-wrote tokens into {n_back} result.json files")

    # Print a quick summary by (model_dir, cell)
    from collections import defaultdict
    agg = defaultdict(list)
    for r in rows:
        agg[(r["model_dir"], r["cell"])].append(r["tokens"])
    print("\n=== per-cell token usage (n, mean, median) ===")
    for key in sorted(agg):
        toks = agg[key]
        toks_sorted = sorted(toks)
        med = toks_sorted[len(toks_sorted) // 2] if toks_sorted else 0
        mean = sum(toks) / len(toks) if toks else 0
        print(f"  {key[0]:12s} / {key[1]:15s}  n={len(toks):2d}  "
              f"mean={mean:>7.0f}  median={med:>6d}")


if __name__ == "__main__":
    main()
