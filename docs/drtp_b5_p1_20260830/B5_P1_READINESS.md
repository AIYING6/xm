# B5-P1 cloud observational cohort readiness

**Status:** `B5_P1_PREPARED / TRAINING_NOT_AUTHORIZED`.

## Frozen purpose

The cohort tests one remaining mechanism family: failure-group-conditioned credit assignment / gradient interference. It does not test a new algorithm and does not modify mainline A.

## Frozen execution

- Arms: UTR and Original DRTP only.
- Independent units: five paired clean training seeds, 3601--3605.
- Budget: exactly 1,000,192 environment steps per trajectory.
- Milestones: 0.25M, 0.5M, 0.75M and 1M; 0.5M is descriptive only.
- Read-only telemetry: failure-aware behavior plus pre-PPO group-conditioned value, advantage and gradient-conflict summaries every 20 updates.
- Evaluation: all four milestones on the independent 600000--600099 five-condition tape; 20,000 episodes total.
- Maximum meaningful training concurrency: 10 trajectories. Evaluation workers are configurable; the package default is 20.

## Hard boundary

The package refuses execution unless a later human command explicitly sets `B5_EXECUTION_AUTHORIZED=YES`. Preparation does not authorize training. No early stopping, checkpoint promotion, seed replacement, performance rerun, continuation beyond 1M or algorithm modification is allowed.

After aggregation, the automatic output is only `B5_1M_MECHANISM_GATE_READY_FOR_REVIEW`. A mechanism requires every frozen temporal-precedence, 2/5 replication, paired-UTR specificity, middle-layer and neighboring-threshold condition. If the complete signature is absent by 1M, B-line algorithm development closes.
