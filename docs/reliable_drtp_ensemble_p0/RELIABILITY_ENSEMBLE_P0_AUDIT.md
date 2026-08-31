# Reliable-DRTP ensemble/distillation P0 design audit

**Verdict:** RELIABILITY_ENSEMBLE_P0_DESIGN_FEASIBLE.

This is a zero-training, zero-rollout, zero-evaluation source-interface audit. It does not create an ensemble, train a student, load checkpoints, or alter Mainline A.

## Feasibility result

The current actor emits categorical logits and the agent constructs Categorical(logits=logits). A future execution-only ensemble can therefore pool each fixed member's action probabilities into one valid categorical distribution. The existing evaluator is deterministic, so a fair future evaluation must use the argmax of the pooled probabilities for every ensemble arm rather than change only one method's action convention.

## Mandatory leakage boundary

Ensemble members, their weights, and any distillation examples must be chosen solely from pre-frozen training seeds and training-only rollouts. Formal, independent, and held-out evaluation tapes; all evaluation returns; final seed labels; and future trajectory information are prohibited from member selection, teacher targets, thresholds, or loss weights. A distilled student may use stop-gradient pooled teacher probabilities only on its training data.

## Mandatory fair-comparison boundary

A future study must compare E-DRTP with E-UTR under identical ensemble size K, member training budgets, architecture, seed allocation, checkpoint convention, pooling rule, action convention and evaluation tape. Single-policy DRTP and UTR remain references, not causal controls for an ensemble effect. The independent unit is an ensemble bundle/training seed, never its episodes or constituent members.

## Compute disclosure

An execution-only ensemble requires K actor forward passes per environment decision. Distillation adds teacher forward compute during student training. Both costs must be reported separately from environment interactions; neither may be presented as a single-policy compute match.

## P0 checks

- PASS — discrete categorical policy distribution (Categorical(logits=logits)).
- PASS — explicit probability sampling path (torch.multinomial(probs).
- PASS — deterministic policy-action interface (deterministic: bool = False).
- PASS — existing evaluator uses deterministic actions (deterministic=True).
- PASS — evaluation tape is explicit data, not training input (tape = json.loads).
- PASS — evaluation manifest records held-out status (held_out_tape_used).
- PASS — training/evaluation mode is an explicit configuration boundary (evaluation_enabled: bool = True).

## Stop boundary

P0 authorizes no training, evaluation, checkpoint/member selection, hyperparameter sweep, or paper modification. Any P1 must be separately authorized with a frozen K, member construction rule, training-only distillation source, E-UTR comparator, cohort structure, and GO/NO-GO gate.

## Input hashes

- algorithms/ri_gmappo/simple_ri_gmappo.py: 312b0696acd93e011d2eac2ef1fe7fe3a77f8d24b7ea71d2a9a9e78b53f19acb
- scripts/run_phase_rsg1_development_smoke.py: e697ddcc683c765c89c0e502a33872c24bad025f4d4c9a886a45f04668eb3f46
- scripts/run_drtp_sg_development_evaluation.py: 001c6aef6f4b4a7c8599147bb1b16af1270491fb899f8ea1624810772044eafe
