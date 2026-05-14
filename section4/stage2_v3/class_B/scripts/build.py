#!/usr/bin/env python3
"""Build Class B sandboxes (2 tasks × 4 conditions = 8 cells) using mechanism-inquiry template + bank_v3.A."""
import json, pathlib

PAPER = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper")
SEC4 = PAPER / "Negative_Knowledge" / "section4"
CLASS_B = SEC4 / "stage2_v3" / "class_B"
BANK_DIR = SEC4 / "stage1_v3" / "bank"
POS_PATH = BANK_DIR / "bank_v3A_positive.jsonl"
NEG_PATH = BANK_DIR / "bank_v3A_negative.jsonl"
TASKS_PATH = CLASS_B / "tasks" / "definitions.json"
TEMPLATE_PATH = CLASS_B / "prompts" / "mechanism_inquiry_template.md"
VENV_PY = str(PAPER / "experiments" / "pde_pilot_2026-05-11" / ".venv" / "bin" / "python")

CONDITIONS = ["NoKB", "PosOnly", "NegOnly", "PosNeg"]


def load_split_banks():
    pos = [json.loads(l) for l in open(POS_PATH) if l.strip()]
    neg = [json.loads(l) for l in open(NEG_PATH) if l.strip()]
    return pos, neg


def format_entry(e, kind_label):
    eid = e.get("task_id") or e.get("id") or "<unknown>"
    depth_hint = e.get("_v3_depth_hint", 1)
    depth_str = f" depth={depth_hint}" if depth_hint > 1 else ""
    head = f"### {eid}  ({kind_label}{depth_str})"
    if "rounds_summary" in e:
        body_lines = [
            f"  [DEEP SYNTHESIS, {e.get('depth','N')} rounds]",
            f"  synthesised_diagnosis: {e.get('synthesised_diagnosis','')}",
            f"  ruled_out_routes:",
        ]
        for x in e.get("ruled_out_routes", []):
            body_lines.append(f"    - {x}")
        body_lines.append(f"  recommended_alternative: {e.get('recommended_alternative','')}")
    elif "attempted_route" in e:
        body_lines = [
            f"  attempted_route: {e.get('attempted_route','')}",
            f"  observation: {e.get('observation','')}",
            f"  rationale: {e.get('rationale','')}",
            f"  recommended_alternative: {e.get('recommended_alternative', e.get('applicability',''))}",
        ]
        f = e.get("failure", {})
        if f:
            body_lines.append(f"  failure: layer={f.get('layer','')}, scope={f.get('scope','')}, action={f.get('recommended_action','')}, risk={f.get('risk','')}")
    else:
        body_lines = [
            f"  method: {e.get('method','')}",
            f"  claim: {e.get('claim','')}",
            f"  regime: {e.get('regime','')}",
            f"  applicability: {e.get('applicability','')}",
        ]
    if e.get("is_trivial"):
        body_lines.append(f"  is_trivial: true (trivial_degree={e.get('trivial_degree',1)})")
    return head + "\n" + "\n".join(body_lines) + "\n"


def build_memory_block(condition, pos, neg):
    if condition == "NoKB":
        return "## Memory: no knowledge bank.\n\nYou have no prior knowledge bank for this mechanism inquiry. Use your general knowledge of PDEs.\n"
    if condition == "PosOnly":
        body = "\n".join(format_entry(e, "positive") for e in pos)
        return (
            f"## Memory: positive-knowledge bank ({len(pos)} entries, v3.A — includes BKdV stress-test entries S1-S7)\n\n"
            "Positive entries describe methods, regimes, or observations VALIDATED in related settings. Deep synthesis entries (depth≥2) span multiple stage-1 stress-test rounds.\n\n"
            f"{body}"
        )
    if condition == "NegOnly":
        body = "\n".join(format_entry(e, "negative") for e in neg)
        return (
            f"## Memory: negative-knowledge bank ({len(neg)} entries, v3.A — includes BKdV stress-test entries S1-S7)\n\n"
            "Negative entries describe methods, regimes, or paths that FAILED in related settings. Deep synthesis entries (depth≥2) are strongest negative signals — they represent N-round path closures.\n\n"
            f"{body}"
        )
    # PosNeg
    body = (
        "\n".join(format_entry(e, "positive") for e in pos)
        + "\n"
        + "\n".join(format_entry(e, "negative") for e in neg)
    )
    return (
        f"## Memory: full bank v3.A ({len(pos)} positive + {len(neg)} negative = {len(pos)+len(neg)} total)\n\n"
        "Both positive and negative entries with depth tags. Deep synthesis entries (depth≥2) are strongest signals on either side.\n\n"
        f"{body}"
    )


def make_prompt(task_id, condition, task_spec, pos, neg):
    cwd = CLASS_B / "runs" / task_id / condition

    if condition == "NoKB":
        bank_pos_path = "(none)"
        bank_neg_path = "(none)"
    elif condition == "PosOnly":
        bank_pos_path = str(POS_PATH)
        bank_neg_path = "(not provided in this condition)"
    elif condition == "NegOnly":
        bank_pos_path = "(not provided in this condition)"
        bank_neg_path = str(NEG_PATH)
    else:
        bank_pos_path = str(POS_PATH)
        bank_neg_path = str(NEG_PATH)

    memory_block = build_memory_block(condition, pos, neg)
    physics_anchoring_block = "\n".join(f"- {p}" for p in task_spec["physics_anchoring"])
    observables_block = "\n".join(f"- {o}" for o in task_spec["key_observables_to_consider"])

    template = TEMPLATE_PATH.read_text()
    subs = {
        "{task_id}": task_id,
        "{task_title}": task_spec["title"],
        "{research_question}": task_spec["research_question"],
        "{physics_anchoring_block}": physics_anchoring_block,
        "{observables_block}": observables_block,
        "{cwd}": str(cwd),
        "{bank_pos_path}": bank_pos_path,
        "{bank_neg_path}": bank_neg_path,
        "{venv_py}": VENV_PY,
        "{memory_block}": memory_block,
    }
    for k, v in subs.items():
        template = template.replace(k, v)
    return template


def main():
    pos, neg = load_split_banks()
    tasks = json.load(open(TASKS_PATH))
    print(f"bank_v3.A: {len(pos)} positive + {len(neg)} negative")
    print(f"tasks: {list(tasks.keys())}")
    print(f"conditions: {CONDITIONS}")

    built = 0
    for task_id, task_spec in tasks.items():
        for cond in CONDITIONS:
            cwd = CLASS_B / "runs" / task_id / cond
            (cwd / "evidence").mkdir(parents=True, exist_ok=True)
            (cwd / "pred_results").mkdir(parents=True, exist_ok=True)
            meta = {
                "task_id": task_id, "condition": cond, "version": "v3A_class_B_mechanism_inquiry",
                "iter_budget": 3,
                "tools_allowed": ["Read", "Write", "Bash"],
                "bank": "bank_v3.A (58 entries: 15 pos + 43 neg, 7 deep)",
                "title": task_spec["title"],
                "research_question": task_spec["research_question"],
                "physics_anchoring": task_spec["physics_anchoring"],
            }
            (cwd / "meta.json").write_text(json.dumps(meta, indent=2))
            mem = build_memory_block(cond, pos, neg)
            (cwd / "memory.md").write_text(mem)
            prompt = make_prompt(task_id, cond, task_spec, pos, neg)
            (cwd / "prompt.md").write_text(prompt)
            (cwd / "research_state.jsonl").write_text("")
            (cwd / "session_log.md").write_text(f"# Session log: {task_id} / {cond}\n\n")
            built += 1
            print(f"  built {task_id}/{cond}  ({len(prompt)} chars)")

    print(f"\n{built} Class B sandboxes ready")


if __name__ == "__main__":
    main()
