#!/usr/bin/env python3
"""Build Stage 2 round 3 sandboxes for cells that failed in r2."""
import json, pathlib

ROOT = pathlib.Path("")
STAGE2 = ROOT / "stage2"
BANK_PATH = ROOT / "stage1/knowledge_bank.jsonl"


def load_bank():
    return [json.loads(l) for l in open(BANK_PATH) if l.strip()]


def format_entry(e):
    head = f"### {e['id']}  ({e['kind']}, domain={e['domain']})"
    if e["kind"] == "positive":
        body = f"  method: {e.get('method','')}\n  claim: {e.get('claim','')}\n  applicability: {e.get('applicability','')}"
    else:
        f = e["failure"]
        body = f"  attempted_route: {e.get('attempted_route','')}\n  observation: {e.get('observation','')}\n  failure: layer={f['layer']}, scope={f['scope']}, action={f['recommended_action']}, risk={f['risk']}\n  applicability: {e.get('applicability','')}"
    return f"{head}\n{body}\n"


def build_memory_block(condition, bank):
    if condition == "NoKB":
        return "## Memory: no knowledge bank.\n"
    if condition == "PosOnly":
        pos = [e for e in bank if e["kind"] == "positive"]
        return f"## Memory: positive-knowledge bank ({len(pos)} entries)\n\n" + "\n".join(format_entry(e) for e in pos)
    return f"## Memory: full positive+negative knowledge bank ({len(bank)} entries)\n\n" + "\n".join(format_entry(e) for e in bank)


def summarize_round(task, cond, round_n):
    rd = STAGE2 / "runs" / task / cond / f"round{round_n}"
    if not (rd / "result.json").exists(): return "  (no data)"
    r = json.load(open(rd / "result.json"))
    reasoning = (rd / "reasoning.md").read_text()[:500] if (rd / "reasoning.md").exists() else ""
    diag = r.get("diag") or {}
    code = (rd / "candidate.py").read_text() if (rd / "candidate.py").exists() else ""
    code_excerpt = code[:800]

    if not r.get("output_exists"):
        what = f"crashed (exit_code={r.get('exit_code')})"
    elif not diag.get("all_finite", True):
        what = "NaN/Inf in output (numerical blow-up)"
    elif diag.get("error"):
        what = f"shape error: {diag['error']}"
    elif r.get("useful"):
        what = "succeeded — should not be here"
    else:
        what = f"finite but did not satisfy phenomenon: {diag.get('reason','')}"

    return f"""### Round {round_n} attempt
Approach (excerpt from reasoning.md):
> {reasoning[:300]}

candidate.py (first 800 chars):
```python
{code_excerpt}
```

Outcome: {what}
Diagnostics: {json.dumps({k:v for k,v in diag.items() if k not in ('reason','error')}, default=float)}
"""


def make_prompt_r3(task, cond, bank):
    cwd = STAGE2 / "runs" / task / cond / "round3"
    meta = json.load(open(STAGE2 / "runs" / task / cond / "round1" / "meta.json"))

    pde_block = """## PDE — Coupled Burgers-swept-KdV system

```
u_t + 3 u u_x = -∂_x (3 v^2 + v_xx)
v_t + 6 v v_x + v_xxx = -∂_x (u v)
```
γ = ν = 1. Periodic x ∈ [-15, 15], Nx = 256.
"""

    r1 = summarize_round(task, cond, 1)
    r2 = summarize_round(task, cond, 2)
    bank_block = build_memory_block(cond, bank)

    return f"""You are in round 3 of an autoresearch iteration on a hard PDE problem. Round 1 and round 2 both failed. This is your last attempt.

Working directory: {cwd}
You will make EXACTLY TWO Write calls:
1) {cwd}/candidate.py
2) {cwd}/reasoning.md (under 500 words: Synthesis of prior failures / Method / Use of bank / Final risks)

# Sub-task {task}: {meta['title']}

{meta['description']}

{pde_block}

## Initial condition
{meta['ic']}

## Final time
T = {meta['T_final']}

## Output
Save to: `{meta['output_path']}`
Output shape: {meta['output_shape_spec']}
IMPORTANT: save at least 5 snapshots so mass conservation can be measured over time.

## Phenomenon target
{meta['phenomenon_target']}

## Your prior failed attempts

{r1}

{r2}

# Synthesis directive
Identify the COMMON FAILURE PATTERN between round 1 and round 2. Do not repeat either approach. If both used variants of explicit time integration, switch to implicit. If both used spectral with same dt, change the dt by an order of magnitude OR change the discretization. If both crashed on the nonlinear term, lower the IC amplitude or change variables.

{bank_block}

## Reasoning note structure
- **Pattern from r1+r2**: what's the COMMON THING that failed in both?
- **New method**: what's qualitatively different in r3?
- **Use of bank**: (if non-empty) cite bank entries by `id`
- **Final risks**

## Hard constraints
1. Use Write tool EXACTLY TWICE.
2. Only numpy, scipy, matplotlib.
3. Script runs as `python candidate.py` from working dir.
4. No Read of other files, no Bash, no Edit.
5. After writes, ONE short sentence describing your method.
"""


def main():
    bank = load_bank()
    needs_r3 = []
    for t in ["T_A", "T_B", "T_C"]:
        for c in ["NoKB", "PosOnly", "PosNeg"]:
            r2 = STAGE2 / "runs" / t / c / "round2" / "result.json"
            if not r2.exists(): continue
            r = json.load(open(r2))
            if not r.get("useful"): needs_r3.append((t, c))
    print(f"{len(needs_r3)} cells need round 3:")
    for t, c in needs_r3: print(f"  {t}/{c}")

    for t, c in needs_r3:
        cwd = STAGE2 / "runs" / t / c / "round3"
        (cwd / "pred_results").mkdir(parents=True, exist_ok=True)
        prompt = make_prompt_r3(t, c, bank)
        (cwd / "prompt.md").write_text(prompt)
        meta = json.load(open(STAGE2 / "runs" / t / c / "round1" / "meta.json"))
        meta["round"] = 3
        (cwd / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"built {len(needs_r3)} round-3 sandboxes")


if __name__ == "__main__":
    main()
