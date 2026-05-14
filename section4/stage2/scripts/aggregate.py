#!/usr/bin/env python3
"""Aggregate Section 4 stage-2 verified eval into a comparison table.

Reads verified_results.json (produced by run_eval.py), groups by
(task, condition), and prints both a console table and a markdown table.
Also writes summary.md next to verified_results.json.
"""
import json, pathlib

STAGE2 = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage2")
VR = STAGE2 / "verified_results.json"
SUMMARY = STAGE2 / "summary.md"

TASKS = ["T_A", "T_B", "T_C"]
CONDS = ["NoKB", "PosOnly", "NegOnly", "PosNeg"]


def row_lookup(rows):
    return {(r["task"], r["condition"]): r for r in rows}


def main():
    rows = json.loads(VR.read_text())
    rl = row_lookup(rows)

    md = []
    md.append("# Section 4 — Stage 2 verified eval summary\n\n")
    md.append(f"Cells: {len(TASKS)} tasks × {len(CONDS)} conditions = {len(TASKS)*len(CONDS)} sandboxes.\n")
    md.append("All evals run on the parent side via `eval/phenomenon_checks.py` "
              "(deterministic, task-specific phenomenon checks; no closed-form reference).\n\n")

    md.append("## Per-task verdict (PASS / FAIL)\n\n")
    md.append("| Task | " + " | ".join(f"**{c}**" for c in CONDS) + " |\n")
    md.append("|---|" + "---|" * len(CONDS) + "\n")
    for t in TASKS:
        cells = []
        for c in CONDS:
            r = rl[(t, c)]
            mark = "✓" if r["useful"] else "✗"
            cells.append(f"{mark} ({r['iterations']}it)")
        md.append(f"| {t} | " + " | ".join(cells) + " |\n")
    md.append("\nLegend: ✓/✗ = parent-verified PASS/FAIL, `(Nit)` = number of Experiment nodes (1–3).\n\n")

    md.append("## Useful rate by condition\n\n")
    md.append("| Condition | PASS / 3 | Avg iterations | Avg bank cites | Avg bank rejects |\n")
    md.append("|---|---|---|---|---|\n")
    for c in CONDS:
        subset = [r for r in rows if r["condition"] == c]
        n_pass = sum(1 for r in subset if r["useful"])
        avg_it = sum(r["iterations"] for r in subset) / len(subset)
        avg_c = sum(r["bank_cites"] for r in subset) / len(subset)
        avg_rj = sum(r["bank_rejects"] for r in subset) / len(subset)
        md.append(f"| {c} | {n_pass}/3 | {avg_it:.1f} | {avg_c:.1f} | {avg_rj:.1f} |\n")
    md.append("\n")

    md.append("## Per-cell metrics\n\n")
    md.append("| Task | Cond | Iter | Cites | Rejects | PASS? | vT_max | u_max | peaks | reason |\n")
    md.append("|---|---|---|---|---|---|---|---|---|---|\n")
    for t in TASKS:
        for c in CONDS:
            r = rl[(t, c)]
            d = r["diag"]
            md.append(
                f"| {t} | {c} | {r['iterations']} | {r['bank_cites']} | {r['bank_rejects']} "
                f"| {'PASS' if r['useful'] else 'FAIL'} "
                f"| {d.get('vT_max', float('nan')):.2f} "
                f"| {d.get('u_max', float('nan')):.2f} "
                f"| {d.get('n_dominant_peaks_vT', '-')} "
                f"| {d.get('reason','')} |\n"
            )
    md.append("\n")

    md.append("## Bank-entry usage (cite / reject lists, sample)\n\n")
    for t in TASKS:
        for c in CONDS:
            r = rl[(t, c)]
            if r["bank_cites"] == 0 and r["bank_rejects"] == 0:
                continue
            md.append(f"### {t} / {c}\n")
            if r["cite_ids"]:
                md.append(f"- **cites** ({len(r['cite_ids'])}): " + ", ".join(r["cite_ids"]) + "\n")
            if r["reject_ids"]:
                md.append(f"- **rejects** ({len(r['reject_ids'])}): " + ", ".join(r["reject_ids"]) + "\n")
            md.append("\n")

    SUMMARY.write_text("".join(md))
    print(f"wrote {SUMMARY}")


if __name__ == "__main__":
    main()
