# M2R identity-preserving acquisition control

**Status:** `M2R_COLLECTOR_INTEGRATION_AND_FROZEN_TWO_SEED_PILOT_AUTHORIZED`

M2-V1 is retained as a development `PARTIAL` result.  Its Full arm produced a
nearly constant modulation scale and seed-dependent action collapse.  M2R does
not tune that model.  It replaces only the risky control interface.

## Paired mechanism

Both Full and B1 use identical legal target/self histories, actor input,
hybrid action space, centralized critic, reward, optimizer and parameter count.
Their base actor produces all five hybrid distribution logits.  Full alone adds
`0.25 * tanh(residual(progress))` to the two continuous turn/climb means.
The residual is zero initialized, so Full equals B1 at initialization.  It is
strictly bounded and cannot modify action scale or the attacker commit logit.
B1 retains an identically sized but disconnected residual branch for capacity
matching.

No reward, observation, evidence-expiry semantics, mission physics, horizon,
or commit semantics changes in M2R.

## Frozen development pilot

The collector integration is part of the method contract: a valid target claim
creates target history, expiry clears it on the real policy-step path, and a
fresh valid claim may establish a new history.  The residual must remain in
`[-0.25, 0.25]` for turn/climb and must never change the commit logit.

The pilot stores evidence-window turn/climb variation, commit rate, residual
magnitude, and residual-bound hit rate.  A Full arm with constant guidance,
all-zero/all-one commit, a permanently zero residual, or persistent residual
boundary saturation cannot support a PASS verdict even if a final mission
metric is favorable.

The authorized development pilot is Full versus B1 on the fixed L4 task,
using fresh training seeds `9601` and `9602`, 60 updates per arm, and the
existing frozen evaluation episodes.  Its four independent training arms may
run concurrently for engineering throughput; concurrency does not create
additional experimental arms or alter the frozen per-run configuration.

The pilot is not formal evidence.  It may only end as PASS, PARTIAL, or NO-GO
under the prewritten aggregation rule in
`scripts/finalize_m2r_acquisition_residual_pilot.py`.
