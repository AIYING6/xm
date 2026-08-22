# DRTP-SEED-S1 Telemetry Contract

Status: `FROZEN`

## Training update telemetry

Store compact update-level rows for approximate KL, clip fraction, policy/value/entropy losses, explained variance, actor/critic gradient norms, actor/critic update norms where available, advantage statistics, value-target statistics, learning rate, topology group, sampled group, difficulty, EMA difficulty, raw adaptive score, normalized weights, nominal-anchor contribution, and group frequency.

Unavailable fields must be recorded as `NOT_AVAILABLE`; no proxy may be relabeled as the requested quantity.

## Diagnostic trajectory telemetry

At the frozen milestones, store per-step Scout/Relay/Attacker position, velocity, action, action magnitude, task stage, progress, stage dwell, relative geometry, target-relative state, failure-relative time, legal graph, active path, task-support state, timeout/collision precursor, and terminal reason.

## Stagnation definition

The pre-registered diagnostic is: movement magnitude above `0.05` normalized position units while task-progress increment is below `0.01` for at least `12` consecutive steps. The thresholds are fixed before S1-A final results and are not tuned post hoc. The rule is a diagnostic label, not a reward or stopping criterion.

## Policy probes

Frozen actor-legal observations are evaluated at fixed checkpoints. Report action mean/variance, action-distribution KL/TVD where defined, entropy, and latent distance only as descriptive evidence. Latent distance alone is never a causal result.

## Provenance

Every row is bound to git commit, config hash, RNG tuple, training seed/stream tuple, checkpoint hash, device, training step, diagnostic tape hash, condition, episode count, and schema version.

