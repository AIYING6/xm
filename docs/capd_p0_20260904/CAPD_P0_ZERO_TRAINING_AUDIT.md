# CAPD P0 zero-training design audit

**Verdict:** `CAPD_P0_FEASIBLE_FOR_P05_ASSET_SIGNAL_AUDIT`.

This audit establishes design and interface feasibility only. It loaded no checkpoint, constructed no environment, executed no rollout, performed no PPO update, and read no evaluation tape.

## Decision

The current categorical actor can support a training-time population-to-single-policy method. A future CAPD pipeline may use one frozen UTR anchor and three predeclared EGTR explorers to construct a continuous policy-space consensus target, while ordinary PPO trains one central student on fixed-stratified training rollouts. Deployment uses only that student actor.

This is not the failed execution-time ensemble: teacher probabilities are temporary training targets, no member votes during deployment, and no evaluation outcome selects a teacher or final checkpoint.

## Frozen mathematical skeleton

For actor-legal training state x, the EGTR centroid is the normalized geometric mean of three fixed explorer policies. Mean Jensen-Shannon divergence from that centroid defines disagreement D(x). EGTR influence is the continuous value c(x)=exp(-D(x)/tau). The teacher target is the normalized geometric interpolation between the UTR anchor and EGTR centroid. The student minimizes ordinary fixed-stratified PPO plus a bounded forward-KL distillation term. Teacher tensors are stop-gradient; the critic remains ordinary PPO.

Numeric tau, distillation strength and schedule are deliberately not selected in P0. They require one separate formula-freeze step and may not use evaluation outcomes.

## Gate results

- PASS — actor class is explicit and independently callable.
- PASS — actor exposes categorical logits before sampling.
- PASS — policy distribution is categorical.
- PASS — deterministic and stochastic execution share one interface.
- PASS — checkpoint initialization is already supported.
- PASS — training/evaluation boundary is explicit.
- PASS — frozen EGTR explorer implementation exists.
- PASS — EGTR runtime state is serializable.
- PASS — geometric centroids and targets are finite probability simplexes.
- PASS — explorer disagreement continuously reduces EGTR influence.
- PASS — identical anchor/explorer policies preserve the anchor exactly.
- PASS — the rule has no discrete promotion or evaluation threshold.
- PASS — teacher targets are stop-gradient actor probabilities on training-only states.
- PASS — evaluation tapes and outcome labels are forbidden from training.
- PASS — teacher membership is fixed before downstream outcomes.
- PASS — final deployment contains one student actor.
- PASS — training population size is finite and predeclared.
- PASS — deployment inference cost equals one ordinary actor.
- PASS — training compute is disclosed rather than claimed compute-matched.

## Unresolved evidence gate

The repository does not locally establish that every completed 10M UTR/EGTR teacher checkpoint is present, architecture-identical, hash-valid, and behaviorally nonredundant. P0 therefore does not claim that useful consensus signal exists. A separately authorized P0.5 must inventory the archived checkpoints and test policy-space headroom on a new training-only state tape without training a student.

## Cost boundary

The full pipeline may require up to five training actors (one UTR anchor, three EGTR explorers and one central student) and four teacher forwards per student state. This is not compute-matched to single-policy UTR/EGTR and must be disclosed. Final inference remains exactly one actor forward.

## Stop boundary

No CAPD implementation, checkpoint loading, rollout, distillation, PPO training, evaluation, cloud execution, parameter choice or paper claim is authorized. The only possible next action is an explicitly authorized P0.5 teacher-asset and training-only consensus-signal audit.

## Source hashes

- `algorithms/ri_gmappo/simple_ri_gmappo.py`: `73ef2d9b54060061a6db1b7770cc541cfc7cc9d48321732d9c7d5e25cf1e7187`
- `algorithms/ri_gmappo/drtp_topology_sampler.py`: `3127bf78b5d89b349abee2da925afb0695a2ab77f8cd8aaee6c30d2ab14e9dc1`
- `configs/capd_p0_design_freeze.json`: `c6ae7b2a18a0fb8a34a7134bf183b243ee4e037117c6cce42a2f6b6478094fbb`
