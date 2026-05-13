#!/usr/bin/env python3
"""Build Stage 2 round 2 sandboxes for cells that failed in r1.

For each failed (task, condition):
- Re-use same Stage 1 knowledge bank (condition-dependent)
- ADD r1 finding record: what was tried, what failed, why
- Agent has internal memory of own r1 attempt
"""
import json, pathlib

ROOT = pathlib.Path("")
STAGE2 = ROOT / "stage2"
BANK_PATH = ROOT / "stage1/knowledge_bank.jsonl"

TASKS = ["T_A", "T_B", "T_C"]
CONDITIONS = ["NoKB", "PosOnly", "PosNeg"]


def status_of_run(task_id, condition):
    """Read r1 result.json to decide if r2 needed."""
    p = STAGE2 / "runs" / task_id / condition / "round1" / "result.json"
    if not p.exists():
        return "missing"
    r = json.load(open(p))
    return "useful" if r.get("useful") else "fail"


def load_bank():
    return [json.loads(l) for l in open(BANK_PATH) if l.strip()]


def format_entry(e):
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
        return "## Memory: no knowledge bank provided\n\nYou have no prior knowledge bank for this problem family.\n"
    if condition == "PosOnly":
        pos = [e for e in bank if e["kind"] == "positive"]
        return f"## Memory: positive-knowledge bank ({len(pos)} entries)\n\n" + "\n".join(format_entry(e) for e in pos)
    pos_count = sum(1 for e in bank if e["kind"]=="positive")
    return f"## Memory: full positive+negative knowledge bank ({len(bank)} entries; {pos_count} positive, {len(bank)-pos_count} negative)\n\n" + "\n".join(format_entry(e) for e in bank)


def build_r1_finding(task_id, condition):
    """Extract round-1 finding for this cell."""
    r1_dir = STAGE2 / "runs" / task_id / condition / "round1"
    result = json.load(open(r1_dir / "result.json"))
    meta = json.load(open(r1_dir / "meta.json"))
    reasoning = (r1_dir / "reasoning.md").read_text() if (r1_dir / "reasoning.md").exists() else ""
    code = (r1_dir / "candidate.py").read_text() if (r1_dir / "candidate.py").exists() else ""
    exec_log = (r1_dir / "exec.log").read_text() if (r1_dir / "exec.log").exists() else ""
    diag = result.get("diag") or {}

    # what went wrong
    if not result.get("output_exists"):
        what_failed = f"Script crashed (exit_code={result.get('exit_code')}). No output produced."
    elif not diag.get("all_finite", True):
        what_failed = f"Output contains NaN/Inf (numerical blow-up). All 256 values invalid."
    elif diag.get("error"):
        what_failed = f"Output shape error: {diag['error']}"
    elif not result.get("useful"):
        what_failed = f"Output is finite but does NOT satisfy phenomenon target: {diag.get('reason','')}. Diagnostics: {json.dumps({k:v for k,v in diag.items() if k!='reason'}, default=float)}"
    else:
        what_failed = "Actually succeeded (this shouldn't be in r2)."

    # extract one-sentence approach from reasoning
    approach_line = ""
    for line in reasoning.splitlines():
        if "Approach" in line or "Method" in line:
            idx = reasoning.find(line)
            approach_line = reasoning[idx:idx+500].split("\n\n")[0][:400]
            break

    tail_err = "\n".join(exec_log.splitlines()[-10:])
    code_excerpt = code[:1500] if len(code) > 1500 else code

    return f"""## Memory: your own round-1 attempt's finding record

You ALREADY attempted this task once. Here is what happened:

### Round-1 candidate's method (your previous approach)
{approach_line if approach_line else '(approach summary not extracted, see code below)'}

### Round-1 candidate.py (first 1500 chars)
```python
{code_excerpt}
```

### Round-1 outcome
{what_failed}

### Round-1 exec.log tail
```
{tail_err}
```

### Round-2 task
Address what failed. If your previous method was numerically unstable, change it. If it produced wrong-shape output, fix the shape. If it produced wrong-phenomenon output, change parameters or method to recover the target phenomenon. Do NOT repeat the exact same approach.
"""


def make_prompt_r2(task_id, condition, bank):
    """Same as r1 prompt but with r1-finding block prepended to memory."""
    cwd = STAGE2 / "runs" / task_id / condition / "round2"
    meta = json.load(open(STAGE2 / "runs" / task_id / condition / "round1" / "meta.json"))

    pde_block = """## PDE — Coupled Burgers-swept-KdV system (Holm et al. 2025)

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```

with γ = 1, ν = 1. On periodic domain x ∈ [-15, 15], Nx = 256.
"""

    r1_finding = build_r1_finding(task_id, condition)
    bank_block = build_memory_block(condition, bank)
    return f"""You are studying a real coupled PDE system. This is round 2 of an autoresearch iteration. Round 1 failed.

Working directory: {cwd}
You will make EXACTLY TWO Write calls:
1) {cwd}/candidate.py
2) {cwd}/reasoning.md (under 500 words: Approach / Method / Risks / Use of r1 finding / Use of bank)

# Sub-task {task_id}: {meta['title']}

{meta['description']}

{pde_block}

## Initial condition
{meta['ic']}

## Final time
T = {meta['T_final']}

## Required output
Save to: `{meta['output_path']}`
Output shape: {meta['output_shape_spec']}
IMPORTANT: include at least 5 snapshots so eval can measure conservation over time.

## Phenomenon target (this is the eval criterion)
{meta['phenomenon_target']}

There is NO closed-form reference solution. Eval checks (deterministically): finiteness, mass conservation of v, peak count via scipy.signal.find_peaks, amplitude check, boundedness.

{r1_finding}

{bank_block}

## Reasoning note structure
Write reasoning.md with these sections:
- **Method**: what changed vs round 1 and why
- **Use of r1 finding**: explicitly describe what went wrong in r1 and how the new method addresses it
- **Use of bank**: (if memory section is non-empty) explicitly cite which bank entries influenced your new choices by `id`
- **Risks**: 2-3 specific things that could still go wrong

## Hard constraints
1. Use Write tool EXACTLY TWICE.
2. Only numpy, scipy, matplotlib are available.
3. Script must run as `python candidate.py` from the working directory.
4. No Read of any file other than this prompt. No Bash. No Edit.
5. The script must save the output at `{meta['output_path']}` with the correct shape.
6. After the two writes, return ONE short sentence describing your numerical scheme.
"""


def main():
    bank = load_bank()
    print(f"loaded {len(bank)} bank entries")

    needs_r2 = []
    for t in TASKS:
        for c in CONDITIONS:
            st = status_of_run(t, c)
            if st == "fail":
                needs_r2.append((t, c))
    print(f"\n{len(needs_r2)} cells need round 2:")
    for t, c in needs_r2:
        print(f"  - {t}/{c}")

    for t, c in needs_r2:
        cwd = STAGE2 / "runs" / t / c / "round2"
        (cwd / "pred_results").mkdir(parents=True, exist_ok=True)
        prompt = make_prompt_r2(t, c, bank)
        (cwd / "prompt.md").write_text(prompt)
        # copy meta from r1
        meta = json.load(open(STAGE2 / "runs" / t / c / "round1" / "meta.json"))
        meta["round"] = 2
        (cwd / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\n{len(needs_r2)} round-2 sandboxes built")


if __name__ == "__main__":
    main()
