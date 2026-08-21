# TC-SAM-D0 Implementation Report

## Code mapping

| Contract element | Implementation |
|---|---|
| Frozen switches | `RIGMAPPOConfig.sam_enabled`, `sam_rho=0.05`, `sam_epsilon=1e-12` in `algorithms/ri_gmappo/simple_ri_gmappo.py` |
| Scope | `agent.actor.parameters()` only in `_update_policy_conditioned_actor` |
| SAM perturbation | `_sam_perturbations` |
| Exact restore | `_restore_parameter_copies` in a `finally` block |
| UTR baseline | Existing `actor_gradient_mode="utr"`; unchanged branch when `sam_enabled=False` |
| Critic | Existing `value_loss.backward()` path remains unperturbed |
| Final clip / step | Existing global `clip_grad_norm_` followed by one `optimizer.step()` |
| Checkpoint compatibility | Existing `save_training_checkpoint` / `load_training_checkpoint` |
| Unit tests | `tests/test_tc_sam.py` |
| Offline audit | `scripts/run_tc_sam_d0_audit.py` |

TC-SAM requires the already-frozen UTR conditioned-actor path and its exact 256-graph update (`128` nominal and `128` failure graphs). It does not create a new actor-gradient mode. Therefore the fixed sampler and UTR bookkeeping stay identical; only the final actor gradient is replaced by the gradient evaluated at the temporary SAM perturbation.

## Training-only telemetry

The existing actor-gradient telemetry now records nominal/failure sample counts; first-gradient, perturbation, and second-pass gradient norms; two SHA-256 minibatch-index hashes that must match; and the pre-existing final gradient norm and PPO diagnostics. UTR rows retain the same schema with SAM quantities set to zero/empty values.

No runtime actor feature, action head, critic input, relation edge, or inference operation is added. The implementation contains no DRTP `q`, EMA, difficulty, completed-return, or adaptive-sampling state in the SAM branch. It does not change learning rate, PPO clipping, entropy/value coefficients, topology groups, rewards, or failure timing. No environment rollout, tape creation, evaluation, or training seed was used during D0.
