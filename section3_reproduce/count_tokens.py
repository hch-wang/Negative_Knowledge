#!/usr/bin/env python3
"""count_tokens.py — recompute the three token figures in Table 1 of the paper.

Table 1 reports memory-object size in tokens, measured with the
``cl100k_base`` tokenizer:

    Negative knowledge retry (depth-1)   296 tokens   (-73.3% vs self-debug)
    Self-debug                         1,109 tokens   (baseline)
    Deep negative knowledge (depth-3)    795 tokens   (-28.3%)

This script reads only files under ``logs/`` and prints the per-task token
counts and medians used in the paper. It does NOT call any LLM API.

Run:
    pip install tiktoken
    python3 count_tokens.py

Inputs (all under logs/):
    nk_records/task_<id>.json          depth-1 NK record (the memory object
                                       shown to the next attempt under
                                       "Negative knowledge retry")
    nk_records/task_<id>_deep.json     depth-3 NK record (memory object under
                                       "Deep negative knowledge retry")
    self_debug_inputs/task_<id>/       the three round-1 artifacts that the
        candidate.py, exec.log,        self-debug condition shows to the
        eval.log                       next attempt (concatenated)

The 24-task NK-test subset is recovered from the saved solver dispatches
(``logs/dispatches/solver/task_*__round1.json``); ``task_003`` is excluded,
matching ``analyze_results.py`` (its self-debug log is a 280 kB outlier
"log bomb" that distorts the median).
"""
from __future__ import annotations
import json
import pathlib
import statistics
import sys

try:
    import tiktoken
except ImportError:
    sys.exit("tiktoken is required. Install with: pip install tiktoken")

HERE = pathlib.Path(__file__).resolve().parent
LOGS = HERE / "logs"
EXCLUDE = {"003"}  # log-bomb outlier; same exclusion as analyze_results.py

ENC = tiktoken.get_encoding("cl100k_base")


def ntok(text: str) -> int:
    return len(ENC.encode(text, disallowed_special=()))


def nk_test_subset() -> list[str]:
    """The 24-task NK-test subset, identified by saved round-1 dispatches."""
    ids = []
    for p in (LOGS / "dispatches" / "solver").glob("task_*__round1.json"):
        ids.append(p.name.split("__")[0].removeprefix("task_"))
    return sorted(set(ids))


def memory_tokens_nkr_d1(tid: str) -> int | None:
    p = LOGS / "nk_records" / f"task_{tid}.json"
    return ntok(p.read_text()) if p.exists() else None


def memory_tokens_nkr_d3(tid: str) -> int | None:
    p = LOGS / "nk_records" / f"task_{tid}_deep.json"
    return ntok(p.read_text()) if p.exists() else None


def memory_tokens_self_debug(tid: str) -> int | None:
    """Self-debug shows the next attempt three artifacts from the prior round:
    candidate.py + exec.log + eval.log (the latter is often empty)."""
    d = LOGS / "self_debug_inputs" / f"task_{tid}"
    if not d.exists():
        return None
    parts = []
    for name in ("candidate.py", "exec.log", "eval.log"):
        f = d / name
        if f.exists():
            parts.append(f.read_text(errors="replace"))
    return ntok("\n".join(parts)) if parts else None


def main() -> int:
    subset = [t for t in nk_test_subset() if t not in EXCLUDE]
    print(f"NK-test subset (excluding task_003): n = {len(subset)} tasks\n")

    rows = []
    for tid in subset:
        rows.append({
            "task": tid,
            "nkr_d1": memory_tokens_nkr_d1(tid),
            "self_debug": memory_tokens_self_debug(tid),
            "nkr_d3": memory_tokens_nkr_d3(tid),
        })

    print(f"{'task':<6}{'NKR-d1':>10}{'Self-debug':>14}{'NKR-d3':>10}")
    for r in rows:
        print(f"{r['task']:<6}"
              f"{r['nkr_d1'] if r['nkr_d1'] is not None else '--':>10}"
              f"{r['self_debug'] if r['self_debug'] is not None else '--':>14}"
              f"{r['nkr_d3'] if r['nkr_d3'] is not None else '--':>10}")

    def med(col):
        xs = [r[col] for r in rows if r[col] is not None]
        return int(statistics.median(xs)) if xs else None, len(xs)

    nkr_d1, n1 = med("nkr_d1")
    sd, n2 = med("self_debug")
    nkr_d3, n3 = med("nkr_d3")

    print(f"\nMedians (cl100k_base tokens):")
    print(f"  Negative knowledge retry        {nkr_d1:>6}   (n={n1})   paper: 296")
    print(f"  Self-debug                      {sd:>6}   (n={n2})   paper: 1,109")
    print(f"  Deep negative knowledge retry   {nkr_d3:>6}   (n={n3})   paper: 795")

    print(f"\nMemory savings vs Self-debug:")
    print(f"  NKR depth-1 :  -{(1-nkr_d1/sd)*100:5.1f}%   paper: -73.3%")
    print(f"  NKR depth-3 :  -{(1-nkr_d3/sd)*100:5.1f}%   paper: -28.3%")

    expected = [
        ("Negative knowledge retry", nkr_d1, 296),
        ("Self-debug",                sd,     1109),
        ("Deep negative knowledge",   nkr_d3, 795),
    ]
    mismatch = [(n, g, e) for (n, g, e) in expected if g != e]
    if mismatch:
        print("\n  MISMATCH(es):")
        for n, g, e in mismatch:
            print(f"   - {n}: got {g}, paper says {e}")
        return 1
    print("\n  All three medians match the paper exactly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
