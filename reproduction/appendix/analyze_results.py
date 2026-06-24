#!/usr/bin/env python3
"""Mode A — verify saved logs reproduce the paper-appendix claims.

Reads logs/verified_results.json and the bundled per-cell verified_eval.json
files, then checks each numerical / qualitative claim made in the appendix.

Usage:
  python3 analyze_results.py

Exit code 0 if all claims match; non-zero on mismatch. Detailed report
written to results/claim_report.md.
"""
import importlib.util
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "scripts"))
from _paths import (
    REPRO_ROOT, RESULTS_DIR, LOGS_DIR, VERIFIED_RESULTS,
    BANK_NLS, BANK_BKDV_POS, BANK_BKDV_NEG,
    STAGE3_LOGS, STAGE1_BNLS_LOGS, PHENOM_CHECKS,
    CONDITIONS, TASKS, cell_dir,
)

# Load eval module so we can re-run phenomenon checks if needed
spec = importlib.util.spec_from_file_location("pc", PHENOM_CHECKS)
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)


def jload(p):
    return json.loads(pathlib.Path(p).read_text())


def jlines(p):
    return [json.loads(l) for l in open(p) if l.strip()]


class ClaimReport:
    def __init__(self):
        self.rows = []

    def check(self, claim, expected, actual, evidence_path):
        ok = expected == actual
        self.rows.append({
            "claim": claim, "expected": expected, "actual": actual,
            "match": ok, "evidence": str(evidence_path),
        })
        return ok

    def summarize(self):
        n_match = sum(1 for r in self.rows if r["match"])
        n_total = len(self.rows)
        return n_match, n_total

    def write_markdown(self, path):
        n_match, n_total = self.summarize()
        lines = [f"# Appendix-reproduce claim report\n\n",
                 f"**{n_match}/{n_total} claims match.**\n\n",
                 "| # | Claim | Expected | Actual | Match | Evidence |\n",
                 "|---|---|---|---|---|---|\n"]
        for i, r in enumerate(self.rows, 1):
            mark = "✓" if r["match"] else "✗"
            lines.append(f"| {i} | {r['claim']} | {r['expected']} | {r['actual']} | {mark} | `{r['evidence']}` |\n")
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(path).write_text("".join(lines))


def main():
    report = ClaimReport()

    # ---- Bank composition claims (Section §1) ----
    nls_entries = jlines(BANK_NLS)
    n_nls = len(nls_entries)
    n_struct = sum(1 for e in nls_entries if e.get("depth") == "structural")
    n_family = sum(1 for e in nls_entries if e.get("depth") == "family-level")
    report.check("NLS bank size (21 entries)", 21, n_nls, BANK_NLS)
    report.check("NLS bank — structural depth count", 2, n_struct, BANK_NLS)
    report.check("NLS bank — family-level depth count", 4, n_family, BANK_NLS)

    bkdv_pos = jlines(BANK_BKDV_POS)
    bkdv_neg = jlines(BANK_BKDV_NEG)
    report.check("BKdV positive bank size", 10, len(bkdv_pos), BANK_BKDV_POS)
    report.check("BKdV negative bank size", 20, len(bkdv_neg), BANK_BKDV_NEG)

    # ---- Verified results table (Section §1.1) ----
    rows = jload(VERIFIED_RESULTS)
    pass_by_cond = {c: sum(1 for r in rows if r["condition"] == c and r["useful"]) for c in CONDITIONS}
    report.check("NoKB pass rate", 0, pass_by_cond["NoKB"], VERIFIED_RESULTS)
    report.check("BKdV pass rate", 2, pass_by_cond["BKdV"], VERIFIED_RESULTS)
    report.check("NLS pass rate", 3, pass_by_cond["NLS"], VERIFIED_RESULTS)
    report.check("NLSBKdV pass rate", 3, pass_by_cond["NLSBKdV"], VERIFIED_RESULTS)

    # Per-task verdicts
    expected_grid = {
        ("T_A", "NoKB"): False, ("T_A", "BKdV"): True,
        ("T_A", "NLS"): True, ("T_A", "NLSBKdV"): True,
        ("T_B", "NoKB"): False, ("T_B", "BKdV"): False,
        ("T_B", "NLS"): True, ("T_B", "NLSBKdV"): True,
        ("T_C", "NoKB"): False, ("T_C", "BKdV"): False,
        ("T_C", "NLS"): True, ("T_C", "NLSBKdV"): True,
        ("T_D", "NoKB"): False, ("T_D", "BKdV"): True,
        ("T_D", "NLS"): False, ("T_D", "NLSBKdV"): False,
    }
    for (task, cond), expected in expected_grid.items():
        actual = next(r["useful"] for r in rows if r["task"] == task and r["condition"] == cond)
        report.check(f"verdict {task}/{cond}", expected, actual, VERIFIED_RESULTS)

    # ---- Negative-transfer signature (T_B BKdV << T_B NoKB; Section §2b.1) ----
    # The signature is that T_B/BKdV blew up unboundedly (u_max ~ 100s) while
    # T_B/NoKB stayed bounded (u_max < 1) but padded — both fail, but in
    # opposite directions: BKdV agent had "false confidence" from a wrong
    # bank entry and pushed the method into UV cascade.
    nokb_TB = next(r for r in rows if r["task"] == "T_B" and r["condition"] == "NoKB")["diag"]
    bkdv_TB = next(r for r in rows if r["task"] == "T_B" and r["condition"] == "BKdV")["diag"]
    report.check("T_B/NoKB stays bounded (no UV cascade — slow failure)",
                 True, bool(nokb_TB.get("bounded", False)), VERIFIED_RESULTS)
    report.check("T_B/BKdV becomes unbounded (UV cascade from misleading bank entry)",
                 True, not bool(bkdv_TB.get("bounded", True)), VERIFIED_RESULTS)
    report.check("T_B/BKdV u-field magnitude >> T_B/NoKB (140× degradation signature)",
                 True, bkdv_TB.get("u_max_abs", 0) > 100 * nokb_TB.get("u_max_abs", 1),
                 VERIFIED_RESULTS)

    # ---- T_D BKdV conservative truncation kept mass drift < 5% (Section §2b.2) ----
    td_bkdv_mass = next(r for r in rows if r["task"] == "T_D" and r["condition"] == "BKdV")["diag"]["mass_drift_rel"]
    report.check("T_D/BKdV mass drift below 5% gate", True, td_bkdv_mass < 0.05, VERIFIED_RESULTS)
    td_nls_mass = next(r for r in rows if r["task"] == "T_D" and r["condition"] == "NLS")["diag"]["mass_drift_rel"]
    report.check("T_D/NLS mass drift exceeds 5% gate", True, td_nls_mass >= 0.05, VERIFIED_RESULTS)

    # ---- Stage 1 stress test artifacts present ----
    for s in ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]:
        kf = STAGE1_BNLS_LOGS / s / "knowledge_findings.json"
        report.check(f"Stage 1 {s} knowledge_findings.json present", True, kf.exists(), kf)

    # ---- Stage 3 cell artifacts present ----
    for task in TASKS:
        for cond in CONDITIONS:
            npy = cell_dir(task, cond) / "pred_results" / f"{task}.npy"
            report.check(f"Stage 3 {task}/{cond} pred_results .npy present",
                         True, npy.exists(), npy)

    # ---- Write report and exit ----
    report_path = RESULTS_DIR / "claim_report.md"
    report.write_markdown(report_path)
    n_match, n_total = report.summarize()
    print(f"{n_match}/{n_total} claims match")
    print(f"detailed report: {report_path}")

    if n_match < n_total:
        print("\n--- mismatches ---")
        for r in report.rows:
            if not r["match"]:
                print(f"  ✗ {r['claim']}  expected={r['expected']}  actual={r['actual']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
