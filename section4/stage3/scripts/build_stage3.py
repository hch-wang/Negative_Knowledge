#!/usr/bin/env python3
"""Build Stage 3 sandboxes for the B-NLS Research Graph experiment.

12 cells total = 4 tasks (T_A, T_B, T_C, T_D) × 3 conditions:
  NoKB    — no knowledge bank
  NLS     — only the NLS-specific bank from stage1_bnls
  NLSBKdV — both NLS bank + BKdV bank from stage1 (cross-domain transfer)
"""
import json, pathlib

PAPER = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper")
SECTION4 = PAPER / "Negative_Knowledge" / "section4"
STAGE3 = SECTION4 / "stage3"

BANK_NLS = SECTION4 / "stage1_bnls" / "bank" / "nls_knowledge.jsonl"
BANK_BKDV_POS = SECTION4 / "stage1" / "bank" / "positive_knowledge.jsonl"
BANK_BKDV_NEG = SECTION4 / "stage1" / "bank" / "negative_knowledge.jsonl"

TASKS_PATH = STAGE3 / "tasks" / "definitions.json"
TEMPLATE_PATH = STAGE3 / "prompts" / "template.md"
VENV_PY = str(PAPER / "experiments" / "pde_pilot_2026-05-11" / ".venv" / "bin" / "python")

CONDITIONS = ["NoKB", "NLS", "NLSBKdV"]


def load_jsonl(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def format_nls_entry(e):
    return (
        f"### {e['id']}  ({e['kind']}, domain={e['domain']}, depth={e['depth']})\n"
        f"  claim: {e['claim']}\n"
        f"  applicability: {e.get('applicability', '')}\n"
        f"  evidence: {e.get('evidence', '')}\n"
        f"  recommended_action: {e.get('recommended_alternative_or_action', '')}\n"
    )


def format_bkdv_positive(e):
    return (
        f"### {e['id']}  (positive, domain={e['domain']})\n"
        f"  method: {e.get('method','')}\n"
        f"  claim: {e.get('claim','')}\n"
        f"  applicability: {e.get('applicability','')}\n"
    )


def format_bkdv_negative(e):
    f = e["failure"]
    return (
        f"### {e['id']}  (negative, domain={e['domain']})\n"
        f"  attempted_route: {e.get('attempted_route','')}\n"
        f"  observation: {e.get('observation','')}\n"
        f"  failure: layer={f['layer']}, scope={f['scope']}, degree={f['degree']}, action={f['recommended_action']}, risk={f['risk']}\n"
        f"  applicability: {e.get('applicability','')}\n"
    )


def build_memory_block(condition, nls, bkdv_pos, bkdv_neg):
    if condition == "NoKB":
        return ("## Memory: no knowledge bank.\n\n"
                "You have no prior knowledge bank. Use general PDE / numerical-methods knowledge.\n")

    if condition == "NLS":
        body = "\n".join(format_nls_entry(e) for e in nls)
        return (
            f"## Memory: NLS-specific knowledge bank ({len(nls)} entries)\n\n"
            "Curated from 8 B-NLS stress tests in stage1_bnls. Mix of positive (recommended methods) "
            "and negative (warned-against routes) entries. The depth field indicates how robustly "
            "the finding has been confirmed:\n"
            "- structural: mathematical identity / algebraic, not a measurement\n"
            "- family-level: confirmed independently by multiple stress tests\n"
            "- multi-experiment: needed comparing >=2 method variants in one test\n"
            "- single-experiment: standard error message — agent could discover this in 1 run\n\n"
            f"{body}"
        )

    # NLSBKdV
    body_nls = "\n".join(format_nls_entry(e) for e in nls)
    body_pos = "\n".join(format_bkdv_positive(e) for e in bkdv_pos)
    body_neg = "\n".join(format_bkdv_negative(e) for e in bkdv_neg)
    return (
        f"## Memory: NLS bank + BKdV bank ({len(nls)} NLS + {len(bkdv_pos) + len(bkdv_neg)} BKdV = "
        f"{len(nls) + len(bkdv_pos) + len(bkdv_neg)} total entries)\n\n"
        "Two banks. The NLS bank is domain-specific (B-NLS / NLS stress-tests). "
        "The BKdV bank is from a related but mechanistically different system (Burgers-swept-KdV). "
        "Some BKdV entries (Burgers shock methods, dealiasing) transfer; some do not "
        "(NLS quantum pressure has no analog in BKdV). **Cross-check before importing BKdV claims.**\n\n"
        f"### Section A — NLS-specific entries\n\n{body_nls}\n\n"
        f"### Section B — BKdV positive entries\n\n{body_pos}\n\n"
        f"### Section C — BKdV negative entries\n\n{body_neg}\n"
    )


def make_prompt(task_id, condition, tasks, nls, bkdv_pos, bkdv_neg):
    task = tasks[task_id]
    cwd = STAGE3 / "runs" / task_id / condition

    if condition == "NoKB":
        bank_nls_path = "(none)"
        bank_bkdv_pos_path = "(none)"
        bank_bkdv_neg_path = "(none)"
    elif condition == "NLS":
        bank_nls_path = str(BANK_NLS)
        bank_bkdv_pos_path = "(not provided)"
        bank_bkdv_neg_path = "(not provided)"
    else:  # NLSBKdV
        bank_nls_path = str(BANK_NLS)
        bank_bkdv_pos_path = str(BANK_BKDV_POS)
        bank_bkdv_neg_path = str(BANK_BKDV_NEG)

    memory_block = build_memory_block(condition, nls, bkdv_pos, bkdv_neg)
    template = TEMPLATE_PATH.read_text()

    subs = {
        "{task_id}": task_id,
        "{task_title}": task["title"],
        "{task_description}": task["description"],
        "{task_ic}": task["ic"],
        "{task_T_final}": str(task["T_final"]),
        "{task_output_path}": task["output_path"],
        "{task_output_shape}": task["output_shape_spec"],
        "{task_phenomenon_target}": task["phenomenon_target"],
        "{task_domain_x}": str(task["domain_x"]),
        "{task_Nx}": str(task["Nx"]),
        "{task_kappa}": str(task["kappa"]),
        "{cwd}": str(cwd),
        "{bank_nls_path}": bank_nls_path,
        "{bank_bkdv_pos_path}": bank_bkdv_pos_path,
        "{bank_bkdv_neg_path}": bank_bkdv_neg_path,
        "{venv_py}": VENV_PY,
        "{memory_block}": memory_block,
    }
    for k, v in subs.items():
        template = template.replace(k, v)
    return template


def main():
    nls = load_jsonl(BANK_NLS)
    bkdv_pos = load_jsonl(BANK_BKDV_POS)
    bkdv_neg = load_jsonl(BANK_BKDV_NEG)
    tasks = json.load(open(TASKS_PATH))

    print(f"banks: {len(nls)} NLS + {len(bkdv_pos)} BKdV-positive + {len(bkdv_neg)} BKdV-negative")
    print(f"tasks: {list(tasks.keys())}")
    print(f"conditions: {CONDITIONS}")

    sizes = {}
    built = 0
    for task_id in tasks:
        for cond in CONDITIONS:
            cwd = STAGE3 / "runs" / task_id / cond
            (cwd / "pred_results").mkdir(parents=True, exist_ok=True)

            meta = {
                "task_id": task_id, "condition": cond, "version": "stage3_bnls_v1",
                "iter_budget": 3,
                "tools_allowed": ["Read", "Write", "Bash"],
                **tasks[task_id],
            }
            (cwd / "meta.json").write_text(json.dumps(meta, indent=2))

            mem = build_memory_block(cond, nls, bkdv_pos, bkdv_neg)
            (cwd / "memory.md").write_text(mem)

            prompt = make_prompt(task_id, cond, tasks, nls, bkdv_pos, bkdv_neg)
            (cwd / "prompt.md").write_text(prompt)

            (cwd / "research_state.jsonl").write_text("")
            (cwd / "session_log.md").write_text(f"# Session log: {task_id} / {cond}\n\n")

            sizes[(task_id, cond)] = len(prompt)
            built += 1
            print(f"  built {task_id}/{cond}  ({len(prompt)} chars)")

    print(f"\n{built} stage 3 sandboxes ready (4 tasks × 3 conditions)")
    print(f"\nPrompt size summary (chars):")
    for tid in tasks:
        row = "  " + tid + ": "
        for cond in CONDITIONS:
            row += f"{cond}={sizes[(tid, cond)]:>6}  "
        print(row)


if __name__ == "__main__":
    main()
