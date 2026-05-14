#!/usr/bin/env python3
"""Build Stage 2 v2 sandboxes for the Research Graph framework.

12 cells total = 3 sub-tasks × 4 memory conditions.

Conditions:
  NoKB     — agent gets no knowledge bank
  PosOnly  — agent reads ONLY positive_knowledge.jsonl (10 entries)
  NegOnly  — agent reads ONLY negative_knowledge.jsonl (20 entries)
  PosNeg   — agent reads BOTH files (30 entries total)

Knowledge bank files are placed on disk so the agent can `cat` them via Bash.
The relevant content is also embedded directly in the prompt for convenience.
Each cell hosts one long-running sub-agent session implementing the Research
Graph protocol (≤3 Experiment nodes per session).
"""
import json, pathlib

# paper-artifact canonical paths
PAPER = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper")
SECTION4 = PAPER / "Negative_Knowledge" / "section4"
STAGE2 = SECTION4 / "stage2"
BANK_DIR = SECTION4 / "stage1" / "bank"
POS_PATH = BANK_DIR / "positive_knowledge.jsonl"
NEG_PATH = BANK_DIR / "negative_knowledge.jsonl"
TASKS_PATH = STAGE2 / "tasks" / "definitions.json"
TEMPLATE_PATH = STAGE2 / "prompts" / "research_graph_template.md"
# Python venv still lives under the pilot directory (avoid duplicating ~1 GB venv)
VENV_PY = str(PAPER / "experiments" / "pde_pilot_2026-05-11" / ".venv" / "bin" / "python")

CONDITIONS = ["NoKB", "PosOnly", "NegOnly", "PosNeg"]


def load_split_banks():
    pos = [json.loads(l) for l in open(POS_PATH) if l.strip()]
    neg = [json.loads(l) for l in open(NEG_PATH) if l.strip()]
    return pos, neg


def format_positive(e):
    return (
        f"### {e['id']}  (positive, domain={e['domain']})\n"
        f"  method: {e.get('method','')}\n"
        f"  claim: {e.get('claim','')}\n"
        f"  regime: {e.get('regime','')}\n"
        f"  applicability: {e.get('applicability','')}\n"
    )


def format_negative(e):
    f = e["failure"]
    return (
        f"### {e['id']}  (negative, domain={e['domain']})\n"
        f"  attempted_route: {e.get('attempted_route','')}\n"
        f"  observation: {e.get('observation','')}\n"
        f"  failure: layer={f['layer']}, scope={f['scope']}, degree={f['degree']}, action={f['recommended_action']}, risk={f['risk']}\n"
        f"  rationale: {e.get('rationale','')}\n"
        f"  applicability: {e.get('applicability','')}\n"
    )


def build_memory_block(condition, pos, neg):
    """Build the prompt's embedded memory section, condition-specific."""
    if condition == "NoKB":
        return "## Memory: no knowledge bank.\n\nYou have no prior knowledge bank for this problem family. Use your general knowledge of PDE numerical methods.\n"
    if condition == "PosOnly":
        body = "\n".join(format_positive(e) for e in pos)
        return (
            f"## Memory: positive-knowledge bank ({len(pos)} entries)\n\n"
            "Each entry describes a numerical method or parameter regime that WORKED in its tested setting. "
            "Use these as a guide for what to try; they do not cover failure modes.\n\n"
            f"{body}"
        )
    if condition == "NegOnly":
        body = "\n".join(format_negative(e) for e in neg)
        return (
            f"## Memory: negative-knowledge bank ({len(neg)} entries)\n\n"
            "Each entry describes a numerical method or parameter regime that FAILED in its tested setting, "
            "structured by the 6-field bounded failure schema (layer / scope / degree / recommended_action / risk). "
            "Use these to avoid known pitfalls; they do not directly tell you what to do, only what to avoid.\n\n"
            f"{body}"
        )
    # PosNeg
    body = "\n".join(format_positive(e) for e in pos) + "\n" + "\n".join(format_negative(e) for e in neg)
    return (
        f"## Memory: full positive + negative knowledge bank ({len(pos)} positive, {len(neg)} negative; {len(pos)+len(neg)} total)\n\n"
        "Both positive entries (methods that worked) and negative entries (methods that failed, structured by 6-field schema). "
        "Use positive entries to choose approaches and negative entries to avoid pitfalls.\n\n"
        f"{body}"
    )


def make_prompt(task_id, condition, tasks, pos, neg):
    task = tasks[task_id]
    cwd = STAGE2 / "runs" / task_id / condition

    # The bank file paths exposed to the agent in this condition
    if condition == "NoKB":
        bank_pos_path = "(none)"
        bank_neg_path = "(none)"
    elif condition == "PosOnly":
        bank_pos_path = str(POS_PATH)
        bank_neg_path = "(not provided in this condition)"
    elif condition == "NegOnly":
        bank_pos_path = "(not provided in this condition)"
        bank_neg_path = str(NEG_PATH)
    else:  # PosNeg
        bank_pos_path = str(POS_PATH)
        bank_neg_path = str(NEG_PATH)

    memory_block = build_memory_block(condition, pos, neg)

    template = TEMPLATE_PATH.read_text()
    template = template.replace("{% raw %}", "").replace("{% endraw %}", "").strip()
    # Manual substitution to avoid clashing with JSON `{...}` literals
    subs = {
        "{task_id}": task_id,
        "{task_title}": task["title"],
        "{task_description}": task["description"],
        "{task_ic}": task["ic"],
        "{task_T_final}": str(task["T_final"]),
        "{task_output_path}": task["output_path"],
        "{task_output_shape}": task["output_shape_spec"],
        "{task_phenomenon_target}": task["phenomenon_target"],
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
    print(f"banks: {len(pos)} positive + {len(neg)} negative")
    print(f"tasks: {list(tasks.keys())}")
    print(f"conditions: {CONDITIONS}")

    # Clean any previously-built v2 sandboxes
    for tid in tasks:
        old = STAGE2 / "runs" / tid
        if old.exists():
            import shutil
            for cond_dir in old.iterdir():
                if cond_dir.is_dir() and cond_dir.name in CONDITIONS:
                    shutil.rmtree(cond_dir)
                    print(f"  cleaned old {tid}/{cond_dir.name}")

    built = 0
    sizes = {}
    for task_id in tasks:
        for cond in CONDITIONS:
            cwd = STAGE2 / "runs" / task_id / cond
            (cwd / "pred_results").mkdir(parents=True, exist_ok=True)

            # save meta
            meta = {
                "task_id": task_id, "condition": cond, "version": "v2_research_graph",
                "iter_budget": 3,
                "tools_allowed": ["Read", "Write", "Bash"],
                **tasks[task_id],
            }
            (cwd / "meta.json").write_text(json.dumps(meta, indent=2))

            # save memory block as separate file for audit
            mem = build_memory_block(cond, pos, neg)
            (cwd / "memory.md").write_text(mem)

            # write prompt
            prompt = make_prompt(task_id, cond, tasks, pos, neg)
            (cwd / "prompt.md").write_text(prompt)

            # write empty initial research_state.jsonl placeholder so agent appends, not creates
            (cwd / "research_state.jsonl").write_text("")
            (cwd / "session_log.md").write_text(f"# Session log: {task_id} / {cond}\n\n")

            sizes[(task_id, cond)] = len(prompt)
            built += 1
            print(f"  built {task_id}/{cond}  ({len(prompt)} chars)")

    print(f"\n{built} v2 sandboxes ready (3 tasks × 4 conditions)")
    print(f"\nPrompt size summary (chars):")
    for tid in tasks:
        row = "  " + tid + ": "
        for cond in CONDITIONS:
            row += f"{cond}={sizes[(tid, cond)]:>6}  "
        print(row)


if __name__ == "__main__":
    main()
