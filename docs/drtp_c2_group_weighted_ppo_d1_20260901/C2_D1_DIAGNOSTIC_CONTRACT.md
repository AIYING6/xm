# C2-D1 Rescue-versus-Harm retrospective diagnostic contract

## Scope

This is a zero-training, retrospective diagnostic of the completed frozen C2
pilot. It reads only archived C2 training logs and runtime artifacts. It does
not launch an environment, evaluate a checkpoint, modify a model, tune a
weight, replace a seed, or alter Mainline A.

## Frozen seed labels

The labels are outcome labels for retrospective comparison only. They are not
online features and are not changed by this diagnostic.

| Label | Seeds | Definition |
| --- | --- | --- |
| Rescue | 4802, 4807, 4809 | The candidate removed the completed Original-DRTP catastrophic outcome or materially improved the completed paired outcome. |
| Harm | 4804, 4805, 4806, 4808, 4810 | The candidate introduced a completed catastrophic outcome. |
| Neutral/mixed | 4801, 4803 | Retained in the ledger but excluded from the primary rescue-versus-harm contrast. |

Cohort A is 4801--4805 and Cohort B is 4806--4810. They are never pooled for
a decision.

## Training-only evidence and fixed summaries

The diagnostic reads only `group_weighted_utr_sg` training logs. The following
non-overlapping windows are frozen before inspecting the output:

| Window | Updates | Purpose |
| --- | --- | --- |
| Early | 2--488 | The earliest period after the unit-weight bootstrap update. |
| Middle | 489--976 | Intermediate training-only state. |
| Late | 977--1953 | Descriptive terminal training state; it cannot establish precedence. |

The analyzable fields are lagged group TD-residual scores, applied group actor
weights, groupwise post-update surrogate values, aggregate PPO telemetry and
the fixed sampler log. All quantities are descriptive. The completed C2
endpoint is used only to assign the frozen retrospective labels above.

## Non-identifiability rules

If archived artifacts lack an exact item, the report must say so rather than
reconstruct it with new rollouts or surrogate assumptions:

- no per-group actor gradient tensors -> `GRADIENT_CONFLICT_NOT_IDENTIFIABLE_FROM_EXISTING_C2_ARTIFACTS`;
- no per-group advantage samples -> direct advantage-sign and actor-loss
  decompositions are not identifiable;
- no role-conditioned action-distribution or behavior telemetry -> policy-role
  collapse and task-behavior analyses are not identifiable.

## Verdict discipline

`D1_CANDIDATE_MECHANISM_FOUND` requires an analyzable, training-only,
group-weighted-PPO-specific pattern that occurs before terminal evaluation,
repeats across multiple rescue and harm seeds, is directionally consistent in
both cohorts, and maps naturally to one minimal prospective intervention.

`D1_INCONCLUSIVE` applies when a nontrivial training-only direction is visible
but required measurement layers or temporal linkage are absent.

`D1_NO_ACTIONABLE_MECHANISM` applies when no repeatable early direction is
visible, labels share the same signals, or the apparent differences are only
late/post-hoc. No outcome authorizes C2-v2, tuning, continuation, or a new
algorithm automatically.
