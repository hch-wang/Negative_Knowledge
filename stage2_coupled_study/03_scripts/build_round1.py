#!/usr/bin/env python3
"""Build Stage 2 sandboxes: 3 sub-tasks × 3 conditions × round 1.

Conditions:
  NoKB     — no knowledge bank in prompt
  PosOnly  — only kind=positive entries (10)
  PosNeg   — full bank (30 entries)
"""
import json, pathlib

ROOT = pathlib.Path("")
STAGE2 = ROOT / "stage2"
BANK_PATH = ROOT / "stage1/knowledge_bank.jsonl"

TASKS = {
    "T_A": {
        "title": "Soliton stability in coupled Burgers-swept-KdV",
        "description": "Take a sech^2 soliton IC for v with u initially close to (but not exactly) v^2/2, propagate the coupled system long-time, and study whether the soliton structure survives.",
        "ic": """v(x, 0) = 2 * sech^2(x + 5)
u(x, 0) = 0.5 * v(x, 0)^2 + 0.2 * v(x, 0)
  (Note: u != v^2/2 exactly, so we are perturbed from the m=0 Gardner reduction by 0.2 v.)""",
        "T_final": 8.0,
        "output_path": "pred_results/T_A.npy",
        "output_shape_spec": "shape (n_snapshots, 2, 256) where dim-1 channels are (u, v); save at least 5 snapshots evenly spaced from t=0 to t=T_final. The LAST snapshot is what eval focuses on but having time-series is useful for diagnostics.",
        "phenomenon_target": "Final v(x, T) should still contain a single dominant peak with amplitude >= 0.5 of the initial 2.0. mass(v) should drift < 8%. Both u and v should stay bounded (|max| < 15).",
    },
    "T_B": {
        "title": "Gaussian wave packet -> soliton train decomposition",
        "description": "Initialize v as a localized Gaussian wave packet in v (u=0 initially) and check whether the dispersive coupling decomposes it into a train of solitons (a hallmark of KdV-type integrable inverse scattering).",
        "ic": """v(x, 0) = 4 * exp(-((x + 5)^2) / 2.25)   (Gaussian, amplitude 4, width sigma=1.5)
u(x, 0) = 0""",
        "T_final": 6.0,
        "output_path": "pred_results/T_B.npy",
        "output_shape_spec": "shape (n_snapshots, 2, 256) where dim-1 channels are (u, v); save at least 5 snapshots. Eval focuses on final snapshot.",
        "phenomenon_target": "Final v should contain >= 2 well-separated peaks each with amplitude >= 0.8 (soliton train). mass(v) drift < 8%.",
    },
    "T_C": {
        "title": "Burgers bore interacting with a KdV soliton",
        "description": "Initialize u as a smoothed bore (descending step) and v as a soliton to its left moving rightward. Study what happens when the soliton encounters the bore: does it transmit (refract), reflect, fuse, or get destroyed?",
        "ic": """u(x, 0) = 1.5 * (1 - tanh(x / 0.5)) / 2     (smoothed bore: u_L = 1.5, u_R = 0, transition centered at 0 with width 0.5)
v(x, 0) = 1.5 * sech^2(x + 8)               (KdV soliton, amplitude 1.5, initially at x = -8, will move right toward bore)""",
        "T_final": 8.0,
        "output_path": "pred_results/T_C.npy",
        "output_shape_spec": "shape (n_snapshots, 2, 256); save 5+ snapshots so the bore-soliton encounter is visible.",
        "phenomenon_target": "Final v should still contain a recognizable peak with amplitude >= 0.5 (soliton survived). u should stay bounded (|u_max| < 5). Bore should not have blown up.",
    },
}

PDE_BLOCK = """## PDE — Coupled Burgers-swept-KdV system (Holm et al. 2025)

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = 1, ν = 1 (both coupling/dispersion coefficients normalized to 1). On periodic domain x ∈ [-15, 15], Nx = 256 grid points.

In the special reduction `m := u - v^2/2 = 0`, the system reduces to a Gardner equation `v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0`.
"""

CONDITION_HEADERS = {
    "NoKB": "## Memory: no knowledge bank provided\n\nYou have no prior knowledge bank for this problem family. Use your general knowledge of PDE numerical methods.\n",
    "PosOnly": "## Memory: positive-knowledge bank ({n} entries)\n\nBelow are positive findings from prior component-PDE stress tests on Burgers, KdV, Shallow Water, and Gardner equations. These describe methods that WORKED in their tested regimes. They do NOT cover failure modes.\n\nEach entry has: id, kind, domain, claim (or method+regime), evidence, applicability to coupled Burgers-swept-KdV.\n\n",
    "PosNeg": "## Memory: full positive+negative knowledge bank ({n} entries)\n\nBelow are findings from prior component-PDE stress tests on Burgers, KdV, Shallow Water, and Gardner equations. Both positive and negative entries:\n- Positive: methods that worked in tested regime\n- Negative: methods that failed, with structured failure record (layer / scope / degree / recommended_action / risk).\n\nEach entry has identifiers and evidence files. Use them to choose your method and to avoid known pitfalls.\n\n",
}


def load_bank():
    entries = [json.loads(l) for l in open(BANK_PATH) if l.strip()]
    return entries


def format_entry(e):
    """Format a single bank entry as compact text for inclusion in prompt."""
    head = f"### {e['id']}  ({e['kind']}, domain={e['domain']})"
    if e["kind"] == "positive":
        body = (
            f"  method: {e.get('method','')}\n"
            f"  claim: {e.get('claim','')}\n"
            f"  regime: {e.get('regime','')}\n"
            f"  applicability: {e.get('applicability','')}"
        )
    else:
        f = e["failure"]
        body = (
            f"  attempted_route: {e.get('attempted_route','')}\n"
            f"  observation: {e.get('observation','')}\n"
            f"  failure: layer={f['layer']}, scope={f['scope']}, degree={f['degree']}, action={f['recommended_action']}, risk={f['risk']}\n"
            f"  rationale: {e.get('rationale','')}\n"
            f"  applicability: {e.get('applicability','')}"
        )
    return f"{head}\n{body}\n"


def build_memory_block(condition, bank):
    if condition == "NoKB":
        return CONDITION_HEADERS["NoKB"]
    if condition == "PosOnly":
        pos = [e for e in bank if e["kind"] == "positive"]
        header = CONDITION_HEADERS["PosOnly"].format(n=len(pos))
        return header + "\n".join(format_entry(e) for e in pos)
    # PosNeg
    header = CONDITION_HEADERS["PosNeg"].format(n=len(bank))
    return header + "\n".join(format_entry(e) for e in bank)


def make_prompt(task_id, condition, bank):
    task = TASKS[task_id]
    cwd = STAGE2 / "runs" / task_id / condition / "round1"
    mem = build_memory_block(condition, bank)
    return f"""You are studying a real coupled PDE system. Your job: write a Python script that numerically solves the system from the specified initial condition for the specified final time, save the (u, v) field at multiple snapshots, and write a reasoning note describing your method, your use of any provided memory, and the risks.

Working directory: {cwd}
You will make EXACTLY TWO Write calls:
1) {cwd}/candidate.py
2) {cwd}/reasoning.md (under 500 words: Approach / Numerical method / Risks / Use of memory)

# Sub-task {task_id}: {task['title']}

{task['description']}

{PDE_BLOCK}

## Initial condition
{task['ic']}

## Final time
T = {task['T_final']}

## Required output
Save to: `{task['output_path']}`
Output shape: {task['output_shape_spec']}

## Phenomenon target (this is the eval criterion)
{task['phenomenon_target']}

There is NO closed-form reference solution for this problem. The phenomenon target above is checked deterministically by a fixed eval script using: (a) finiteness, (b) mass conservation of v, (c) peak count of v at final time via scipy.signal.find_peaks, (d) amplitude check, (e) boundedness of u and v.

{mem}

## Reasoning note structure
Write reasoning.md with these sections:
- **Method**: which numerical schemes you chose for u and v equations (spatial discretization + time integration). Explain why these are appropriate for THIS PDE system specifically.
- **Use of memory**: (if memory section above is non-empty) explicitly cite which bank entries influenced your choices by `id`. Identify entries you considered but REJECTED for this task and why. (If no memory, skip this section.)
- **Risks**: 2-4 specific things that could go wrong with your method on this task.

## Hard constraints
1. Use Write tool EXACTLY TWICE.
2. Only numpy, scipy, matplotlib are available.
3. Script must run as `python candidate.py` from the working directory.
4. No Read of any file other than this prompt. No Bash. No Edit.
5. The script must save the output at `{task['output_path']}` with the correct shape.
6. After the two writes, return ONE short sentence describing your numerical scheme.
"""


def main():
    bank = load_bank()
    print(f"loaded {len(bank)} bank entries")

    built = 0
    for task_id in TASKS:
        for condition in ["NoKB", "PosOnly", "PosNeg"]:
            cwd = STAGE2 / "runs" / task_id / condition / "round1"
            (cwd / "pred_results").mkdir(parents=True, exist_ok=True)
            # save task metadata
            meta = {"task_id": task_id, "condition": condition, "round": 1, **TASKS[task_id]}
            (cwd / "meta.json").write_text(json.dumps(meta, indent=2))
            # save memory block as separate file for audit
            (cwd / "memory.md").write_text(build_memory_block(condition, bank))
            # write prompt
            prompt = make_prompt(task_id, condition, bank)
            (cwd / "prompt.md").write_text(prompt)
            built += 1
            print(f"  built {task_id}/{condition}/round1 ({len(prompt)} chars)")
    print(f"\n{built} round-1 sandboxes ready")

    # also save task definitions for later analysis
    (STAGE2 / "tasks" / "definitions.json").write_text(json.dumps(TASKS, indent=2))


if __name__ == "__main__":
    main()
