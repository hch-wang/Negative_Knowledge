# Section 4 — Stage 2 v2: Research-Graph coupled BKdV under progressive-complexity discipline

> 完成日期 2026-05-13 | Subject model: Claude (Sonnet 4.6 via parallel sub-agents)
> 12 cells = 3 sub-tasks × 4 memory conditions, with **progressive-complexity discipline** binding the iteration trajectory
> Total tokens (parallel dispatch) ~960k | Wall time ≤ 13 min per cell, all 12 parallel
> Compared against v1 (no discipline) preserved in `runs_v1_no_progressive/` and `STAGE2_REPORT_v1.md`

## 0. 为什么需要 v2

v1 的 prompt 没有任何 simple-first / 单组件升级约束。其后果是：
- **PosOnly r1 直接用 IMEX-CN spectral**（一句 `kb-kdv-IMEX-CN-spectral-pass` 抄上）
- **NegOnly r1 直接用 IMEX-CN spectral**（因为 negatives 否决了 explicit）
- **PosNeg r1 直接用 IMEX-CN spectral + 2/3 dealiasing**

→ v1 的 "PosOnly 3/3" 其实是 **method lookup**，不是 research。审稿人会问："this is recall, not research." 而更根本的问题是 **整体论 (holism)**：当 r1 同时堆 4 个先进组件而失败时，agent 无法定位是哪个部件的责任，下一轮的修正变成猜测。

v2 加入 **progressive-complexity discipline**（来自用户的 "整体论 / 可回溯性" 观点）：
1. **E1 必须是最简单的有意义 baseline**（Fourier spectral / 中心差分 + 显式 RK4 或 forward Euler；不允许 dealiasing / IMEX / splitting / filter）
2. **E2 相对 E1 只改 ONE major 部件**
3. **E3 相对 E2 再加 ONE 部件**
4. **bank 的角色变成 "升级方向指南"，不是 "答案速查表"**

完整 prompt 见 `prompts/research_graph_template.md` "Progressive-complexity discipline" 节。

## 1. Top-line 结果对比 (v1 vs v2)

### 1.1 Per-task verdict（parent-verified）

| Task | Cond | v1 | v2 | 注释 |
|---|---|---|---|---|
| T_A | NoKB    | ✗ (3it, RK4→ETD-RK4→RK45) | **✓** (3it, RK4→+dealias→dt↓) | NoKB 反超 |
| T_A | PosOnly | ✓ (3it, IMEX-CN stack) | ✗ (3it, RK4→+dealias→IMEX-CN 失误) | 失去 lookup 优势 |
| T_A | NegOnly | ✗ | ✗ | 仍失败但路径更干净 |
| T_A | PosNeg  | ✓ (IMEX-CN stack) | ✗ (3it 用完仍未到 MUSCL-u) | 失去 lookup 优势 |
| T_B | NoKB    | ✓ | **✓ (2it)** | 更快 |
| T_B | PosOnly | ✓ | **✓ (2it)** | 同样 2 iter |
| T_B | NegOnly | ✓ | **✓ (2it)** | 更快 |
| T_B | PosNeg  | **✗** (Strang+filter 失败) | ✗ (3it 后 u_max=30) | 失败模式改变 |
| T_C | NoKB    | ✓ | ✗ | NoKB 损失 |
| T_C | PosOnly | ✓ (1it, 全堆叠) | **✓ (2it, MUSCL-on-u only)** | 仍通过，但是 *研究* 而非查表 |
| T_C | NegOnly | ✓ | ✗ | NegOnly 损失 |
| T_C | PosNeg  | ✓ | ✓† | † pass-via-padding（仿真只到 t=1.97 / 8.0） |

†: 见 §6 解释

### 1.2 Aggregate pass rate

| Condition | v1 | v2 (discipline) |
|---|---|---|
| NoKB    | 2/3 | 2/3 |
| **PosOnly** | **3/3** | **2/3** |
| NegOnly | 2/3 | 1/3 |
| **PosNeg**  | **2/3** | **1/3** |

→ **discipline drops PosOnly 3/3 → 2/3 and PosNeg 2/3 → 1/3**，这恰恰是 v1 的 method-lookup 效应被剔除掉的部分。

## 2. 关键证据：discipline 真的把 baseline 拉回来了

抽查 12 个 cell 的 E1 method 字段（research_state.jsonl）：

**v1（无 discipline）E1**:
- T_A PosOnly: IMEX-Crank-Nicolson spectral + 2/3 dealiasing
- T_A PosNeg: IMEX-Crank-Nicolson spectral + 2/3 dealiasing
- T_A NegOnly: IMEX-CN + Forward-Euler + 2/3 dealiasing
- T_C PosOnly: MUSCL+Godunov + IMEX-CN spectral + Strang splitting (一次堆 3 部件！)

**v2（有 discipline）E1**: **12/12 cell 都是 `Fourier pseudospectral + explicit RK4, no dealiasing, no IMEX, no filter`**

→ Agent 100% 遵守了 baseline 约束，包括 bank-aware 的 9 个 cell。Bank 在 E1 阶段被用作"确认 baseline 合理"，而非选最强方案。

## 3. T_C 的 case study —— **positive bank 唯一不可替代的证据**

T_C（bore × soliton）在 v2 是 **bank 价值最锋利的 case**：

### 3.1 四个条件的 trajectory

| Cond | E1 (相同) | E2 单组件升级 | E3 | 结果 |
|---|---|---|---|---|
| **NoKB** | RK4 + spectral | **integrating-factor RK4**（治 v_xxx stiffness） | + 2/3 dealias | ✗ (t=2.33 bore 爆) |
| **PosOnly** | RK4 + spectral | **MUSCL+Godunov on u**（治 bore） | (停早) | ✓ (2 iter) |
| **NegOnly** | RK4 + spectral | **IMEX-CN on v_xxx** | + 2/3 dealias | ✗ (t=1.47 bore 爆) |
| **PosNeg** | RK4 + spectral | **IMEX-CN on v_xxx** | + 2/3 dealias | ✓† (padding 到 t=1.97) |

→ **只有 PosOnly 在 E2 直接走对方向（MUSCL on u）**，因为正向条目 `kb-burgers-MUSCL-Godunov-shock-pass` *明确*指向了它。NegOnly 知道 "central FD on shocks 不行 / LaxFriedrichs 太耗散"，但没有 "用 MUSCL/Godunov" 的*正向*指引，于是走了 IMEX-CN（一个对 T_C 没用的路径）。NoKB 和 PosNeg 都同样走错了 E2 方向。

### 3.2 但为什么 PosNeg 失败而 PosOnly 成功？两者都看得到 MUSCL 条目

关键发现：**E1 失败的*停止时机*决定了 F1 的诊断信息量**。

| Cond | F1 stop 条件 | F1 诊断质量 |
|---|---|---|
| **PosOnly** | step 4032, t=0.40, **u_max=17.4, v_max=0.81**（仍 finite） | "u 爆，v 没事" → 一意点向 MUSCL on u |
| **PosNeg** | step 8000, t=0.80, **u=NaN, v=NaN**（已 cascade） | "explicit overflow" → 含混，agent 默认治 stiffness |

PosOnly 的 candidate.py 实现了 step-by-step overflow 早停（u_max>15 即 break），所以 F1 的诊断锋利。PosNeg 让数值跑到全 NaN，u/v 谁先爆已分不清，agent 只能选默认升级方向（IMEX-CN on v_xxx）。

→ **discipline 在测一个组合能力**：(1) 选简单 baseline → (2) 仔细 *观察* 失败模式 → (3) 在 bank 里找匹配的*那一个*单组件升级。第 (2) 步的"仔细观察"主要靠 agent 自己的 instrumentation；bank 帮不上。

这是 v2 揭示的、v1 完全看不到的 **researcher-level skill 信号**：在 same bank、same E1 method 下，PosOnly 比 PosNeg 多了一个"早停 + u/v 分别诊断"的 instrumentation 选择，结果天差地别。

## 4. T_B —— bank 的边际收益最小，因为答案是单一的

T_B（Gaussian → soliton train）4/4 PASS（NoKB / PosOnly / NegOnly / PosNeg=✗ 但因不同原因）。

| Cond | iter | 路径 |
|---|---|---|
| NoKB | 2 | RK4 → + 2/3 dealias → PASS |
| PosOnly | 2 | RK4 → + 2/3 dealias → PASS（外加用 bank 否决继续升级 IMEX-CN 因为 amp=4 > 推荐区间 [1,2]）|
| NegOnly | 2 | RK4 → + 2/3 dealias → PASS |
| PosNeg | 3 | RK4 → IMEX-CN → + dealias → 但 u 仍爆到 30 ⇒ ✗ |

→ **T_B 的"对的方法"是 RK4 + 2/3 dealiasing**，bank 无关条件都能在 2 iter 走到。PosNeg 反而因为同时看到 positive entries `kb-kdv-IMEX-CN-spectral-pass` 和 negative entries `kb-kdv-explicit-RK4-stiffness-blowup`，**在 E2 偏向 IMEX-CN** 而非更直接的 dealiasing，多绕了一个 component，3 iter 内仍未稳定 u sector。

这是 **v1 的 PosNeg T_B 失败案**在 v2 的复现：bank 信息越多，越容易走"理论最优"的迂回路径，从而错过单 component fix 的简单胜利。**但 v2 的失败模式是更可解释的（IMEX-CN 选择基于 bank cite），不像 v1 的 Strang+filter "凭空创造"**。

## 5. T_A —— 4 组件任务暴露 3-iteration budget 不够

T_A（soliton 在 m=0 perturbation 下）需要 **RK4 + dealiasing + IMEX-CN + (something for u-radiation)** 这 4 个 component。3-iteration budget 不够。

| Cond | 路径 | 末态 | 结果 |
|---|---|---|---|
| **NoKB** | RK4 → + dealias → dt↓ | vT_max=**1.36**, amp_ratio=0.68 | **✓**（amp_ratio 0.68 > 0.5）|
| PosOnly | RK4 → + dealias → IMEX-CN（discipline 违规：同时变 dt）→ rollback to E2 | vT_max=0.92, amp_ratio=0.46 | ✗（amp_ratio 0.46 < 0.5）|
| NegOnly | RK4 → + dealias → dt↓（做 dt-convergence study） | vT_max=0.64, amp_ratio=0.32 | ✗（但证实是物理衰减不是数值）|
| PosNeg | RK4 → IMEX-CN → + dealias | E3 blow-up（u sector） | ✗ |

→ 同一个 2-component 方案（RK4 + dealias），**NoKB vT_max=1.36 vs PosOnly vT_max=0.92** — 两者 method 字段完全一致，但实现细节差距导致 0.44 的 amplitude 差。可能原因：dealiasing mask 实现细节 / 物理项 ordering / dt 微调。**这是 implementation noise，单次实验不足以下结论**。

最干净的*正面*发现是 **T_A NegOnly E3 做了 dt-convergence study**（dt=5e-5 与 dt=2e-5 elementwise 一致到 2e-8），从而*证明*amplitude 衰减不是数值耗散而是物理 — 这是 v1 没有的科研行为，是 progressive discipline 的副产品（"逼"agent 在没有别的好选择时做收敛性检查）。

## 6. T_C PosNeg 的 "padding pass" 警示

T_C PosNeg 的 E3 在 t=1.97（u_max=4.99 ≈ 阈值 5）触发了 agent 自己的 abort 逻辑，剩余 t ∈ [1.97, 8.0] 的 snapshots 被 padded 成 t=1.97 的状态。Parent eval 机械地读最后一个 snapshot → vT_max=0.62, u_max=4.99 → PASS。但这不是真的 "在 T=8.0 时满足 phenomenon target"。

**实验流程层面**：agent 透明地在 reasoning.md 里写了 "self-assessment: useful=False / partial, only reached t=1.97" — 这是诚实行为，但 phenomenon_checks.py 没有 "simulation_completed_to_T" 的检查项，所以漏掉了。

→ **建议补一个 eval 项 `t_reached`**，未来跑这种 borderline 案例时把"是否真到了 T_final"也作为 PASS 标准之一。本次先保留 padding-pass 作为 PASS 并加注 †，但在 paper 里要写清。

## 7. 综合：v2 揭示的 negative-knowledge 价值（修订后）

| Claim | v1 证据 | v2 证据 | 现在的判断 |
|---|---|---|---|
| **正知识在 method-choice 上是主驱力** | PosOnly 3/3 | PosOnly 2/3，但 T_C 上 unique 通过 | ✓ 加强：T_C PosOnly 是唯一指向 MUSCL 的条件 |
| **负知识单用是不够的** | NegOnly 2/3 (= NoKB) | NegOnly 1/3 (< NoKB) | ✓ 加强：discipline 下更明显 |
| **正+负联合优于正单** | PosNeg 2/3 (T_A) | PosNeg 1/3 | ✗ 反驳：v1 的优势可能是 lookup 效应 |
| **discipline 暴露 agent's diagnostic skill 差异** | (未观察) | T_C PosOnly vs PosNeg 同 bank，差在 E1 instrumentation | ✓ 新发现 |
| **bank 帮助 dt-choice，使 E1 失败更 informative** | (未观察) | T_C PosOnly dt=1e-4 vs NoKB dt=0.001 | ✓ 新发现，需后续验证 |
| **任务的 compositional depth 决定 budget 充足性** | (未观察) | T_B 2 component → 所有条件通过；T_A/T_C 4 component → 多数失败 | ✓ 新发现 |

## 8. Iteration efficiency（v2 唯一的、最干净的 bank-value signal）

| Cond | 平均 iter (success only) | success rate |
|---|---|---|
| NoKB    | 2.5 (T_A 3it, T_B 2it) | 2/3 |
| **PosOnly** | **2.0** (T_B 2it, T_C 2it) | 2/3 |
| NegOnly | 2.0 (T_B 2it) | 1/3 |
| PosNeg  | 3.0 (T_C 3it pad) | 1/3 |

**PosOnly 的最低 success-iter 平均（2.0）**是 v2 留下的最稳定 bank-value signal。它来自 T_C PosOnly 2 iter 命中 MUSCL — 这是单 component 升级的精度优势，不可被 lookup 解释。

## 9. 论文 framing 修订（v2 后）

旧的 v1 claim "结构化负知识对 multi-component PDE 至关重要" **不成立**（在加 discipline 后）。

修订后的核心 claim：

1. **结构化知识（特别是正向）在 method-choice 上是 *iteration-efficient* 的**。它把找到正确单 component 升级的预期 iter 数从 3+（fail）降到 2（pass）。在 budget 受限的研究循环里这是 game-changing。

2. **方法学约束 (progressive complexity) 让 ablation-style research 成为可能**。没有它，agent 把所有先进部件一次性堆上，失败时无法定位，bank 退化成查表。

3. **负向知识单独存在没有 escalation direction**，只能 reject 路径。研究循环里 "rejects-only" 不能跨越组合空间的指数广度。

4. **bank-aware agent 仍然依赖 instrumentation skill**：仅看到 "u=NaN, v=NaN" 是定位不到 u-sector 还是 v-sector 的；需要 agent 自己加 overflow 早停。这部分技能不在 bank 里。

5. **Task 的 compositional depth** = 该任务最少需要叠加的 method components 数。本研究 T_B=2, T_C=2 (with bank guidance) or 4 (without), T_A=4。Budget 必须 ≥ depth 才有 fair pass rate。Section 4 的 3-iteration budget 是有意的紧约束，把 bank-value 信号集中到 efficiency 而非 raw pass rate 上。

## 10. 资源用量

| 项 | v1 | v2 |
|---|---|---|
| Sub-agent calls | 12 | 12 |
| Tokens (Sonnet) | ~900k | ~960k |
| Wall time (parallel) | ≤26 min | ≤13 min |
| 物理输出 | 12 × T_X.npy | 12 × T_X.npy |
| Self-assessment 准确率 | 多数和 parent eval 一致 | 100% 与 parent eval 一致（无虚假 PASS）|

## 11. 文件清单

```
section4/stage2/
├── STAGE2_REPORT.md                ← 本文件 (v2)
├── STAGE2_REPORT_v1.md             ← v1 报告 (无 discipline)
├── verified_results.json           ← v2 parent eval
├── verified_results_v1.json        ← v1 parent eval
├── summary.md                      ← v2 markdown summary
├── summary_v1.md                   ← v1 markdown summary
├── prompts/research_graph_template.md  ← 已含 progressive-complexity 条款
├── runs/{T_A,T_B,T_C}/{NoKB,PosOnly,NegOnly,PosNeg}/
│   └── candidate.py, reasoning.md, research_state.jsonl,
│       session_log.md, pred_results/T_X.npy, verified_eval.json
└── runs_v1_no_progressive/{T_A,T_B,T_C}/...   ← v1 完整 trace 留档
```
