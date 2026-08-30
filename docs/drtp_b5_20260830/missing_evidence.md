# Missing evidence for B5

The current archive set is rich in global PPO, sampler, intervention, and endpoint evidence but has a systematic blind spot at the credit-assignment layer.

Required read-only telemetry:

- per update × failure group: sample count, return target, value prediction, TD/value residual, value loss and explained variance;
- raw and normalized advantage mean, SD and frozen quantiles by group;
- actor and critic gradient norm by group, plus pairwise cosine/conflict rate between groups;
- the existing sampler q/exposure and failure-relative behavior/task-support telemetry on the same update axis;
- matched UTR controls with the identical logger;
- deterministic save/resume and telemetry-on/off trajectory equivalence.

These fields are log-only. They must not enter actor/critic inputs, PPO buffers, rewards, or sampler decisions.
