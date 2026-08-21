# TC-SAM-D0 Compute and Stability Audit

## Compute

SAM performs one extra actor forward/backward loss evaluation per PPO actor minibatch. Environment interaction, rollout count, stored trajectories, inference graph, and parameter count are unchanged. The critic still uses one ordinary PPO backward pass.

The training-free synthetic CPU micro-audit measured a mean update multiplier of **1.14x** (`0.0459 s` TC-SAM versus `0.0401 s` UTR across three local synthetic trials). This is a local implementation proxy, not a cloud-GPU throughput claim. For prospective planning, report an approximate **up-to-2x optimizer-side cost** and measure actual wall clock in any separately authorized run. The environment-sample budget remains exactly matched.

The actor contains 97,177 parameters. Temporary perturbation copies and their gradients require approximately an extra `97,177 * 4 bytes ≈ 0.37 MiB` per float32 tensor at the instant of the second pass, plus autograd activations. Adam state is unchanged from UTR; no persistent SAM optimizer state is added. Checkpoint payload and inference FLOPs are unchanged because neither stores a SAM-specific runtime tensor or executes a second inference forward pass.

## Stability conclusion

The numerical smoke had finite first/second gradients, exact restoration, single-step Adam state advancement, and exact checkpoint continuation. D0 identifies no technical instability requiring a new mechanism.

This does not establish learning stability, OOD robustness, or seed reliability; those remain hypotheses for a separately authorized fixed-budget comparison.
