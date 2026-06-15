#!/usr/bin/env python3
"""Aggregate the §4 BKdV bank inside the self-contained reproduce kit.

Inputs:
- bundled 30-entry pilot legacy bank in logs/banks/pilot_legacy_*.jsonl
- 28 BKdV Stage-1 curator records from REPRO_RUNS/nk_records if present,
  otherwise the bundled logs/nk_records archive

Outputs:
- REPRO_RUNS/banks/bank_positive.jsonl
- REPRO_RUNS/banks/bank_negative.jsonl
- REPRO_RUNS/banks/bank_all.jsonl
- REPRO_RUNS/banks/bank_index.json
"""
import json

from _paths import BANKS, NK_RECORDS, RUNS


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]


def write_jsonl(path, records):
    with open(path, "w") as fh:
        for record in records:
            fh.write(json.dumps(record) + "\n")


def normalize_legacy_entry(entry, kind):
    """Normalize a v2-era bank entry into the v3 single-round NK shape."""
    return {
        "task_id": entry.get("id", "<unknown>"),
        "round": 1,
        "attempted_route": entry.get("attempted_route", ""),
        "observation": entry.get("observation", ""),
        "failure": entry.get("failure", {}),
        "rationale": entry.get("rationale", ""),
        "recommended_alternative": entry.get("applicability", ""),
        "is_trivial": False,
        "trivial_degree": 0,
        "_source": "logs/banks/pilot_legacy",
        "_v3_kind_hint": kind,
        "_v3_depth_hint": 1,
    }


def normalize_stage1_record(record, file_name):
    out = dict(record)
    out["_source"] = f"logs/nk_records/{file_name}"
    if "depth" in record:
        out["_v3_depth_hint"] = record["depth"]
    elif "round" in record:
        out["_v3_depth_hint"] = 1
    else:
        out["_v3_depth_hint"] = 1
    return out


def is_positive(record):
    failure = record.get("failure", {})
    degree = failure.get("degree", "")
    action = failure.get("recommended_action", "")

    if degree in ("contradicted", "unstable", "overclaimed",
                  "artifact_driven"):
        return False
    if action == "abandon_route":
        return False
    if action == "retry":
        return True

    alt = record.get("recommended_alternative", "").lower()
    if any(key in alt for key in ("extend", "increase amp", "test on",
                                  "continue", "scan higher")):
        return True
    return False


def resolve_stage1_records_dir():
    generated = RUNS / "nk_records"
    if any(generated.glob("*.json")):
        return generated
    return NK_RECORDS


def main():
    out_dir = RUNS / "banks"
    out_dir.mkdir(parents=True, exist_ok=True)

    legacy_pos = read_jsonl(BANKS / "pilot_legacy_positive.jsonl")
    legacy_neg = read_jsonl(BANKS / "pilot_legacy_negative.jsonl")
    normalized_pos = [normalize_legacy_entry(entry, "positive")
                      for entry in legacy_pos]
    normalized_neg = [normalize_legacy_entry(entry, "negative")
                      for entry in legacy_neg]

    nk_dir = resolve_stage1_records_dir()
    stage1_records = {
        path.name: normalize_stage1_record(json.loads(path.read_text()),
                                           path.name)
        for path in sorted(nk_dir.glob("*.json"))
    }

    stage1_pos = []
    stage1_neg = []
    for record in stage1_records.values():
        if is_positive(record):
            stage1_pos.append(record)
        else:
            stage1_neg.append(record)

    all_pos = normalized_pos + stage1_pos
    all_neg = normalized_neg + stage1_neg
    all_records = all_pos + all_neg

    write_jsonl(out_dir / "bank_positive.jsonl", all_pos)
    write_jsonl(out_dir / "bank_negative.jsonl", all_neg)
    write_jsonl(out_dir / "bank_all.jsonl", all_records)

    index = {
        "version": "v3.A",
        "built_at_utc": "2026-05-13",
        "n_positive": len(all_pos),
        "n_negative": len(all_neg),
        "n_total": len(all_records),
        "sources": {
            "pilot_legacy": {
                "positive": len(legacy_pos),
                "negative": len(legacy_neg),
            },
            "bkdv_stage1": {
                "positive": len(stage1_pos),
                "negative": len(stage1_neg),
                "record_count": len(stage1_records),
                "source_dir": str(nk_dir),
            },
        },
        "depth_distribution": {
            "depth_1_per_round_or_legacy": sum(
                1 for record in all_records
                if record.get("_v3_depth_hint", 1) == 1),
            "depth_deep_synthesis": sum(
                1 for record in all_records
                if record.get("_v3_depth_hint", 1) > 1),
        },
        "files": {
            "positive": str(out_dir / "bank_positive.jsonl"),
            "negative": str(out_dir / "bank_negative.jsonl"),
            "all": str(out_dir / "bank_all.jsonl"),
        },
    }
    (out_dir / "bank_index.json").write_text(json.dumps(index, indent=2))

    print(f"legacy: {len(legacy_pos)} positive + {len(legacy_neg)} negative")
    print(f"BKdV stage1: {len(stage1_pos)} positive + {len(stage1_neg)} negative")
    print(f"bank v3.A: {len(all_pos)} positive + {len(all_neg)} negative = {len(all_records)} total")
    print(f"wrote {out_dir}/bank_{{positive,negative,all}}.jsonl + bank_index.json")


if __name__ == "__main__":
    main()
