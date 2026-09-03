# P2.13 — Scout-and-Terminal assigned baseline requalification contract

## Scope

P2.13 is the first learnability qualification after the P2.11 Scout-coverage
finding and P2.12 interface validation. It compares only the corrected learner
under Plain and UTR collection; no DRTP, curriculum, reward change, or new
algorithm is in scope.

## Frozen future training plan

- arms: `plain_scout_terminal_assigned_role_sg_mappo` and
  `utr_scout_terminal_assigned_role_sg_mappo`;
- training seeds: `67011–67015`, paired across arms;
- budget: 1,000,192 environment steps / 3,907 PPO updates per trajectory;
- observation: `assignment_observation=True` and
  `scout_assignment_observation=True`;
- checkpoints: 0, 125k, 250k, 500k, 750k, 1M;
- development tape, when authorized: seven frozen conditions × twelve episodes
  at each checkpoint; the training seed remains the independent unit.

## Reserved disjoint seeds

- independent replication: `67021–67025`;
- confirmatory cohort: `67031–67035`.

## Prohibitions

No reward, transition, action-mask, topology, failure, learner, PPO, sampler,
seed replacement, early stopping, best checkpoint, or automatic continuation
is permitted. This preflight itself performs no rollout, PPO update, evaluation,
or checkpoint selection.

## Gate boundary

This contract and its preflight authorize neither P2.13 training nor P3. A
separate explicit authorization is required after `P2_13_PREFLIGHT_PASS`.
