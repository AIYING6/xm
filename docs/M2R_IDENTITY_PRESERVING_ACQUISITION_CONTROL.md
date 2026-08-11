# M2R identity-preserving acquisition control

**Status:** `M2R_IDENTITY_PRESERVING_ACQUISITION_CONTROL_REDESIGN_AUTHORIZED__NO_TRAINING`

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
or commit semantics changes in M2R.  The next allowed work is deterministic
contract validation only; a new pilot requires a separate authorization and
fresh development seeds.
