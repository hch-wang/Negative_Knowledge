#!/usr/bin/env python3
"""Build deep-curator sandboxes for the 19 tasks where 3 rounds of B2
Self-Debug all failed.

Each sandbox materialises sab_curator_deep.md into prompt.md, pointing
at the round 1 / round 2_B2 / round 3_B2 artifacts and at an output
path for the deep NK file.
"""
from __future__ import annotations
import json
import pathlib

PILOT = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/experiments/pilot_2026-05-10"
)
SECTION3 = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/Negative_Knowledge/section3"
)

# 19 tasks that failed all three rounds of B2 (Self-Debug covering memory)
DEEP_TASKS = [
    "002", "012", "018", "021", "022", "026", "029", "034", "035",
    "037", "044", "058", "060", "067", "072", "078", "085", "087", "101",
]


def _yn(path: pathlib.Path) -> str:
    return "Present — read it." if path.exists() else (
        "ABSENT — script crashed before producing output, evaluator not run."
    )


def main():
    tmpl_path = SECTION3 / "02_prompts/sab_curator_deep.md"
    raw = tmpl_path.read_text()
    body = raw.split("# Materialized prompt (template body)", 1)[1].lstrip()

    built = []
    skipped = []
    for tid in DEEP_TASKS:
        spec = json.load(open(PILOT / f"tasks/task_{tid}.json"))
        r1 = PILOT / f"runs/task_{tid}/sonnet_4.6/v3/round1"
        r2 = PILOT / f"runs/task_{tid}/sonnet_4.6/v3/round2_B2"
        r3 = PILOT / f"runs/task_{tid}/sonnet_4.6/v3/round3_B2"

        # Sanity check: round 1 must have candidate.py + exec.log + reasoning.md;
        # rounds 2 and 3 same. eval.log is optional throughout.
        ok = True
        for d, label in [(r1, "round1"), (r2, "round2_B2"), (r3, "round3_B2")]:
            for fn in ("candidate.py", "exec.log", "reasoning.md"):
                if not (d / fn).exists():
                    print(f"  SKIP task_{tid}: {label}/{fn} missing")
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            skipped.append(tid)
            continue

        run_dir = SECTION3 / f"04_outputs/curator_runs/task_{tid}_deep"
        run_dir.mkdir(parents=True, exist_ok=True)

        nk_out = SECTION3 / f"04_outputs/nk_records/task_{tid}_deep.json"
        nk_out.parent.mkdir(parents=True, exist_ok=True)

        prompt = (
            body
            .replace("{TASK_ID}", tid)
            .replace("{TASK_INST}", spec["task_inst"])
            .replace("{ROUND1_DIR}", str(r1))
            .replace("{ROUND2_DIR}", str(r2))
            .replace("{ROUND3_DIR}", str(r3))
            .replace("{ROUND2_EVAL_PRESENT}", _yn(r2 / "eval.log"))
            .replace("{ROUND3_EVAL_PRESENT}", _yn(r3 / "eval.log"))
            .replace("{OUTPUT_NK_PATH}", str(nk_out))
        )
        (run_dir / "prompt.md").write_text(prompt)
        built.append(str(run_dir))

    print(f"\nbuilt {len(built)} deep-curator sandboxes "
          f"(skipped {len(skipped)})")
    for d in built:
        rel = d.replace(str(SECTION3) + "/", "")
        print(f"  {rel}")


if __name__ == "__main__":
    main()
