#!/usr/bin/env python3
"""count_tokens.py — verify the three token figures in Table 1 of the paper.

Table 1 reports memory-object size in tokens, measured with the
``cl100k_base`` tokenizer:

    Negative knowledge retry (depth-1)   296 tokens   (-73.3% vs self-debug)
    Self-debug                         1,109 tokens   (baseline)
    Deep negative knowledge (depth-3)    795 tokens   (-28.3%)

The per-task token counts are precomputed and shipped as
``logs/memory_tokens.json`` (the token-side analogue of the existing
``logs/b2_covering_bytes.json`` byte file). This script reads that JSON,
recomputes the three medians and the savings, and exits 0 iff they
match the paper.

Run (no install required, no LLM API):
    python3 count_tokens.py

The shipped ``logs/self_debug_inputs/`` directory contains the raw
self-debug artifacts (``candidate.py`` + ``exec.log`` + ``eval.log`` for
each task) so that the JSON can be re-derived from primary inputs:
    pip install tiktoken
    python3 count_tokens.py --regenerate

``task_003`` is excluded throughout, matching ``analyze_results.py``
(its self-debug log is a 280 kB outlier "log bomb" that distorts the
median).
"""
from __future__ import annotations
import argparse
import json
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
LOGS = HERE / "logs"
JSON_PATH = LOGS / "memory_tokens.json"
EXCLUDE = {"003"}


def regenerate() -> int:
    """Re-derive logs/memory_tokens.json from the raw artifacts."""
    try:
        import tiktoken
    except ImportError:
        sys.exit("--regenerate needs tiktoken: pip install tiktoken")
    enc = tiktoken.get_encoding("cl100k_base")
    def ntok(s: str) -> int: return len(enc.encode(s, disallowed_special=()))

    sys.path.insert(0, str(HERE / "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("ar", HERE / "analyze_results.py")
    ar = importlib.util.module_from_spec(spec); spec.loader.exec_module(ar)
    nk24 = ar.all_tasks_in_cell(ar.load_solver_dispatches(LOGS), "primary_4.6", "round1")

    out: dict = {"tokenizer": "cl100k_base", "per_task": {}}
    for tid in sorted(nk24):
        rec: dict = {}
        p1 = LOGS / "nk_records" / f"task_{tid}.json"
        if p1.exists():
            rec["nkr_d1"] = ntok(p1.read_text())
        p3 = LOGS / "nk_records" / f"task_{tid}_deep.json"
        if p3.exists():
            rec["nkr_d3"] = ntok(p3.read_text())
        sd = LOGS / "self_debug_inputs" / f"task_{tid}"
        if sd.exists():
            parts = []
            for name in ("candidate.py", "exec.log", "eval.log"):
                p = sd / name
                if p.exists():
                    parts.append(p.read_text(errors="replace"))
            if parts:
                rec["self_debug"] = ntok("\n".join(parts))
        out["per_task"][tid] = rec
    JSON_PATH.write_text(json.dumps(out, indent=2, sort_keys=True))
    print(f"wrote {JSON_PATH.relative_to(HERE)} ({len(out['per_task'])} tasks)")
    return 0


def verify() -> int:
    if not JSON_PATH.exists():
        sys.exit(f"missing {JSON_PATH.relative_to(HERE)}; run with --regenerate")
    data = json.loads(JSON_PATH.read_text())
    print(f"tokenizer: {data.get('tokenizer', '?')}")
    per_task = data["per_task"]
    rows = sorted(
        (tid, rec) for tid, rec in per_task.items() if tid not in EXCLUDE
    )
    print(f"NK-test subset (excluding task_003): n = {len(rows)} tasks\n")

    print(f"{'task':<6}{'NKR-d1':>10}{'Self-debug':>14}{'NKR-d3':>10}")
    for tid, r in rows:
        print(f"{tid:<6}"
              f"{r.get('nkr_d1', '--'):>10}"
              f"{r.get('self_debug', '--'):>14}"
              f"{r.get('nkr_d3', '--'):>10}")

    def med(col: str):
        xs = [r[col] for _, r in rows if col in r]
        return (int(statistics.median(xs)) if xs else None, len(xs))

    nkr_d1, n1 = med("nkr_d1")
    sd, n2     = med("self_debug")
    nkr_d3, n3 = med("nkr_d3")

    print(f"\nMedians (cl100k_base tokens):")
    print(f"  Negative knowledge retry        {nkr_d1:>6}   (n={n1})   paper: 296")
    print(f"  Self-debug                      {sd:>6}   (n={n2})   paper: 1,109")
    print(f"  Deep negative knowledge retry   {nkr_d3:>6}   (n={n3})   paper: 795")

    print(f"\nMemory savings vs Self-debug:")
    print(f"  NKR depth-1 :  -{(1 - nkr_d1/sd)*100:5.1f}%   paper: -73.3%")
    print(f"  NKR depth-3 :  -{(1 - nkr_d3/sd)*100:5.1f}%   paper: -28.3%")

    expected = [("Negative knowledge retry", nkr_d1, 296),
                ("Self-debug",               sd,     1109),
                ("Deep negative knowledge",  nkr_d3, 795)]
    bad = [(n, g, e) for (n, g, e) in expected if g != e]
    if bad:
        print("\n  MISMATCH(es):")
        for n, g, e in bad:
            print(f"   - {n}: got {g}, paper says {e}")
        return 1
    print("\n  All three medians match the paper exactly.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--regenerate", action="store_true",
                    help="Re-derive logs/memory_tokens.json from raw "
                         "artifacts (requires `pip install tiktoken`).")
    args = ap.parse_args()
    return regenerate() if args.regenerate else verify()


if __name__ == "__main__":
    sys.exit(main())
