# CAPD P0.5 training-only teacher-signal audit

**Verdict:** `CAPD_P05_NO_CANDIDATE_CONSENSUS_SIGNAL`.

All `20` frozen UTR/EGTR checkpoints passed manifest hash and exact architecture checks. The diagnostic generated `168` fixed, outcome-free training states (`3360` environment steps) and performed no PPO update or student training.

The signal gate asks only whether three predeclared EGTR policies sometimes agree with one another while their geometric centroid differs materially from the matched UTR anchor. It does not test whether that direction is correct, safe or high-return.

## Cohort results

- Cohort A: supporting meta-seeds `0/5`, median signal fraction `0.0000`, median pairwise EGTR JS `0.451072`, pass `False`.
- Cohort B: supporting meta-seeds `0/5`, median signal fraction `0.0000`, median pairwise EGTR JS `0.624552`, pass `False`.

## Boundary

A positive result authorizes at most a separate formula-freeze and same-state distillation mechanism audit. It does not authorize fresh-seed training, cloud execution or an algorithm-performance claim. A negative result closes CAPD without training a student.
