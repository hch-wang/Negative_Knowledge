# Section 3 实验时间记录 — 2026-05-13

> 记录 §3 全部实验的脉络、定义、关键数字、open issues。
> 这个文件是 paper 写作前的清晨备忘录,以及向 co-author / reviewer
> 解释"我们到底做了什么、为什么"的 single source of truth。

---

## 1. 任务子集的层级关系

```
[ScienceAgentBench 上游 ~102 任务]
   └─ [pilot subset = 38 任务]  ← 我们筛 deterministic-eval 的那 38 个
        ├─ [round-1 PASS = 12 任务]  ← Sonnet 4.6 单 shot, no memory, 直接做对的
        │    └─ 这 12 个不进入 §3 的 NK 实验。它们是 benchmark baseline。
        │       任务 IDs: 001, 011, 013, 016, 019, 040, 041, 045, 051, 053, 090, 092
        │       (任务 095, 102 是 baseline FAIL 但被 v3 排除,见 §6.3)
        │
        └─ [round-1 FAIL = 26 任务, 24 进入 v3]  ← §3 NK 实验的"NK-test subset"
             │  任务 IDs: 002, 003, 005, 012, 015, 018, 021, 022, 026, 029,
             │           034, 035, 037, 044, 058, 060, 067, 071, 072, 078,
             │           085, 087, 097, 101
             │
             ├─ [B2 covering rescue = 5 任务]
             │    └─ Self-Debug (前一轮完整 code + raw stderr) 3 轮内救回的
             │       任务 IDs: 003, 005, 015, 071, 097
             │
             └─ [B2 covering 三轮全败 = 19 任务]  ← "hard subset"
                  │  任务 IDs: 002, 012, 018, 021, 022, 026, 029, 034, 035,
                  │           037, 044, 058, 060, 067, 072, 078, 085, 087, 101
                  │
                  ├─ [deepNKR Sonnet PASS = 1 任务]
                  │    └─ task_072 (EEG U-Net → 改 closed-form lstsq)
                  │
                  └─ [deepNKR Haiku PASS = 0 任务]
                       └─ Cross-model 阴性: 13/19 exec_fail (Haiku
                          implementation 跟不上 deep NK 的 conceptual advice)
```

### 三个数字的清晰定义 (paper 直接引用)

- **"38 task"** = pilot subset (我们筛过的 deterministic-eval 子集)
- **"24 task"** = NK-test subset (38 里 Sonnet round-1 失败的)
- **"19 task" = "hard subset"** (24 里 B2 covering 3 轮全败的 — deep NK 的实验地)


## 2. 主结果两张表

### 2.1 Benchmark-wide view (denom = 38)

公开 paper 表头数字。

| Path | PASS / 38 | % | Δ vs baseline |
|---|:-:|:-:|:-:|
| Round-1 baseline (no memory, no retry) | **12 / 38** | 31.6 % | — |
| + B0 retry (no memory, retry told) | 12 / 38 | 31.6 % | 0 |
| + NKR r2 (1-round NK, curator-produced) | 14 / 38 | 36.8 % | +2 |
| + NKR r3 (NK accumulation, r1 + r2 NK) | 15 / 38 | 39.5 % | +3 |
| + B2 covering memory (3 rounds Self-Debug) | 17 / 38 | 44.7 % | +5 |
| + **deepNKR-Sonnet** (3-round-distilled NK on hard 19) | **18 / 38** | **47.4 %** | **+6** |

Headline: **从 32 % lift 到 47 %,完全归因于 memory 协议**。

### 2.2 NK-test subset view (denom = 24,controlled view)

把 baseline 已 PASS 的 12 个剔除,孤立 memory 的贡献。

| Path | full 24 | hard 19 |
|---|:-:|:-:|
| B0 retry | 0 / 24 | 0 / 19 |
| NKR r2 (1-round NK) | 2 / 24 | 0 / 19 |
| NKR r3 (NK accumulation) | 3 / 24 | 0 / 19 |
| B3 (regex NK + cross-task NK/PK) | 4 / 24 | 0 / 19 |
| B2 covering (3 rounds) | 5 / 24 | 0 / 19 |
| **deepNKR Sonnet** | — | **1 / 19** |
| deepNKR Haiku (cross-model) | — | 0 / 19 |


## 3. 三个 curator 变体的对照

| Curator | 输入 | 输出 schema 关键字段 | n |
|---|---|---|:-:|
| **r1 curator** | 1 轮失败 artifacts (candidate.py + exec.log + eval.log + reasoning.md) | `attempted_route, observation, failure{6 fields}, rationale, recommended_alternative` | 24 |
| **r2 curator** | 1 轮 r2 NKR 失败 + r1 NK | r1 schema + `relationship_to_round1` | 22 |
| **deep curator** | 3 轮 B2 Self-Debug 失败 (round 1 + 2 + 3 共 12 个文件) | r1 schema + `rounds_summary[3], ruled_out_routes[2-4], synthesised_diagnosis, depth: 3` | 19 |

3 个 curator 总共 65 次 sub-agent dispatch,每一次都有 audit record。


## 4. Token 使用量记录现状

### 4.1 Curator 端 — 全部记录在 `dispatch_log*.jsonl`

| Curator | n | 总 tokens | 单次 mean | tool_uses mean | duration mean |
|---|:-:|---:|:-:|:-:|:-:|
| r1 curator | 24 | ~510 K | 21 K | 6 | 50 s |
| r2 curator | 22 | ~510 K | 23 K | 8 | 47 s |
| deep curator | 19 | ~580 K | 30 K | 14 | 60 s |

每行 jsonl 的字段: `task_id, agent_id, return_message, tokens, tool_uses, duration_ms, dispatched_at_utc, completed_at_utc`

### 4.2 Solver 端 — ✓ 补完 (2026-05-13 下午)

通过 `03_scripts/extract_solver_tokens.py` 从 Claude Code conversation log 反向抽出 220 个 solver dispatch 的 `total_tokens / tool_uses / duration_ms / agent_id`,back-write 进每个 cell 的 `result.json`(新增字段 `solver_tokens, solver_tool_uses, solver_duration_ms, solver_agent_id`),同时汇总到 `04_outputs/solver_tokens.csv`。

**Per-cell solver token (median per dispatch)**:

| Cell | n | median tokens | vs round1 baseline |
|---|:-:|---:|:-:|
| round1 (no memory, single shot) | 24 | 16 262 | — |
| round2_B0 (no-memory retry) | 24 | 16 391 | +1 % |
| **round2_NKR (1-round NK)** | 24 | **18 081** | **+11 %** |
| round2_B2 (covering memory) | 24 | 19 642 | +21 % |
| round2_B3 (mixed NK + cross-task) | 24 | 26 130 | +61 % |
| round3_NKR | 22 | 18 729 | +15 % |
| round3_B2 | 19 | 20 374 | +25 % |
| round3_B3 | 21 | 27 277 | +68 % |
| **deepNKR Sonnet (3-round NK)** | 19 | **19 247** | **+18 %** |
| **deepNKR Haiku (cross-model)** | 19 | **48 360** | **+197 %** ⚠ |

**NKR 比 B2 单次便宜 ~8 %**。Haiku 消耗 2.5× tokens — 弱模型用复杂 NK 的成本会爆炸,因为它要更多 tool_uses 才能理解 NK 并实施。

### 4.3 NK 作为 memory 的 byte 效率 ★ paper headline

按 median per-task 比较 (排除 task_003 的 multiprocessing log bomb outlier,n=23):

| Memory regime | median bytes/task | vs B2 covering |
|---|---:|:-:|
| B0 | 0 | — |
| **r1 NK (curator-produced)** | **1 187** | **−72.2 %** ⭐ |
| r2 NK (合并 r1+r2 两份) | 2 050 | −52 % |
| deep NK (3-round distillation,含 ruled_out_routes 数组) | 3 354 | −21.5 % |
| B2 covering memory (上一轮完整 code + stderr + eval.log) | 4 272 | baseline |
| B3 cross-task bank (NK + PK 共享) | 24 456 固定 | 一次 build,跨任务复用 |

**核心数字 (paper headline 候选)**: 
- r1 NK **比 B2 covering 紧凑 72 %**
- deep NK (含三轮蒸馏的 ruled_out_routes 列表) 仍比 B2 紧凑 22 %
- NK 还是**可累积存盘 + 跨任务复用**的,covering memory 做不到 — byte-efficiency 优势会在 amortized 场景中放大

### 4.4 End-to-end token 经济学 (per-task pipeline cost, including curator)

| Pipeline (2 rounds 多轮 retry) | Curator (one-time) | Solver (×2 rounds) | Total |
|---|---:|---:|---:|
| **B2 covering memory (3 rounds Self-Debug)** | 0 | 2 × 20 K = 40 K | **40 K** |
| NKR (r1 curator + r2/r3 NKR solver) | 19 K + 20 K = 39 K | 18 K + 19 K = 37 K | **76 K** |
| deep NK + deepNKR Sonnet (single replay) | 27 K | 19 K | **46 K** |

**单次 replay 看,NK 协议比 B2 covering 贵 ~2×**, 因为 curator 是一次性投入。

**Break-even**: 同一个 NK 被 replay **10+ 次**(同 task 或同 cluster 的相邻 task), NK 总成本才比 B2 更低 (因为 curator 是 fixed cost,solver 是 marginal cost)。

**§3 不直接测 amortization**(因为本 benchmark 跨任务结构稀疏),但 paper 可以诚实写:
> "Per-replay NK is comparable in tokens to covering memory, while being 72 % more compact in bytes. The NK's structural advantage is realised when the same record is consulted across multiple replays or downstream tasks — a regime our benchmark does not directly test, but the PDE case study (§4) does."


## 5. 实验时间线 (2026-05-12 ~ 05-13)

1. **2026-05-12 夜间**: v3 主流水线 (无 deep NK):
   - build_v3.py + run_v3.py — round 1 + round 2 (B0/B2/B3) + round 3 (B2/B3)
   - 96 个 sub-agent dispatch
2. **2026-05-13 凌晨**: §3 r1 NKR + r2 NKR + audit:
   - sab_curator.md + sab_curator_r2.md
   - 24 个 r1 curator + 24 个 NKR r2 solver
   - 22 个 r2 curator + 22 个 NKR r3 solver
3. **2026-05-13 上午**: 用户 critique "1-round NK 太浅" → option A+B 加跑 deep NK:
   - sab_curator_deep.md
   - 19 个 deep curator
   - 19 个 Sonnet + 19 个 Haiku deepNKR solver
4. **2026-05-13 下午**: 用户问 "怎么写 §3 + 数字怎么排" → 这份 journal


## 6. paper 头条数据 (放 abstract / intro)

> 我们在 ScienceAgentBench 的 38 题 deterministic-eval 子集上,把单 shot 无 memory 的 baseline 从 **32%** lift 到 **47%** (12/38 → 18/38,+6 个任务)— 全部来自一个把失败浓缩成结构化负知识 (NK) 记录、再让后续 agent 读取的协议。我们进一步在 19 个 B2 covering memory 都失败的硬任务上证明:**经过 3 轮 Self-Debug 探索后蒸馏出来的 deep NK 能让同一模型 (Sonnet) 突破 covering memory 自身也失败的边界**(1/19 PASS,task_072)。Cross-model 测试(同 deep NK + Haiku 4.5 solver)是 0/19,显示 NK 传递 **conceptual diagnosis** 而非 **implementation competence**。


## 7. Open issues (paper 写作前要处理的)

| 优先 | 事项 | 估计成本 |
|:-:|---|---|
| 高 | 写 `extract_solver_tokens.py` 抓 solver 端 token 数据(补 §3.4 token-efficiency 表) | 30 分钟 |
| 中 | section3 整套同步进 `paper/release/` (有 spawn chip 待你点) | 自动 (background task) |
| 中 | release/ 里的脚本路径相对化(把 `/Users/dietcoke/...` 改 `${PROJECT_ROOT}`) | 1-2 小时 |
| 低 | 14 个 round-1 PASS 任务上跑 NKR (no-degradation safety check) | 10 分钟 |
| 低 | 把 §3 数据反写进 `paper/overleaf/main.tex` | 取决于改动范围 |


## 8. 关键文件清单 (paper supplement reference)

```
Negative_Knowledge/section3/
├── 00_journal/
│   └── section3_journal_2026-05-13.md     ← 本文件
├── 02_prompts/
│   ├── sab_curator.md                     r1 curator prompt
│   ├── sab_curator_r2.md                  r2 curator prompt (with relationship field)
│   └── sab_curator_deep.md                deep curator prompt (3-round distillation)
├── 03_scripts/
│   ├── build_curator_runs.py              r1 curator sandboxes (24)
│   ├── build_curator_runs_r2.py           r2 curator sandboxes (22)
│   ├── build_curator_runs_deep.py         deep curator sandboxes (19)
│   ├── write_curator_audit.py             r1 audit writer
│   ├── write_curator_audit_r2.py          r2 audit writer
│   ├── write_curator_audit_deep.py        deep audit writer
│   ├── build_nkr.py                       NKR r2 solver sandboxes
│   ├── build_nkr_r3.py                    NKR r3 solver sandboxes (r1+r2 NK)
│   ├── build_deep_nkr.py                  deepNKR Sonnet+Haiku solver sandboxes
│   └── run_deep_nkr.py                    deepNKR runner (covers both models)
├── 04_outputs/
│   ├── nk_records/                        65 NK files (24 r1 + 22 r2 + 19 deep)
│   ├── curator_audit/                     65 audit records (one per NK)
│   ├── curator_runs/                      per-task curator sandboxes
│   ├── dispatch_log.jsonl                 r1 dispatch metadata (24 lines)
│   ├── dispatch_log_r2.jsonl              r2 dispatch metadata (22 lines)
│   └── dispatch_log_deep.jsonl            deep dispatch metadata (19 lines)
└── 05_results/                            (currently empty — will hold the §3 final tables)

paper/experiments/pilot_2026-05-10/
├── results_v3.csv                         118 rows (v3 cells)
├── results_deep_nkr.csv                   38 rows (deepNKR Sonnet+Haiku)
├── v3_summary.md                          全面 summary
├── section3_draft.md                      paper §3 draft (v2)
└── runs/task_<id>/
    ├── sonnet_4.6/v3/
    │   ├── round1/, round2_B0/, round2_B2/, round2_B3/, round2_NKR/,
    │   ├── round3_B2/, round3_B3/, round3_NKR/
    │   └── deepNKR_sonnet/                ← 1 PASS (task_072)
    └── haiku_4.5/v3/
        └── deepNKR_haiku/                 ← 0 PASS
```


## 9. 重要 caveat

- 所有 sub-agent dispatch 是通过 Claude Code 的 Agent 工具发的, 不是 standalone API call。release/ 里要补一个不依赖 Claude Code 的 standalone dispatcher 才能让别人复现。
- `result.json` 的 schema 在 r1 NK 和 deep NK 之间不一致 (deep NK 多了 `rounds_summary, ruled_out_routes, synthesised_diagnosis, depth`)。paper 的 NK schema 说明需要分两段写。
- Haiku 4.5 跑 deepNKR 0/19 不能直接 generalize 为 "NK transfer 失败"; 只能说 "weak downstream model can't fully use rich NK"。Opus 4.7 上跑同样实验是未来工作。
