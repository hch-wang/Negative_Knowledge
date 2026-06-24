#!/usr/bin/env python3
"""Dispatch one sandbox through the provider-neutral agent command bridge."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys


REPRODUCTION = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPRODUCTION))
from agent_command import resolve_model, run_subagent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sandbox", type=pathlib.Path)
    parser.add_argument("--model", default="default")
    parser.add_argument("--read-allowlist", nargs="*", default=[])
    parser.add_argument("--output-files", nargs="+", required=True)
    parser.add_argument("--record-out", type=pathlib.Path)
    args = parser.parse_args()

    sandbox = args.sandbox.resolve()
    prompt_path = sandbox / "prompt.md"
    if not prompt_path.is_file():
        raise SystemExit(f"missing prompt: {prompt_path}")
    reads = {str(pathlib.Path(path).resolve()) for path in args.read_allowlist}
    reads.add(str(prompt_path))
    writes = {str(pathlib.Path(path).resolve()) for path in args.output_files}
    record = run_subagent(prompt_path.read_text(), args.model, reads, writes)
    record.update(
        {
            "sandbox": str(sandbox),
            "dispatched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "write_allowlist": sorted(writes),
        }
    )
    output = args.record_out or sandbox / "dispatch_record.json"
    output.write_text(json.dumps(record, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
