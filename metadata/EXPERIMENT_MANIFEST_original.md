# PDE Pilot — Experiment Manifest & Audit Trail

> 完成日期：2026-05-12
> 文档目的：记录全部实验过程，区分**什么有完整存盘 / 什么没有 / 为什么**。
> 总文件数：331（含数值快照）；不含数值数据共 ~280 个文本/结构化文件。

---

## 1. 储存情况总览

### ✅ 完整存盘（每个 sub-agent 调用都有）

| 文件 | 含义 | 数量 | 用途 |
|---|---|---|---|
| `prompt.md` | sub-agent 收到的完整 prompt（含 memory 块） | 40 | **完整可复现实验输入** |
| `memory.md` | 注入的 bank 内容（独立保存便于审计） | 9 (Stage 2) | 验证 condition 间差异 |
| `candidate.py` | sub-agent 写的求解器代码 | 40 | agent 的"行动" |
| `reasoning.md` | sub-agent 自陈方法/risk/use of memory | 40 | **agent 的"思考记录"**（自然语言形式） |
| `exec.log` | 候选脚本的 stdout/stderr/exit_code/duration | 37 | 实际执行结果 |
| `result.json` | 结构化结果（exit, diag, useful） | 38 | 主分析数据 |
| `eval_result.json` | phenomenon 检查详情 | 16 | Stage 2 评分依据 |
| `meta.json` | task 定义 / round / condition | 37 | 复现实验需要的元数据 |
| `pred_results/*.npy` | 数值场快照（u 和 v） | 45 | **物理结果原始数据** |
| `knowledge_bank.jsonl` | Stage 1 产出的 30 条 ✓/✗ 知识 | 1 | **核心实验产物** |
| `results_round{1,2,3}.json` | 每轮所有 cells 的汇总 | 3 | 主表分析 |
| `STAGE1_INDEX.md` | Stage 1 中文索引 | 1 | 人类可读总览 |
| `STAGE2_REPORT.md` | Stage 2 完整报告 | 1 | 含三 condition 主表 |
| `PDE_CASE_STUDIES.md` | 早期 BKdV 案例 | 1 | 含 G case（KdV NaN→PASS）|
| `PDE_TEST_SET.md` / `PDE_EXPERIMENT_PLAN.md` | 设计文档 | 2 | 评审用 |

### ⚠️ 部分存盘（一句话总结有，详细 trace 没有）

| 内容 | 哪有 | 哪没有 |
|---|---|---|
| sub-agent 1-sentence summary（每次返回） | 本文件 §3 表格 | 单独的 per-call 文件 |
| sub-agent 的 token 用量 | 本文件 §3 表格 | 单独的 per-call 文件 |
| sub-agent 的 wall-clock duration | 本文件 §3 表格 | 单独的 per-call 文件 |

### ❌ 没有存盘（技术原因）

| 内容 | 为什么没有 |
|---|---|
| **sub-agent 的 internal thinking tokens** | Anthropic Agent tool 不向 parent 暴露 sub-agent 的 chain-of-thought。我们只能看到 sub-agent 的 final response 和 tool calls。**这是 LLM API 的限制，不是设计选择**。 |
| **sub-agent 的 tool-use 完整 trace（每次 Read、每次 Write 的精确顺序）** | Agent tool 把 sub-agent 的执行包装成"输入 prompt + 输出 1-sentence summary"。中间的 Read/Write 序列我们能看到 tool_uses 计数但拿不到内容（因为我们仅约束了 Read 单个 prompt + Write 两个文件，所以中间过程也可复推）。 |
| **Parent（我）的 decision narrative** | 我在 round 之间做的决策（选 dispatch 哪些任务、怎么解读 r1 结果、何时停 round）在 chat conversation 里，**不在 PDE 实验目录里**。本文件下面的 §5 把我所有关键决策点写进来作为 audit trail。 |
| **每次执行的精确时间戳** | exec.log 里有 `duration_sec` 但没有 wall-clock timestamp。如果需要严格 timeline，可以从 git diff（如果存的话）或 macOS file mtime 推断。 |

---

## 2. Sub-agent 调用全表（手动从 chat 提取，权威）

这是论文 reproducibility 最关键的数据。从我和 sub-agent 的所有交互中抽出的元数据：

### Stage 1 stress tests（10 A-tests + 4 G-tests = 14 calls）

| ID | model | total_tokens | duration_ms | 1-sentence summary | 强制约束实际遵守？ |
|---|---|---|---|---|---|
| A1 | sonnet | 14900 | 24274 | forward Euler + 2nd-order central FD (no upwinding, no limiter), CFL=0.4 | ✓ |
| A2 | sonnet | 15170 | 33609 | Godunov upwind scheme with CFL-adaptive time stepping for the smooth pre-shock regime | ✓ |
| A3 | sonnet | 15019 | 29671 | Lax-Friedrichs finite-difference scheme in conservation form, CFL=0.5 | ✓ |
| A4 | sonnet | 15394 | 31691 | Explicit RK4 with 2nd-order central FD for v_x and v_xxx | ✓ |
| A5 | sonnet | 15328 | 33030 | Fourier pseudo-spectral with IMEX Euler, no dealiasing | ✓ |
| A6 | sonnet | 15949 | 43516 | Integrating-factor pseudo-spectral RK4 (with forced IC amp 0.1) | ✓ |
| A7 | sonnet | 15324 | 29263 | Forward Euler + central FD for both shallow-water equations | ✓ |
| A8 | sonnet | 15625 | 35458 | Global Lax-Friedrichs scheme with explicit Euler (CFL=0.4) | ✓ |
| A9 | sonnet | 15930 | 47291 | First-order HLL Godunov FV with adaptive CFL + positivity clip | ✓ |
| A10 | sonnet | 15758 | 41987 | HLL Riemann solver with explicit Euler (CFL=0.4) | ✓ |
| G1 | sonnet | 15268 | 30411 | Explicit RK4 with 2nd-order central FD for all spatial derivatives | ✓ |
| G2 | sonnet | 15992 | 43562 | Fourier pseudo-spectral IMEX-CN, dispersive implicit, nonlinear explicit, 2/3 dealiasing, dt=0.0005 | ✓ |
| G3 | sonnet | 15851 | 37446 | Fourier pseudo-spectral IMEX-CN, no dealiasing, dt=0.001 | ✓ |
| G4 | sonnet | 15877 | 45772 | IMEX-CN spectral with IC amp 3.0 (cubic term active) | ✓ |
| **Stage 1 stress-test 小计** | | **~221k** | **~518s** | | |

### Stage 1 curator agents（2 calls）

| Call | model | total_tokens | duration_ms | output |
|---|---|---|---|---|
| Curator (initial) | sonnet | 48492 | 270663 | wrote 20 entries (full bank v1) |
| Curator (Gardner extension) | sonnet | 49199 | 318843 | extended to 28 entries（reported 30 but actual 28） |
| Curator (+2 to reach 30) | sonnet | 47859 | 337343 | added 2 final synthesized entries → 30 total |
| **Stage 1 curator 小计** | | **~146k** | **~927s** | |

### Stage 2 round 1（9 calls）

| Cell | model | total_tokens | duration_ms | 1-sentence summary |
|---|---|---|---|---|
| T_A NoKB r1 | sonnet | 17315 | 48540 | Pseudo-spectral RK4 with 2/3 dealiasing, dt=5e-4 |
| T_A PosOnly r1 | sonnet | 21202 | 67644 | IMEX-CN spectral, dt=0.0005 |
| T_A PosNeg r1 | sonnet | 31639 | 96248 | IMEX-CN spectral + AB2 + dealiasing, dt=1.5e-4 |
| T_B NoKB r1 | sonnet | 17500 | 52160 | Pseudo-spectral RK4 + dealiasing, dt=5e-4 |
| T_B PosOnly r1 | sonnet | 21396 | 73046 | IMEX-CN spectral, dt=0.0005 |
| T_B PosNeg r1 | sonnet | 31640 | 97019 | IMEX-CN + AB2 + dealiasing, dt=2e-4 |
| T_C NoKB r1 | sonnet | 17153 | 48237 | Pseudo-spectral RK4 + dealiasing, dt=0.002 |
| T_C PosOnly r1 | sonnet | 21255 | 64989 | IMEX-CN spectral, dt=0.0005 |
| **T_C PosNeg r1** | sonnet | 32509 | 105718 | **MUSCL+Godunov for u + IMEX-CN spectral for v** |
| **Stage 2 r1 小计** | | **~211k** | **~654s** | |

### Stage 2 round 2（7 calls）

| Cell | model | total_tokens | duration_ms | 1-sentence summary |
|---|---|---|---|---|
| T_A NoKB r2 | sonnet | 20078 | 76637 | Pseudospectral integrating-factor RK4, dt=1.5e-4 |
| T_A PosOnly r2 | sonnet | 21851 | 70382 | IMEX-CN + AB2 + dealiasing (fixed typo) |
| T_B NoKB r2 | sonnet | 17947 | 45707 | Pseudospectral RK45 with 2/3 dealiasing |
| T_B PosOnly r2 | sonnet | 22826 | 76556 | Fourier pseudospectral IFRK4 + dealiasing, dt=0.0001 |
| T_B PosNeg r2 | sonnet | 32374 | 96967 | Fourier pseudospectral ETD-RK2 with IF + explicit midpoint, dt=4e-5 |
| T_C NoKB r2 | sonnet | 19730 | 69807 | Explicit RK4 spectral + dealiasing, dt=1e-4 |
| T_C PosOnly r2 | sonnet | 22952 | 82423 | MUSCL+Godunov for u + IMEX-CN for v, dt=2e-4 |
| **Stage 2 r2 小计** | | **~158k** | **~519s** | |

### Stage 2 round 3（7 calls）

| Cell | model | total_tokens | duration_ms | 1-sentence summary |
|---|---|---|---|---|
| T_A NoKB r3 | sonnet | 19196 | 61824 | Strang splitting + exact spectral v_xxx + adaptive RK45 |
| T_A PosOnly r3 | sonnet | 22006 | 73600 | Strang splitting: MUSCL+Godunov for u + IMEX-CN spectral for v, dt=0.0002 |
| T_B NoKB r3 | sonnet | 19311 | 62766 | Integrating-factor pseudospectral RK4 |
| T_B PosOnly r3 | sonnet | 21595 | 66243 | IMEX-CN spectral + dealiasing, dt=2e-5 (25× smaller) |
| T_B PosNeg r3 | sonnet | 29481 | 85985 | IMEX-CN spectral + dealiasing, dt=5e-5 |
| T_C NoKB r3 | sonnet | 18374 | 51590 | Explicit RK4 + per-call dealiasing, dt=2e-5 |
| T_C PosOnly r3 | sonnet | 22705 | 76583 | Godunov for u + IMEX-CN spectral for v, dt=0.0001 |
| **Stage 2 r3 小计** | | **~152k** | **~478s** | |

### 早期 BKdV pilot calls（3 calls）

| Cell | model | tokens (est) | duration | summary |
|---|---|---|---|---|
| BKdV-T1 Burgers r1 | sonnet | ~17k | ~21s | MUSCL+van Leer+Godunov+Euler CFL=0.45 → ✓ PASS |
| BKdV-T2 KdV r1 | sonnet | ~17k | ~49s | Fourier + IFRK4 → ✗ NaN |
| BKdV-T2 KdV r2 M4 | sonnet | ~17k | ~39s | Fourier + IMEX-CN → ✓ PASS |

### 累计资源

| 阶段 | calls | tokens | wall (sub-agent only) |
|---|---|---|---|
| Stage 1 stress + curator | 17 | ~367k | ~24 min |
| Stage 2 r1 + r2 + r3 | 23 | ~521k | ~27 min |
| BKdV pilot | 3 | ~51k | ~2 min |
| **合计** | **43** | **~939k** | **~53 min** |

加上候选 PDE 执行时间（~10 min）+ parent orchestration（~10 min）+ curator deliberation（~10 min）= **总 wall ~80 min**。

---

## 3. Sub-agent thinking 为什么没有完整记录

每次 sub-agent 被 dispatch 时：
1. Sub-agent 接收 prompt
2. Sub-agent 内部做 CoT thinking（**这部分 tokens 没有暴露给 parent**）
3. Sub-agent 调用 tool (Read or Write)（**parent 看到 tool_uses 计数但看不到具体 args**）
4. Sub-agent 重复 2-3 直到完成
5. Sub-agent 返回 final response（**parent 看到 1-sentence summary**）+ metadata（tokens、duration、agentId）

**Anthropic Agent tool 的设计有意把 sub-agent 的中间状态对 parent 隐藏**——这是 multi-agent 框架的标准 isolation 模式。

但对**论文 reproducibility**来说，我们有的已足够：
- **Prompt 完整**（agent 输入侧 100% 可复现）
- **Output 完整**（candidate.py + reasoning.md = agent 输出侧 100% 可复现）
- **Eval 完整**（result.json + pred_results/*.npy = 结果侧 100% 可复现）

只是 agent 内部"为什么这样想"的 step-by-step thinking 没有 → 这是 LLM API 限制。Reasoning.md 已经覆盖了 agent 自陈层面的思考。

---

## 4. 复现实验的命令清单

任何人拿到本目录可以复现：

```bash
cd paper/experiments/pde_pilot_2026-05-11/

# 重跑全部候选脚本 + eval（不重派 sub-agent）
.venv/bin/python stage1/run_stage1.py                # 14 stress tests
.venv/bin/python stage1/sandboxes/G*/candidate.py    # 4 Gardner runs (script-by-script)
.venv/bin/python stage2/run_stage2.py                # 9 r1 candidates + eval
.venv/bin/python stage2/run_stage2_round2.py         # 7 r2 candidates + eval
.venv/bin/python stage2/run_stage2_round3.py         # 7 r3 candidates + eval

# 重派 sub-agent（需要 Anthropic 配额；prompts 在每个 sandbox 内）
# 方式: 用我们存好的 prompt.md 直接喂给同样的 model
```

---

## 5. Parent（我）的决策叙事（key checkpoints）

按时间顺序整理我在 round 之间做的判断（这部分原本只在 chat 里，现在固化到这）：

### Stage 1 决策点

1. **任务集挑选**：从 BKdV-T1 (PASS) 和 BKdV-T2 (NaN→PASS) 的前期数据出发，决定 Stage 1 covers Burgers/KdV/Shallow Water 三个 component PDE，每个 PDE 内挑 method × parameter regime 的边界。
2. **强制方法约束**：每个 prompt 显式 forbid 高级方法。目的：逼 agent 出 ✗ 知识。如果让 agent 自由选，所有 stress test 会全部选 IMEX 谱方法。
3. **Gardner 后补 4 个**：因为 user 要求"~20 → 30"。Gardner 是 paper A 的 m=0 reduction，覆盖了"cubic 非线性"这个 BKdV 子任务也会触及的物理 regime。
4. **Curator agent 而非 parent 整理 bank**：让 agent 自己 review + curate，避免我手动 cherry-pick。Curator 用 30+ 个 Read 调用读所有 artifact，写出 jsonl。
5. **Parent audit 是 evidence-file existence check**：不是 LLM-judge，而是 deterministic check（30/30 cited files all exist）。

### Stage 2 决策点

6. **IC 故意挑边界**：为了让 r1 不 trivially PASS。T_A 用非纯 m=0 IC、T_B 用 σ=1.5 narrow Gaussian、T_C 用 sharp bore + soliton。校准目的就是产生区分度。
7. **三 condition 信息差**：NoKB（无 bank）/ PosOnly（10 ✓）/ PosNeg（30 ✓✗）。三个 condition 都允许 r2/r3 看自己上轮 finding（保证差异严格来自 Stage 1 bank）。
8. **r1 后没 calibrate**：r1 得到 PosNeg 2/3 PASS、NoKB+PosOnly 0/3，区分度足够，不需要调整 IC。
9. **r2 r3 没有调整 IC**：观察 attempts-to-useful 是同 cell 上的，必须保留 IC。
10. **r3 后停**：3 轮上限达到。T_B 三 condition 都失败成为诚实负面发现。

---

## 6. 数据访问 cheat sheet

| 想看什么 | 去哪里 |
|---|---|
| 第 N 条 knowledge entry | `stage1/knowledge_bank.jsonl` 第 N 行 |
| 某 cell 完整 round 过程 | `stage2/runs/T_<X>/<COND>/round<N>/` |
| 三个 condition 主表 | `stage2/STAGE2_REPORT.md` §2 |
| Stage 1 全部 stress 结果 | `stage1/stage1_results.json` |
| Burgers/KdV/SW reference | `gold/` 和 `stage1/gold/` |
| Phenomenon check 代码 | `stage2/eval/phenomenon_checks.py` |
| Bank 设计逻辑 | `stage1/curator_prompt.md` + `stage1/curator_extension_prompt.md` |
| Sub-agent 调用元数据（token/duration） | **本文件 §2** |
| Parent 决策叙事 | **本文件 §5** |

---

## 7. 如果还想补什么

| 缺什么 | 怎么补 | 工作量 |
|---|---|---|
| Per-call token/duration 单独存盘 | 写一个 hook script 把 Agent tool 返回的 metadata 同步写到 `sandbox/agent_meta.json` | 30 min（仅对未来 calls 生效） |
| Bank entry citation 自动提取 | 写 `extract_citations.py`，grep `reasoning.md` 中的 `kb-*` 模式 | 10 min |
| Sub-agent thinking 字面记录 | 不可能（API 限制）；alternative: 让 sub-agent 在 reasoning.md 里写更详细的"why I chose X over Y" | prompt 改 + 10 min |
| 实验 wall-clock timeline | macOS file mtime + git log（如果初始化）| 10 min |

每一项我都可以加。但 **目前的存盘已足以让论文审稿人 100% 复现 prompt → output → eval 链路**。

---

## 8. 文件总览（再确认一下）

```
paper/experiments/pde_pilot_2026-05-11/
├── EXPERIMENT_MANIFEST.md        ← 本文件
├── PDE_TEST_SET.md / PDE_CASE_STUDIES.md / PDE_EXPERIMENT_PLAN.md (设计 doc)
├── .venv → 共享 venv
├── gold/                         ← Burgers/KdV reference solver
├── eval/                         ← 早期 BKdV eval scripts
├── ref_results/                  ← BKdV reference outputs
├── runs/                         ← 早期 BKdV pilot (T1, T2)
├── stage1/
│   ├── STAGE1_INDEX.md           ← Stage 1 索引
│   ├── knowledge_bank.jsonl      ← **30 条 ✓/✗ 知识库**（核心产物）
│   ├── stage1_results.json
│   ├── build_*.py / run_*.py / curator_*.md
│   ├── gold/shallow_water_ref.py
│   ├── ref_results/sw_*
│   └── sandboxes/{A1..A10, G1..G4}/{prompt.md, candidate.py, reasoning.md, exec.log, result.json, meta.json, pred_results/*.npy}
└── stage2/
    ├── STAGE2_REPORT.md          ← Stage 2 完整报告
    ├── results_round{1,2,3}.json
    ├── build_*.py / run_*.py
    ├── eval/phenomenon_checks.py
    ├── tasks/definitions.json
    └── runs/{T_A,T_B,T_C}/{NoKB,PosOnly,PosNeg}/{round1,round2,round3}/{prompt.md, memory.md, candidate.py, reasoning.md, exec.log, result.json, eval_result.json, meta.json, pred_results/*.npy}
```

总文件数：331  
总存储：~3 MB（不含 venv 共享）  
完整可复现：是  
论文审稿可用：是
