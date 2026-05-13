# Stage 1 Knowledge Production — Index & Summary

> 完成日期：2026-05-12  
> 累计 sub-agent calls：16 (10 A-stress + 4 G-stress + 2 curator)  
> 累计 tokens：~330k (Sonnet 4.6)  
> Wall time：~12 min  
> 产出：`knowledge_bank.jsonl` 共 30 条 ✓/✗ 条目，30/30 evidence 引用真实存在

---

## 1. 14 个 stress-test sandboxes 概览

每个 sandbox 含 `prompt.md` / `candidate.py` / `reasoning.md` / `exec.log` / `result.json` / `meta.json`，路径 `sandboxes/<ID>/`.

### Burgers 系列 (3 个)

| ID | 强制约束 | 实测 outcome |
|---|---|---|
| **A1** | forward Euler + central FD（禁限制器） | finite 但 21 个 peaks，振幅冲到 ±3.6（IC ±1）— Gibbs 振荡 |
| **A2** | T=0.1（shock 未形成） | 平滑波 1 peak max_jump=0.05 — 没 shock 特征 |
| **A3** | T=10（boundary contamination） | 振幅衰减到 ±0.09 — LF 长时间过度耗散 |

### KdV 系列 (3 个)

| ID | 强制约束 | 实测 outcome |
|---|---|---|
| **A4** | explicit RK4 only | dt=1e-5 没崩，但 soliton 碎成 10 peaks |
| **A5** | Fourier spectral 但**无 dealiasing** | 振幅膨胀 2.87（IC 2），4 spurious peaks |
| **A6** | amplitude=0.1（小） | 振幅 0.05，8 peaks — soliton character 丢失 |

### Shallow Water 系列 (4 个)

| ID | 强制约束 | 实测 outcome |
|---|---|---|
| **A7** | forward Euler + central FD | **h 跌负 (h_min = -0.139)**，momentum 5.3e10 — 灾难 |
| **A8** | global Lax-Friedrichs | h ∈ [1.45, 1.81]，mass=300 守恒 — works 但 diffusive |
| **A9** | dry-bed IC (h_R=0) | h_min=0.002（加了 positivity clip）但 hu 巨大 |
| **A10** | HLL Riemann solver | h ∈ [1.45, 1.87]，mass=300，干净 dam-break |

### Gardner 系列 (4 个)

| ID | 强制约束 | 实测 outcome |
|---|---|---|
| **G1** | explicit RK4 | mass=3.000 但 14 peaks，soliton 碎 |
| **G2** | IMEX-CN spectral + 2/3 dealiasing | 稳定 mass=3.000，但 IC 不是真 Gardner soliton 所以 radiates（peak 衰减到 0.61） |
| **G3** | IMEX-CN spectral，**无 dealiasing** | 11 peaks，振幅 1.545（轻微 inflation），cubic aliasing |
| **G4** | IMEX-CN 但 IC amplitude=3.0 | **全 256 NaN** — 非线性 CFL 振幅依赖 |

### Prior pilot（已有 3 个 BKdV 案例）

| 来源 | 方法 | outcome |
|---|---|---|
| Pilot Burgers T=0.5 | MUSCL+vanLeer+Godunov+Euler | ✓ PASS（L¹=0.003） |
| Pilot KdV T=2 r1 | Fourier + integrating-factor RK4 | ✗ 全 NaN |
| Pilot KdV T=2 r2 | Fourier + Crank-Nicolson IMEX | ✓ PASS（peak=3.05, amp=2.03, mass=4.000） |

---

## 2. 30 条 Knowledge Bank（按 domain × kind）

| Domain | ✓ Positive | ✗ Negative | 小计 |
|---|---|---|---|
| Burgers | 2 | 3 | 5 |
| KdV | 4 | 3 | 7 |
| Shallow water | 2 | 3 | 5 |
| Gardner | 2 | 7 | 9 |
| General (cross-domain syntheses) | 1 | 3 | 4 |
| **合计** | **10** | **20** | **30** |

### Negative entries 的 schema 字段分布（20 条）

| field | distribution |
|---|---|
| layer | method_failure 11 / hypothesis 4 / measurement 3 / implementation 2 |
| scope | regime_bound **12** / general 6 / local 2 |
| degree | partial 9 / contradicted 5 / unstable 3 / overclaimed 2 / artifact_driven 1 |
| recommended_action | **narrow_claim 13** / change_method 7 |
| risk | high_risk_false_progress 10 / medium_risk_drift 8 / low_risk_omission 2 |

---

## 3. 30 个 entry 一行列表

```
 1. [✓] [burgers] kb-burgers-MUSCL-Godunov-shock-pass
 2. [✗] [burgers] kb-burgers-fwdEuler-centralFD-Gibbs
 3. [✓] [burgers] kb-burgers-Godunov-preShock-smooth
 4. [✗] [burgers] kb-burgers-LaxFriedrichs-longTime-dissipation
 5. [✗] [burgers] kb-burgers-LaxFriedrichs-periodic-longTime-contamination
 6. [✓] [kdv]     kb-kdv-IMEX-CN-spectral-pass
 7. [✗] [kdv]     kb-kdv-IFRK4-blowup
 8. [✗] [kdv]     kb-kdv-explicit-RK4-stiffness-blowup
 9. [✗] [kdv]     kb-kdv-noDealiasing-aliasing-artifacts
10. [✓] [kdv]     kb-kdv-smallAmplitude-dispersiveRegime
11. [✗] [kdv]     kb-kdv-amplitude-threshold-soliton
12. [✗] [shallow] kb-shallowWater-centralFD-fwdEuler-hNegative
13. [✓] [shallow] kb-shallowWater-LaxFriedrichs-stable-smeared
14. [✗] [shallow] kb-shallowWater-LaxFriedrichs-overdiffusion
15. [✓] [shallow] kb-shallowWater-HLL-dam-break-pass
16. [✗] [shallow] kb-shallowWater-dryBed-naiveClip-hu-singular
17. [✗] [general] kb-general-centralFD-hyperbolic-shockFormation
18. [✗] [general] kb-general-finiteness-not-accuracy
19. [✓] [kdv]     kb-kdv-spectral-solitonAmplitude-conservation
20. [✓] [general] kb-general-firstOrder-Godunov-preShock-baseline
21. [✗] [gardner] kb-gardner-G1-explicitRK4-finiteFrag
22. [✓] [gardner] kb-gardner-G2-IMEX-CN-dealiased-stableRadiation
23. [✗] [gardner] kb-gardner-G3-noDealiasing-cubicAliasing
24. [✗] [gardner] kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup
25. [✗] [gardner] kb-gardner-sech2IC-not-exact-soliton
26. [✗] [gardner] kb-gardner-cubicTerm-tightens-nonlinearCFL
27. [✗] [general] kb-general-massConservation-insufficient-diagnostic
28. [✗] [gardner] kb-gardner-GardnerIsM0-coupledSystemInstability
29. [✓] [gardner] kb-gardner-KdV-method-transfer-moderate-amplitude
30. [✗] [gardner] kb-gardner-nonlinearCFL-amplitude-boundary
```

---

## 4. 30 个 entries → Stage 2 三个子任务的迁移映射

### T-A: 孤子稳定性（coupled BKdV，IC 接近 m=0 reduction）

**最相关 KB**:
- #6 IMEX-CN-spectral-pass（KdV 基准方法）
- #22 Gardner-G2-stableRadiation（Gardner 退化下的可工作方法）
- #25 sech²IC-not-Gardner-soliton（IC choice 警告）
- #28 GardnerIsM0-coupledSystemInstability（Gardner 反例直接预警 coupled）
- #1 Burgers MUSCL-Godunov-shock（u 场的可用方法）

### T-B: Gaussian → 孤子列

**最相关 KB**:
- #10 KdV-smallAmplitude-dispersiveRegime（小 amp 散开变线性）
- #11 KdV-amplitude-threshold-soliton（amplitude 必须够大）
- #9 KdV-noDealiasing-aliasing-artifacts（Gaussian 窄 → dealiasing 必备）
- #19 spectral-solitonAmplitude-conservation（mass/amp 守恒检查）

### T-C: Bore × soliton 相互作用

**最相关 KB**:
- #1 Burgers MUSCL-Godunov（bore 处理基础）
- #15 SW HLL-dam-break-pass（强非线性 bore 范例）
- #2 / #12 / #17 中心差分双曲灾难（明确警告）
- #6 / #22 IMEX-CN 谱方法（v 部分必备）
- #26 Gardner cubicTerm-CFL（bore 振幅大时的 CFL 警告）

---

## 5. 文件清单

```
stage1/
├── STAGE1_INDEX.md              ← 本文件
├── knowledge_bank.jsonl         ← 30 entries
├── stage1_results.json          ← 14 runs 的 diagnostic
├── build_stage1.py / build_gardner.py
├── run_stage1.py
├── curator_prompt.md / curator_extension_prompt.md
├── sandboxes/{A1..A10, G1..G4}/
│   ├── prompt.md
│   ├── candidate.py
│   ├── reasoning.md
│   ├── exec.log
│   ├── result.json
│   └── meta.json
├── gold/
│   ├── shallow_water_ref.py
│   ├── burgers_shock_ref.py  (in parent dir, reused)
│   └── kdv_soliton_ref.py    (in parent dir, reused)
└── ref_results/sw_T04_REF.{npy,_x.npy}
```

---

## 6. 给 Stage 2 准备的关键 take-aways

1. **必备方法基线**：u 场用 MUSCL+Godunov 或 HLL，v 场用 IMEX-CN spectral + 2/3 dealiasing
2. **必备避坑清单**：禁止中心差分双曲、禁止 explicit RK4 处理 stiff dispersion、禁止 IFRK4 不带 dealiasing
3. **必备 diagnostic**：不能只看 NaN/mass；必须查 peak count / amplitude / oscillation
4. **必备 IC 警告**：sech² IC 在 Gardner 区会 radiate；amp 太小没 soliton；amp 太大触发非线性 CFL
5. **必备 T 警告**：周期边界长时间污染；短时间没现象
