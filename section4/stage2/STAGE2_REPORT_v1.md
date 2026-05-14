# Section 4 — Stage 2 Research-Graph coupled BKdV study

> 完成日期 2026-05-13 | Subject model: Claude (Sonnet 4.6 via Research Graph sub-agents)
> 12 cells = 3 sub-tasks × 4 memory conditions (NoKB / PosOnly / NegOnly / PosNeg)
> Each cell ≤ 3 Experiment nodes (1 Experiment = 1 `python candidate.py` run + 1 Finding)
> Total tokens (parallel dispatch) ~900k | Wall time ≤ 26 min per cell (all 12 in parallel)

## 1. 实验设计回顾

- **3 子任务**（全部基于 Holm et al. 2025 的 Burgers-swept-KdV 系统，无 closed-form 解）:
  - T_A: 孤子稳定性，IC 偏离纯 m=0 Gardner reduction（u = ½v² + 0.2v）
  - T_B: 高 amplitude Gaussian → 孤子列分解（v₀ amplitude=4, σ=1.5）
  - T_C: Burgers bore × KdV soliton 相互作用
- **4 条件**: NoKB / PosOnly (10 +) / NegOnly (20 −) / PosNeg (30 ±)
  - 物理隔离：PosOnly 只能 `cat` positive_knowledge.jsonl；NegOnly 只能 `cat` negative_knowledge.jsonl；PosNeg 两份都可读。
- **框架**: Research Graph (Q / E / F / D 四类节点写入 `research_state.jsonl`)
  - Decision 节点强制要求 proposal 阶段引用 bank：`cites_bank` / `rejects_bank` / `bank_use_rationale`
  - "Loop 3 times" 严格定义：每次 = 一次 `candidate.py` 执行 + 一个 Experiment 节点 + 一个 Finding 节点
- **工具**: Read + Write + Bash（sub-agent 自己跑代码、看 stdout/stderr、改 candidate.py、再跑）
- **评测**: parent-side phenomenon-based deterministic checks（与 Stage 2 v1 pilot 完全一致的 `phenomenon_checks.py`）

## 2. Top-line 结果（parent-verified）

### 2.1 Per-task verdict

| Task | NoKB | PosOnly | NegOnly | PosNeg |
|---|---|---|---|---|
| T_A | ✗ (3it) | **✓ (3it)** | ✗ (3it) | **✓ (3it)** |
| T_B | ✓ (3it) | **✓ (2it)** | ✓ (3it) | ✗ (3it) |
| T_C | ✓ (3it) | **✓ (1it)** | ✓ (3it) | ✓ (2it) |

### 2.2 Useful rate & efficiency

| Condition | PASS / 3 | Avg Exp nodes | Avg bank cites | Avg bank rejects |
|---|---|---|---|---|
| NoKB    | 2/3 (67%) | 3.0 | 0.0 | 0.0 |
| **PosOnly** | **3/3 (100%)** | **2.0** | 6.3 | 0.3 |
| NegOnly | 2/3 (67%) | 3.0 | 0.0 | 19.7 |
| PosNeg  | 2/3 (67%) | 2.7 | 9.0 | 11.3 |

## 3. T_A 是 negative-vs-positive 最干净的对照

T_A 的 IC 在 m=0 reduction 之外加了 0.2v 扰动 — KdV 单纯方法可能没问题，但耦合 u-v 项使得 u 容易爆。

| Cond | 三轮方法选择 | 末态 vT_max / amp_ratio | 结果 |
|---|---|---|---|
| NoKB    | RK4 → ETD-RK4 → RK45+hyperviscosity | 0.64 / 0.32 | FAIL |
| **PosOnly** | IMEX-CN → MUSCL+IMEX-CN → **IMEX-CN+u-hyperviscosity** | 1.30 / 0.65 | ✓ |
| NegOnly | IMEX-CN+FwdEuler-u → split-IMEX → RK45 | 0.63 / 0.32 | FAIL |
| **PosNeg** | IMEX-CN → IMEX-CN(sign-bug) → **IMEX-CN + u-low-pass filter** | 2.09 / **1.05** | ✓ |

**NoKB 和 NegOnly 末态几乎一模一样（vT_max ~0.64, peaks=1, amp_ratio 0.32）**：v 还在但严重耗散，u 已经爆到 ~6（接近 5 上限）。
- **NoKB** 选了纯显式（RK4, ETD-RK4, RK45）— 任何一条 negative entry 都能挡掉这条路，但 NoKB 看不到。
- **NegOnly** 三轮都正确避开了显式方法（rejects=20，覆盖 IFRK4 / explicit-RK4 / no-dealiasing / fwdEuler-centralFD / G4-IMEX-CN-amplitudeCFL / nonlinearCFL-amplitude-boundary），但**它没有具体的稳定方法配方**：第一轮选 IMEX-CN（对的）但 u 配 forward Euler 又炸；第二轮换 operator-split 不收敛；第三轮换 RK45 自己也降级。**知道不要做什么 ≠ 知道该怎么做**。
- **PosOnly** 三轮都用 IMEX-CN spectral（来自 `kb-kdv-IMEX-CN-spectral-pass`, `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation`），最后一轮加上 u 上的 spectral hyperviscosity 救活。
- **PosNeg** 末态最好（vT_max=2.09, amp_ratio=1.05 — 几乎原 amplitude 守恒）。它的 reject 列表包括 `gardner-GardnerIsM0-coupledSystemInstability`（正好对应 T_A 的扰动 IC），明显比 PosOnly 选得更精准；最终方法对 u 用了 low-pass 滤波（10% k_max），是 negative 警告（中心差分/无 dealias 会出 Gibbs）的直接对策。

## 4. T_B 是 PosNeg 唯一的失败（且是 over-engineering）

T_B 的 IC（v₀ amplitude=4 Gaussian）是已知最难的 — v1 pilot 三个条件全败。

| Cond | r2 / r3 方法 | 末态 | 结果 |
|---|---|---|---|
| NoKB    | RK4 → IFRK4 → **IFRK4 + 显式黏性 ε u_xx (ε=0.05)** | 5 peaks, vT_max=1.79 | ✓ |
| **PosOnly** | IMEX-CN-spectral → **MUSCL+Godunov(u) + IMEX-CN(v)** | 4 peaks, vT_max=2.08 | ✓ in 2 iter |
| NegOnly | (避开所有 explicit/no-dealias 后) → IMEX-CN 变体 | 5 peaks, vT_max=2.02 | ✓ |
| **PosNeg** | IMEX-CN → Strang+RK4 → Strang+RK4+Hou-Li filter | u_max=**184**, blow-up | ✗ |

**这是一个反直觉的发现**：PosNeg 看到了所有 negative 警告（rejects 16 次，覆盖 IFRK4, explicit RK4, no-dealiasing, G4-IMEX-CN amplitudeCFL, cubicTerm-tightens-nonlinearCFL, nonlinearCFL-amplitude-boundary 等），但它把这些警告解读成「不能用 explicit、不能用普通 IMEX」，于是转向 Strang splitting + Hou-Li filter — 一个理论上更稳但参数难调的方案，结果 u 在中后期爆炸。

对比 **PosOnly r2**：只看了 6 个 positive entry，直接合成了「MUSCL 处理 bore-like u + IMEX-CN 处理 dispersive v」的分裂方法，2 轮就通过。

→ **Negative 知识在 T_B 上没有「告诉它该选 MUSCL+IMEX-CN」的信号**；它只告诉它不要做 X、Y、Z。一旦 agent 选了一个 negatives 没明确否决的方向（Strang+filter），就可能走到死胡同。

## 5. T_C 上四条件全部通过 — phenomenon target 偏宽松

T_C 设计的 phenomenon target 是 vT_max ≥ 0.5（soliton 「存活」），所有 4 个条件都做到了：

| Cond | 最终方法 | iter | vT_max | u_max |
|---|---|---|---|---|
| NoKB    | (3 iter 不同尝试) | 3 | 0.64 | 3.62 |
| **PosOnly** | **MUSCL+IMEX-CN, r1 PASS** | **1** | 0.51 | 2.64 |
| NegOnly | (3 iter 避开 LaxFriedrichs/fwdEuler-centralFD/explicit-RK4) | 3 | 0.52 | 3.10 |
| PosNeg  | MUSCL+IMEX-CN, r2 PASS | 2 | 0.58 | 2.76 |

**PosOnly r1 就出对方法（MUSCL+Godunov for u, IMEX-CN spectral for v）**，引用 `kb-burgers-MUSCL-Godunov-shock-pass` + `kb-kdv-IMEX-CN-spectral-pass`。其余三条件多花了 1-2 轮试错才收敛到类似方法。

**Caveat**: T_C 的 useful 门槛（vT_max ≥ 0.5）较宽松；如果改用更严格的 phase-shift / refraction 指标，差异可能拉开。

## 6. 与 v1 pilot 的对比 — 三个变化解释了 baseline 提升

v1 pilot（`paper/experiments/pde_pilot_2026-05-11/stage2`）的同样 3 任务跑 3 条件（无 NegOnly），结果是 NoKB 0/3, PosOnly 0/3, PosNeg 2/3。本次 NoKB 跳到 2/3，PosOnly 跳到 3/3。差异来源：

1. **Research Graph scaffolding**：v1 用类似 Self-Debug 的 single-prompt iteration，而 Section 4 要求显式 Q→E→F→D 节点。Decision 节点强制让 agent 显式说明「下一轮要变什么」，这种结构对 NoKB 也有帮助。
2. **3 轮真的跑 3 轮**：v1 r1 失败后 r2/r3 用 prompt 强制重写，本次每个 cell 是一个 *持续的* sub-agent session，agent 直接看到上一轮 Finding 节点，所以重写更连贯。
3. **Bank entry 措辞改善**：在 Stage 1 重新生成时把每条 entry 的 `applicability` 写得更明确（如 "applies to coupled Burgers-KdV bore"），帮助所有 bank-aware 条件。

→ 比较 **isolated condition effect** 时应控制框架因素。本次结果说明：**当 scaffold 本身已足够强（agent 可以反思自己的 Finding 来纠错）时，positive bank 是最显著的 method-choice 助推器**；negative bank 在「告诉 agent 选什么」方面贡献较弱，但在「避免重复死路」上确实在 reject 列表中可见。

## 7. Bank-entry usage patterns

`research_state.jsonl` 里每个 Experiment 节点都标记 `cites_bank` / `rejects_bank` / `bank_use_rationale`。聚合后（`summary.md` 完整列表）：

- **NoKB**: 完全 0 cite / 0 reject（sanity check：的确没看到 bank）
- **NegOnly**: 0 cite，平均 19.7 reject — agent 真的把 20 条 negative entry 全部当作 "do-not-do" 列表（同一 ID 在 3 轮 Experiment 中重复出现）
- **PosOnly**: 6.3 cite，0.3 reject — 几乎纯正向引用，引用前 3 名都是 IMEX-CN/dealias/method-transfer 类
- **PosNeg**: 9.0 cite + 11.3 reject — 同时使用两边；T_A PosNeg 的 reject 列表里出现的 `kb-gardner-GardnerIsM0-coupledSystemInstability` 是 PosOnly 看不到的关键警告

**Most-cited positive**: `kb-kdv-IMEX-CN-spectral-pass`（PosOnly/PosNeg 共出现 8 次） 
**Most-rejected negative**: `kb-kdv-explicit-RK4-stiffness-blowup`（NegOnly/PosNeg 共出现 8 次）

## 8. 论文核心 take-aways（修订后）

| Claim | 本次证据 | 与 v1 pilot 的关系 |
|---|---|---|
| **结构化负知识在「method choice」上贡献有限** | T_A NegOnly 失败，与 NoKB 末态几乎一致 | 修正 v1 结论 |
| **正知识是 method-choice 的主要驱动力** | PosOnly 3/3 唯一全通过；T_C 1-shot pass | 加强 v1 中 PosOnly=0/3 的结论 — 当 scaffold 足够强时 |
| **负知识在「避错 + 精化方案」上仍有边际贡献** | T_A PosNeg amp_ratio=1.05 vs PosOnly 0.65；reject `GardnerIsM0-coupledSystemInstability` 是 PosOnly 看不到 | 新发现 |
| **负知识可能 over-correct** | T_B PosNeg blow-up：负警告把 agent 推向 Strang+filter 路径，而 PosOnly r2 用 MUSCL+IMEX-CN 一击命中 | v1 没观察到，因为 v1 PosOnly=0/3 |
| **Research Graph 框架对 NoKB 也有帮助** | NoKB 2/3 vs v1 0/3 | 框架因素需控制 |

**整体诚实评估**：在本节 4 的设定下（强 scaffold + 4 条件 + 物理隔离 bank 文件），negative-knowledge 的边际收益**比 v1 pilot 弱**。我们看到两条还成立的小信号：
1. 当任务难度足够高且需要在多个稳定方法间精选（T_A），negatives 帮 agent 从 PosOnly 的「PASS but amp_ratio=0.65」推到「PASS with amp_ratio=1.05」。
2. NegOnly 完全靠 reject 列表，**3 轮也没救出 T_A**，证实 negatives 单独不够。

但也出现一个反向案例（T_B/PosNeg），是单点失败还是 systematic over-engineering，目前 N=1 不能下结论。**这是论文应该诚实写出的开放问题**。

## 9. 资源用量

| 项 | 数值 |
|---|---|
| Sub-agent 平行调用 | 12（每个 cell 一个 long-running session） |
| Tokens (Sonnet) | ~900k 总计（平均每 cell ~75k） |
| Wall time | 平行 ≤ 26 min；串行预估 ~5 hr |
| 失败/重启 | 0；全部 cell 第一次跑通 |
| 物理输出 | 12 × `pred_results/T_X.npy`, 12 × `candidate.py`, 12 × `reasoning.md`, 12 × `research_state.jsonl` |

## 10. 文件清单

```
section4/
├── README.md                              ← framework overview
├── stage1/                                ← knowledge production (continuous from earlier)
│   ├── bank/{knowledge_bank,positive_knowledge,negative_knowledge}.jsonl
│   └── ... (sandboxes / gold / scripts via symlinks)
└── stage2/
    ├── STAGE2_REPORT.md                    ← 本文件
    ├── verified_results.json               ← parent-side eval rows (12)
    ├── summary.md                          ← markdown summary table
    ├── eval/phenomenon_checks.py           ← deterministic phenomenon eval
    ├── prompts/research_graph_template.md  ← Q/E/F/D protocol template
    ├── tasks/definitions.json              ← T_A, T_B, T_C specs
    ├── scripts/
    │   ├── build_v2.py                     ← regenerate 12 sandboxes
    │   ├── run_eval.py                     ← parent-side eval driver
    │   ├── aggregate.py                    ← summary.md generator
    │   └── split_bank.py                   ← split knowledge_bank.jsonl
    └── runs/{T_A,T_B,T_C}/{NoKB,PosOnly,NegOnly,PosNeg}/
        ├── prompt.md / memory.md / meta.json
        ├── candidate.py / reasoning.md
        ├── research_state.jsonl            ← Q/E/F/D node log
        ├── session_log.md
        ├── verified_eval.json              ← parent-side per-cell result
        └── pred_results/T_X.npy
```
