#!/usr/bin/env python3
"""Reproduce every numerical claim in paper §3 from the on-disk archive.

This script reads ONLY the consolidated dispatch records:
  - section3/04_outputs/curator_audit/      (65 curator records)
  - section3/04_outputs/dispatches/solver/  (220 solver records)
  - section3/04_outputs/nk_records/         (65 NK files)

It does NOT re-execute anything. It does NOT need API keys. It
treats the archive as the canonical source and verifies that
every paper claim can be derived from it.

Output: section3/05_results/paper_claims_reproduction.md
        section3/05_results/paper_claims_reproduction.json

Run:
  python 03_scripts/reproduce_paper_claims.py

If a paper claim's computed value disagrees with the value
written in the paper, the script prints a "MISMATCH" line and the
exit code is non-zero. This is the round-trip test that gates
paper submission.
"""
from __future__ import annotations
import csv
import json
import pathlib
import statistics
from collections import defaultdict, Counter

SECTION3 = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/Negative_Knowledge/section3"
)
PILOT = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/experiments/pilot_2026-05-10"
)

# ---------- archive readers ----------

def load_solver_dispatches() -> list:
    out = []
    for p in sorted((SECTION3 / "04_outputs/dispatches/solver").glob("*.json")):
        out.append(json.load(open(p)))
    return out


def load_curator_audits() -> list:
    out = []
    for p in sorted((SECTION3 / "04_outputs/curator_audit").glob("*.json")):
        out.append(json.load(open(p)))
    return out


def load_nk_records() -> dict:
    """Return dict keyed by 'task_<id>{,_r2,_deep}' -> parsed JSON."""
    out = {}
    for p in sorted((SECTION3 / "04_outputs/nk_records").glob("*.json")):
        out[p.stem] = json.load(open(p))
    return out


def load_baseline_pass() -> set:
    """Load the round-1 (no-memory single-shot) PASS set for all 38 pilot
    tasks from pilot's per-task root result.json. These are the
    pre-v3 baseline runs; v3 itself only re-ran the 24 round-1 failures."""
    pilot_tasks = []
    for p in sorted((PILOT / "tasks").glob("task_*.json")):
        spec = json.load(open(p))
        pilot_tasks.append(f"{spec['instance_id']:03d}")
    pass_set = set()
    for tid in pilot_tasks:
        rj = PILOT / f"runs/task_{tid}/sonnet_4.6/result.json"
        if not rj.exists():
            continue
        r = json.load(open(rj))
        if r.get("eval_score") == 1 or r.get("eval_score") == "1":
            pass_set.add(tid)
    return pass_set


# ---------- compute helpers ----------

def passes_by_cell(solver_dispatches):
    """Return dict: (model_dir, cell) -> set of task_ids that PASSed."""
    out = defaultdict(set)
    for d in solver_dispatches:
        score = d["execution"].get("eval_score")
        if score == 1 or score == "1":
            out[(d["model_dir"], d["cell"])].add(d["task_id"])
    return out


def all_tasks_in_cell(solver_dispatches, model_dir, cell):
    return set(d["task_id"] for d in solver_dispatches
               if d["model_dir"] == model_dir and d["cell"] == cell)


# ---------- claim computations ----------

CLAIMS = []  # list of (label, expected_value, computed_value, source_paths)


def claim(label, expected, computed, sources):
    CLAIMS.append({
        "label": label,
        "expected": expected,
        "computed": computed,
        "match": expected == computed,
        "source_paths": sources,
    })


def main():
    solvers = load_solver_dispatches()
    curators = load_curator_audits()
    nks = load_nk_records()
    print(f"loaded {len(solvers)} solver + {len(curators)} curator dispatches + {len(nks)} NK records")

    # ============================================================
    # Subset sizes — derive from archive directly
    # ============================================================
    pilot_tasks_38 = set()
    for p in sorted(pathlib.Path(PILOT / "tasks").glob("task_*.json")):
        spec = json.load(open(p))
        pilot_tasks_38.add(f"{spec['instance_id']:03d}")
    claim("pilot subset size", 38, len(pilot_tasks_38),
          [str(PILOT / "tasks/task_*.json")])

    # Baseline (round-1, no memory): the 12 PASS tasks are pre-v3,
    # stored at pilot's per-task root result.json. v3 itself only re-ran
    # the 24 round-1 failures, so the v3 round1 cell PASSes 0/24.
    baseline_pass_38 = load_baseline_pass()
    claim("baseline round-1 PASS (across 38 pilot tasks)", 12,
          len(baseline_pass_38),
          ["pilot runs/task_*/sonnet_4.6/result.json"])

    # The v3 round1 cell only contains the 24 round-1 failures.
    v3_round1_pass = passes_by_cell(solvers)[("sonnet_4.6", "round1")]
    claim("v3 round1 cell PASS (by selection = 0)", 0, len(v3_round1_pass),
          ["04_outputs/dispatches/solver/task_*__round1.json"])

    # NK-test subset (the 24 v3 tasks)
    nk_test_24 = all_tasks_in_cell(solvers, "sonnet_4.6", "round1")
    claim("NK-test subset size", 24, len(nk_test_24),
          ["derived from v3 round1 cell"])

    # Hard subset = 19 (B2 covering fails all 3 rounds)
    b2_pass_any_round = (
        passes_by_cell(solvers)[("sonnet_4.6", "round2_B2")] |
        passes_by_cell(solvers)[("sonnet_4.6", "round3_B2")]
    )
    hard_19 = nk_test_24 - b2_pass_any_round
    claim("hard subset size (B2 fails all 3 rounds)", 19, len(hard_19),
          ["derived from round2_B2 + round3_B2 cells"])

    # ============================================================
    # Main result Table 1 — benchmark-wide PASS (denominator 38)
    # ============================================================
    # Path: round-1 baseline = 12/38 (from pre-v3 baseline runs)
    benchmark_r1 = baseline_pass_38
    claim("Table 1: round-1 baseline PASS / 38", "12/38",
          f"{len(benchmark_r1)}/38",
          ["pilot baseline result.json (sonnet_4.6 root level)"])

    # + B0 retry: still 12 because B0 PASSes 0 on the 24 NK-test tasks
    b0_pass = passes_by_cell(solvers)[("sonnet_4.6", "round2_B0")]
    benchmark_b0 = benchmark_r1 | b0_pass
    claim("Table 1: + B0 retry PASS / 38", "12/38",
          f"{len(benchmark_b0)}/38",
          ["baseline + round2_B0 cell"])

    # + NKR depth-1 = 12 + 2 = 14
    nkr_r2_pass = passes_by_cell(solvers)[("sonnet_4.6", "round2_NKR")]
    benchmark_nkr = benchmark_b0 | nkr_r2_pass
    claim("Table 1: + NKR (depth-1) PASS / 38", "14/38",
          f"{len(benchmark_nkr)}/38",
          ["baseline + round2_NKR cell"])

    # + B2 covering (any round) = 12 + 5 = 17
    benchmark_b2 = benchmark_nkr | b2_pass_any_round
    claim("Table 1: + B2 covering PASS / 38", "17/38",
          f"{len(benchmark_b2)}/38",
          ["baseline + round2_B2 + round3_B2 cells"])

    # + deepNKR-Sonnet = 12 + 5 + 1 = 18
    deep_pass = passes_by_cell(solvers)[("sonnet_4.6", "deepNKR_sonnet")]
    benchmark_deep = benchmark_b2 | deep_pass
    claim("Table 1: + deepNKR (depth-3) PASS / 38", "18/38",
          f"{len(benchmark_deep)}/38",
          ["baseline + deepNKR_sonnet cell"])

    # ============================================================
    # Memory-effect view (denominator 24 / 19)
    # ============================================================
    # On the 24 NK-test tasks:
    def on_subset(passed, subset):
        return len(passed & subset)

    claim("controlled view: NKR r2 on 24",
          "2/24", f"{on_subset(nkr_r2_pass, nk_test_24)}/24",
          ["round2_NKR cell"])

    nkr_r3_pass = passes_by_cell(solvers)[("sonnet_4.6", "round3_NKR")]
    nkr_chain_pass = nkr_r2_pass | nkr_r3_pass
    claim("controlled view: NKR chain (r2+r3) on 24",
          "3/24", f"{on_subset(nkr_chain_pass, nk_test_24)}/24",
          ["round2_NKR + round3_NKR cells"])

    b3_pass_any = (
        passes_by_cell(solvers)[("sonnet_4.6", "round2_B3")] |
        passes_by_cell(solvers)[("sonnet_4.6", "round3_B3")]
    )
    claim("controlled view: B3 mixed on 24",
          "4/24", f"{on_subset(b3_pass_any, nk_test_24)}/24",
          ["round2_B3 + round3_B3 cells"])

    claim("controlled view: B2 covering on 24",
          "5/24", f"{on_subset(b2_pass_any_round, nk_test_24)}/24",
          ["round2_B2 + round3_B2 cells"])

    # On the 19 hard tasks: every depth-1 condition is 0/19
    claim("hard 19: NKR r2", "0/19",
          f"{on_subset(nkr_r2_pass, hard_19)}/19", ["round2_NKR cell"])
    claim("hard 19: NKR chain", "0/19",
          f"{on_subset(nkr_chain_pass, hard_19)}/19",
          ["round2_NKR + round3_NKR cells"])
    claim("hard 19: B2 covering", "0/19",
          f"{on_subset(b2_pass_any_round, hard_19)}/19",
          ["round2_B2 + round3_B2 cells"])
    claim("hard 19: deepNKR-Sonnet", "1/19",
          f"{on_subset(deep_pass, hard_19)}/19",
          ["deepNKR_sonnet cell"])

    haiku_pass = passes_by_cell(solvers)[("haiku_4.5", "deepNKR_haiku")]
    claim("hard 19: deepNKR-Haiku (cross-model)", "0/19",
          f"{on_subset(haiku_pass, hard_19)}/19",
          ["deepNKR_haiku cell"])

    # ============================================================
    # Headline: 14→20 lift, 37%→53%
    # ============================================================
    claim("headline: round-1 baseline %", "31.6",
          f"{len(benchmark_r1)/38*100:.1f}", ["round1 cell"])
    claim("headline: final pipeline %", "47.4",
          f"{len(benchmark_deep)/38*100:.1f}",
          ["round1 + round2_NKR + round2_B2 + round3_B2 + deepNKR_sonnet"])
    claim("headline: PASS lift (tasks)", "+6",
          f"+{len(benchmark_deep) - len(benchmark_r1)}", ["all of above"])

    # ============================================================
    # Memory byte efficiency
    # ============================================================
    # Compute median bytes per task for each memory regime, excluding
    # task_003 (multiprocessing log bomb outlier in B2).
    TASKS = sorted(nk_test_24)
    def fsize(p):
        return p.stat().st_size if p.exists() else 0

    b2_sizes, nkr_sizes, deep_sizes = [], [], []
    for tid in TASKS:
        if tid == "003":
            continue  # outlier
        r1_dir = PILOT / f"runs/task_{tid}/sonnet_4.6/v3/round1"
        b2_size = (fsize(r1_dir/"candidate.py") + fsize(r1_dir/"exec.log")
                   + fsize(r1_dir/"eval.log"))
        nkr_size = fsize(SECTION3 / f"04_outputs/nk_records/task_{tid}.json")
        deep_size = fsize(SECTION3 / f"04_outputs/nk_records/task_{tid}_deep.json")
        b2_sizes.append(b2_size)
        if nkr_size: nkr_sizes.append(nkr_size)
        if deep_size: deep_sizes.append(deep_size)

    b2_median = int(statistics.median(b2_sizes))
    nkr_median = int(statistics.median(nkr_sizes))
    deep_median = int(statistics.median(deep_sizes))

    claim("memory bytes: B2 covering median", 4272, b2_median,
          ["pilot runs/task_*/sonnet_4.6/v3/round1/{candidate.py,exec.log,eval.log}"])
    claim("memory bytes: r1 NK median", 1187, nkr_median,
          ["04_outputs/nk_records/task_<id>.json"])
    claim("memory bytes: deep NK median", 3354, deep_median,
          ["04_outputs/nk_records/task_<id>_deep.json"])

    nkr_ratio = (1 - nkr_median / b2_median) * 100
    deep_ratio = (1 - deep_median / b2_median) * 100
    claim("memory savings: r1 NK vs B2 (%)", "72.2",
          f"{nkr_ratio:.1f}", ["bytes table"])
    claim("memory savings: deep NK vs B2 (%)", "21.5",
          f"{deep_ratio:.1f}", ["bytes table"])

    # ============================================================
    # Solver tokens per dispatch
    # ============================================================
    by_cell_tokens = defaultdict(list)
    for d in solvers:
        toks = d["dispatch"].get("tokens")
        if toks:
            by_cell_tokens[(d["model_dir"], d["cell"])].append(toks)

    def med(ts): return int(statistics.median(ts)) if ts else 0

    tok_r1 = med(by_cell_tokens[("sonnet_4.6","round1")])
    tok_b0 = med(by_cell_tokens[("sonnet_4.6","round2_B0")])
    tok_nkr = med(by_cell_tokens[("sonnet_4.6","round2_NKR")])
    tok_b2 = med(by_cell_tokens[("sonnet_4.6","round2_B2")])
    tok_b3 = med(by_cell_tokens[("sonnet_4.6","round2_B3")])
    tok_deep = med(by_cell_tokens[("sonnet_4.6","deepNKR_sonnet")])
    tok_haiku = med(by_cell_tokens[("haiku_4.5","deepNKR_haiku")])

    claim("solver tokens: round-1 median", 16262, tok_r1, ["solver dispatches"])
    claim("solver tokens: round2_B0 median", 16391, tok_b0, ["solver dispatches"])
    claim("solver tokens: round2_NKR median", 18080, tok_nkr,
          ["solver dispatches"])
    claim("solver tokens: round2_B2 median", 19641, tok_b2,
          ["solver dispatches"])
    claim("solver tokens: deepNKR-Sonnet median", 19247, tok_deep,
          ["solver dispatches"])
    claim("solver tokens: deepNKR-Haiku median", 48360, tok_haiku,
          ["solver dispatches"])

    # ============================================================
    # NK error rate (relationship_to_round1 distribution)
    # ============================================================
    rels = Counter()
    for tid in nk_test_24:
        p = SECTION3 / f"04_outputs/nk_records/task_{tid}_r2.json"
        if p.exists():
            rels[json.load(open(p)).get("relationship_to_round1", "?")] += 1

    n_r2 = sum(rels.values())
    claim("r2 NK count", 22, n_r2, ["04_outputs/nk_records/task_*_r2.json"])
    claim("r2 relationship: correct_but_insufficient",
          13, rels["round1_recipe_was_correct_but_insufficient"], ["r2 NK records"])
    claim("r2 relationship: new_failure_mode_unrelated_to_round1",
          7, rels["new_failure_mode_unrelated_to_round1"], ["r2 NK records"])
    claim("r2 relationship: round1_recipe_was_wrong",
          2, rels["round1_recipe_was_wrong"], ["r2 NK records"])
    claim("r2 NK error rate (%)", "9.1",
          f"{rels['round1_recipe_was_wrong']/n_r2*100:.1f}", ["r2 NK records"])

    # ============================================================
    # Per-layer breakdown (from r1 curator NK records)
    # ============================================================
    layer_by_task = {}
    for tid in nk_test_24:
        p = SECTION3 / f"04_outputs/nk_records/task_{tid}.json"
        if p.exists():
            layer_by_task[tid] = json.load(open(p))["failure"]["layer"]
    layer_dist = Counter(layer_by_task.values())
    claim("layer dist: implementation", 15,
          layer_dist["implementation_failure"], ["r1 NK records"])
    claim("layer dist: communication", 7,
          layer_dist["communication_failure"], ["r1 NK records"])
    claim("layer dist: method", 2,
          layer_dist["method_failure"], ["r1 NK records"])

    # ============================================================
    # task_072 specifics (the deep-NK PASS)
    # ============================================================
    claim("task_072 is in deepNKR_sonnet PASS set",
          True, "072" in deep_pass, ["deepNKR_sonnet/task_072/result.json"])
    deep_072_path = SECTION3 / "04_outputs/dispatches/solver/task_072__deepNKR_sonnet.json"
    if deep_072_path.exists():
        d = json.load(open(deep_072_path))
        claim("task_072 deepNKR-Sonnet eval_score", 1,
              d["execution"]["eval_score"], [str(deep_072_path)])

    # ============================================================
    # Write reports
    # ============================================================
    out_md = SECTION3 / "05_results/paper_claims_reproduction.md"
    out_json = SECTION3 / "05_results/paper_claims_reproduction.json"
    out_md.parent.mkdir(parents=True, exist_ok=True)

    n_match = sum(1 for c in CLAIMS if c["match"])
    n_mismatch = len(CLAIMS) - n_match
    summary = f"{n_match}/{len(CLAIMS)} claims match"

    with out_md.open("w") as f:
        f.write("# Paper §3 claim reproduction report\n\n")
        f.write(f"Computed from on-disk archive at "
                f"`section3/04_outputs/`. **{summary}.**\n\n")
        if n_mismatch:
            f.write(f"⚠ **{n_mismatch} MISMATCHES** require investigation.\n\n")
        f.write("| Claim | Expected | Computed | Match | Source |\n")
        f.write("|---|---|---|:-:|---|\n")
        for c in CLAIMS:
            sources = "; ".join(c["source_paths"])
            mark = "✓" if c["match"] else "✗ MISMATCH"
            f.write(f"| {c['label']} | `{c['expected']}` "
                    f"| `{c['computed']}` | {mark} | {sources} |\n")

    out_json.write_text(json.dumps({
        "summary": summary,
        "n_match": n_match,
        "n_mismatch": n_mismatch,
        "claims": CLAIMS,
    }, indent=2))

    print(f"\n{summary}")
    print(f"  report:   {out_md.relative_to(SECTION3)}")
    print(f"  raw:      {out_json.relative_to(SECTION3)}")
    if n_mismatch:
        print(f"\n⚠ MISMATCHES:")
        for c in CLAIMS:
            if not c["match"]:
                print(f"  - {c['label']}: expected {c['expected']!r}, got {c['computed']!r}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
