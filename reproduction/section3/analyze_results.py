#!/usr/bin/env python3
"""analyze_results.py — recompute the main §3 evaluation table from logs/.

This script reads ONLY the archive under logs/ and recomputes the
headline ScienceAgentBench pass-rate and memory table, together with
count-based provenance checks. It does NOT touch the Anthropic API; it
does NOT re-run any sub-agent. Each check prints a one-line provenance
noting the files it was computed from, so a reader can independently
re-derive it by hand.

Run:
    python analyze_results.py
    python analyze_results.py --logs /custom/path/to/logs

Outputs:
    results/claim_report.md     Markdown report: paper table + provenance checks
    results/claim_report.json   Same data, JSON for machine consumption

Exits 0 iff every provenance check matches the archived data.

================================================================
What this script computes (in execution order)
================================================================

(A) Subset sizes
    -- pilot subset size (38)
    -- baseline round-1 PASS count (12, from logs/baseline_results/)
    -- NK-test subset size (24, from the v3 round1 cell in dispatches/solver/)
    -- hard subset size (19, those for which B2 covering also fails all 3 rounds)

(B) Benchmark-wide PASS rate (Table 1 in paper)
    -- baseline           12/38  31.6%
    -- + B0 retry          12/38  31.6% (no lift)
    -- + NKR depth-1       14/38  36.8%
    -- + B2 covering       17/38  44.7%
    -- + deepNKR depth-3   18/38  47.4%  ★ headline lift = +6 tasks

(C) Controlled view
    -- NKR depth-1 on 24:           2/24
    -- B2 covering on 24:           5/24
    -- deepNKR-Sonnet on 19 hard:   1/19  ★ depth-3 breakthrough
    -- deepNKR-Haiku on 19 hard:    0/19  ★ cross-model bound

(D) Memory bytes (median per task, n=23 excluding task_003's log bomb)
    -- B2 covering:        4,272 bytes
    -- r1 NK (depth-1):    1,187 bytes  (72.2% smaller than B2)
    -- deep NK (depth-3):  3,354 bytes  (21.5% smaller than B2)

(E) Solver tokens per dispatch (median)
    -- round-1 baseline:   16,262
    -- NKR (depth-1):      18,080
    -- deepNKR Sonnet:     19,247
    -- deepNKR Haiku:      48,360  ★ 2.5x Sonnet's cost on same NK

(F) NK error rate (r2 curator self-report)
    -- correct_but_insufficient:  13
    -- new_failure_mode:           7
    -- round1_recipe_was_wrong:    2  ★ 9.1% NK error rate
    -- misapplied:                 0

(G) task_072 verification
    -- The single deepNKR-Sonnet PASS on the hard 19. The depth-3 NK
       diagnosed "CPU-bound tensor arithmetic, not iteration count"
       across 3 rounds of PyTorch U-Net timeouts, recommended
       numpy.linalg.lstsq closed-form regression; the Sonnet solver
       implemented it and PASSed.
================================================================
"""
from __future__ import annotations
import argparse
import json
import pathlib
import statistics
import sys
from collections import defaultdict, Counter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))
from _paths import REPRO_ROOT, LOGS, TASKS


# --------------------------------------------------------------------
# Claim-tracking infrastructure
# --------------------------------------------------------------------

CLAIMS = []  # list of dicts: label, expected, computed, match, source


def check(label: str, expected, computed, source: str = ""):
    """Record a claim. Print one-line verdict immediately."""
    match = expected == computed
    CLAIMS.append({
        "label": label,
        "expected": expected,
        "computed": computed,
        "match": match,
        "source": source,
    })
    mark = "✓" if match else "✗"
    exp_s = repr(expected)
    got_s = repr(computed)
    print(f"  {mark} {label:<55s} expected={exp_s:<15s} got={got_s}")


# --------------------------------------------------------------------
# Archive readers
# --------------------------------------------------------------------

def load_solver_dispatches(logs: pathlib.Path) -> list:
    return [json.load(open(p)) for p in
            sorted((logs / "dispatches" / "solver").glob("*.json"))]


def load_baseline_pass(logs: pathlib.Path) -> set:
    out = set()
    base_dir = logs / "baseline_results"
    if not base_dir.exists():
        return out
    for p in sorted(base_dir.glob("task_*.json")):
        r = json.load(open(p))
        if r.get("eval_score") == 1 or r.get("eval_score") == "1":
            out.add(p.stem.replace("task_", ""))
    return out


def passes_by_cell(solvers):
    out = defaultdict(set)
    for d in solvers:
        if d["execution"].get("eval_score") == 1:
            out[(d["model_dir"], d["cell"])].add(d["task_id"])
    return out


def all_tasks_in_cell(solvers, model_dir, cell):
    return {d["task_id"] for d in solvers
            if d["model_dir"] == model_dir and d["cell"] == cell}


# --------------------------------------------------------------------
# Main analysis
# --------------------------------------------------------------------

def analyze(logs: pathlib.Path):
    logs = logs.resolve()
    try:
        logs_display = logs.relative_to(REPRO_ROOT)
    except ValueError:
        logs_display = logs

    print("=" * 70)
    print(f"Analyzing §3 logs at: {logs_display}")
    print("=" * 70)

    solvers = load_solver_dispatches(logs)
    baseline_pass = load_baseline_pass(logs)
    print(f"\nLoaded {len(solvers)} solver dispatch records, "
          f"{len(baseline_pass)} baseline-PASS tasks.\n")

    # ============== (A) Subset sizes ==============
    print("(A) Subset sizes")
    print("    Derived from logs/baseline_results/ and v3 round1 cell.")

    pilot_38 = {f"{json.load(open(p))['instance_id']:03d}"
                for p in sorted(TASKS.glob("task_*.json"))}
    check("pilot subset size", 38, len(pilot_38), "tasks/")

    check("baseline round-1 PASS (38 tasks)", 12, len(baseline_pass),
          "logs/baseline_results/task_*.json with eval_score==1")

    nk_test_24 = all_tasks_in_cell(solvers, "sonnet_4.6", "round1")
    check("NK-test subset size", 24, len(nk_test_24),
          "v3 round1 cell in logs/dispatches/solver/")

    b2_any = (passes_by_cell(solvers)[("sonnet_4.6", "round2_B2")] |
              passes_by_cell(solvers)[("sonnet_4.6", "round3_B2")])
    hard_19 = nk_test_24 - b2_any
    check("hard subset size (B2 fails all 3 rounds)", 19, len(hard_19),
          "round2_B2 + round3_B2 cells")

    # ============== (B) Benchmark-wide PASS (Table 1) ==============
    print("\n(B) Benchmark-wide PASS rate (Table 1 in paper)")
    print("    Each line *adds* the corresponding memory component to baseline.")

    pass_b0 = passes_by_cell(solvers)[("sonnet_4.6", "round2_B0")]
    pass_nkr = passes_by_cell(solvers)[("sonnet_4.6", "round2_NKR")]
    pass_deep = passes_by_cell(solvers)[("sonnet_4.6", "deepNKR_sonnet")]

    cum_baseline = baseline_pass
    cum_b0 = cum_baseline | pass_b0
    cum_nkr = cum_b0 | pass_nkr
    cum_b2 = cum_nkr | b2_any
    cum_deep = cum_b2 | pass_deep

    check("Table 1: baseline / 38", "12/38",
          f"{len(cum_baseline)}/38", "baseline_results/")
    check("Table 1: + B0 retry / 38", "12/38",
          f"{len(cum_b0)}/38", "round2_B0 cell")
    check("Table 1: + NKR depth-1 / 38", "14/38",
          f"{len(cum_nkr)}/38", "round2_NKR cell")
    check("Table 1: + B2 covering / 38", "17/38",
          f"{len(cum_b2)}/38", "round2_B2 + round3_B2 cells")
    check("Table 1: + deepNKR depth-3 / 38", "18/38",
          f"{len(cum_deep)}/38", "deepNKR_sonnet cell")

    print(f"\n    Headline lift: {len(cum_deep) - len(cum_baseline):+d} tasks "
          f"({len(cum_baseline)/38*100:.1f}% → {len(cum_deep)/38*100:.1f}%) "
          f"— entirely from the memory protocol (B0 retry adds 0).")

    check("headline: baseline %", "31.6",
          f"{len(cum_baseline)/38*100:.1f}", "(B) cumulative")
    check("headline: final %", "47.4",
          f"{len(cum_deep)/38*100:.1f}", "(B) cumulative")
    check("headline: lift (tasks)", "+6",
          f"+{len(cum_deep) - len(cum_baseline)}", "(B) cumulative")

    # ============== (C) Controlled view ==============
    print("\n(C) Controlled view (denominator = NK-test subset, isolates memory)")

    check("NKR depth-1 on 24", "2/24",
          f"{len(pass_nkr & nk_test_24)}/24", "round2_NKR cell")
    check("B2 covering on 24", "5/24",
          f"{len(b2_any & nk_test_24)}/24",
          "round2_B2 + round3_B2 cells")
    check("deepNKR-Sonnet on 19 hard", "1/19",
          f"{len(pass_deep & hard_19)}/19",
          "deepNKR_sonnet cell on hard subset")

    pass_haiku = passes_by_cell(solvers)[("haiku_4.5", "deepNKR_haiku")]
    check("deepNKR-Haiku (cross-model) on 19 hard", "0/19",
          f"{len(pass_haiku & hard_19)}/19",
          "deepNKR_haiku cell")

    # ============== (D) Memory bytes ==============
    print("\n(D) Memory byte efficiency (median per task, n=23 ex task_003)")

    def fsize(p):
        return p.stat().st_size if p.exists() else 0

    nkr_sizes, deep_sizes = [], []
    for tid in sorted(nk_test_24):
        if tid == "003":
            continue
        p1 = logs / "nk_records" / f"task_{tid}.json"
        p3 = logs / "nk_records" / f"task_{tid}_deep.json"
        if p1.exists():
            nkr_sizes.append(fsize(p1))
        if p3.exists():
            deep_sizes.append(fsize(p3))

    b2_bytes_path = logs / "b2_covering_bytes.json"
    if b2_bytes_path.exists():
        b2_map = json.load(open(b2_bytes_path))
        b2_sizes = [v for k, v in b2_map.items() if k != "003"]
        b2_m = int(statistics.median(b2_sizes))
        check("B2 covering median (bytes/task)", 4272, b2_m,
              "b2_covering_bytes.json")

    nkr_m = int(statistics.median(nkr_sizes)) if nkr_sizes else 0
    deep_m = int(statistics.median(deep_sizes)) if deep_sizes else 0
    check("r1 NK median (bytes/task)", 1187, nkr_m, "nk_records/task_*.json")
    check("deep NK median (bytes/task)", 3354, deep_m,
          "nk_records/task_*_deep.json")

    if b2_bytes_path.exists():
        nkr_savings = f"{(1 - nkr_m/b2_m)*100:.1f}"
        deep_savings = f"{(1 - deep_m/b2_m)*100:.1f}"
        check("byte savings: r1 NK vs B2 (%)", "72.2", nkr_savings,
              "(D) median ratio")
        check("byte savings: deep NK vs B2 (%)", "21.5", deep_savings,
              "(D) median ratio")

    # ============== (E) Solver tokens ==============
    print("\n(E) Solver tokens per dispatch (median)")

    by_cell_tok = defaultdict(list)
    for d in solvers:
        t = d["dispatch"].get("tokens")
        if t:
            by_cell_tok[(d["model_dir"], d["cell"])].append(t)

    def med(ts): return int(statistics.median(ts)) if ts else 0

    check("solver tokens: round-1 median", 16262,
          med(by_cell_tok[("sonnet_4.6", "round1")]),
          "round1 dispatches")
    check("solver tokens: NKR median", 18080,
          med(by_cell_tok[("sonnet_4.6", "round2_NKR")]),
          "round2_NKR dispatches")
    check("solver tokens: deepNKR-Sonnet median", 19247,
          med(by_cell_tok[("sonnet_4.6", "deepNKR_sonnet")]),
          "deepNKR_sonnet dispatches")
    check("solver tokens: deepNKR-Haiku median", 48360,
          med(by_cell_tok[("haiku_4.5", "deepNKR_haiku")]),
          "deepNKR_haiku dispatches")

    # ============== (F) NK error rate ==============
    print("\n(F) Depth-1 NK self-reported error rate (r2 curator)")

    rels = Counter()
    for tid in nk_test_24:
        p = logs / "nk_records" / f"task_{tid}_r2.json"
        if p.exists():
            rels[json.load(open(p)).get("relationship_to_round1", "?")] += 1

    check("r2 NK count", 22, sum(rels.values()),
          "nk_records/task_*_r2.json")
    check("r2 rel: correct_but_insufficient", 13,
          rels["round1_recipe_was_correct_but_insufficient"],
          "r2 NK records")
    check("r2 rel: round1_recipe_was_wrong", 2,
          rels["round1_recipe_was_wrong"], "r2 NK records")
    if sum(rels.values()) > 0:
        err_rate = rels["round1_recipe_was_wrong"] / sum(rels.values()) * 100
        check("r2 NK error rate (%)", "9.1", f"{err_rate:.1f}",
              "r2 NK records")

    # ============== (G) task_072 specifics ==============
    print("\n(G) task_072 — the depth-3 deepNKR breakthrough")

    check("task_072 in deepNKR_sonnet PASS set", True,
          "072" in pass_deep,
          "deepNKR_sonnet dispatch for task_072")

    deep_072 = next(
        (d for d in solvers if d["task_id"] == "072"
         and d["cell"] == "deepNKR_sonnet"), None
    )
    if deep_072:
        check("task_072 deepNKR-Sonnet eval_score", 1,
              deep_072["execution"]["eval_score"],
              "task_072__deepNKR_sonnet.json")

    # ============== Write reports ==============
    n_match = sum(1 for c in CLAIMS if c["match"])
    summary = f"{n_match}/{len(CLAIMS)} provenance checks match"
    print("\n" + "=" * 70)
    print(f"  {summary}")
    print("=" * 70)

    out_md = REPRO_ROOT / "results" / "claim_report.md"
    out_json = REPRO_ROOT / "results" / "claim_report.json"
    out_md.parent.mkdir(parents=True, exist_ok=True)

    paper_table = [
        {
            "method": "Base",
            "pass_rate_percent": 31.6,
            "memory_bytes": None,
            "memory_display": "--",
        },
        {
            "method": "Retry",
            "pass_rate_percent": 31.6,
            "memory_bytes": None,
            "memory_display": "--",
        },
        {
            "method": "Negative knowledge retry (d=1)",
            "pass_rate_percent": 36.8,
            "memory_bytes": 1187,
            "memory_display": "1,187 (-72.2%)",
        },
        {
            "method": "Self-debug (round=3)",
            "pass_rate_percent": 44.7,
            "memory_bytes": 4272,
            "memory_display": "4,272 (baseline)",
        },
        {
            "method": "Deep negative knowledge retry (d=3)",
            "pass_rate_percent": 47.4,
            "memory_bytes": 3354,
            "memory_display": "3,354 (-21.5%)",
        },
    ]

    try:
        logs_display = f"{logs.resolve().relative_to(REPRO_ROOT)}/"
    except ValueError:
        logs_display = str(logs.resolve())

    lines = [
        "# Section 3 reproduction report\n",
        f"Generated by `analyze_results.py` from `{logs_display}`.\n\n",
        f"**{summary}.**\n\n",
        "## Main evaluation table\n\n",
        "| Method | Pass rate (%) | Memory (B) |\n",
        "|---|---:|---:|\n",
    ]
    for row in paper_table:
        pass_rate = f"{row['pass_rate_percent']:.1f}"
        if row["method"] == "Deep negative knowledge retry (d=3)":
            pass_rate = f"**{pass_rate}**"
        lines.append(
            f"| {row['method']} | {pass_rate} | {row['memory_display']} |\n"
        )

    lines.append("\n## Provenance checks\n\n")
    if n_match != len(CLAIMS):
        lines.append("⚠ MISMATCHES require investigation before submission.\n\n")
    lines.append(
        "The table below keeps the raw checks used to verify the "
        "paper-facing percentages and memory values above. Each row's "
        "*Source* column names the on-disk files used to compute the value.\n\n"
    )
    lines.append("| # | Check | Expected | Computed | Match | Source |\n")
    lines.append("|--:|---|---|---|:-:|---|\n")
    for i, c in enumerate(CLAIMS, 1):
        mark = "✓" if c["match"] else "✗ **MISMATCH**"
        lines.append(
            f"| {i} | {c['label']} | `{c['expected']}` | "
            f"`{c['computed']}` | {mark} | {c['source']} |\n"
        )
    out_md.write_text("".join(lines))
    out_json.write_text(json.dumps({
        "summary": summary,
        "n_match": n_match,
        "n_total": len(CLAIMS),
        "paper_table": paper_table,
        "provenance_checks": CLAIMS,
    }, indent=2))

    print(f"\n  Report:    {out_md.relative_to(REPRO_ROOT)}")
    print(f"  Raw JSON:  {out_json.relative_to(REPRO_ROOT)}\n")

    if n_match != len(CLAIMS):
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(
        description="Recompute the main §3 evaluation table from logs/."
    )
    ap.add_argument("--logs", type=pathlib.Path, default=LOGS,
                    help="Logs archive (default: <repo>/logs).")
    args = ap.parse_args()

    if not args.logs.exists():
        sys.exit(f"logs directory not found: {args.logs}")

    analyze(args.logs)


if __name__ == "__main__":
    main()
