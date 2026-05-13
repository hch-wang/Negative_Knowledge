# PDE numerical-method test set — real autoresearch case studies

> 基于 Holm et al. 2025 (arXiv:2505.17026) 提出的 **Burgers-swept KdV 系统** 与经典 **Cahn-Hilliard / Willmore** 类 4-阶 PDE，设计 4 个数值求解任务。每个任务都有真实的物理失败模式（不稳定、blow-up、mass loss、wrong soliton speed），让 autoresearch 框架在"模型自由选择数值方案"的设定下试解，记录 bounded failure record，再传给下一轮。

---

## 目标

- 跑出**真实的 PDE solver 失败**（不是 ScienceAgentBench 的 schema mismatch）
- 失败应能自然落到 6-field schema 上：
  - `layer = method_failure / implementation_failure`
  - `scope = regime_bound`（"在 ν<ε 时方案不稳"）
  - `degree = unstable / contradicted / artifact_driven`
  - `recommended_action = change_method / narrow_claim`
- 形成 4 个"案例"补论文 §6

---

## 测试任务

### **BKdV-T1：Inviscid Burgers shock formation**

经典激波形成测试，所有有限差分入门题。

**PDE**: `u_t + u u_x = 0` on x ∈ [-1, 1] periodic, Nx=200

**IC**: `u_0(x) = -sin(π x)`

**Final time**: T = 0.5（远过激波形成时刻 t = 1/π ≈ 0.318）

**Output**: `pred_results/burgers_T05.npy`, shape (200,) array of u(x, T) on grid x = -1 + 2k/200 for k=0..199

**Eval criterion**: L¹-norm of error vs reference < 0.10

**Reference solver**: WENO-5 + TVD-RK3 on fine grid (Nx=2000), downsample。

**Expected failure modes**:
- Central differences → Gibbs oscillations near shock
- Naive upwind → too much numerical diffusion (smearing)
- Explicit Euler with CFL > 0.5 → blow-up
- 正确解需要 TVD/WENO + 限制器

**Why this is a research-style task**: 一个看似简单的 IVP，但默认 numpy 思路（中心差分 + RK4）会失败；需要选对方法（限制器 / TVD）。

---

### **BKdV-T2：KdV single soliton propagation**

3-阶 spatial derivative，弱非线性 + 强 dispersion，要求隐式或谱方法。

**PDE**: `v_t + 6 v v_x + v_xxx = 0` on x ∈ [-15, 15] periodic, Nx=256

**IC**: `v_0(x) = 2 sech²(x + 5)`（孤子幅度 2，初始位置 x=-5）

**Final time**: T = 2.0 (孤子速度 = 4，期待位置 x = +3)

**Output**: `pred_results/kdv_T2.npy`, shape (256,)

**Eval criterion**:
- Peak position within ±0.5 of x=+3
- Peak amplitude within ±0.15 of 2.0
- Mass `∫ v dx` 保守 within 1%

**Reference solver**: Fourier spectral + ETDRK4

**Expected failure modes**:
- Explicit Euler / RK4 → instability（third derivative requires dt ~ dx³，CFL 极小）
- Pure implicit → over-damping → 孤子幅度衰减
- IMEX (treat dispersion implicitly, nonlinearity explicitly) → 成功
- 或谱方法 + ETDRK4

---

### **BKdV-T3：Coupled Burgers-swept KdV (Gardner regime)**

论文主方程的特殊情形：m=0 → 退化为 Gardner 方程。测试"两个不同速度的孤子相互作用"。

**PDE (Gardner)**: `v_t + 6 v v_x + (3/2) v² v_x + v_xxx = 0` on x ∈ [-30, 30] periodic, Nx=512

**IC**: 两个 Gardner 孤子（较大幅度在左，较小在右；较大那个会追上）

**Final time**: T = 5.0（足以看到追上 + 通过）

**Output**: `pred_results/gardner_T5.npy`, shape (512,)

**Eval criterion**:
- Mass + energy conserved within 2%
- Final state 含两个分离的 peaks
- 较大孤子在较小孤子右边（通过事件已完成）

**Expected failure modes**:
- 同 T2，但 3-阶 + 5-阶非线性更难
- Conservation 失稳 → 任意一个 conserved quantity 飘移 > 2%

---

### **WCH-T1：Cahn-Hilliard 1D periodic phase separation**

4-阶 phase-field PDE，stiff，需要 IMEX or convex-splitting (Eyre)。

**PDE**: `u_t = ∂_xx (-∂_xx u + W'(u))`, with `W(u) = (1 - u²)² / 4`, so `W'(u) = u³ - u`
On x ∈ [0, 2π] periodic, Nx=128

**IC**: `u_0(x) = 0.05 * cos(x) + 0.02 * sin(3x)`（确定性小扰动，便于 reproducibility）

**Final time**: T = 50

**Output**: `pred_results/ch_T50.npy`, shape (128,)

**Eval criterion**:
- Mass conserved: `|mean(u_T) - mean(u_0)| < 1e-3`
- Phase separated: ≥ 80% of points have `|u| > 0.8`
- Energy `F = ∫ [½(u_x)² + W(u)] dx` 单调下降

**Reference**: Fourier spectral + IMEX-Euler with implicit linear part

**Expected failure modes**:
- Fully explicit → 立刻 blow up（4-阶 stiff）
- Naive implicit on nonlinear part → mass not conserved
- Eyre splitting / IMEX → 成功

---

## Pilot 选择

先从 **BKdV-T1 (Burgers shock)** 开始：
- 物理直观，所有学过 PDE numerics 的人都见过
- 失败模式可观察可视化（Gibbs oscillations）
- Reference solver 短（~50 行 WENO-5 + RK3）
- 单次求解 < 5s

如果跑通 framework，再扩展到 T2/T3/T4。

---

## Autoresearch 框架适配

**Round-1 (B1 Direct)**:
- Sub-agent 看 task spec（PDE 公式 + IC + BC + 输出格式）
- 自己写 solver，不给 hint 用什么方法
- 期待：很多 agent 会选默认 central diff + RK4 → 失败

**Round-2 (B3 Research Graph with M4 memory)**:
- Sub-agent 看 task spec + round-1 failure record
- failure record 应该编码"oscillations near shock" → layer=method, action=change_method
- 期待：sub-agent 改用 TVD/WENO → 成功

**Eval pipeline**:
- 跑 candidate.py → 看是否输出 `pred_results/<name>.npy`
- 跑 eval script → L¹ 误差 vs reference
- 自动分类失败：
  - NaN/Inf in output → `degree=unstable`
  - large oscillations (|Δu| local > 2 * |u|_max) → `degree=artifact_driven`
  - L¹ > threshold but smooth → `degree=contradicted`（错算法但稳）

---

## 资源预算

| 阶段 | 内容 | 估计 |
|---|---|---|
| 编 reference solver + eval 4 tasks | ~200 行 Python | 我自己写，不动 sub-agent |
| Pilot BKdV-T1 round-1 (Sonnet) | 1 sub-agent call | ~15k tokens |
| Pilot BKdV-T1 round-2 with M4 | 1 sub-agent call | ~16k tokens |
| 扩展 4 tasks × {r1, r2} = 8 calls | full pilot | ~150k tokens |
| Wall time (每个 task solver 跑 < 30s) | | 8 calls × 30s + ~5 min sub-agent = ~10 min |

非常便宜。先 pilot T1 (2 calls)，再扩展。

---

## 期待的论文贡献增量

如果实验跑通，§6 case studies 多 4 个**真实物理任务**：

| Case | 任务 | Layer | 故事 |
|---|---|---|---|
| F | BKdV-T1 Burgers | method | r1 默认 central diff → Gibbs；M4 记录 `change_method` → r2 用 WENO/TVD → PASS |
| G | BKdV-T2 KdV | implementation | r1 explicit RK4 → blow up；M4 → r2 IMEX/spectral → PASS |
| H | BKdV-T3 Gardner | method | r1 conservation 漂移；M4 hint → r2 用 symplectic/conserving 方案 |
| I | WCH-T1 Cahn-Hilliard | implementation | r1 explicit → blow up at T~0.01；M4 → r2 IMEX-Euler → PASS |

每个都是"PDE 数值方法"教材里的失败 → 修复路径，**比 ScienceAgentBench schema-mismatch 案例更有说服力**（因为是真物理问题）。
