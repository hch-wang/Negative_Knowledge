#!/usr/bin/env python3
"""Build round-2 curator sandboxes for the 22 round-2 NKR fails.

For each round-2 NKR-fail task:
  - materialise sab_curator_r2.md
  - drop it as prompt.md in
    section3/04_outputs/curator_runs/task_<id>_r2/
  - point the curator at the round-2 NKR sandbox artifacts AND the
    round-1 NK file (so it knows what was already tried).
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

# 22 tasks that failed round-2 NKR
R2_FAIL_TASKS = [
    "002", "005", "012", "018", "021", "022", "026", "029", "034", "035",
    "037", "044", "058", "060", "067", "071", "072", "078", "085", "087",
    "097", "101",
]


def main():
    tmpl_path = SECTION3 / "02_prompts/sab_curator_r2.md"
    raw = tmpl_path.read_text()
    marker = "# Materialized prompt (template body)"
    body = raw.split(marker, 1)[1].lstrip()

    built = []
    skipped = []
    for tid in R2_FAIL_TASKS:
        spec = json.load(open(PILOT / f"tasks/task_{tid}.json"))
        r2_dir = PILOT / f"runs/task_{tid}/sonnet_4.6/v3/round2_NKR"
        r1_nk = SECTION3 / f"04_outputs/nk_records/task_{tid}.json"

        # Sanity check round-2 artifacts
        required = ("candidate.py", "exec.log", "reasoning.md")
        missing = [f for f in required if not (r2_dir / f).exists()]
        if missing:
            print(f"  SKIP task_{tid}: round2_NKR missing {missing}")
            skipped.append(tid)
            continue
        if not r1_nk.exists():
            print(f"  SKIP task_{tid}: round-1 NK missing at {r1_nk}")
            skipped.append(tid)
            continue
        eval_present = (r2_dir / "eval.log").exists()

        run_dir = SECTION3 / f"04_outputs/curator_runs/task_{tid}_r2"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Output path for the round-2 NK (separate file from round-1)
        nk_out = SECTION3 / f"04_outputs/nk_records/task_{tid}_r2.json"
        nk_out.parent.mkdir(parents=True, exist_ok=True)

        eval_note = (
            "Present — read it." if eval_present else
            "ABSENT — the round-2 script crashed before producing an "
            "output, so the evaluator was never run. Diagnose from "
            "candidate.py + exec.log + reasoning.md alone."
        )
        prompt = (
            body
            .replace("{TASK_ID}", tid)
            .replace("{TASK_INST}", spec["task_inst"])
            .replace("{ROUND2_DIR}", str(r2_dir))
            .replace("{ROUND1_NK_PATH}", str(r1_nk))
            .replace("{OUTPUT_NK_PATH}", str(nk_out))
            .replace("{EVAL_LOG_STATUS}", eval_note)
        )
        (run_dir / "prompt.md").write_text(prompt)
        built.append(str(run_dir))

    print(f"\nbuilt {len(built)} round-2 curator sandboxes "
          f"(skipped {len(skipped)})")
    for d in built:
        rel = d.replace(str(SECTION3) + "/", "")
        print(f"  {rel}")


if __name__ == "__main__":
    main()
