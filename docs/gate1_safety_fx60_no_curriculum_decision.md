# Decision: Defer No-Curriculum Ablation

Last updated: 2026-07-19

## Decision

Defer the `no_curriculum` ablation for the current fixed-update-60 hardened safety package.

Do not delete the idea. Keep it as a later training-method ablation if the paper explicitly claims that topology curriculum is a main contribution.

## Reasons

The current strongest evidence supports the graph/message mechanism claim:

- Full `multi_relation` recovery is `88.6%`.
- `single` recovery is `53.2%`.
- `no_graph` recovery is `21.8%`.
- `no_role_pair_gate` recovery is `64.8%`, and the seed-aware recovery delta separates in favor of the full method.
- `no_task_support` recovery is also `64.8%`, but its confidence interval crosses zero, so it is supportive only.

The `no_curriculum` ablation would answer a different question: whether the training schedule, rather than the graph/message mechanism, drives the gain. That is useful, but not currently the highest-value next step.

## Risk

If the manuscript presents topology curriculum as a core contribution, reviewers may ask for a no-curriculum comparison.

Mitigation:

- In the current paper draft, make the primary method claim about multi-relation role graph learning and role-pair-conditioned message passing.
- Describe curriculum as a training protocol that stabilizes learning under topology randomization unless the no-curriculum ablation is later completed.
- If runtime allows later, run `no_curriculum` under the same fixed `update_0060` safety protocol and add it as a training-method ablation.

## Current Priority

Move effort to paper-facing result packaging:

1. Use `docs/gate1_safety_fx60_paper_tables.md` as the current result table package.
2. Polish mechanism figures and captions.
3. Write the 3v1 strict-sensing relay-failure experiment section.
4. Then decide whether scenario-depth work, such as mild maneuvering or jammer, is needed before a Q1 attempt.
