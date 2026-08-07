# Task-Support Mechanism Report (v1.5) — FINAL

- protocol: TASK_SUPPORT_MECHANISM_PROTOCOL_V1_5 (+ Addendum B/C)
- frozen windows: [-20,-1]/[0,20]/[rec-20,rec-1]/[rec,rec+20]; 9 blue-blue pairs
- extraction: 1200 episodes (2 scenarios x 2 methods x 3 seeds x 100), GPU; behavioral equivalence: event 60/60, action-hash 60/60, independent window 60/60

## A. Full internal task-support dynamics (window mean strength, 9 pairs)

| window | Full pooled mean | seed0 | seed1 | seed2 |
|---|---|---|---|---|
| pre_failure | 0.1409 | 0.1333 | 0.1417 | 0.1476 |
| early_post_failure | 0.0920 | 0.0923 | 0.0911 | 0.0927 |
| pre_recovery | 0.0898 | 0.0909 | 0.0877 | 0.0913 |
| post_recovery | nan | nan | nan | nan |

early_post - pre_failure (pooled): -0.0488
pre_recovery - early_post (pooled): -0.0022
cross-seed early-vs-pre direction: {'0': 'down', '1': 'down', '2': 'down'}

DATA FACT (post_recovery): in all recovered episodes of these two relay-failure scenarios, recovery coincides with episode termination (recovery_step == steps for 100% of 952 recovered episodes). post_recovery window is therefore undefined here; pre_recovery is the effective tail window.

## B. Full recovered vs failed (descriptive, n=3 seeds pooled over episodes)

| metric | recovered | failed |
|---|---|---|
| first_support_after_failure | 32.963 | 32.229 |
| support_persistence | 4.735 | 8.795 |
| unique_active_pairs | 2.996 | 3.000 |
| pre_recovery_boost | -0.008 | nan |
| n_episodes | 517 | 83 |

## C. Pre-registered verdict

**EMPIRICAL SUPPORT ONLY**


## D. Cases (frozen rule, smallest episode index)

- C1: dropout030_delay2_relay_failure ep4 (full_succ=1, fail_step=39, full_rec=46, wot_rec=49)
- C2: dropout030_delay2_relay_failure ep25 (full_succ=1, fail_step=39, full_rec=44, wot_rec=-1)
- C3: dropout030_delay2_relay_failure ep95 (full_succ=0, fail_step=39, full_rec=-1, wot_rec=-1)

## Interpretation guard (Addendum C)

- Full vs w/o relation strength difference is NOT mechanism evidence (ablation definition).
- Mechanism evidence is Full's internal temporal dynamics above.
- If EMPIRICAL SUPPORT ONLY: performance effect is locked and stable; internal temporal re-organization is not supported. Paper wording limited to the ablation effect + 'task-dependent relational mask' phrasing.