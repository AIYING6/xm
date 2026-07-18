# Fair Baseline Source Policy

Last updated: 2026-07-17

## Purpose

This policy fixes how source checkpoints are handled before formal strict-sensing fair baseline experiments.

The immediate risk is that `no_graph` seed 2 is weak. Replacing only that seed after seeing validation or test behavior would bias the comparison.

## Current Policy

For development diagnostics:

- Keep all existing `no_graph` seeds `0, 1, 2`.
- Report seed-level variance.
- Treat the weak seed as evidence that the no-message-passing baseline is less stable.

For formal paper reporting:

- Do not selectively replace only `no_graph` seed 2.
- Use one of two predefined policies before looking at final test results:
  - Policy A: keep all seeds and report variance;
  - Policy B: retrain all `no_graph` source seeds with one stronger standardized source budget, then freeze those sources before strict-sensing fine-tuning.

## Current Recommendation

The 30-update and 60-update bottleneck diagnostics have now completed enough development work to choose the formal rule.

The post-Gate-1 three-method safety-selected diagnostic confirms the same decision pressure under communication-feasible semantics:

- `no_graph` has high seed variance;
- seed 1 can recover, but seeds 0 and 2 fail completely under the safety-selected validation/test protocol;
- selectively replacing only failed `no_graph` seeds would bias the final table.

For development reporting:

- Keep Policy A and report the existing weak-source variance transparently.
- Use it only to justify the next experiment, not as the final paper table.

For paper-facing five-seed reporting:

- Prefer Policy B if runtime permits: retrain all `no_graph` source seeds with one stronger predefined source budget before strict-sensing fine-tuning.
- Do not replace only the collapsed `no_graph` seeds.
- If Policy B is too expensive, use Policy A but explicitly label the source policy and include seed-level results; do not hide the weak seeds.

Reason:

- The current bottleneck diagnostic gives a strong method ordering signal, but a final paper table must be robust to the criticism that the weakest baseline used weaker or unstable source checkpoints.
- Retraining all `no_graph` sources under one fixed rule is cleaner than repairing individual failed seeds after seeing results.
- The final claim does not require `no_graph` to be artificially strong, but it does require the comparison procedure to be defensible.

Recommended next action:

Before launching the five-seed formal run:

- use a single predefined source policy for all `no_graph` seeds;
- do not repair only weak seeds;
- include seed-level appendix rows;
- if runtime permits, prefer generating all missing seed `3` and `4` sources for every method before strict-sensing continuation.

## Reporting Rule

Any paper-facing table must state:

- source checkpoint policy;
- number of training seeds;
- validation checkpoint selection rule;
- test split independence;
- whether weak seeds were retained or all sources were retrained under a fixed rule.
