#!/usr/bin/env python3
"""Build per-test sandboxes for stage1_bnls stress-tests."""
import json, pathlib

PAPER = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper")
STAGE1 = PAPER / "Negative_Knowledge" / "section4" / "stage1_bnls"
VENV_PY = str(PAPER / "experiments" / "pde_pilot_2026-05-11" / ".venv" / "bin" / "python")

TESTS_PATH = STAGE1 / "tests" / "definitions.json"
TEMPLATE_PATH = STAGE1 / "prompts" / "template.md"


def main():
    tests = json.load(open(TESTS_PATH))
    template = TEMPLATE_PATH.read_text()
    built = 0
    for test_id, t in tests.items():
        cwd = STAGE1 / "runs" / test_id
        (cwd / "pred_results").mkdir(parents=True, exist_ok=True)
        description_block = (
            f"**Domain**: {t['domain']}\n\n"
            f"**Why this matters**: {t.get('stress_question','')}"
        )
        subs = {
            "{test_id}": test_id,
            "{title}": t["title"],
            "{description_block}": description_block,
            "{ic}": t["ic"],
            "{T_final}": str(t["T_final"]),
            "{domain_x}": str(t["domain_x"]),
            "{Nx_default}": str(t["Nx_default"]),
            "{cwd}": str(cwd),
            "{venv_py}": VENV_PY,
            "{stress_question}": t["stress_question"],
            "{parameters_to_sweep}": t.get("parameters_to_sweep", ""),
            "{required_observations}": ", ".join(t.get("required_observations", [])),
            "{ground_truth}": t.get("ground_truth", "(unknown — record what you observe)"),
        }
        prompt = template
        for k, v in subs.items():
            prompt = prompt.replace(k, v)
        (cwd / "prompt.md").write_text(prompt)
        (cwd / "research_state.jsonl").write_text("")
        (cwd / "session_log.md").write_text(f"# Session log: {test_id}\n\n")
        # save a meta.json for traceability
        (cwd / "meta.json").write_text(json.dumps({**t, "test_id": test_id, "version": "stage1_bnls_v1"}, indent=2))
        built += 1
        print(f"  built {test_id}: {len(prompt)} chars")
    print(f"\n{built} stress-test sandboxes ready under {STAGE1 / 'runs'}")


if __name__ == "__main__":
    main()
