# Section 4 claim verification report

**20/20 claims match.**

| ✓/✗ | Claim | Expected | Computed | Source |
|---|---|---|---|---|
| ✓ | Stage 1 program count | `7` | `7` | logs/stage1/BKdV-S*/ |
| ✓ | Stage 1 NK records total | `28` | `28` | logs/nk_records/*.json |
| ✓ |   per-round (depth-1) records | `21` | `21` | *_r{1,2,3}.json |
| ✓ |   deep-synthesis records | `7` | `7` | *_deep.json |
| ✓ | Final bank total entries | `58` | `58` | logs/banks/bank_all.jsonl |
| ✓ |   positive entries | `15` | `15` | bank_positive.jsonl |
| ✓ |   negative entries | `43` | `43` | bank_negative.jsonl |
| ✓ |   deep entries in bank (depth ≥ 2) | `7` | `7` | bank entries with depth hint ≥ 2 |
| ✓ |   legacy pilot positive (input) | `10` | `10` | pilot_legacy_positive.jsonl |
| ✓ |   legacy pilot negative (input) | `20` | `20` | pilot_legacy_negative.jsonl |
| ✓ | NoKB    PASS/3 | `0` | `0` | verified_results.json |
| ✓ | PosOnly PASS/3 | `1` | `1` | verified_results.json |
| ✓ | NegOnly PASS/3 | `3` | `3` | verified_results.json |
| ✓ | PosNeg  PASS/3 | `3` | `3` | verified_results.json |
| ✓ | T-A amp_ratio threshold = 0.25 | `True` | `True` | scripts/phenomenon_checks.py |
| ✓ | T-A single-dominant-peak check present | `True` | `True` | scripts/phenomenon_checks.py |
| ✓ | S6 prescribes nu_linear=5e-2 (or 0.05) | `True` | `True` | BKdV-S6_deep.json |
| ✓ | S6 vs BKdV-S4 envelope: 13 orders too weak | `True` | `True` | BKdV-S6_deep.json |
| ✓ | S7 reports -62.8% v_max decay | `True` | `True` | BKdV-S7_deep.json |
| ✓ | S7 reports cos-sim 0.94 prediction | `True` | `True` | BKdV-S7_deep.json |
