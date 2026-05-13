# Paper §3 claim reproduction report

Computed from on-disk archive at `section3/04_outputs/`. **43/43 claims match.**

| Claim | Expected | Computed | Match | Source |
|---|---|---|:-:|---|
| pilot subset size | `38` | `38` | ✓ | /Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pilot_2026-05-10/tasks/task_*.json |
| baseline round-1 PASS (across 38 pilot tasks) | `12` | `12` | ✓ | pilot runs/task_*/sonnet_4.6/result.json |
| v3 round1 cell PASS (by selection = 0) | `0` | `0` | ✓ | 04_outputs/dispatches/solver/task_*__round1.json |
| NK-test subset size | `24` | `24` | ✓ | derived from v3 round1 cell |
| hard subset size (B2 fails all 3 rounds) | `19` | `19` | ✓ | derived from round2_B2 + round3_B2 cells |
| Table 1: round-1 baseline PASS / 38 | `12/38` | `12/38` | ✓ | pilot baseline result.json (sonnet_4.6 root level) |
| Table 1: + B0 retry PASS / 38 | `12/38` | `12/38` | ✓ | baseline + round2_B0 cell |
| Table 1: + NKR (depth-1) PASS / 38 | `14/38` | `14/38` | ✓ | baseline + round2_NKR cell |
| Table 1: + B2 covering PASS / 38 | `17/38` | `17/38` | ✓ | baseline + round2_B2 + round3_B2 cells |
| Table 1: + deepNKR (depth-3) PASS / 38 | `18/38` | `18/38` | ✓ | baseline + deepNKR_sonnet cell |
| controlled view: NKR r2 on 24 | `2/24` | `2/24` | ✓ | round2_NKR cell |
| controlled view: NKR chain (r2+r3) on 24 | `3/24` | `3/24` | ✓ | round2_NKR + round3_NKR cells |
| controlled view: B3 mixed on 24 | `4/24` | `4/24` | ✓ | round2_B3 + round3_B3 cells |
| controlled view: B2 covering on 24 | `5/24` | `5/24` | ✓ | round2_B2 + round3_B2 cells |
| hard 19: NKR r2 | `0/19` | `0/19` | ✓ | round2_NKR cell |
| hard 19: NKR chain | `0/19` | `0/19` | ✓ | round2_NKR + round3_NKR cells |
| hard 19: B2 covering | `0/19` | `0/19` | ✓ | round2_B2 + round3_B2 cells |
| hard 19: deepNKR-Sonnet | `1/19` | `1/19` | ✓ | deepNKR_sonnet cell |
| hard 19: deepNKR-Haiku (cross-model) | `0/19` | `0/19` | ✓ | deepNKR_haiku cell |
| headline: round-1 baseline % | `31.6` | `31.6` | ✓ | round1 cell |
| headline: final pipeline % | `47.4` | `47.4` | ✓ | round1 + round2_NKR + round2_B2 + round3_B2 + deepNKR_sonnet |
| headline: PASS lift (tasks) | `+6` | `+6` | ✓ | all of above |
| memory bytes: B2 covering median | `4272` | `4272` | ✓ | pilot runs/task_*/sonnet_4.6/v3/round1/{candidate.py,exec.log,eval.log} |
| memory bytes: r1 NK median | `1187` | `1187` | ✓ | 04_outputs/nk_records/task_<id>.json |
| memory bytes: deep NK median | `3354` | `3354` | ✓ | 04_outputs/nk_records/task_<id>_deep.json |
| memory savings: r1 NK vs B2 (%) | `72.2` | `72.2` | ✓ | bytes table |
| memory savings: deep NK vs B2 (%) | `21.5` | `21.5` | ✓ | bytes table |
| solver tokens: round-1 median | `16262` | `16262` | ✓ | solver dispatches |
| solver tokens: round2_B0 median | `16391` | `16391` | ✓ | solver dispatches |
| solver tokens: round2_NKR median | `18080` | `18080` | ✓ | solver dispatches |
| solver tokens: round2_B2 median | `19641` | `19641` | ✓ | solver dispatches |
| solver tokens: deepNKR-Sonnet median | `19247` | `19247` | ✓ | solver dispatches |
| solver tokens: deepNKR-Haiku median | `48360` | `48360` | ✓ | solver dispatches |
| r2 NK count | `22` | `22` | ✓ | 04_outputs/nk_records/task_*_r2.json |
| r2 relationship: correct_but_insufficient | `13` | `13` | ✓ | r2 NK records |
| r2 relationship: new_failure_mode_unrelated_to_round1 | `7` | `7` | ✓ | r2 NK records |
| r2 relationship: round1_recipe_was_wrong | `2` | `2` | ✓ | r2 NK records |
| r2 NK error rate (%) | `9.1` | `9.1` | ✓ | r2 NK records |
| layer dist: implementation | `15` | `15` | ✓ | r1 NK records |
| layer dist: communication | `7` | `7` | ✓ | r1 NK records |
| layer dist: method | `2` | `2` | ✓ | r1 NK records |
| task_072 is in deepNKR_sonnet PASS set | `True` | `True` | ✓ | deepNKR_sonnet/task_072/result.json |
| task_072 deepNKR-Sonnet eval_score | `1` | `1` | ✓ | /Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section3/04_outputs/dispatches/solver/task_072__deepNKR_sonnet.json |
