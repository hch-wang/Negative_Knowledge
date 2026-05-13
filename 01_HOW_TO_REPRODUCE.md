# How to Reproduce

Two modes:

- **Mode A — Replay only**: re-run all `candidate.py` scripts and eval against the saved artifacts. **No LLM API needed.** ~15 min, validates that all 43 saved runs reproduce their reported outcomes.
- **Mode B — Full pipeline**: re-dispatch all 43 sub-agents from the saved prompts. **Requires LLM API access.** ~80 min wall, produces functionally equivalent (but not bit-identical) results.

---

## Mode A — Replay only (no API)

### Prerequisites

Python 3.11+ with:
```
numpy >= 1.25
scipy >= 1.11
matplotlib >= 3.7
```

Create a venv at the **repo root** so the scripts find it (this is the only env-specific assumption):

```bash
cd Negative_Knowledge/
python3 -m venv .venv
source .venv/bin/activate
pip install numpy scipy matplotlib
```

### Step 1 — Replay Stage 1 candidates

```bash
cd stage1_knowledge_production/
# Each sandbox's candidate.py is self-contained (uses numpy/scipy only)
for sandbox in 04_outputs/A* 04_outputs/G*; do
    echo "Running $sandbox"
    (cd "$sandbox" && ../../../../.venv/bin/python candidate.py)
done
```

This regenerates each `pred_results/*.npy` and is bit-identical to the saved outputs (modulo BLAS non-determinism on certain platforms).

### Step 2 — Replay Stage 2 candidates (3 tasks × 3 conditions × up to 3 rounds = 23 runs)

```bash
cd stage2_coupled_study/
# Use the existing run scripts — they iterate over all sandbox dirs
../.venv/bin/python 03_scripts/run_round1.py
../.venv/bin/python 03_scripts/run_round2.py
../.venv/bin/python 03_scripts/run_round3.py
```

**Note**: these scripts have hardcoded absolute paths (legacy from the original experiment). Update line 6 of each (`ROOT = pathlib.Path(...)`) to point to your local `stage2_coupled_study/04_outputs/` directory before running.

### Step 3 — Re-evaluate phenomenon checks

The eval logic lives in `stage2_coupled_study/03_scripts/eval/phenomenon_checks.py`. The run scripts above already invoke it. To re-run eval only on existing `pred_results/*.npy`:

```bash
cd stage2_coupled_study/04_outputs/T_A/PosNeg/round1
python -c "
import sys; sys.path.insert(0, '../../../../03_scripts/eval')
from phenomenon_checks import EVALS
useful, diag = EVALS['T_A']('pred_results/T_A.npy')
print('useful:', useful, 'diag:', diag)
"
```

### Step 4 — Audit the knowledge bank

```bash
cd stage1_knowledge_production/05_knowledge_bank/
python -c "
import json, pathlib
bank = pathlib.Path('knowledge_bank.jsonl')
entries = [json.loads(l) for l in bank.open()]
print(f'Total entries: {len(entries)}')
print(f'  positive: {sum(1 for e in entries if e[\"kind\"]==\"positive\")}')
print(f'  negative: {sum(1 for e in entries if e[\"kind\"]==\"negative\")}')

# Audit: every entry must cite a valid file (under \${PROJECT_ROOT}/...)
# In this repo, \${PROJECT_ROOT} maps to the parent of stage1_knowledge_production/
PROJECT_ROOT = pathlib.Path('../../..').resolve() / 'Negative_Knowledge'
valid = 0
for e in entries:
    for ev in e.get('evidence', []):
        f = ev['file'].replace('\${PROJECT_ROOT}', str(PROJECT_ROOT))
        if pathlib.Path(f).exists():
            valid += 1
            break
print(f'Audit: {valid}/{len(entries)} entries cite at least one existing evidence file')
"
```

---

## Mode B — Full pipeline (with LLM API)

This re-dispatches all 43 sub-agents. Results will be **functionally equivalent** (same method choices in most cases) but **not bit-identical** because Sonnet 4.6 sampling is non-deterministic.

### Prerequisites

In addition to Mode A's deps:

- An Anthropic API key (`anthropic` Python SDK) **or** Claude Code with Agent tool access
- Sonnet 4.6 model availability

### Two sub-agent backends

The original experiment used **Claude Code's `Agent` tool** which is not directly portable. To re-run, two options:

#### Option B.1 — Claude Code (original setup)
Open this repo in Claude Code. For each prompt in `stage1_knowledge_production/02_prompts/A*.md` and `stage2_coupled_study/02_prompts/round*/T_*.md`, dispatch a sub-agent with:

```
Read <prompt-file>. Follow its instructions exactly.
Use Read once on this prompt + Write twice (candidate.py + reasoning.md). No other tools.
Return ONE short sentence describing your numerical scheme.
```

Set sub-agent model to `sonnet` (= Sonnet 4.6).

This will write `candidate.py` and `reasoning.md` to each sandbox dir. Then run Mode A steps 1–3 to evaluate.

#### Option B.2 — Anthropic SDK (portable)
Use the `anthropic` Python SDK. Pseudo-code:

```python
from anthropic import Anthropic
import pathlib, json

client = Anthropic()
for prompt_file in pathlib.Path('stage1_knowledge_production/02_prompts').glob('A*.md'):
    prompt = prompt_file.read_text()
    # Adjust ${PROJECT_ROOT} in prompt to your local repo path
    prompt = prompt.replace('${PROJECT_ROOT}', str(pathlib.Path.cwd()))

    msg = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=20000,
        messages=[{'role': 'user', 'content': prompt}]
    )
    # The response should contain "```python ... ```" for candidate.py
    # and a markdown explanation for reasoning.md. Parse and save.
    ...
```

You'll need to parse the response and split into candidate.py / reasoning.md. The original Agent-tool runs did this automatically via the Write tool; with the SDK you parse text yourself.

### Step 3 — Re-run Stage 1 curator

After all 14 stress tests run, dispatch the curator:

```
Read stage1_knowledge_production/02_prompts/curator_v1.md and follow it.
Then run curator_v2_extension.md to extend with Gardner findings.
```

Curator output is `knowledge_bank.jsonl`. Then dispatch a final curator pass to top up to ~30 entries if needed (see `curator_v2_extension.md` for the prompt; the third pass was done by SendMessage continuation in the original run).

### Step 4 — Run Stage 2 in three rounds

For each round 1 → 2 → 3:
1. Build sandboxes using `stage2_coupled_study/03_scripts/build_round{N}.py` (adjust paths)
2. Dispatch sub-agents on each new prompt
3. Run Mode A's evaluation

---

## Expected outcomes (sanity check)

After Mode A replay completes, you should observe:

| Verification | Expected value |
|---|---|
| Stage 1 stress-test count | 14 |
| Knowledge bank entries | 30 (10 ✓ + 20 ✗) |
| Stage 2 cells in r1 | 9 (3 tasks × 3 conditions) |
| Stage 2 useful in r1 | 2 (T_A PosNeg, T_C PosNeg) |
| Stage 2 useful across all rounds | 2 (same — no new successes in r2/r3) |
| Total `pred_results/*.npy` files | 45+ |
| `*.json` result files matching `useful: true` | exactly 2 in `results_round*.json` (across all rounds) |

If you run Mode B, you'll likely see the same qualitative pattern (PosNeg >> NoKB ≈ PosOnly) but specific cells passing might differ.

---

## Troubleshooting

- **`candidate.py` blow-up with NaN** — that's the experimental finding for many cells. See `result.json` for the diag. Not a reproduction error.
- **Eval shape mismatch** — `phenomenon_checks.py` expects `(2, Nx)` or `(T_save, 2, Nx)`. If the candidate saved different shape, it's a candidate error (also documented in original experiment).
- **Bank citations point to `${PROJECT_ROOT}`** — paths are anonymized for the repo. Replace with your local absolute path when running audit scripts.

---

## What you cannot reproduce

- **Sub-agent chain-of-thought tokens**: Anthropic's API does not expose the model's internal reasoning to the caller. The closest proxy is `reasoning.md`, the agent's self-reported method narrative.
- **Original wall-clock timing**: depends on hardware and API latency. The token counts in `metadata/agent_calls.csv` are invariant.
