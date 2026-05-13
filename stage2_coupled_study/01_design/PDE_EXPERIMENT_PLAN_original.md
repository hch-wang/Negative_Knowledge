# Burgers-swept-KdV Negative Knowledge 实验计划

> **目的**：把 PDE case study 从“若干 PDE benchmark 的单任务修复”改成一个具体科研目标：使用 multi-agent AutoResearch 框架研究 **Burgers-swept-KdV / Burgers-phi-KdV** 方程的数值性质，并比较在研究前是否维护 **Negative Knowledge (NK)** 对研究过程的影响。
>
> **核心对比**：同一个 coupled Burgers-swept-KdV 研究任务，在同样模型、预算、工具和 evaluator 下，比较 `No-NK` 与 `NK` 两种条件。`NK` 条件在进入 coupled-system 研究前，会先从 Burgers、KdV、Gardner、shallow-water 等 component PDE 的短时间模拟中制作一个 negative-knowledge bank。

---

## 1. 实验主张

我们不是要证明“AI 可以直接解一个复杂 PDE”。我们要证明：

> 在一个真实科研任务族中，结构化记录失败可以成为 multi-agent research team 的共享资产，使后续 agent 更少重复数值错误、更快避开无价值路线，并更容易选择合理的简化情形来研究 coupled system。

这和论文主张的对应关系：

| 论文主张 | PDE 实验对应 |
|---|---|
| Negative knowledge 不只是 debug trace | 记录的不只是代码错误，也包括现象没出现、物理上没意义、路线应放弃 |
| NK 是 team-level shared asset | source agents 的失败记录被 target agents 用来研究 coupled Burgers-swept-KdV |
| 失败需要 bounded 记录 | 区分数值失败、结果偏差、科学价值不足，避免把无效结果写成 positive progress |
| Research Graph 是基本结构维持形式 | 每次 PDE attempt 产出 question / experiment / finding / decision / failure record |

---

## 2. 科学目标

### 2.1 目标方程

主研究对象是 Burgers-swept-KdV 系统：

```text
u_t + 3 u u_x = -∂_x (3 v^2 + γ v_xx)
v_t + 6 v v_x + γ v_xxx = -∂_x (u v)
```

其中：

- `u` 是 Burgers-like current field；
- `v` 是 KdV-like wave field；
- 第一条方程包含 Burgers 非线性 + 来自 `v` 的 forcing；
- 第二条方程包含 KdV 非线性/色散 + 来自 `u` 的 sweep/coupling；
- 特殊情形 `m := u - v^2/2 = 0` 可退化到 Gardner-type 方程。

### 2.2 研究问题

我们希望 multi-agent team 研究以下性质：

1. 单独 Burgers 的 shock / conservation / limiter 经验，是否能帮助研究 coupled system 的 `u` 场？
2. 单独 KdV 的 soliton / dispersion / stiffness 经验，是否能帮助研究 coupled system 的 `v` 场？
3. Gardner reduction 是否是 full coupled system 太难时的合理简化路线？
4. shallow-water 方程作为双变量守恒系统，能否提供 positivity、Riemann flux、conservation drift 的对照经验？
5. Coupled Burgers-swept-KdV 是否出现有价值的现象，例如 soliton speed shift、reflection/refraction、fusion、shock-dispersion interaction、mass/invariant drift？
6. NK 条件是否比 No-NK 条件更少产生 false progress：例如数值已经不稳定，却被 agent 描述成“发现了新现象”。

---

## 3. 两阶段实验设计

实验分成两个阶段。

### 阶段 A：Making Negative Knowledge

先让 source agents 跑一组简单、短时间、低成本的 component PDE simulations。目的不是最终论文中的 PDE 发现，而是制作一个 negative-knowledge bank。

Source tasks:

| ID | 方程 | 目的 | 可能产生的 NK |
|---|---|---|---|
| S1 | Burgers shock | 测 shock capturing、conservative flux、limiter | central difference Gibbs；非守恒格式；CFL blow-up；T 太短 shock 未形成 |
| S2 | KdV soliton | 测 dispersion stiffness、phase speed、mass conservation | explicit/IF implementation unstable；wrong phase speed；aliasing；mass drift |
| S3 | Gardner reduction | 测 KdV-like nonlinear dispersive extension | KdV 方法迁移条件；非线性更强导致 invariant drift；需要 dealiasing |
| S4 | Shallow water | 测双变量双曲守恒系统 | water height negative；Riemann flux 错；momentum drift；dry-state instability |
| S5 | Weak coupled sanity | 极弱 coupling 下检查 u/v 方向和符号 | coupling sign error；energy injection；变量插值不守恒 |

每个 source task 的输出不是“成功解”，而是：

```text
runs/source/<task_id>/<agent_id>/
├── prompt.md
├── candidate.py
├── reasoning.md
├── exec.log
├── eval.log
├── result.json
└── failure_record.json     # 若失败、偏差、无科学价值
```

### 阶段 B：Coupled-System Study

然后让 target agents 研究 Burgers-swept-KdV / Burgers-phi-KdV coupled system，并比较两种条件。

| Condition | Agent 可见信息 | 目的 |
|---|---|---|
| `No-NK` | 只给 coupled-system research brief、方程、预算、输出要求 | baseline：不维护失败资产 |
| `NK` | 给同样 brief + 阶段 A 产生的 negative-knowledge bank | 测 NK 是否减少重复失败并改善路线选择 |

重要：`NK` 不应直接给 gold solver 或“标准答案”。它只给失败记录、边界条件、证据和推荐动作。

---

## 4. Negative Knowledge 的三类失败

本实验中 failure 不只等于程序崩溃。我们记录三类失败：

### F1. 数值失败（numerical failure）

代码或数值过程不能可信运行。

例子：

- 输出 NaN / Inf；
- solver blow-up；
- CFL 太大；
- matrix solve singular；
- explicit scheme 对 stiff dispersion 不稳定；
- shallow-water height `h < 0`；
- boundary condition / grid mismatch。

典型字段：

```json
{
  "layer": "method_failure 或 implementation_failure",
  "degree": "unstable",
  "recommended_action": "change_method 或 retry",
  "risk": "medium_risk_drift"
}
```

### F2. 结果偏差（phenomenon/result failure）

程序跑通，但结果不是研究目标需要的现象。

例子：

- Burgers shock 没形成，因为 `T` 太短；
- KdV soliton 位置不对，phase speed 错；
- Gardner 双 soliton 没有 overtaking；
- coupled system 的 u/v 几乎 decouple，没有 observable interaction；
- mass / momentum / energy drift 超阈值；
- coupling sign 错导致现象方向相反。

典型字段：

```json
{
  "layer": "measurement_failure 或 method_failure",
  "degree": "partial 或 contradicted",
  "recommended_action": "revise_hypothesis 或 narrow_claim",
  "risk": "medium_risk_drift"
}
```

### F3. 科学价值不足（scientific-value failure）

结果数值上可行，但没有研究价值，不值得继续投入。

例子：

- 振幅太小，coupling effect 不可见；
- 时间太短，只有 trivial propagation；
- 时间太长，周期边界污染主现象；
- 参数 regime 退化成已知单方程行为；
- 可视化有结果，但无法支持任何明确 claim。

典型字段：

```json
{
  "layer": "hypothesis_failure 或 inference_failure",
  "degree": "inconclusive",
  "recommended_action": "narrow_claim 或 abandon_route",
  "risk": "low_risk_omission"
}
```

这类失败对本文尤其重要：它展示 NK 不是 debug log，而是科学路线选择的记忆。

---

## 5. Bounded Failure Record 格式

每条 NK record 使用同一个 schema：

```json
{
  "id": "nk-kdv-ifrk4-nan-001",
  "source_task": "S2_kdv_soliton",
  "target": "Propagate a KdV soliton to T=2.0",
  "attempted_route": "Fourier pseudospectral + integrating-factor RK4",
  "observation": "Output contains all NaN values; evaluator rejects as non-finite.",
  "evidence": [
    {"kind": "eval_log", "ref": "eval.log", "summary": "256 NaN/Inf"},
    {"kind": "candidate_code", "ref": "candidate.py", "summary": "IFRK4 without dealiasing"}
  ],
  "failure": {
    "layer": "implementation_failure",
    "scope": "regime_bound",
    "degree": "unstable",
    "reproducibility": "observed_once",
    "recommended_action": "change_method",
    "risk": "medium_risk_drift"
  },
  "rationale": "The method is plausible, but this implementation is unstable in the tested regime. Future agents should avoid repeating this exact route without dealiasing, smaller dt, or an alternative IMEX/ETD treatment.",
  "transfer_hint": "Relevant to Gardner and coupled v-equation because both contain KdV-like dispersive stiffness.",
  "review_status": "auto_draft"
}
```

附加要求：

- `rationale` 可以说“可能原因”，不能假装已证明；
- `transfer_hint` 只说明可能相关，不提供 gold solver；
- record 必须引用本地证据文件；
- 如果失败只是 implementation bug，不能直接推成 hypothesis refutation；
- 如果结果无科学价值，应明确 `recommended_action = abandon_route` 或 `narrow_claim`。

---

## 6. Multi-agent 角色设计

每个 condition 使用同样的 agent team 结构：

| Agent | 职责 | 输出 |
|---|---|---|
| Planner | 选择要研究的 regime / IC / T / grid / observable | `plan.md`, `research_questions.json` |
| Solver | 写 solver 并运行模拟 | `candidate.py`, `run_config.json`, `exec.log` |
| Analyzer | 检查守恒量、现象、可视化、failure mode | `analysis.md`, `metrics.json`, `plots/` |
| Reviewer | 判断结果是否支持 scientific claim，是否 false progress | `review.md`, `accepted_findings.json`, `failure_record.json` |

No-NK 与 NK 的唯一区别：

- No-NK team 的 Planner / Solver / Analyzer / Reviewer 只看 coupled-system brief；
- NK team 额外看阶段 A 的 `negative_knowledge_bank.jsonl`；
- 两组不能看对方运行结果；
- 两组使用相同模型、相同最大轮数、相同 token/time/tool budget。

建议最小配置：

```text
2 conditions × 3 target regimes × 4 agents = 24 agent calls
```

如果预算更紧，可以先做：

```text
2 conditions × 2 target regimes × 4 agents = 16 agent calls
```

---

## 7. Coupled-system target regimes

目标任务不应该只问“能否跑通 full system”。要让 agent 选择并比较有科学意义的 regime。

### T1. Weak-coupling sanity regime

目的：检查 coupling sign、u/v 交互方向、守恒量是否合理。

预期有用现象：

- v soliton 在弱 u 背景中 speed shift；
- u 场有小幅但可见 response；
- no blow-up, no trivial decoupling。

失败例子：

- coupling effect 完全不可见；
- sign 错导致 v 朝反方向偏移；
- u/v interpolation 不守恒。

### T2. Gardner reduction regime

目的：当 full coupled system 太难时，测试是否能合理 narrow 到 `m = u - v^2/2 = 0` 的 Gardner-type reduction。

预期有用现象：

- 单 soliton 或双 soliton propagation；
- overtaking / interaction；
- mass / energy 近似守恒；
- 与 KdV soliton 有可解释差异。

失败例子：

- 只得到 KdV-like trivial behavior；
- invariant drift 过大；
- 非线性项 aliasing 导致假峰值。

### T3. Full coupled interaction regime

目的：探索 Burgers-swept-KdV 的核心现象。

预期有用现象：

- current-wave interaction；
- soliton refraction/reflection/fusion；
- shock-dispersion interaction；
- coupling-induced speed/amplitude shift。

失败例子：

- solver blow-up；
- boundary wrap-around 污染；
- full coupling 太 brittle，没有稳定 regime；
- agent 把数值 artifact 误称为新物理现象。

---

## 8. 实验条件与主表

### 8.1 条件

| Condition | NK bank | 目标 |
|---|---|---|
| `No-NK` | 不提供 | baseline，观察 agent 是否重复 source-task 已知错误 |
| `NK` | 提供阶段 A 结构化 NK | 测是否减少重复失败、降低成本、改善 route selection |

可选扩展：

| Condition | 用途 |
|---|---|
| `Success-only` | 只给成功方法摘要，测试“正知识是否足够” |
| `Raw-log` | 给原始 logs，测试结构化 NK 是否比 raw trace 更经济/可用 |

主文 4 页优先只写 `No-NK` vs `NK`，扩展条件放 appendix 或 follow-up。

### 8.2 主表模板

| Target regime | Condition | Valid exec ↑ | Useful phenomenon ↑ | Repeated failure ↓ | Invariant drift ↓ | False progress ↓ | Tokens ↓ | Decision |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Weak coupling | No-NK | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Weak coupling | NK | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Gardner reduction | No-NK | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Gardner reduction | NK | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Full coupled | No-NK | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Full coupled | NK | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

---

## 9. 评分指标

### 9.1 工程/数值指标

| Metric | 定义 |
|---|---|
| `valid_exec` | candidate 是否运行完成并产生 finite output |
| `nan_or_blowup` | 是否出现 NaN / Inf / numerical blow-up |
| `mass_drift` | 相关 conserved quantity 的相对漂移 |
| `energy_drift` | KdV/Gardner-like invariant 的相对漂移 |
| `positivity_violation` | shallow-water `h < 0` 或物理变量越界 |
| `boundary_artifact` | 周期边界 wrap-around 是否污染主要现象 |

### 9.2 科学结果指标

| Metric | 定义 |
|---|---|
| `useful_phenomenon` | 是否出现可解释、有价值的现象 |
| `phenomenon_match` | 是否符合预期方向，如 soliton speed shift / shock formation |
| `route_selection_quality` | 是否选择了合理 regime，而不是无意义参数 |
| `narrowing_quality` | full system 失败时，是否合理转向 Gardner / weak coupling |
| `claim_support` | 最终 claim 是否被数值证据支持 |
| `false_progress` | 是否把失败、artifact 或 inconclusive result 写成 positive discovery |

### 9.3 共享资产指标

| Metric | 定义 |
|---|---|
| `repeated_failure_rate` | target agent 是否重复 NK bank 中已记录 failure |
| `nk_usage_rate` | agent reasoning / plan 中是否引用相关 NK |
| `nk_relevance` | 引用的 NK 是否与当前问题相关 |
| `attempts_to_useful_result` | 达到有用结果所需尝试轮数 |
| `token_cost` | prompt + completion token 或字符数 |
| `wall_time` | 总 wall-clock time |

主 claim 最应该看：

```text
repeated_failure_rate, false_progress, route_selection_quality, useful_phenomenon, token_cost
```

PASS 不是唯一核心，因为本实验关注的是研究过程质量。

---

## 10. 成功判定

### 10.1 强支持

如果出现以下结果，可以在论文中较强地说：

> 在 Burgers-swept-KdV 研究任务中，Negative Knowledge 作为 team-level shared asset 减少了重复失败，并帮助 agent 选择更有科学价值的研究路线。

需要满足：

- NK 条件 repeated failure 明显少于 No-NK；
- NK 条件 false progress 更少；
- NK 条件更快找到至少一个 useful phenomenon 或合理 reduced regime；
- NK 条件中 agent 明确使用 source-task failure records；
- No-NK 中出现 NK bank 已记录过的错误。

### 10.2 中等支持

如果 NK 没提高 final useful result，但减少了 NaN、invariant drift、false progress，可以说：

> NK 未直接提高最终发现率，但改善了研究过程的可靠性和审计性。

### 10.3 负结果但仍有价值

如果 NK 也没有帮助，仍可以作为论文 limitation：

> 单纯把 failure records 提供给 agent 不足以支撑复杂 coupled PDE 研究；需要更强 retrieval、planner constraint、或 domain-specific validators。

这仍符合本文主题，因为失败本身也应被记录。

---

## 11. Prompt 设计规范

### 11.1 No-NK prompt 必须包含

- 目标方程；
- 可用 package；
- 输出格式；
- 预算限制；
- 要求 agent 说明选择的 regime、observable、expected phenomenon；
- 要求避免 unsupported claim。

不能包含：

- 阶段 A 的 failure records；
- “不要用某方法”这类来自 NK 的暗示；
- gold solver；
- evaluator 内部答案。

### 11.2 NK prompt 额外包含

- `negative_knowledge_bank.jsonl` 的相关记录；
- 每条 record 的 `target / observation / failure fields / rationale / transfer_hint`；
- 明确要求 agent 在 plan 中说明哪些 NK 被采用、哪些被拒绝、为什么。

不能包含：

- 直接可复制的 reference solver；
- “正确答案是 IMEX-spectral”这类专家菜单；
- 从 coupled target 先验泄漏出来的失败。

---

## 12. 文件结构

建议重组到当前目录下：

```text
paper/experiments/pde_pilot_2026-05-11/
├── PDE_EXPERIMENT_PLAN.md
├── PDE_TEST_SET.md
├── PDE_CASE_STUDIES.md
├── prompts/
│   ├── source_burgers.md
│   ├── source_kdv.md
│   ├── source_gardner.md
│   ├── source_shallow_water.md
│   ├── target_coupled_no_nk.md
│   └── target_coupled_with_nk.md
├── nk_bank/
│   ├── negative_knowledge_bank.jsonl
│   └── nk_review_table.csv
├── gold/
│   ├── burgers_shock_ref.py
│   ├── kdv_soliton_ref.py
│   └── ...
├── eval/
│   ├── burgers_T05_eval.py
│   ├── kdv_T2_eval.py
│   ├── coupled_regime_eval.py
│   └── nk_quality_eval.py
├── runs/
│   ├── source/
│   └── coupled/
│       ├── no_nk/
│       └── nk/
└── reports/
    ├── NK_PRODUCTION_REPORT.md
    ├── COUPLED_SYSTEM_COMPARISON.md
    └── FIGURES/
```

当前已有文件可以继续保留：

- `gold/burgers_shock_ref.py`
- `gold/kdv_soliton_ref.py`
- `eval/burgers_T05_eval.py`
- `eval/kdv_T2_eval.py`
- `runs/burgers_T05/...`
- `runs/kdv_T2/...`

这些作为阶段 A 的 seed/pilot。

---

## 13. 现有 pilot 状态

已经完成：

| Task | Outcome | 用途 |
|---|---|---|
| Burgers shock | PASS, `L1=0.0029` | 验证 pipeline 可跑；提供成功正例 |
| KdV soliton r1 | FAIL, all NaN | 可转化为 NK：unstable time-integration route |
| KdV soliton r2 | PASS after method change | 只作为 feasibility，不作为严格 NK-vs-NoNK 对比 |

注意：

- 现有 KdV round2 prompt 带有候选方法提示，因此不能作为“纯 NK 比 raw/no NK 更强”的主证据；
- 在新实验中，它只用于说明阶段 A 可以制作 research-style negative knowledge；
- 主证据必须来自 coupled-system `No-NK` vs `NK` 对比。

---

## 14. 执行步骤

### Step 1. 写 source prompts

为 S1-S5 写统一格式 prompt，要求 agent：

1. 选择数值方法；
2. 运行短时间模拟；
3. 输出 observable；
4. 判断是否出现预期现象；
5. 若失败或无价值，写 failure_record.json。

### Step 2. 跑 source tasks 并生成 NK bank

最小版本：

```text
S1 Burgers shock × 1 agent
S2 KdV soliton × 1 agent
S3 Gardner reduction × 1 agent
S4 Shallow water × 1 agent
```

收集所有 `failure_record.json`，人工/规则审核后合并：

```text
nk_bank/negative_knowledge_bank.jsonl
```

### Step 3. 写 coupled research brief

同一个 brief 同时用于 No-NK 和 NK，描述：

- Burgers-swept-KdV 方程；
- 可选 target regimes；
- 预算；
- 输出格式；
- evaluator / metrics；
- 禁止 unsupported discovery claim。

### Step 4. 跑 No-NK team

```text
Planner -> Solver -> Analyzer -> Reviewer
```

落盘：

```text
runs/coupled/no_nk/<regime_or_run_id>/
```

### Step 5. 跑 NK team

同样流程，但 prompt 额外包含 `negative_knowledge_bank.jsonl`。

落盘：

```text
runs/coupled/nk/<regime_or_run_id>/
```

### Step 6. 汇总对比

生成：

```text
reports/COUPLED_SYSTEM_COMPARISON.md
reports/FIGURES/*.png
```

主表填入：

- valid execution；
- useful phenomenon；
- repeated failure；
- invariant drift；
- false progress；
- token/time；
- selected route / final decision。

---

## 15. 论文写法

主文只写短版：

1. 我们的科学目标是研究 Burgers-swept-KdV 的性质；
2. 我们先用 component PDE 制作 NK；
3. 然后比较 No-NK vs NK 的 coupled-system multi-agent research；
4. 评价不是只看代码是否跑通，而看是否减少重复失败、是否找到有价值现象、是否避免 false progress；
5. 当前 Burgers/KdV pilot 证明 NK production phase 可行，完整 coupled 对比作为核心实验。

不要在主文中铺满 PDE spec。PDE spec、prompt、eval、records 放 appendix / repo。

---

## 16. 风险与控制

| 风险 | 控制 |
|---|---|
| NK prompt 泄漏答案 | 不提供 gold solver，不列专家方法菜单，只给 failure boundary 和 transfer hint |
| No-NK 和 NK 不公平 | 同模型、同预算、同 target brief、同 evaluator |
| Coupled system 太难 | 允许 route narrowing 到 Gardner / weak coupling，并把 narrowing quality 当指标 |
| Agent 只追求跑通 | 要求报告 useful phenomenon 和 claim support |
| 结果是 artifact | Reviewer agent 检查 invariant drift、boundary artifact、false progress |
| 样本量小 | 作为 workshop case study，不主张统计显著；报告 trace 和失败案例 |
| Reference/eval 自写偏差 | 使用解析性质、守恒律、可视化、多个 observable 交叉验证 |

---

## 17. 最小可交付版本

如果时间紧，最低完成：

1. Source NK bank:
   - Burgers shock；
   - KdV soliton；
   - shallow-water dam break；
   - Gardner reduction。
2. Coupled-system comparison:
   - `No-NK` 1 个 full/weak-coupling run；
   - `NK` 1 个 full/weak-coupling run；
   - 若 full coupled 失败，允许 Gardner reduction。
3. 报告：
   - `NK_PRODUCTION_REPORT.md`；
   - `COUPLED_SYSTEM_COMPARISON.md`；
   - 一张主表；
   - 2-4 条最有代表性的 failure records。

最小结论可以是：

> 在 Burgers-swept-KdV 研究流程中，NK 条件未必直接“解出”耦合系统，但它使 agent 更少重复已知数值失败，更明确地放弃无价值路线，并更合理地转向 Gardner 或 weak-coupling 简化情形。

