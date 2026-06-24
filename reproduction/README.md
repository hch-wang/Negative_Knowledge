# Reproducing the paper

Everything behind the numbers in *Negative Knowledge as Failure-aware
Shared Memory for AutoResearch*, one subdirectory per study:

- [`section3/`](section3/) — §3 ScienceAgentBench negative-knowledge retry study
- [`section4/`](section4/) — §4 BKdV controlled memory-condition study
- [`appendix/`](appendix/) — Burgers-NLS appendix cross-system transfer study

Each subdirectory is **self-contained**: it bundles the run's logs,
banks, prompts, eval scripts, and its own copy of the curator code used
for that study, so it reproduces the exact run reported in the paper.
(The clean, reusable version of the curator lives in the top-level
[`negative_knowledge/`](../negative_knowledge) module.)

## Two ways to reproduce

**Verify-only (no API key, seconds).** Every reported number is backed
by a file already checked into `logs/`. Each study ships an
`analyze_results.py` that recomputes its paper claims from those files:

```bash
cd section3 && python3 analyze_results.py    # 31/31 claims match
cd section4 && python3 analyze_results.py    # 20/20 claims match
cd appendix && python3 analyze_results.py    # 54/54 claims match
```

§3 additionally ships `count_tokens.py`, which reproduces the Table 1
memory-object token figures (296 / 1,109 / 795) from
`logs/memory_tokens.json` — stdlib only, no install.

**End-to-end (your agent stack).** Fresh runs use a provider-neutral command
adapter and rebuild the artifacts:

```bash
python3 -m pip install -r requirements.txt
export NK_AGENT_COMMAND="python3 /absolute/path/to/agent_adapter.py"

# §3: rerun the depth-3 deepNKR pipeline on the breakthrough task
cd section3
git clone https://github.com/OSU-NLP-Group/ScienceAgentBench
export SAB_BENCH=$(pwd)/ScienceAgentBench/benchmark
python3 run_pipeline.py --task 072 --use-saved-trace

# §4: rerun one Stage-2 cell against the saved bank
cd section4 && python3 run_pipeline.py --task T_C --cond NegOnly --use-saved-trace

# appendix: rerun one Burgers-NLS cell
cd appendix && python3 run_pipeline.py --task T_C --cond NLS --use-saved-trace
```

`--use-saved-trace` reuses bundled inputs and only re-dispatches the
downstream sub-agent (fastest fresh-agent path). Due to model
non-determinism, re-runs reproduce the *direction* of each finding but
not byte-identical artifacts. Each subdirectory's own `README.md` has
the full per-study guide.

`NK_AGENT_COMMAND` receives one JSON object on stdin. It contains the prompt,
model name, read/write allowlists, iteration limit, and declared capabilities.
The adapter performs the agent run, writes only the allowed outputs, exits 0,
and prints one JSON metadata object on stdout. Model aliases can be mapped with
environment variables such as `NK_MODEL_DEFAULT`.
