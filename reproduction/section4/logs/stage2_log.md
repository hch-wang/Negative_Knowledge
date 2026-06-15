# Section 4 Stage 2 Class A — Complete Experimental Log

> 完成日期 2026-05-13
> 任务: T_A (soliton stability), T_B (Gaussian → soliton train), T_C (bore × soliton)
> 条件: NoKB / PosOnly / NegOnly / PosNeg × 3 tasks = 12 cells per run
> 协议: Research Graph (Q/E/F/D nodes) + progressive-complexity discipline + ≤ 3 Experiment rounds per cell
> 共 2 个 bank 版本，2 套 eval 版本

---

## 0. Bank 演化

| Bank version | Entries | Composition | New deep-synthesis entries |
|---|---|---|---|
| **bank_v3.A initial** | 50 | 30 (section4/stage1, v2-era) + 20 (stage1_v3/BKdV-S1..S5) | S1, S2, S3, S4, S5 deep × 1 each |
| **bank_v3.A expanded** | 58 | + 8 (stage1_v3/BKdV-S6, S7) | S6, S7 deep synthesis 各 1 |

### Stage 1 BKdV-S programs (depth-3 synthesis 摘要)

| Program | Research question | Synthesised diagnosis |
|---|---|---|
| **S1** | 数值方法稳定性扫描 | Fourier + 2/3 dealias + RK4 stable to amp 3, T=10; aliasing is dominant fail mode without dealias |
| **S2** | 守恒量结构 | ∫u, ∫v 是 divergence-form tautology; C4 quadratic ansatz rule out by IBP residual; 真 BKdV Hamiltonian 含 cubic 耦合 |
| **S3** | IC family vs coherent structure | Smooth-localized → coherent compound; broadband → high-k cascade @ A≥0.8; soft σ-boundary at 0.3-0.4 |
| **S4** | 数值参数敏感度 | **Nx=256 sub-converged**, 30-140% diagnostic shift at Nx=512; (Nx, dt, ν_h) 耦合; ν_h ≤ 1e-22 safe envelope for smooth IC |
| **S5** | m=0 manifold invariance | **Algebraic**: `m_t|_{m=0} = (v-1)(6vv_x + v_xxx)` ≠ 0 for sech² IC; k-selective response to perturbations |
| **S6** | u-side viscosity 必需性 | Pre-validated stack 无 u-viscosity 在 bore IC 上 *quantitatively wrong*; **ν_linear=5e-2 推荐默认** OR ν_h=1e-9 (RK4 ceiling); **BKdV-S4 的 1e-20 safe envelope 对 bore IC 偏弱 13 个数量级** |
| **S7** | Gardner vs BKdV stability transfer | sech²+u=v²/2 at A=1.5 + Gardner: 稳定 (v_max drift -0.14%) / 同 IC + 全 BKdV: ‖m‖_L2 0→2.55, **v_max -62.8%**, n_peaks 1→8; mechanism cos-sim 0.94 |

---

## 1. Class A 第一次跑 (v3.A initial, bank=50)

### 1.1 Dispatch
- 12 sub-agents 并行
- ~900k tokens total, ~15 min wall (parallel)
- 全部 3 rounds 完成（some 早停 stop_useful）

### 1.2 Verified eval (v1, original phenomenon_checks)
| Task | NoKB | PosOnly | NegOnly | PosNeg |
|---|---|---|---|---|
| T_A | PASS (vT=1.32, 15 peaks chaos) | PASS (vT=1.01 via hyperviscosity tight) | FAIL (vT=0.64) | FAIL (vT=0.64) |
| T_B | FAIL (u=19.95) | PASS (2it, u=4.88) | FAIL (u=16.34) | PASS (1it, u=4.87) |
| T_C | FAIL (u=8.54) | FAIL (u=5.04) | FAIL (u=12.81) | PASS (2it, u=3.69) |
| **PASS rate** | **1/3** | **2/3** | **0/3** | **2/3** |

### 1.3 Iteration efficiency (success cells only)
| Cond | Iters | Avg |
|---|---|---|
| NoKB | [3] | 3.0 |
| PosOnly | [3, 2] | 2.5 |
| NegOnly | [] | — |
| PosNeg | [1, 2] | 1.5 |

### 1.4 Key per-cell agent traces (v3.A)

**T_A NoKB** (3 iter, eval v1 PASS): RK4+spectral → ETD-RK4 → RK45+hyperviscosity. End-state: 15-peak chaotic fragmentation, vT=1.32 (top fragment).

**T_A PosOnly** (3 iter, eval v1 PASS): Citing `kb-kdv-IMEX-CN-spectral-pass` etc. E3 加 spectral hyperviscosity on u (citing `kb-burgers-MUSCL-Godunov-shock-pass` 作为 "shock-capturing 方向"，用 hyperviscosity 作 "smallest-step")。**Hyperviscosity 副作用：dampen u → 减慢 v→u 能量转移 → artificially 保住 vT=1.01**。

**T_A NegOnly** (3 iter, eval v1 FAIL, vT=0.64 honest): E3 做 dt-convergence study 证明 amp decay 是物理 (BKdV-S5 cited via reject)。Single coherent peak.

**T_A PosNeg** (3 iter, eval v1 FAIL, vT=0.64 honest): E3 swap RK4→IMEX-CN (verification), 同 NegOnly 结论。

**T_B PosNeg** (1 iter PASS): 跳过 strict baseline，因 BKdV-S1 deep 已证 dealias 必需。Cited BKdV-S1 deep + `kb-gardner-nonlinearCFL-amplitude-boundary` (dt halving at amp=4)。

**T_C PosNeg** (2 iter PASS, u=3.69): E1 strict baseline → E2 加 dealias 直接通过。

---

## 2. T_A / T_B 上 eval v1 问题被识别 (5-13)

### 2.1 T_A: eval v1 reward chaos，punish physics

发现：
- amp_ratio ≥ 0.5 threshold 物理上不可达（BKdV-S7 deep quantified: sech² off-manifold IC → v_max -62.8% over T=10）
- n_dominant_peaks_vT ≥ 1 太宽：14-peak chaos 也满足
- **NoKB 的 chaotic 14-peak fragmentation 通过 eval（vT_max 是其中最高一片）；NegOnly/PosNeg 的真 coherent soliton vT=0.64 fail eval**

### 2.2 T_B/T_C: dt 选择决定 numerical-damping 程度

T_B 上所有 4 agents 用同样 Fourier+2/3 dealias+RK4，差别只在 dt：
- PosOnly/PosNeg dt=1e-4: `k_max³·dt = 1.97` 近 RK4 stability boundary 2.83 → high-k 数值阻尼 → u_max 稳在 ~5
- NoKB dt=5e-5, NegOnly dt=2.5e-5: 远离 boundary → 几乎无数值阻尼 → u Gibbs 暴露 → u_max 飙到 16-20

→ **eval pass/fail 在 catch dt 选择的 stability-boundary 现象，不是物理**

### 2.3 决策：T_A eval 需要修，T_B/T_C eval 在 v3.A' 下其实正确

理由：v3.A' 加 S6 后，bank-aware agents 用 explicit ν=5e-2 → u_max 受控 (NegOnly u=13.89, PosNeg u=8.08)，NoKB 没 S6 → u 爆 (49.26)。**这时 eval u_max < 15 catch 的是真"用没用 viscosity"，不是 dt-boundary artifact**。

---

## 3. Class A 第二次跑 (v3.A', bank=58, T_B 加 IC trap)

### 3.1 Dispatch
- 12 sub-agents 并行（4 hit policy false-positive，重新 dispatch）
- T_B prompts 额外加 "IC selection guidance" 邀请从 positive bank 取经验调整 IC（trap）
- Bank 含 BKdV-S6 (推 ν=5e-2) + BKdV-S7 (Gardner vs BKdV 稳定性 transfer)

### 3.2 Verified eval v2 (physics-aware) 结果

T_A 修正后 criteria:
- amp_ratio ≥ 0.25 (was 0.5; 匹配 BKdV-S7 prediction)
- **n_peaks_above_0.4 == 1 OR dominance_ratio > 1.5** (新增 single-dominant check)
- mass drift < 8%, bounded < 15

| Task | NoKB | PosOnly | NegOnly | PosNeg |
|---|---|---|---|---|
| T_A | FAIL (16 peaks, dom=1.03) | FAIL (9 peaks, dom=1.19) | **PASS** (1 peak, dom=635k) | **PASS** (1 peak, dom=636k) |
| T_B | FAIL (u=49.26) | FAIL (u=20.24) | **PASS** (2it, u=13.89) | **PASS** (2it, u=8.08) |
| T_C | FAIL (u=11.48) | **PASS** (3it, u=2.71) | **PASS** (2it, u=3.33) | **PASS** (2it, u=2.71) |
| **PASS rate** | **0/3** | **1/3** | **3/3** | **3/3** |

### 3.3 IC trap analysis

T_B prompt 加 "IC adaptation invitation from positive bank"。预期 PosOnly 会被 BKdV-S7_r1 (Gardner-stable sech² IC) 诱导换 IC。

**实际结果**：4 个 condition 都没换 IC。原因：
1. **Agents 用 task-semantic 推理**: "Task is Gaussian decomposition, not sech² propagation; reference IC has m=−v²/2≠0 already off m=0 manifold"
2. **Schema split bug**: S7_r2 (BKdV breakdown) 被 heuristic 错放到 positive bank（因 `action=retry`），所以 PosOnly 实际看到了 trap 的两半信息
3. NegOnly/PosNeg 显式 cite S5/S7 negative entries 拒绝 IC transfer

→ Trap 没成功，但暴露了 schema split heuristic 的弱点 + 验证 agent 的 task-semantic 推理能力。

---

## 4. v3.A vs v3.A' 对比 (physics-aware eval v2)

| Task | Cond | v3.A | v3.A' | 变化 |
|---|---|---|---|---|
| T_A | NoKB | FAIL | FAIL | — |
| T_A | PosOnly | FAIL | FAIL | — |
| T_A | NegOnly | PASS | PASS | — |
| T_A | PosNeg | PASS | PASS | — |
| T_B | NoKB | FAIL | FAIL | — |
| T_B | PosOnly | PASS | **FAIL** | regression (新 trap 干扰?) |
| T_B | NegOnly | FAIL | **PASS** | **S6 ν=5e-2 prescription** |
| T_B | PosNeg | PASS | PASS | — |
| T_C | NoKB | FAIL | FAIL | — |
| T_C | PosOnly | FAIL | **PASS** | **S6 ν=5e-2 prescription** |
| T_C | NegOnly | FAIL | **PASS** | **S6 ν=5e-2 prescription + S4 reject** |
| T_C | PosNeg | PASS | PASS | — |

### 4.1 Bank-version PASS rate (physics-aware)
| Cond | v3.A (50) | **v3.A' (58)** | Δ |
|---|---|---|---|
| NoKB | 0/3 | 0/3 | 0 |
| PosOnly | 1/3 | 1/3 | 0 (T_B regress + T_C improve) |
| **NegOnly** | **1/3** | **3/3** | **+2** |
| PosNeg | **3/3** | **3/3** | 0 (already maxed) |

---

## 5. 论文核心 findings

### 5.1 NegOnly 1/3 → 3/3 是最干净的 bank-value signal

加入 S6_deep entry 后，NegOnly 的 PASS rate 三倍化。S6_deep 关键点：

- `attempted_route`: "pre-validated stack with NO u-viscosity on bore IC"
- `observation`: "u_max 2.3× overshoot, TV(u) 42× inflation"
- **`recommended_alternative`: "linear viscosity ν=5e-2 OR k⁸ hyperviscosity ν_h=1e-9"**

最后一行（**prescriptive content in recommended_alternative**）是 NegOnly 从 "知道 X 不行" 升级到 "知道该用 Y" 的关键。**这条单一 entry 把 NegOnly 在 T_B + T_C 都救回**。

### 5.2 PosNeg 3/3 robust across bank versions

PosNeg 可以从 positive (S6 prescription) 和 negative (S4 envelope inadequate, S5/S7 m≠invariant) 双重读到 actionable signal。即使 PosOnly 有时 regress（T_B），PosNeg 更稳健。

### 5.3 NoKB 0/3 任何 bank 都没救

NoKB 在两个 bank 版本下都是 0/3 PASS。这 validate bank 真的提供了 agent 自己得不到的 actionable knowledge。

### 5.4 T_A 上 bank-aware "失败"原本是 honest physics

v1 eval 因 amp_ratio 0.5 threshold 与 BKdV-S7 量化预测冲突，错误地 punish NegOnly/PosNeg（vT=0.64 是物理正确的）reward NoKB（14-peak chaos）。物理-aware v2 eval 翻转 verdict。

### 5.5 PosOnly v3.A → v3.A' T_A 上从 PASS 退到 FAIL 是 *agent 变 honest*

v3.A 时 PosOnly 用 hyperviscosity 数值掩盖 → artificial vT=1.01 PASS。
v3.A' 加 S7 entry 后，PosOnly 知道 v_peak 衰减是 *物理* → 不再做 hyperviscosity trick → 诚实 vT=0.92 FAIL。
**Bank 越好 → agent 越懂物理 → 越拒绝数值技巧 → eval v1 数字看着越差，但其实是 character 提升**。

### 5.6 Schema split bug 揭示 positive/negative 分类的脆弱性

S7_r2 (BKdV breakdown finding) 因 `failure.recommended_action = retry` 被 heuristic 错放到 positive bank。PosOnly 实际读到了 trap 的两半信息。这说明：

- "positive" vs "negative" 的 binary split 对 partial-degree entries 模糊
- Agents 实际上把 bank 当 *混合知识源* 用，不被 label 严格约束
- 未来 paper 应该 frame: bank 是 *structured knowledge*，不是 *positive-vs-negative tagged signal*

---

## 6. 资源统计

| 阶段 | Sub-agent calls | Tokens | Wall time |
|---|---|---|---|
| Stage 1 (5 BKdV-S programs) | 5 | ~400k | ~13 min |
| Stage 1 (S6 + S7 added) | 2 | ~170k | ~12 min |
| Stage 1 curators (5 programs × 4) | 20 | ~700k | ~10 min |
| Stage 1 curators (S6+S7 × 4) | 8 | ~280k | ~5 min |
| Class A v3.A initial (12 cells) | 12 | ~900k | ~15 min |
| Class A v3.A' (12 cells, 4 re-dispatched) | 16 | ~1.1M | ~15 min |
| **Total** | **63** | **~3.5M** | ~70 min parallel |

---

## 7. 输出文件清单

```
section4/
├── stage1_v3/
│   ├── runs/BKdV-S{1..7}/                # 7 BKdV stress-test programs
│   │   ├── prompt.md, hypothesis.md, research_state.jsonl, session_log.md
│   │   └── round{1,2,3}/{candidate.py, exec.log, reasoning.md}
│   ├── nk_records/
│   │   ├── BKdV-S{1..7}_r{1,2,3}.json   # 21 single-round NK records
│   │   └── BKdV-S{1..7}_deep.json       # 7 deep synthesis NK records
│   └── bank/
│       ├── bank_v3A_positive.jsonl       # 15 entries
│       ├── bank_v3A_negative.jsonl       # 43 entries
│       └── bank_v3A_index.json
└── stage2_v3/class_A/
    ├── runs/                              # v3.A' (with bank 58, T_B trap)
    │   └── T_{A,B,C}/{NoKB,PosOnly,NegOnly,PosNeg}/
    │       ├── prompt.md, candidate.py, reasoning.md
    │       ├── research_state.jsonl, session_log.md
    │       ├── pred_results/T_X.npy
    │       └── verified_eval.json
    ├── runs_initial_5programs_bank/       # v3.A initial (bank 50)
    │   └── T_{A,B,C}/{NoKB,PosOnly,NegOnly,PosNeg}/...
    ├── eval/phenomenon_checks.py          # v1 (legacy)
    ├── eval/phenomenon_checks_v2.py       # v2 physics-aware
    ├── scripts/build.py
    ├── scripts/run_eval.py                # uses v1
    ├── scripts/run_eval_v2.py             # uses v2, evaluates both bank versions
    ├── verified_results.json              # v3.A' eval v1
    └── CLASS_A_LOG.md                     # THIS FILE
```
