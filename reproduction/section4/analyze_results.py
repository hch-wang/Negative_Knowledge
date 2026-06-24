#!/usr/bin/env python3
"""analyze_results.py — derive every paper §4 claim from logs/.

Reads ONLY the archive under logs/; does NOT touch any API; does NOT
re-run any sub-agent. Each claim prints a one-line verdict with file
provenance.

Run:
    python3 analyze_results.py

Outputs:
    results/claim_report.md   Markdown report (claim, expected, computed, ✓/✗)
    results/claim_report.json Same data, machine-readable

Exits 0 iff every claim's computed value matches the paper.

================================================================
What this script computes (in execution order)
================================================================

(A) Stage~1 bank composition
    -- 7 BKdV-S programs (S1..S7), 3 rounds each
    -- 28 NK records produced (21 per-round depth-1 + 7 deep-synthesis)
    -- final bank = 58 entries (15 positive + 43 negative)
    -- 30 entries from the legacy pilot bank (single-shot, depth-1)
    -- 28 entries from the BKdV-S programs (multi-round)
    -- 7 deep-synthesis records (one per program)

(B) Stage~2 — phenomenon-aware eval, 12 cells (3 tasks × 4 conditions)
    -- NoKB     0/3
    -- PosOnly  1/3  (T-C only)
    -- NegOnly  3/3  ★ headline: prescriptive negatives carry actionable content
    -- PosNeg   3/3  (robust)

(C) Eval threshold derivation
    -- T-A amp_ratio threshold: 0.25 (corrected from a 0.5 that was
       physically unattainable per BKdV-S7)
    -- T-A coherence: single-dominant-peak requirement

(D) BKdV-S6 and BKdV-S7 specifics
    -- S6 prescription: nu_linear=5e-2 (or nu_h=1e-9 for k^8 hyperviscosity)
    -- S6: BKdV-S4 safe envelope underestimates by 13 orders of magnitude
    -- S7: cosine similarity 0.94 between predicted and observed m-spectrum
    -- S7: 62.8% v_max decay for sech^2 IC at A=1.5 over T=10
================================================================
"""
from __future__ import annotations
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))
from _paths import (REPRO_ROOT, LOGS, NK_RECORDS, BANKS, VERIFIED_RESULTS,
                    STAGE1_RUNS, STAGE2_RUNS,
                    STAGE2_TASKS, STAGE2_CONDS, RESULTS)


CLAIMS = []


def check(label, expected, computed, source=""):
    match = expected == computed
    CLAIMS.append({"label": label, "expected": expected, "computed": computed,
                   "match": match, "source": source})
    mark = "✓" if match else "✗"
    print(f"  {mark} {label:<60s} expected={expected!r:<14s} got={computed!r}")


def load_nk_records():
    return {p.stem: json.load(open(p)) for p in sorted(NK_RECORDS.glob("*.json"))}


def load_bank(name):
    return [json.loads(line) for line in open(BANKS / f"{name}.jsonl") if line.strip()]


def pass_rate_by_cond(rows):
    counts = {c: 0 for c in STAGE2_CONDS}
    for r in rows:
        cond = r.get("cond") or r.get("condition")
        if r.get("useful") and cond in counts:
            counts[cond] += 1
    return counts


def count_iterations(state_path):
    if not state_path.exists():
        return 0
    n = 0
    for line in state_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("node_type") == "Experiment":
            n += 1
    return n


def analyze():
    print("=" * 75)
    print(f"Analyzing §4 logs at: {LOGS.relative_to(REPRO_ROOT)}")
    print("=" * 75)

    # ==== (A) Stage 1 bank composition ====
    print("\n(A) Stage~1 bank composition")
    print("    Derived from logs/nk_records/, logs/banks/, logs/stage1/.")

    n_programs = sum(1 for p in STAGE1_RUNS.glob("BKdV-S*") if p.is_dir())
    check("Stage 1 program count", 7, n_programs, "logs/stage1/BKdV-S*/")

    nk = load_nk_records()
    check("Stage 1 NK records total", 28, len(nk), "logs/nk_records/*.json")
    n_perround = sum(1 for k in nk if "_r" in k and "_deep" not in k)
    n_deep = sum(1 for k in nk if "_deep" in k)
    check("  per-round (depth-1) records", 21, n_perround, "*_r{1,2,3}.json")
    check("  deep-synthesis records", 7, n_deep, "*_deep.json")

    bank_all = load_bank("bank_all")
    bank_pos = load_bank("bank_positive")
    bank_neg = load_bank("bank_negative")
    check("Final bank total entries", 58, len(bank_all), "logs/banks/bank_all.jsonl")
    check("  positive entries", 15, len(bank_pos), "bank_positive.jsonl")
    check("  negative entries", 43, len(bank_neg), "bank_negative.jsonl")
    n_deep_in_bank = sum(1 for r in bank_all if r.get("_v3_depth_hint", 1) >= 2)
    check("  deep entries in bank (depth ≥ 2)", 7, n_deep_in_bank,
          "bank entries with depth hint ≥ 2")

    # Legacy pilot inputs (30 entries that aggregate_bank.py merges in)
    legacy_pos = load_bank("pilot_legacy_positive")
    legacy_neg = load_bank("pilot_legacy_negative")
    check("  legacy pilot positive (input)", 10, len(legacy_pos), "pilot_legacy_positive.jsonl")
    check("  legacy pilot negative (input)", 20, len(legacy_neg), "pilot_legacy_negative.jsonl")

    # ==== (B) Stage 2 results ====
    print("\n(B) Stage~2 PASS rate (physics-aware eval, 58-entry bank)")

    rows = json.loads((VERIFIED_RESULTS / "verified_results.json").read_text())
    pr = pass_rate_by_cond(rows)
    check("NoKB    PASS/3", 0, pr["NoKB"],    "verified_results.json")
    check("PosOnly PASS/3", 1, pr["PosOnly"], "verified_results.json")
    check("NegOnly PASS/3", 3, pr["NegOnly"], "verified_results.json")
    check("PosNeg  PASS/3", 3, pr["PosNeg"],  "verified_results.json")
    print(f"\n    Headline: NegOnly matches PosNeg at 3/3 with a negative-only "
          f"bank; NoKB stays at 0/3 across all three tasks; PosOnly clears only "
          f"T-C. Prescriptive negative entries carry actionable content.")

    # ==== (C) Phenomenon-check threshold ====
    print("\n(C) Phenomenon-check threshold (T-A)")
    pc_src = (HERE / "scripts" / "phenomenon_checks.py").read_text()
    check("T-A amp_ratio threshold = 0.25", True, 'amp_ratio"] >= 0.25' in pc_src,
          "scripts/phenomenon_checks.py")
    check("T-A single-dominant-peak check present", True,
          "is_single_dominant" in pc_src, "scripts/phenomenon_checks.py")

    # ==== (D) BKdV-S6, S7 specifics from their deep NK records ====
    print("\n(D) BKdV-S6 and BKdV-S7 specifics (from logs/nk_records/*_deep.json)")

    s6 = json.dumps(nk["BKdV-S6_deep"], default=str)
    s7 = json.dumps(nk["BKdV-S7_deep"], default=str)
    check("S6 prescribes nu_linear=5e-2 (or 0.05)", True,
          "5e-2" in s6 or "0.05" in s6 or "5\\cdot 10^{-2}" in s6,
          "BKdV-S6_deep.json")
    check("S6 vs BKdV-S4 envelope: 13 orders too weak", True,
          "13 orders" in s6, "BKdV-S6_deep.json")
    check("S7 reports -62.8% v_max decay", True, "62.8" in s7, "BKdV-S7_deep.json")
    check("S7 reports cos-sim 0.94 prediction", True, "0.94" in s7, "BKdV-S7_deep.json")

    # ==== (E) Sample iteration counts ====
    print("\n(E) Per-cell iteration counts (one Experiment node = one iteration)")
    for c in STAGE2_CONDS:
        for t in STAGE2_TASKS:
            cell = STAGE2_RUNS / t / c
            n = count_iterations(cell / "research_state.jsonl")
            r = next((r for r in rows if r["task"] == t and
                      (r.get("cond") or r.get("condition")) == c), None)
            verdict = "PASS" if r and r["useful"] else "FAIL"
            print(f"    {t}/{c:8s} iter={n}  {verdict}")

    # ==== Summary ====
    n_total = len(CLAIMS)
    n_match = sum(1 for c in CLAIMS if c["match"])
    print()
    print("=" * 75)
    print(f"  {n_match}/{n_total} claims match")
    print("=" * 75)

    RESULTS.mkdir(exist_ok=True)
    md = ["# Section 4 claim verification report", "",
          f"**{n_match}/{n_total} claims match.**", "",
          "| ✓/✗ | Claim | Expected | Computed | Source |",
          "|---|---|---|---|---|"]
    for c in CLAIMS:
        mark = "✓" if c["match"] else "✗"
        md.append(f"| {mark} | {c['label']} | `{c['expected']!r}` | `{c['computed']!r}` | {c['source']} |")
    (RESULTS / "claim_report.md").write_text("\n".join(md) + "\n")
    (RESULTS / "claim_report.json").write_text(json.dumps(CLAIMS, indent=2, default=str))
    print(f"\nwrote {RESULTS / 'claim_report.md'}")
    print(f"wrote {RESULTS / 'claim_report.json'}")

    return n_match == n_total


if __name__ == "__main__":
    sys.exit(0 if analyze() else 1)
