# Paper §3 claim reproduction
Computed from `logs`. **30/30 claims match.**

| Claim | Expected | Computed | Match |
|---|---|---|:-:|
| pilot subset size | `38` | `38` | ✓ |
| baseline round-1 PASS (across 38 pilot tasks) | `12` | `12` | ✓ |
| NK-test subset size | `24` | `24` | ✓ |
| hard subset size | `19` | `19` | ✓ |
| Table 1: baseline PASS / 38 | `12/38` | `12/38` | ✓ |
| Table 1: + B0 retry PASS / 38 | `12/38` | `12/38` | ✓ |
| Table 1: + NKR depth-1 PASS / 38 | `14/38` | `14/38` | ✓ |
| Table 1: + B2 covering PASS / 38 | `17/38` | `17/38` | ✓ |
| Table 1: + deepNKR depth-3 PASS / 38 | `18/38` | `18/38` | ✓ |
| controlled: NKR r2 on 24 | `2/24` | `2/24` | ✓ |
| controlled: B2 covering on 24 | `5/24` | `5/24` | ✓ |
| controlled: deepNKR-Sonnet on 19 hard | `1/19` | `1/19` | ✓ |
| controlled: deepNKR-Haiku (cross-model) on 19 | `0/19` | `0/19` | ✓ |
| headline: baseline % | `31.6` | `31.6` | ✓ |
| headline: final % | `47.4` | `47.4` | ✓ |
| headline: PASS lift | `+6` | `+6` | ✓ |
| bytes: B2 covering median | `4272` | `4272` | ✓ |
| bytes: r1 NK median | `1187` | `1187` | ✓ |
| bytes: deep NK median | `3354` | `3354` | ✓ |
| bytes savings: r1 NK vs B2 (%) | `72.2` | `72.2` | ✓ |
| bytes savings: deep NK vs B2 (%) | `21.5` | `21.5` | ✓ |
| r2 NK count | `22` | `22` | ✓ |
| r2 relationship: correct_but_insufficient | `13` | `13` | ✓ |
| r2 relationship: round1_recipe_was_wrong | `2` | `2` | ✓ |
| r2 NK error rate (%) | `9.1` | `9.1` | ✓ |
| solver tokens: round-1 median | `16262` | `16262` | ✓ |
| solver tokens: round2_NKR median | `18080` | `18080` | ✓ |
| solver tokens: deepNKR-Sonnet median | `19247` | `19247` | ✓ |
| solver tokens: deepNKR-Haiku median | `48360` | `48360` | ✓ |
| task_072 in deepNKR_sonnet PASS set | `True` | `True` | ✓ |
