#!/usr/bin/env python3
"""Build per-task curator-agent sandboxes.

For each of the 24 round-1 failed tasks in pilot_2026-05-10, materialise a
curator prompt from the template at section3/02_prompts/sab_curator.md and
drop it as `prompt.md` in a per-task sandbox under
section3/04_outputs/curator_runs/task_<id>/.

The sandbox also pre-creates the empty target paths for the curator's two
required artifacts:

  - nk_records/task_<id>.json        (the NK record the curator will Write)
  - curator_audit/task_<id>.json     (the audit record the orchestrator
                                       writes AFTER the curator returns)

Run after round-1 has produced the four required artifacts
(candidate.py / exec.log / eval.log / reasoning.md) in each round1 dir.
"""
from __future__ import annotations
import json, pathlib

PILOT = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/experiments/pilot_2026-05-10"
)
SECTION3 = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/Negative_Knowledge/section3"
)

TASKS = ['002', '003', '005', '012', '015', '018', '021', '022', '026', '029',
         '034', '035', '037', '044', '058', '060', '067', '071', '072', '078',
         '085', '087', '097', '101']


def main():
    tmpl_path = SECTION3 / "02_prompts/sab_curator.md"
    # Strip the docstring header so only the materialized prompt body is used.
    raw = tmpl_path.read_text()
    marker = "# Materialized prompt (template body)"
    if marker not in raw:
        raise RuntimeError(f"template missing '{marker}' separator")
    body = raw.split(marker, 1)[1].lstrip()

    built = []
    for tid in TASKS:
        spec_path = PILOT / f"tasks/task_{tid}.json"
        spec = json.load(open(spec_path))
        round1_dir = PILOT / f"runs/task_{tid}/sonnet_4.6/v3/round1"

        # Sanity check inputs exist. eval.log is optional — for tasks that
        # crashed at exec time the candidate never produced an output and the
        # evaluator was never run.
        required = ("candidate.py", "exec.log", "reasoning.md")
        missing = [f for f in required if not (round1_dir / f).exists()]
        if missing:
            print(f"  SKIP task_{tid}: round1 missing {missing}")
            continue
        eval_present = (round1_dir / "eval.log").exists()

        run_dir = SECTION3 / f"04_outputs/curator_runs/task_{tid}"
        run_dir.mkdir(parents=True, exist_ok=True)

        nk_out = SECTION3 / f"04_outputs/nk_records/task_{tid}.json"
        nk_out.parent.mkdir(parents=True, exist_ok=True)

        eval_note = (
            "Present — read it." if eval_present else
            "ABSENT — the round-1 script crashed before producing an "
            "output, so the evaluator was never run. Diagnose from "
            "candidate.py + exec.log + reasoning.md alone."
        )
        prompt = (
            body
            .replace("{TASK_ID}", tid)
            .replace("{TASK_INST}", spec["task_inst"])
            .replace("{ROUND1_DIR}", str(round1_dir))
            .replace("{OUTPUT_NK_PATH}", str(nk_out))
            .replace("{EVAL_LOG_STATUS}", eval_note)
        )
        (run_dir / "prompt.md").write_text(prompt)
        built.append(str(run_dir))

    print(f"built {len(built)} curator sandboxes")
    for d in built:
        rel = d.replace(str(SECTION3) + "/", "")
        print(f"  {rel}")


if __name__ == "__main__":
    main()
