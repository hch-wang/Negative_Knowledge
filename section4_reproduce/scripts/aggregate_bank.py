#!/usr/bin/env python3
"""Aggregate bank_v3.A: existing 30 entries + 20 new BKdV stage-1 NK records.

Output layout (under stage1_v3/bank/):
- bank_v3A_all.jsonl              -- all 50 records, one per line
- bank_v3A_positive.jsonl         -- positive-flavored subset for PosOnly condition
- bank_v3A_negative.jsonl         -- negative-flavored subset for NegOnly condition
- bank_v3A_index.json             -- index with depth tags, source, kind

The split positive vs negative is based on:
- recommended_action: "retry" or general positive notes -> positive
- otherwise -> negative
- Existing 30 entries already split in section4/stage1/bank/{positive,negative}_knowledge.jsonl
- New 20 entries split by inspection of failure.degree (overclaimed/contradicted/unstable -> negative; partial -> case by case)
"""
import json
import pathlib

ROOT = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4")
STAGE1_OLD = ROOT / "stage1" / "bank"
STAGE1_V3 = ROOT / "stage1_v3"
NK_RECORDS = STAGE1_V3 / "nk_records"
BANK_OUT = STAGE1_V3 / "bank"
BANK_OUT.mkdir(exist_ok=True)


def normalize_old_entry(e, kind):
    """Normalize a v2-era entry to v3 single-round NK schema (section-3-compatible)."""
    return {
        "task_id": e.get("id", "<unknown>"),
        "round": 1,
        "attempted_route": e.get("attempted_route", ""),
        "observation": e.get("observation", ""),
        "failure": e.get("failure", {}),
        "rationale": e.get("rationale", ""),
        "recommended_alternative": e.get("applicability", ""),  # old "applicability" carried prescriptive content
        "is_trivial": False,
        "trivial_degree": 0,
        # provenance
        "_source": "section4/stage1/bank (v2 era)",
        "_v3_kind_hint": kind,
        "_v3_depth_hint": 1,
    }


def normalize_new_entry(rec, file_name):
    """Stage-1 v3 records already match v3 schema. Add provenance."""
    out = dict(rec)
    out["_source"] = f"section4/stage1_v3/nk_records/{file_name}"
    # depth hint
    if "depth" in rec:
        out["_v3_depth_hint"] = rec["depth"]
    elif "round" in rec:
        out["_v3_depth_hint"] = 1
    else:
        out["_v3_depth_hint"] = 1
    return out


# ----- Load existing 30 -----
old_pos = [json.loads(l) for l in (STAGE1_OLD / "positive_knowledge.jsonl").read_text().splitlines() if l.strip()]
old_neg = [json.loads(l) for l in (STAGE1_OLD / "negative_knowledge.jsonl").read_text().splitlines() if l.strip()]
print(f"existing: {len(old_pos)} positive + {len(old_neg)} negative")

normalized_pos = [normalize_old_entry(e, "positive") for e in old_pos]
normalized_neg = [normalize_old_entry(e, "negative") for e in old_neg]

# ----- Load new 20 BKdV records -----
new_records = {}
for f in sorted(NK_RECORDS.glob("*.json")):
    rec = json.loads(f.read_text())
    new_records[f.name] = normalize_new_entry(rec, f.name)
print(f"new BKdV: {len(new_records)} records ({sum(1 for r in new_records.values() if r.get('_v3_depth_hint') == 1)} depth-1, {sum(1 for r in new_records.values() if r.get('_v3_depth_hint', 1) > 1)} deep)")

# ----- Split new 20 into pos/neg by failure.degree -----
# Heuristic: if observation/diagnosis indicates working/positive outcome -> positive
# Specifically check failure.degree and synthesised_diagnosis sentiment
POSITIVE_DEGREES = {"partial"}  # partial often = "ran cleanly but bounded result"; case by case
def is_positive(rec):
    f = rec.get("failure", {})
    deg = f.get("degree", "")
    action = f.get("recommended_action", "")
    # Strong signals of negative
    if deg in ("contradicted", "unstable", "overclaimed", "artifact_driven"):
        return False
    if action == "abandon_route":
        return False
    # Positive if recommended_action is retry (proceed similarly)
    if action == "retry":
        return True
    # Check recommended_alternative phrasing — if it says "extend" -> positive
    rec_alt = rec.get("recommended_alternative", "").lower()
    if any(k in rec_alt for k in ("extend", "increase amp", "test on", "continue", "scan higher")):
        return True
    # Default: treat as negative
    return False

new_pos = []
new_neg = []
for name, rec in new_records.items():
    if is_positive(rec):
        new_pos.append(rec)
    else:
        new_neg.append(rec)
print(f"new split: {len(new_pos)} positive + {len(new_neg)} negative")

# ----- Combine -----
all_pos = normalized_pos + new_pos
all_neg = normalized_neg + new_neg
all_records = all_pos + all_neg

print(f"\nbank_v3.A: {len(all_pos)} positive + {len(all_neg)} negative = {len(all_records)} total")

# ----- Write outputs -----
def write_jsonl(path, records):
    with open(path, "w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")

write_jsonl(BANK_OUT / "bank_v3A_positive.jsonl", all_pos)
write_jsonl(BANK_OUT / "bank_v3A_negative.jsonl", all_neg)
write_jsonl(BANK_OUT / "bank_v3A_all.jsonl", all_records)

# ----- Index -----
index = {
    "version": "v3.A",
    "built_at_utc": "2026-05-13",
    "n_positive": len(all_pos),
    "n_negative": len(all_neg),
    "n_total": len(all_records),
    "sources": {
        "section4_stage1": {"positive": len(old_pos), "negative": len(old_neg)},
        "section4_stage1_v3": {"positive": len(new_pos), "negative": len(new_neg), "per_round_count": 15, "deep_count": 5},
    },
    "depth_distribution": {
        "depth_1_per_round_or_v2_legacy": sum(1 for r in all_records if r.get("_v3_depth_hint", 1) == 1),
        "depth_deep_synthesis": sum(1 for r in all_records if r.get("_v3_depth_hint", 1) > 1),
    },
    "files": {
        "positive": str(BANK_OUT / "bank_v3A_positive.jsonl"),
        "negative": str(BANK_OUT / "bank_v3A_negative.jsonl"),
        "all": str(BANK_OUT / "bank_v3A_all.jsonl"),
    },
}
(BANK_OUT / "bank_v3A_index.json").write_text(json.dumps(index, indent=2))
print(f"\nwrote {BANK_OUT}/{{bank_v3A_all,bank_v3A_positive,bank_v3A_negative}}.jsonl + bank_v3A_index.json")
print(json.dumps(index, indent=2))
