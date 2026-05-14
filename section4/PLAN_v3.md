# Section 4 v3 Experimental Plan

> 起草 2026-05-13 | 修订自 v1 (no discipline) / v2 (progressive-complexity discipline) / Tier-1 mechanism-inquiry pilot
> 核心 reframe: NK 的价值要在 **research character** + **knowledge depth** 维度上测，不是在 task-completion PASS/FAIL 维度上测

## 0. 三个关键 reframe（来自前期 5 轮 iteration）

| Reframe | 内容 | 影响 |
|---|---|---|
| 任务性质 | 从 "solve coupled PDE sub-task"（数值求解）扩到 "mechanism inquiry"（科学研究）| 衡量标准从 PASS/FAIL 变成 research character |
| NK 深度 | "试 N 轮失败的 path-level 否决" ≠ "一次失败的 error message" | 采用 **section 3 schema**：单轮 record (depth-1) + 多轮 synthesis (depth-N) 两种文件类型；stage 1 必须多轮迭代生成 |
| NK 内容 | trivial / 跑通但没价值 的 finding 也是 negative information | schema 加可选 `is_trivial` + `trivial_degree` 字段；评估但暂不深度使用 |

**schema 直接复用 section 3** 已落地的设计（见 `section3/04_outputs/nk_records/`），只小幅扩展两个 trivial 字段。这保证 cross-section schema 一致性，curator 流程也可以直接复用 section 3 的 prompt 模板（只换 task 描述）。

---

## 1. NK Schema v3（采用 section 3 schema + 小幅扩展）

**核心思路（来自 section 3）**：深度通过**两种独立的文件类型**表达，不是塞进单条 entry 的多字段里。

### 1.1 文件类型 1：单轮 NK record（depth = 1）

每轮失败产出一份。文件名 `<program_id>_r<N>.json`。

```json
{
  "task_id": "<program_id>",
  "round": 1 | 2 | 3,                                            // 1 时该字段可省
  "attempted_route": "<=200 chars; 具体 method/library/parameter 组合",
  "observation": "<=200 chars; 失败签名 (e.g. NaN at t=0.4, peak v drops from 2.0 to 0.6)",
  "failure": {
    "layer":   "implementation_failure | communication_failure | method_failure",
    "scope":   "local_failure | regime_bound_failure | general_failure",
    "degree":  "contradicted | partial | inconclusive | unstable | artifact_driven | overclaimed",
    "recommended_action": "retry | change_method | narrow_claim | abandon_route",
    "risk":    "low_risk_omission | medium_risk_drift | high_risk_false_progress"
  },
  "rationale": "<=300 chars; 1-2 句 mechanism-level 解释",
  "recommended_alternative": "<=300 chars; 具体 API + 参数",
  "relationship_to_round1": "new_failure_mode_unrelated_to_round1 | fixes_round1_exposes_round2 | refinement_of_round1_failure",  // 仅 round >= 2

  // v3 section-4 扩展（可选）
  "is_trivial": true | false,           // 该发现是否本身 trivial / 无信息量
  "trivial_degree": 0 | 1 | 2 | 3       // 0=非 trivial, 3=完全 tautology
}
```

### 1.2 文件类型 2：深度 NK record（depth = N，N ∈ {2, 3}）

跨多轮的 synthesis。文件名 `<program_id>_deep.json`。这是 user 强调的"真正的"NK ——多轮失败后归纳出的 path-level 否决。

```json
{
  "task_id": "<program_id>",
  "depth": 2 | 3,                                                // 跨几轮
  "rounds_summary": [
    {"round": 1, "attempted_route": "...", "observation": "..."},
    {"round": 2, "attempted_route": "...", "observation": "..."},
    {"round": 3, "attempted_route": "...", "observation": "..."}
  ],
  "ruled_out_routes": [
    "<=150 chars per item; 具体 (library + parameter) 组合，已证不行",
    "..."                                                        // 2-4 项
  ],
  "synthesised_diagnosis": "<=400 chars; ONE coherent mechanism-level 解释，统一所有失败。承重 claim。",
  "failure": { ... },                                            // 同 5-field 分类
  "rationale": "<=300 chars",
  "recommended_alternative": "<=400 chars; 必须 NOT 在 ruled_out_routes 中",

  // v3 section-4 扩展（可选）
  "is_trivial": true | false,
  "trivial_degree": 0 | 1 | 2 | 3
}
```

### 1.3 与 user "1/2/3 轮深度" 的对应

| User 描述 | section 3 实现 | 文件 |
|---|---|---|
| 一轮深度 | round-1 单独失败的 NK | `_r1.json` |
| 一轮深度（不同视角） | round-2 单独失败的 NK | `_r2.json` |
| 两轮深度 | depth=2 的 synthesis（程序在 r2 后 abandon 或 r3 不跑） | `_deep.json` with `depth: 2` |
| 三轮深度 | depth=3 的 synthesis（完整 3 轮失败） | `_deep.json` with `depth: 3` |

**自然产出 depth mix**：每个 3-round program 跑完后，curator 跑两次：
- Per-round（3 次）→ 产出 3 条 depth-1 records（`_r1, _r2, _r3`）
- Synthesis（1 次）→ 产出 1 条 depth-3 record（`_deep`）

bank 里同一个 program 的失败被多种粒度记录。bank-aware agent 既可以 cite 单轮 record（"R1 已知会因 X 失败"），也可以 cite deep record（"这整条路线被 3 轮证不行"）。

### 1.4 现有 30 条 entries 的处理

现有 30 条用的是 v2 的"6-field schema"，**结构上与 section 3 的单轮 NK schema 一致**，只是字段名略不同（v2 的 `evidence`/`applicability` 比 section 3 多）。处理方法：
- **保留全部 30 条** 作为 depth-1 baseline records
- 字段映射轻度修订（删 `kind`，加 `task_id`，加可选 `is_trivial=false / trivial_degree=0`）
- 5 条物理相关的标 high-priority：
  - `kb-gardner-GardnerIsM0-coupledSystemInstability`
  - `kb-gardner-sech2IC-not-exact-soliton`
  - `kb-kdv-amplitude-threshold-soliton`
  - `kb-gardner-G2-IMEX-CN-dealiased-stableRadiation` (positive)
  - `kb-gardner-KdV-method-transfer-moderate-amplitude` (positive)

---

## 2. Stage 1 v3：双层架构

### 2.1 Layer A — 保留现有 isolated-PDE stress tests（depth=1）

无改动。30 条 entries。这些主要是数值方法警告。

### 2.2 Layer B — 新增：直接对 BKdV 系统做 multi-round stress tests

5 个 "stress-test research program"，每个跑 **3 rounds Research-Graph 协议**。每个 program 是一个 research question，不是 "应用方法 X"。

| Program | Research question | 预期产出 |
|---|---|---|
| **BKdV-S1** | "What numerical methods stably integrate BKdV at amp ∈ [1, 3] for T=10? Find a working stack and 2+ failed routes." | 1 positive (success_depth N) + 2-3 negative (failure_depth 1-3) |
| **BKdV-S2** | "What conserved / nearly-conserved quantities exist in BKdV evolution, and which are numerical artifacts vs physical?" | 1-2 positive + 1-2 negative; 可能 trivial findings |
| **BKdV-S3** | "From which IC families does BKdV produce coherent (long-lived localized) structures, and from which does it produce incoherent radiation?" | 1-2 positive (IC families that work) + 1-2 negative (IC families that don't, depth ≥ 2 if multi-round) |
| **BKdV-S4** | "How does dt / Nx affect long-time qualitative behavior of BKdV solutions? Is there a regime where doubling resolution changes the qualitative answer?" | 1-2 negative entries about resolution sensitivity; potentially trivial-finding entries |
| **BKdV-S5** | "Does BKdV have modulational instability? Test by perturbing known stable structures and observing growth rates." | 1 positive (regime where stable) + 1 negative (regime where unstable, depth ≥ 2) |

**Multi-round protocol per program**:
- Round 1: agent proposes simplest meaningful approach to the question
- Round 2: based on F1, modify exactly one component（progressive-complexity discipline 保留）
- Round 3: based on F2, modify one more
- Curator reads full Q/E/F/D trace, identifies:
  - 哪条 path 被试了几轮 → `failure_depth` 标注
  - 哪条 path 成功 → `success_depth` 标注
  - 哪些 finding 是 trivial → `is_trivial` 标注
  - 把 round-by-round 装进 `evidence_chain`

### 2.3 Curator agent 协议（沿用 section 3 双 pass 模式）

每个 BKdV-S program 跑完 3 rounds 后，dispatch 两类 curator：

**Pass 1 — Per-round curators（3 次）**
- 每轮一个 curator agent，只读该轮的 `candidate.py + exec.log + reasoning.md`
- 产出 `<program_id>_r1.json`, `<program_id>_r2.json`, `<program_id>_r3.json`
- 每条是 depth-1 单轮 NK record（schema 见 §1.1）

**Pass 2 — Deep curator（1 次）**
- 一个 curator agent，读所有 3 轮的全部材料
- 产出 `<program_id>_deep.json`，schema 见 §1.2
- 这是 user 强调的"真正"NK ——`synthesised_diagnosis` + `ruled_out_routes` 是承重字段

每个 program 共产出 4 条 NK records（3 单轮 + 1 深度）。

### 2.4 V3 bank 最终构成

| Layer | 来源 | 数量 | depth 分布 | 物理 vs 数值 |
|---|---|---|---|---|
| A (现有) | 14 isolated PDE stress tests | 30 | 全 depth=1 单轮 records | 25 数值 + 5 物理 |
| B (新增 single-round) | 5 BKdV programs × 3 rounds | 15 | depth=1（per-round） | 物理 + 数值 mix |
| B (新增 deep) | 5 BKdV programs × 1 synthesis | 5 | depth=3（synthesis） | 物理 + 数值 mix |
| **总** | | **50** | 45 depth-1 + 5 depth-3 | mix |

(如果某些 program 在 r2 就成功 abandon，则只产 2 单轮 + 1 deep with depth=2，总数略变)

---

## 3. Stage 2 v3：两类任务

### 3.1 Class A — Warm-up sub-tasks（PASS/FAIL 评估）

保留 v2 的 3 个任务，作为 sanity check + baseline：

| Task | Description | Eval |
|---|---|---|
| T_A | Soliton stability under m=0 perturbation | parent-side phenomenon check |
| T_B | Gaussian → soliton train | parent-side phenomenon check |
| T_C | Bore × soliton interaction | parent-side phenomenon check |

- 3 tasks × 4 conditions (NoKB/PosOnly/NegOnly/PosNeg) = **12 cells**
- 协议：v2 progressive-complexity discipline，3 rounds per cell
- 目的：确认新 bank（含 depth tag）至少不比旧 bank 差；保留对论文的连续性

### 3.2 Class B — Mechanism inquiry tasks（research-character 评估）

**新增**两个进阶任务：

#### B1: Compound Soliton 形成机制 + basin + Gardner 关系

**研究问题**：
> 为什么 BKdV 系统从 generic IC 演化会在**局部**收敛到 compound soliton？该 compound soliton 与 Gardner soliton 在什么意义上等价？该 attractor 的 basin of attraction 是什么？

**关键已知物理 anchoring**（写入 prompt）：
- compound soliton 在局部形成，不是 global state
- 局部内 m = u - v²/2 ≈ 0，所以 compound soliton ≈ Gardner soliton（在该局部窗口）
- global ‖m‖_L2 *不* 是合适的诊断量
- ambient radiation 携带 off-manifold 能量但不破坏局部结构

**agent 需要 figure out**:
- 局部 m ≈ 0 的 *机制* —— 是 attracting manifold？radiation cooling？Hamiltonian balance？
- 收敛域（哪些 IC 在 T=20 内形成 compound soliton；哪些不收敛 / 慢；哪些收敛到多 compound）
- compound soliton 参数（amp, width, speed）与 IC 之间的映射关系
- 与 Gardner soliton 的精确对应（同 amp 同 width 同 c？或只是同 functional form？）

**Eval rubric**（rubric details §4.3）：
- 是否区分 local vs global m？
- 是否做了 basin 扫描（≥2 IC 类型）？
- 是否定量对比 compound soliton 和 Gardner soliton 形状？
- 是否提出 mechanism hypothesis 并尝试 falsify？

#### B2: Bore-Soliton Interaction 相图

**研究问题**：
> Bore-soliton interaction 在不同 (bore amplitude, soliton amplitude, relative speed) 参数下产生不同的相态（透射 / 反射 / 融合 / 破坏）。这些相态的边界在哪？相变是 sharp 还是 smooth？

**关键已知物理 anchoring**:
- 至少存在 transmission / reflection / fusion / destruction 几种 regime
- 不知道边界位置，不知道相变 sharpness
- 不知道是否存在 hysteresis 或 multi-stable regions

**agent 需要 figure out**:
- 多少个 distinct regime（≥3? ≥4?）
- 用什么 observable 判断 regime（peak transmission ratio? phase shift? mass exchange?）
- 边界处行为是 abrupt 还是 continuous
- 是否有可能的 "amphiphilic" regime（部分 transmission + 部分 reflection）

**Eval rubric**:
- 识别出几个 regime？
- 边界精度（与 oracle 高分辨率扫描对比）？
- 用了什么 observable，是否 well-justified？
- 是否做 numerical-artifact 控制？

#### Class B 统计

- 2 tasks × 4 conditions = **8 cells**
- 协议：Tier 1 mechanism-inquiry 协议（已验证 viable on compound soliton），3 rounds per cell
- 每 cell 输出：hypothesis.md + research_state.jsonl + evidence/

### 3.3 Stage 2 总 cell 数

- Class A: 12
- Class B: 8
- **总：20 cells**（4 conditions × (3 + 2) tasks）

---

## 4. 实验细节

### 4.1 Conditions（统一 4 个 across both classes）

| Condition | Bank content | 物理隔离方式 |
|---|---|---|
| NoKB | 空 | bank 文件不可读 |
| PosOnly | 所有 positive entries（含新 BKdV-S 来的） | 只能 cat `positive_knowledge.jsonl` |
| NegOnly | 所有 negative entries（含 depth 1/2/3 混合） | 只能 cat `negative_knowledge.jsonl` |
| PosNeg | 全部 | 两个都能读 |

**注**：本轮不做 depth-ablation（NegOnly-shallow vs NegOnly-deep）。先看 mixed-depth bank 的整体表现，根据结果决定是否需要更细的 ablation。

### 4.2 Iteration 协议

- Class A（warm-up）：progressive-complexity discipline + 3 rounds + Research Graph protocol + parent-side PASS/FAIL
- Class B（mechanism）：mechanism-inquiry prompt + 3 rounds + Research Graph protocol + hypothesis.md output

两类共用：
- Q/E/F/D 节点写入 `research_state.jsonl`
- bank 使用 mandatory cites_bank / rejects_bank / bank_use_rationale 字段
- **新增** is_trivial 字段：agent 在 Finding 节点也要 self-flag trivial 发现（已在 Tier 1 prompt 中演示，效果良好）

### 4.3 Eval rubric

**Class A**（4 项 PASS/FAIL）:
- 输出 `T_X.npy` 存在
- mass drift < 8%
- amp_ratio 满足任务阈值
- u, v bounded < 15

**Class B**（每项 0-3 分；总分 0-15）:

| 维度 | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Hypothesis 多样性 | 1 假设 tunnel-vision | 2-3 假设 | 3+ 显式 contrast | 5+ 含 meta-hypothesis |
| Falsification 严肃性 | 都在 confirming | 至少 1 次 attempted falsify | 显式设计 disconfirming exp | 主动 attempted falsify 最强 hypothesis |
| Numerical-vs-physical 区分 | 不区分 | 偶尔提及 | 至少 1 次 explicit control | convergence study + parameter ablation |
| Trivial 识别 | 把 trivial 当 finding | 偶尔标 trivial | 显式 trivial section in hypothesis.md | 主动避免 trivial experiments by design |
| Mechanism 接近度（vs oracle answer） | 完全错 / 没找到 | 部分对 | 大致对 + 1-2 specific claims | 对 + multiple falsifiable claims |

Eval 用 LLM judge（不同模型 + rubric prompt）+ 物理 oracle（我们自己定的 ground-truth picture）双重打分。

### 4.4 Resource budget

| 阶段 | Sub-agent calls | Wall time (parallel) | Tokens |
|---|---|---|---|
| Stage 1 Layer B (5 programs) | 5 | ~15 min | ~400k |
| Curator pass | 1 | ~5 min | ~150k |
| Stage 2 Class A | 12 | ~15 min | ~900k |
| Stage 2 Class B | 8 | ~15 min | ~800k |
| Eval (LLM judge) | 20 | ~10 min | ~300k |
| **Total** | **46** | **~60 min total (mostly parallel)** | **~2.55M tokens** |

---

## 5. 执行顺序

```
Phase 0 (now)     ─── Plan review + user sign-off
Phase 1 (5-13)    ─── Tag existing 30 entries with depth=1 + trivial=0
Phase 2 (5-13)    ─── Build 5 BKdV-S programs (prompts + dispatch)
Phase 3 (5-13)    ─── Curator pass → v3 bank
Phase 4 (5-14)    ─── Stage 2 Class A re-run with v3 bank (12 cells)
Phase 5 (5-14)    ─── Stage 2 Class B run (8 cells)
Phase 6 (5-14)    ─── Eval rubric (LLM judge + oracle compare)
Phase 7 (5-14)    ─── Cross-class analysis + STAGE2_REPORT_v3.md
Phase 8 (5-15)    ─── Section 4 paper draft v3 (revise old framings)
```

---

## 6. 论文 framing（v3 后预期能 claim）

| Claim | 关键 evidence | 风险 |
|---|---|---|
| **NK 有 depth 维度**：depth ≥ 2 的 path-level negation 比 depth=1 error-log 有更高边际价值 | 比较 Stage 2 中 cells 引用的 entries 的 depth 分布与 outcome 的关联 | 数据稀疏；可能要做 follow-up ablation 才能立 claim |
| **NK 在 mechanism-inquiry 任务上比在 task-completion 任务上 价值大** | Class A 上 bank-aware vs NoKB 的 PASS rate 差距 < Class B 上 research-character 分数差距 | 若 Class A 显示 bank 也大幅领先，则 claim 弱 |
| **Trivial-finding 的识别能力本身是 research character 的一部分** | rubric 中 trivial 识别维度的 cross-condition 分数 | Trivial 是 subjective 概念，rubric 一致性需校准 |
| **BKdV compound soliton 局部 ≈ Gardner soliton 是 attractor structure** | Class B B1 任务的 agent 发现 + oracle 物理 picture 一致 | agents 可能不全 reach 这个 finding |
| **Bore-soliton interaction 有 K 个 distinct regime** | B2 任务 agent 输出 + oracle 高分辨率扫描 | K 是未知；Class B B2 可能 agent 都识别不出 |

---

## 7. 与 v2 / v1 的关系

- **v1 (no discipline)**: 整套 archive 到 `runs_v1_no_progressive/`，作为 method-lookup confound 的 negative example
- **v2 (progressive discipline)**: 当前 `runs/`，作为 baseline。v3 计划在 Class A 上**重做** v2 的 12 cells，但用 v3 bank（含 depth tag 和 BKdV-S 新 entries）。
- **Tier 1 mechanism pilot (5-13 early)**: 已确认 mechanism inquiry 任务设计 viable。v3 把它扩为 4 conditions × 2 tasks (B1, B2) = 8 cells。

---

## 8. 用户决策（5-13 已敲定）

1. ✓ **整体形状 OK** (双层 stage 1，双类 stage 2，4 conditions × 5 tasks = 20 cells)
2. ✓ **BKdV-S 程序数 = 5**（不增不减）
3. ✓ **trivial_degree 仅记录不使用**（先有这个字段，不做 ablation condition）
4. ✓ **Class B judge 用 Opus**（比 Sonnet 强一档）
5. ✓ **执行顺序**：Stage 1 → Stage 2 Class A → **Class A traces 也走 curator 产 NK** → Stage 2 Class B（用扩展后的 bank）→ Opus judge

### 8.1 修订后的 bank 演化链

```
Stage 1 (5 BKdV-S programs)
        │
        ├─ per-round curator (3 × 5 = 15 records)
        └─ deep curator (5 deep records)
              │
              ▼
     bank_v3.A (50 records: 30 现有 + 20 stage-1 新)
              │
              ▼
Stage 2 Class A (12 cells, T_A/T_B/T_C × 4 conditions, bank_v3.A)
        │
        └─ Class A traces → curator (per-round + optional deep)
              │
              ▼
     bank_v3.B (~50 + Class-A-derived; depends on # failed cells)
              │
              ▼
Stage 2 Class B (8 cells, B1+B2 × 4 conditions, bank_v3.B)
        │
        └─ Opus judge over hypothesis.md + research_state.jsonl
              │
              ▼
       Section 4 v3 报告
```

新链路里 **Class A 失败的轨迹被 curator 抽出来作为 negative knowledge** —— 因为 Class A 的失败发生在和 Class B 同一个 BKdV 系统上，这些 NK 对 Class B 的 mechanism inquiry 直接相关。这把"研究流程中下游任务能学到上游失败"这件事 closed-loop 化。

Class B 的 PosOnly/NegOnly/PosNeg 等于在跑一个 **bank 比 Class A 时更厚** 的环境，并且 bank 里多出来的部分是 *coupled-system specific* 的 lessons（来自 Class A 上 BKdV 同系统的失败）。NoKB 在两类都不读 bank。

这条链路对 paper 的意义：bank 不是 static 的 ——它 grows as research progresses。Class B 也是 Class A 的下游（在同一 PDE 上）。如果 PosOnly/PosNeg 在 Class B 上比 NoKB 显著强，**部分原因可能是 bank_v3.B 含 Class A 衍生的 entries**，这本身就是 negative knowledge 真实使用场景的 demonstration。

---

## 9. 立即可做的第一步

如果 plan 通过，**最低成本的第一步**：
1. Tag 现有 30 entries → 5 分钟手工
2. 写 5 个 BKdV-S program prompts（沿用 Tier 1 mechanism-inquiry template + 程序特定 question）
3. 并行 dispatch 5 sub-agents（~15 min wall time）
4. 跑完看 trace 评估 depth 分布是否合理

若 (4) 显示 depth=2+ 比例足够（≥ 30%），则继续 Stage 2 Class A + B。
否则需要再 iterate stage 1 design。
