# Why three conditions (NoKB / PosOnly / PosNeg)?

**Two-condition setup** (NoKB vs PosNeg) measures "any bank vs no bank."

**Three-condition** lets us isolate what *negative* knowledge specifically adds:

- NoKB → no bank at all
- PosOnly → only positive findings (= "best practices")
- PosNeg → full bank (positives + structured negative failure records)

If PosOnly ≈ PosNeg, then negative knowledge is **decorative**.
If PosOnly ≈ NoKB but PosNeg >> both, then negative knowledge does **necessary** work.

In our actual results: PosOnly ≈ NoKB ≈ 0/3 useful, PosNeg = 2/3 useful. So negative knowledge does necessary work for the coupled BKdV problem class.

# What's the same across conditions?

- Same Sonnet 4.6 model.
- Same task spec (PDE / IC / T / phenomenon target).
- Same max round budget (3).
- Same internal-iteration memory: every condition's r2/r3 prompt includes its own r1/r2 failure record. (Otherwise NoKB could never receive any feedback signal.)
- Same eval scripts (`phenomenon_checks.py`).

# What's different?

Only the Stage 1 bank content embedded in the prompt:
- NoKB: 0 bank entries
- PosOnly: 10 entries (positive only)
- PosNeg: 30 entries (all)

The memory blocks given to each condition are saved in `02_prompts/memory_blocks/T_*_*.md` for inspection.

# Why allow internal iteration in NoKB?

If NoKB had only r1 attempt, the comparison would conflate "bank effect" with "iteration effect." Allowing all conditions equal iteration isolates the bank effect.
