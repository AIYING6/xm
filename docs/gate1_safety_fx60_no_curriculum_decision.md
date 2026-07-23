# Decision: Reopen No-Curriculum Ablation as a Contribution-Risk Check

Last updated: 2026-07-22

## Decision

Do not claim topology curriculum as an independently proven main contribution in the current fixed-update-60 hardened safety package.

The no-curriculum ablation has been reopened because the project target has been raised toward Q1 quality. The seed-0 diagnostic in `docs/gate1_safety_fx60_no_curriculum_seed0_dev60_summary.md` showed that fixed full-difficulty no-curriculum training is competitive with the original topology-curriculum checkpoint on the matched 30-episode development split.

The follow-up three-seed diagnostic in `docs/gate1_safety_fx60_no_curriculum_3seed_dev60_summary.md` confirmed the same boundary: curriculum is not clearly better in this setting.

Current rule:

- main contribution: multi-relation role graph and role-pair-conditioned message passing;
- training protocol: topology curriculum;
- promote curriculum to a contribution only if a multi-seed no-curriculum ablation clearly supports it.

## Reasons

The current strongest evidence supports the graph/message mechanism claim:

- Full `multi_relation` recovery is `88.6%`.
- `single` recovery is `53.2%`.
- `no_graph` recovery is `21.8%`.
- `no_role_pair_gate` recovery is `64.8%`, and the seed-aware recovery delta separates in favor of the full method.
- `no_task_support` recovery is also `64.8%`, but its confidence interval crosses zero, so it is supportive only.

The `no_curriculum` ablation would answer a different question: whether the training schedule, rather than the graph/message mechanism, drives the gain. That is useful, but not currently the highest-value next step.

## Current Evidence

Seed-0 fixed full-difficulty no-curriculum diagnostic:

- no-curriculum fixed update 60 recovery: `70.0%`;
- original topology-curriculum fixed update 60 recovery: `63.3%`;
- both have `0.0%` collision on the matched diagnostic split.

Three-seed development diagnostic:

- validation-selected recovery: `88.9%` no-curriculum versus `87.8%` topology curriculum;
- fixed-update-60 recovery: `85.6%` no-curriculum versus `87.8%` topology curriculum;
- both have `0.0%` collision on the matched diagnostic split.

These results do not prove no-curriculum is better. They show that the project cannot honestly claim a curriculum-specific benefit from the current evidence.

## Risk

If the manuscript presents topology curriculum as a core contribution, reviewers may ask for a no-curriculum comparison.

Mitigation:

- In the current paper draft, make the primary method claim about multi-relation role graph learning and role-pair-conditioned message passing.
- Describe curriculum as a training protocol unless a future harder curriculum-specific stressor shows a clear benefit.
- Do not spend a five-seed formal no-curriculum budget in the current saturated setting.

## Current Priority

Move effort back to graph/message mechanism evidence:

1. Keep the fixed-update-60 main table frozen.
2. Keep topology curriculum as training support, not a main contribution.
3. Improve seed-level scatter and mechanism visualization for the existing graph/message ablations.
4. If adding a new experiment, prefer a harder graph-relation stressor over more no-curriculum runs in the same saturated setting.
