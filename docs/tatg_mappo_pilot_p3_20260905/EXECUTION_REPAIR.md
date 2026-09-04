# TATG pilot V2 execution invalidation and V3 repair

The first cloud launch of package V2 is **invalidated as an execution failure**,
not interpreted as a pilot result.  The three snapshot-UTR trajectories began
training, but all nine temporal trajectories exited before their first PPO
update because the temporal snapshot builder referenced a non-existent
`UAVIntercept3DEnv.num_blue` attribute.

The repair uses the environment's shared `num_agents` interface.  A new
source-only test constructs a 3D-shaped snapshot with an environment-like
object exposing only `num_agents`, so that this interface mismatch cannot
recur unnoticed.  The repaired V3 cloud bundle was built only after all TATG
mechanics, runner and package tests passed.

The prior output directory must be retained as an aborted execution record and
must not be pooled with or reported as part of the registered three-seed pilot.
The repaired complete run uses a fresh output directory while retaining the
already frozen arm definitions, seed IDs, endpoint and all scientific
hyperparameters.
