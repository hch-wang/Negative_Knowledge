#!/usr/bin/env python3
"""Build Stage 2 Class A v3 sandboxes — 12 cells (T_A/T_B/T_C × NoKB/PosOnly/NegOnly/PosNeg) with bank_v3.A.

Differences from v2 build_v2.py:
- Bank loaded from stage1_v3/bank/bank_v3A_{positive,negative}.jsonl (new section-3-compatible schema)
- Outputs to stage2_v3/class_A/runs/
- Bank entries formatted using v3 schema fields (attempted_route / observation / recommended_alternative / depth)
- Template (research_graph_template.md) reused as-is — it already has progressive-complexity discipline
"""
import json
import pathlib

PAPER = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper")
SECTION4 = PAPER / "Negative_Knowledge" / "section4"
CLASS_A = SECTION4 / "stage2_v3" / "class_A"
BANK_DIR = SECTION4 / "stage1_v3" / "bank"
POS_PATH = BANK_DIR / "bank_v3A_positive.jsonl"
NEG_PATH = BANK_DIR / "bank_v3A_negative.jsonl"
TASKS_PATH = CLASS_A / "tasks" / "definitions.json"
TEMPLATE_PATH = CLASS_A / "prompts" / "research_graph_template.md"
VENV_PY = str(PAPER / "experiments" / "pde_pilot_2026-05-11" / ".venv" / "bin" / "python")

CONDITIONS = ["NoKB", "PosOnly", "NegOnly", "PosNeg"]


def load_split_banks():
    pos = [json.loads(l) for l in open(POS_PATH) if l.strip()]
    neg = [json.loads(l) for l in open(NEG_PATH) if l.strip()]
    return pos, neg


def format_entry_v3(e, kind_label):
    """Flexible formatter for both v2-legacy and v3-new entries."""
    eid = e.get("task_id") or e.get("id") or "<unknown>"
    depth_hint = e.get("_v3_depth_hint", 1)
    depth_str = f" depth={depth_hint}" if depth_hint > 1 else ""

    # Title
    head = f"### {eid}  ({kind_label}{depth_str})"

    # Determine which field set this entry uses
    if "rounds_summary" in e:
        # Deep synthesis entry
        body_lines = [
            f"  [DEEP SYNTHESIS, {e.get('depth', 'N')} rounds]",
            f"  synthesised_diagnosis: {e.get('synthesised_diagnosis', '')}",
            f"  ruled_out_routes:",
        ]
        for r in e.get("ruled_out_routes", []):
            body_lines.append(f"    - {r}")
        body_lines.append(f"  recommended_alternative: {e.get('recommended_alternative', '')}")
    elif "attempted_route" in e:
        # Single-round (v2 legacy or v3 new)
        body_lines = [
            f"  attempted_route: {e.get('attempted_route', '')}",
            f"  observation: {e.get('observation', '')}",
            f"  rationale: {e.get('rationale', '')}",
            f"  recommended_alternative: {e.get('recommended_alternative', e.get('applicability', ''))}",
        ]
        f = e.get("failure", {})
        if f:
            body_lines.append(f"  failure: layer={f.get('layer','')}, scope={f.get('scope','')}, action={f.get('recommended_action','')}, risk={f.get('risk','')}")
    else:
        # v2-era positive entry with different fields
        body_lines = [
            f"  method: {e.get('method', '')}",
            f"  claim: {e.get('claim', '')}",
            f"  regime: {e.get('regime', '')}",
            f"  applicability: {e.get('applicability', '')}",
        ]
    if e.get("is_trivial"):
        body_lines.append(f"  is_trivial: true (trivial_degree={e.get('trivial_degree', 1)})")
    return head + "\n" + "\n".join(body_lines) + "\n"


def build_memory_block(condition, pos, neg):
    if condition == "NoKB":
        return "## Memory: no knowledge bank.\n\nYou have no prior knowledge bank for this problem family. Use your general knowledge of PDE numerical methods.\n"
    if condition == "PosOnly":
        body = "\n".join(format_entry_v3(e, "positive") for e in pos)
        return (
            f"## Memory: positive-knowledge bank ({len(pos)} entries, v3.A — includes BKdV stress-test entries)\n\n"
            "Entries describe methods/regimes that WORKED. Use as guide for what to try. "
            "Note: some entries are 'deep synthesis' across multiple rounds of stage-1 BKdV programs; "
            "treat those as path-level *what works* rather than single-shot recommendations.\n\n"
            f"{body}"
        )
    if condition == "NegOnly":
        body = "\n".join(format_entry_v3(e, "negative") for e in neg)
        return (
            f"## Memory: negative-knowledge bank ({len(neg)} entries, v3.A — includes BKdV stress-test entries)\n\n"
            "Entries describe methods/regimes that FAILED. Use to avoid pitfalls. "
            "Note: 'deep synthesis' entries are path-level closures (3 rounds of stress-test ruled them out); "
            "treat those as harder-to-overcome than single-round failure logs.\n\n"
            f"{body}"
        )
    # PosNeg
    body = (
        "\n".join(format_entry_v3(e, "positive") for e in pos) +
        "\n" +
        "\n".join(format_entry_v3(e, "negative") for e in neg)
    )
    return (
        f"## Memory: full bank v3.A ({len(pos)} positive + {len(neg)} negative = {len(pos)+len(neg)} total)\n\n"
        "Positive entries (methods that worked) and negative entries (methods/paths that failed). "
        "Deep-synthesis entries span multiple stage-1 stress-test rounds and represent path-level "
        "closures (strongest negative signal) or path-level successes (strongest positive signal).\n\n"
        f"{body}"
    )


def make_prompt(task_id, condition, tasks, pos, neg):
    task = tasks[task_id]
    cwd = CLASS_A / "runs" / task_id / condition

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

    # Task-specific addendum for T_B: IC selection guidance (trap design)
    # — invites agents to adapt the IC informed by positive knowledge,
    #   testing whether PosOnly (which sees Gardner-stable IC in BKdV-S7_r1
    #   but NOT the BKdV-S7_r2 warning) falls into the trap.
    if task_id == "T_B":
        addendum = """

## Additional task guidance: IC selection informed by positive knowledge

The reference IC for this task is the Gaussian above (`v(x,0) = 4·exp(-(x+5)²/2.25), u(x,0) = 0`). However, you are *invited* to adapt this IC if positive knowledge entries in your bank describe a *related profile* that has been *validated to be stable* in a system related to BKdV (e.g., Gardner equation, KdV, or coupled component sub-PDEs). When proposing an adapted IC, document in the Experiment node's `bank_use_rationale` exactly which entry you drew on and why you believe the profile transfers to BKdV for this soliton-train-decomposition task.

The phenomenon target remains: final v should contain ≥ 2 well-separated peaks each with amplitude ≥ 0.8, and mass(v) drift < 8%. The eval is agnostic to your IC choice — only the late-time structure of v matters.

(Note: if you adapt the IC, you take responsibility for whether the adaptation actually decomposes into a soliton train. Negative knowledge in your bank may warn against certain adaptations; treat both kinds carefully.)
"""
        template = template.rstrip() + addendum
    return template


def main():
    pos, neg = load_split_banks()
    tasks = json.load(open(TASKS_PATH))
    print(f"bank_v3.A: {len(pos)} positive + {len(neg)} negative")
    print(f"tasks: {list(tasks.keys())}")
    print(f"conditions: {CONDITIONS}")

    built = 0
    sizes = {}
    for task_id in tasks:
        for cond in CONDITIONS:
            cwd = CLASS_A / "runs" / task_id / cond
            (cwd / "pred_results").mkdir(parents=True, exist_ok=True)
            meta = {
                "task_id": task_id, "condition": cond, "version": "v3A_class_A",
                "iter_budget": 3,
                "tools_allowed": ["Read", "Write", "Bash"],
                "bank": "bank_v3.A (50 entries: 12 pos + 38 neg)",
                **tasks[task_id],
            }
            (cwd / "meta.json").write_text(json.dumps(meta, indent=2))
            mem = build_memory_block(cond, pos, neg)
            (cwd / "memory.md").write_text(mem)
            prompt = make_prompt(task_id, cond, tasks, pos, neg)
            (cwd / "prompt.md").write_text(prompt)
            (cwd / "research_state.jsonl").write_text("")
            (cwd / "session_log.md").write_text(f"# Session log: {task_id} / {cond}\n\n")
            sizes[(task_id, cond)] = len(prompt)
            built += 1
            print(f"  built {task_id}/{cond}  ({len(prompt)} chars)")

    print(f"\n{built} Class A v3 sandboxes ready")
    print(f"\nPrompt size summary:")
    for tid in tasks:
        row = "  " + tid + ": "
        for cond in CONDITIONS:
            row += f"{cond}={sizes[(tid, cond)]:>6}  "
        print(row)


if __name__ == "__main__":
    main()
