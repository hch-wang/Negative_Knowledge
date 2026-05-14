#!/usr/bin/env python3
"""Split knowledge_bank.jsonl into positive_knowledge.jsonl and negative_knowledge.jsonl.

This ensures the NegOnly / PosOnly / PosNeg conditions read disjoint files —
no risk of the PosOnly condition accidentally seeing negative entries.
"""
import json, pathlib

NK = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pde_pilot_2026-05-11/Negative_Knowledge")
BANK = NK / "bank" / "knowledge_bank.jsonl"
POS = NK / "bank" / "positive_knowledge.jsonl"
NEG = NK / "bank" / "negative_knowledge.jsonl"

entries = [json.loads(l) for l in open(BANK) if l.strip()]
print(f"Loaded {len(entries)} total entries from {BANK}")

pos = [e for e in entries if e["kind"] == "positive"]
neg = [e for e in entries if e["kind"] == "negative"]

with POS.open("w") as f:
    for e in pos:
        f.write(json.dumps(e) + "\n")
with NEG.open("w") as f:
    for e in neg:
        f.write(json.dumps(e) + "\n")

print(f"  → wrote {len(pos)} positive entries to {POS.name}")
print(f"  → wrote {len(neg)} negative entries to {NEG.name}")

# verify integrity: union equals original, disjoint kinds
assert len(pos) + len(neg) == len(entries), "split is non-conservative"
print(f"\nintegrity: pos + neg = {len(pos)} + {len(neg)} = {len(pos)+len(neg)} ✓ matches total")

# domain distribution check
from collections import Counter
print(f"\nPositive by domain: {dict(Counter(e['domain'] for e in pos))}")
print(f"Negative by domain: {dict(Counter(e['domain'] for e in neg))}")
