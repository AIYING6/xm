# L4 mission-failure stage localization v1

**Status:** `RESEARCH_PROBLEM_IDENTIFIED__READY_FOR_METHOD_DESIGN`

The two frozen corrected-contract L4 checkpoints and 32 fixed development
episode seeds are replayed without training or configuration changes. Each
episode receives one mutually exclusive terminal-stage label:

1. no legal target evidence;
2. no attack-range acquisition;
3. no legal attack geometry;
4. no commit while in legal geometry;
5. no four-step hold;
6. post-hold non-neutral termination; or
7. neutralized.

A research problem is considered identified only if the same non-neutral stage
accounts for at least 50% of failures in both checkpoints. Otherwise the result
is `NO_IDENTIFIABLE_ALGORITHMIC_GAP__STOP_METHOD_HUNTING`. This is the final
method-free localization step; it does not authorize training, task changes, or
method design by itself.

## Frozen outcome

The two frozen corrected-contract L4 checkpoints (`8901`, `8902`) were each
replayed on the same 32 fixed development episodes.  No training, task,
environment, policy, or evaluation-protocol change was made.

| Exclusive terminal stage | Seed 8901 | Seed 8902 |
| --- | ---: | ---: |
| `NO_ATTACK_RANGE_ACQUISITION` | 12/24 failures (50.0%) | 12/24 failures (50.0%) |
| `NO_LEGAL_GEOMETRY` | 9/24 (37.5%) | 9/24 (37.5%) |
| `NO_FOUR_STEP_HOLD` | 3/24 (12.5%) | 3/24 (12.5%) |

The pre-registered decision rule is met exactly: the same exclusive stage,
`NO_ATTACK_RANGE_ACQUISITION`, accounts for at least 50% of non-neutralized
episodes in both checkpoints.  The identified research problem is therefore
**mission-stage acquisition under strict recipient-specific information and
range/loss/delay-constrained communication**.  This is a checkpoint-only
development diagnosis, not evidence that any particular communication factor
caused the failure and not evidence for any proposed method.

The corresponding immutable development artifacts are under
`results/l4_mission_failure_stage_localization/` and are intentionally not
maintained in git.
