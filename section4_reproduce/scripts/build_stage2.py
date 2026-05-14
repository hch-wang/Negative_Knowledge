#!/usr/bin/env python3
"""Build 12 Stage-2 BKdV sandboxes inside REPRO_RUNS/stage2.

The builder prefers a freshly aggregated bank in REPRO_RUNS/banks. If
that does not exist, it falls back to the bundled canonical bank under
logs/banks so the release remains directly runnable.
"""
import json

from _paths import (
    BANKS, PROMPTS, PY, RUNS, STAGE2_CONDS, STAGE2_TASKS, TASKS,
)


def resolve_bank_dir():
    generated = RUNS / "banks"
    if ((generated / "bank_positive.jsonl").exists()
            and (generated / "bank_negative.jsonl").exists()):
        return generated
    return BANKS


def load_split_banks(bank_dir):
    pos_path = bank_dir / "bank_positive.jsonl"
    neg_path = bank_dir / "bank_negative.jsonl"
    pos = [json.loads(line) for line in open(pos_path) if line.strip()]
    neg = [json.loads(line) for line in open(neg_path) if line.strip()]
    return pos, neg, pos_path, neg_path


def format_entry_v3(entry, kind_label):
    """Flexible formatter for both v2-legacy and v3-new entries."""
    entry_id = entry.get("task_id") or entry.get("id") or "<unknown>"
    depth_hint = entry.get("_v3_depth_hint", 1)
    depth_str = f" depth={depth_hint}" if depth_hint > 1 else ""
    head = f"### {entry_id}  ({kind_label}{depth_str})"

    if "rounds_summary" in entry:
        body_lines = [
            f"  [DEEP SYNTHESIS, {entry.get('depth', 'N')} rounds]",
            f"  synthesised_diagnosis: {entry.get('synthesised_diagnosis', '')}",
            "  ruled_out_routes:",
        ]
        for route in entry.get("ruled_out_routes", []):
            body_lines.append(f"    - {route}")
        body_lines.append(
            f"  recommended_alternative: {entry.get('recommended_alternative', '')}")
    elif "attempted_route" in entry:
        body_lines = [
            f"  attempted_route: {entry.get('attempted_route', '')}",
            f"  observation: {entry.get('observation', '')}",
            f"  rationale: {entry.get('rationale', '')}",
            "  recommended_alternative: "
            f"{entry.get('recommended_alternative', entry.get('applicability', ''))}",
        ]
        failure = entry.get("failure", {})
        if failure:
            body_lines.append(
                "  failure: "
                f"layer={failure.get('layer','')}, "
                f"scope={failure.get('scope','')}, "
                f"action={failure.get('recommended_action','')}, "
                f"risk={failure.get('risk','')}")
    else:
        body_lines = [
            f"  method: {entry.get('method', '')}",
            f"  claim: {entry.get('claim', '')}",
            f"  regime: {entry.get('regime', '')}",
            f"  applicability: {entry.get('applicability', '')}",
        ]

    if entry.get("is_trivial"):
        body_lines.append(
            f"  is_trivial: true (trivial_degree={entry.get('trivial_degree', 1)})")
    return head + "\n" + "\n".join(body_lines) + "\n"


def build_memory_block(condition, pos, neg):
    if condition == "NoKB":
        return ("## Memory: no knowledge bank.\n\n"
                "You have no prior knowledge bank for this problem family. "
                "Use your general knowledge of PDE numerical methods.\n")
    if condition == "PosOnly":
        body = "\n".join(format_entry_v3(entry, "positive") for entry in pos)
        return (
            f"## Memory: positive-knowledge bank ({len(pos)} entries, v3.A — includes BKdV stress-test entries)\n\n"
            "Entries describe methods/regimes that WORKED. Use as guide for what to try. "
            "Note: some entries are 'deep synthesis' across multiple rounds of stage-1 BKdV programs; "
            "treat those as path-level what-works signals rather than single-shot recommendations.\n\n"
            f"{body}"
        )
    if condition == "NegOnly":
        body = "\n".join(format_entry_v3(entry, "negative") for entry in neg)
        return (
            f"## Memory: negative-knowledge bank ({len(neg)} entries, v3.A — includes BKdV stress-test entries)\n\n"
            "Entries describe methods/regimes that FAILED. Use to avoid pitfalls. "
            "Note: deep-synthesis entries are path-level closures from 3-round stress tests; "
            "treat those as harder-to-overcome than single-round failure logs.\n\n"
            f"{body}"
        )

    body = (
        "\n".join(format_entry_v3(entry, "positive") for entry in pos)
        + "\n"
        + "\n".join(format_entry_v3(entry, "negative") for entry in neg)
    )
    return (
        f"## Memory: full bank v3.A ({len(pos)} positive + {len(neg)} negative = {len(pos)+len(neg)} total)\n\n"
        "Positive entries and negative entries are both available. Deep-synthesis entries span multiple "
        "stage-1 stress-test rounds and represent path-level closures or path-level successes.\n\n"
        f"{body}"
    )


def make_prompt(task_id, condition, tasks, pos, neg, pos_path, neg_path, out_root):
    task = tasks[task_id]
    cwd = out_root / task_id / condition

    if condition == "NoKB":
        bank_pos_path = "(none)"
        bank_neg_path = "(none)"
    elif condition == "PosOnly":
        bank_pos_path = str(pos_path)
        bank_neg_path = "(not provided in this condition)"
    elif condition == "NegOnly":
        bank_pos_path = "(not provided in this condition)"
        bank_neg_path = str(neg_path)
    else:
        bank_pos_path = str(pos_path)
        bank_neg_path = str(neg_path)

    template = (PROMPTS / "stage2_template.md").read_text()
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
        "{venv_py}": str(PY),
        "{memory_block}": build_memory_block(condition, pos, neg),
    }
    for key, value in subs.items():
        template = template.replace(key, value)

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
    bank_dir = resolve_bank_dir()
    pos, neg, pos_path, neg_path = load_split_banks(bank_dir)
    tasks = json.load(open(TASKS / "stage2_definitions.json"))
    out_root = RUNS / "stage2"

    print(f"bank v3.A: {len(pos)} positive + {len(neg)} negative from {bank_dir}")
    print(f"tasks: {STAGE2_TASKS}")
    print(f"conditions: {STAGE2_CONDS}")

    built = 0
    sizes = {}
    for task_id in STAGE2_TASKS:
        for condition in STAGE2_CONDS:
            cwd = out_root / task_id / condition
            (cwd / "pred_results").mkdir(parents=True, exist_ok=True)
            meta = {
                "task_id": task_id,
                "condition": condition,
                "version": "section4_reproduce_v1",
                "iter_budget": 3,
                "tools_allowed": ["Read", "Write", "Bash"],
                "bank": f"bank v3.A ({len(pos)+len(neg)} entries: {len(pos)} pos + {len(neg)} neg)",
                **tasks[task_id],
            }
            (cwd / "meta.json").write_text(json.dumps(meta, indent=2))
            (cwd / "memory.md").write_text(build_memory_block(condition, pos, neg))
            prompt = make_prompt(task_id, condition, tasks, pos, neg,
                                 pos_path, neg_path, out_root)
            (cwd / "prompt.md").write_text(prompt)
            (cwd / "research_state.jsonl").write_text("")
            (cwd / "session_log.md").write_text(
                f"# Session log: {task_id} / {condition}\n\n")
            sizes[(task_id, condition)] = len(prompt)
            built += 1
            print(f"  built {task_id}/{condition}  ({len(prompt)} chars)")

    print(f"\n{built} Stage-2 sandboxes ready under {out_root}")
    print("\nPrompt size summary:")
    for task_id in STAGE2_TASKS:
        row = "  " + task_id + ": "
        for condition in STAGE2_CONDS:
            row += f"{condition}={sizes[(task_id, condition)]:>6}  "
        print(row)


if __name__ == "__main__":
    main()
