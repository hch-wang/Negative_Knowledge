#!/usr/bin/env python3
"""Build sandbox prompts for the 4×4 = 16 Stage-3 cells (B-NLS appendix).

This self-contained builder reads bank files from the appendix's own
bank/ directory and writes cell artifacts under logs/stage3/.

Usage:
  python scripts/build_sandboxes.py                # rebuild all 16 cells
  python scripts/build_sandboxes.py --task T_C    # subset by task
  python scripts/build_sandboxes.py --cond BKdV   # subset by condition
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _paths import (
    REPRO_ROOT, LOGS_DIR, STAGE3_TASKS, STAGE3_TEMPLATE,
    BANK_NLS, BANK_BKDV_POS, BANK_BKDV_NEG, PY_VENV,
    CONDITIONS, TASKS, cell_dir,
)


def load_jsonl(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def format_nls_entry(e):
    return (
        f"### {e['id']}  ({e['kind']}, domain={e['domain']}, depth={e['depth']})\n"
        f"  claim: {e['claim']}\n"
        f"  applicability: {e.get('applicability','')}\n"
        f"  evidence: {e.get('evidence','')}\n"
        f"  recommended_action: {e.get('recommended_alternative_or_action','')}\n"
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
        f"  failure: layer={f['layer']}, scope={f['scope']}, degree={f['degree']}, "
        f"action={f['recommended_action']}, risk={f['risk']}\n"
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
            "Curated from 8 B-NLS stress tests in the appendix's stage 1. Entries are tagged with depth:\n"
            "- structural: mathematical identity / algebraic, not a measurement\n"
            "- family-level: confirmed independently by multiple stress tests\n"
            "- multi-experiment: needed comparing >=2 method variants in one test\n"
            "- single-experiment: standard error message — agent could discover this in 1 run\n\n"
            f"{body}"
        )
    if condition == "BKdV":
        body_pos = "\n".join(format_bkdv_positive(e) for e in bkdv_pos)
        body_neg = "\n".join(format_bkdv_negative(e) for e in bkdv_neg)
        return (
            f"## Memory: BKdV knowledge bank ONLY ({len(bkdv_pos)}+{len(bkdv_neg)}={len(bkdv_pos)+len(bkdv_neg)} entries)\n\n"
            "This bank is from a RELATED-BUT-DIFFERENT system (Burgers-swept-KdV — Holm 2025), "
            "constructed in Section §3 of this paper. **No NLS-specific entries available.** "
            "Some BKdV entries cover shared mechanisms with B-NLS (Burgers shock methods, dealiasing, "
            "mass-conservation-not-sufficient). Other entries are mechanism-mismatched: the v_xxx KdV "
            "dispersion has no analog in B-NLS, Gardner cubic-amplitude CFL does not apply to NLS Kerr, "
            "shallow-water HLL/Lax-Friedrichs assume non-Madelung hydrodynamics. **NLS Madelung quantum "
            "pressure (sqrt N)_xx/(2 sqrt N) has NO analog in this bank — reason from general principles.**\n\n"
            f"### Section B — BKdV positive entries\n\n{body_pos}\n\n"
            f"### Section C — BKdV negative entries\n\n{body_neg}\n"
        )
    # NLSBKdV
    body_nls = "\n".join(format_nls_entry(e) for e in nls)
    body_pos = "\n".join(format_bkdv_positive(e) for e in bkdv_pos)
    body_neg = "\n".join(format_bkdv_negative(e) for e in bkdv_neg)
    return (
        f"## Memory: NLS bank + BKdV bank ({len(nls)} NLS + {len(bkdv_pos)+len(bkdv_neg)} BKdV = "
        f"{len(nls)+len(bkdv_pos)+len(bkdv_neg)} total entries)\n\n"
        "Two banks. NLS bank is domain-specific (B-NLS / NLS stress tests). BKdV bank is from a "
        "related but mechanistically different system. Some BKdV entries transfer; some do not. "
        "**Cross-check before importing BKdV claims.**\n\n"
        f"### Section A — NLS-specific entries\n\n{body_nls}\n\n"
        f"### Section B — BKdV positive entries\n\n{body_pos}\n\n"
        f"### Section C — BKdV negative entries\n\n{body_neg}\n"
    )


def make_prompt(task_id, condition, tasks, nls, bkdv_pos, bkdv_neg):
    task = tasks[task_id]
    cwd = cell_dir(task_id, condition)

    if condition == "NoKB":
        bank_nls_path = "(none)"; bank_bkdv_pos_path = "(none)"; bank_bkdv_neg_path = "(none)"
    elif condition == "NLS":
        bank_nls_path = str(BANK_NLS); bank_bkdv_pos_path = "(not provided)"; bank_bkdv_neg_path = "(not provided)"
    elif condition == "BKdV":
        bank_nls_path = "(not provided)"; bank_bkdv_pos_path = str(BANK_BKDV_POS); bank_bkdv_neg_path = str(BANK_BKDV_NEG)
    else:
        bank_nls_path = str(BANK_NLS); bank_bkdv_pos_path = str(BANK_BKDV_POS); bank_bkdv_neg_path = str(BANK_BKDV_NEG)

    memory_block = build_memory_block(condition, nls, bkdv_pos, bkdv_neg)
    template = STAGE3_TEMPLATE.read_text()

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
        "{venv_py}": PY_VENV,
        "{memory_block}": memory_block,
    }
    for k, v in subs.items():
        template = template.replace(k, v)
    return template


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=TASKS, default=None)
    p.add_argument("--cond", choices=CONDITIONS, default=None)
    args = p.parse_args()

    nls = load_jsonl(BANK_NLS)
    bkdv_pos = load_jsonl(BANK_BKDV_POS)
    bkdv_neg = load_jsonl(BANK_BKDV_NEG)
    tasks = json.load(open(STAGE3_TASKS))

    print(f"banks: {len(nls)} NLS + {len(bkdv_pos)} BKdV-positive + {len(bkdv_neg)} BKdV-negative")

    targets_t = [args.task] if args.task else TASKS
    targets_c = [args.cond] if args.cond else CONDITIONS

    built = 0
    for tid in targets_t:
        for cond in targets_c:
            cwd = cell_dir(tid, cond)
            (cwd / "pred_results").mkdir(parents=True, exist_ok=True)
            meta = {"task_id": tid, "condition": cond, "version": "appendix_reproduce_v1",
                    "iter_budget": 3, **tasks[tid]}
            (cwd / "meta.json").write_text(json.dumps(meta, indent=2))
            (cwd / "memory.md").write_text(build_memory_block(cond, nls, bkdv_pos, bkdv_neg))
            prompt = make_prompt(tid, cond, tasks, nls, bkdv_pos, bkdv_neg)
            (cwd / "prompt.md").write_text(prompt)
            # Initialize empty research_state.jsonl and session_log if not already populated
            rs = cwd / "research_state.jsonl"
            if not rs.exists() or rs.stat().st_size == 0:
                rs.write_text("")
            sl = cwd / "session_log.md"
            if not sl.exists():
                sl.write_text(f"# Session log: {tid} / {cond}\n\n")
            built += 1
            print(f"  built {tid}/{cond}  ({len(prompt)} chars)")

    print(f"\n{built} cells ready under {LOGS_DIR}/stage3/")


if __name__ == "__main__":
    main()
