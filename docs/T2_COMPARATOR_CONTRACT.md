# T2 Comparator Contract for a Future Q2 Method

## Status and scope

This contract freezes the **minimal future comparison set**, not a training
authorization. No comparator is implemented, trained, evaluated, or promoted
by T2. Historical Full, RSG-TC, CTP, DRTP, and TCR remain closed and may only
be cited as negative/instability evidence.

The target context is the frozen S2 topology-perturbation task. Every future
new run must be from scratch, use a newly frozen tape and seeds, preserve the
actor information boundary, and use final-budget checkpoints only.

## Mandatory comparator set

| Arm | Scientific role | Actor inputs | Graph inputs | Training distribution | Parameter rule | PPO / CTDE / evaluation rule |
|---|---|---|---|---|---|---|
| MAPPO | No-graph control: isolates whether legal graph structure is useful. | Each agent’s frozen legal `obs` only. | None in actor. | Fixed 50% nominal; remaining 50% conditional-uniform over the six frozen failure groups. | Build must be capacity matched to 116,728 within ±1%; count frozen before performance inspection. | Same PPO hyperparameters, critic `share_obs`, rollout contract, environment/reward/failure semantics, train steps, and paired evaluation tape as all graph arms. |
| Matched SG-MAPPO | Topology-aware but non-robust-training baseline. | Same frozen legal actor inputs. | Same union Single-Graph node/edge/adjacency inputs as UTR. | Nominal-only training; no failure sampling. | Exactly 116,728. | Same PPO/CTDE/evaluation contract; makes the cost/benefit of topology-perturbation exposure visible. |
| UTR-SG-MAPPO | Conservative fixed-mixture robustness reference and required main baseline. | Same frozen legal actor inputs. | Same union Single-Graph inputs. | Fixed 50% nominal + 50% conditional-uniform six-group failure exposure. No adaptive sampler. | Exactly 116,728. | Same PPO/CTDE/evaluation contract. |
| Future final method | Single targeted response to the T2 mechanism decision. | Must use only the same frozen actor-legal inputs; diagnostic labels cannot be injected. | At most the frozen legal graph inputs unless a later method contract proves otherwise. | Exactly the same fixed mixture as UTR. | Exactly 116,728 unless a later method contract pre-registers a matched-capacity alternative for every graph arm. | Same PPO, critic, steps, seed sets, final-checkpoint rule, and evaluation tape. |
| HAPPO | Exactly one external structural comparator: role-heterogeneous sequential policy optimization without actor graph messaging. | Same per-agent legal `obs`; no diagnostic fields. | None in actor. | Same fixed 50%/six-group distribution as UTR/final method. | Count all trainable actor-critic parameters before any run; report it and matched compute. It is structural, not a capacity-matched graph ablation. | Same environment/reward/failure/evaluation contract; CTDE critic must not leak information to actor. |

HAPPO is selected because an audited local role-heterogeneous no-graph HAPPO
implementation exists (`scripts/train_happo_baseline.py`) and its sequential
policy update is a meaningful structural control. Old HAPPO results are not
valid evidence for this future protocol and cannot be reused.

## Common fairness invariants

Every future comparator must satisfy all of the following:

1. Same frozen S2 environment, reward, failure groups, onset/duration
   semantics, action space, and actor information boundary.
2. The decentralized actor cannot receive global topology, shortest path,
   failure truth/label, future link state, diagnostic positions, task-support
   truth, or critic-only state. `share_obs` remains critic-only under CTDE.
3. Same rollout geometry, PPO hyperparameters, update count/environment-step
   budget, strict-continuous runtime persistence, and final checkpoint rule.
4. Same training-seed set per compared arm; no seed exclusion, early stopping,
   best-checkpoint selection, or arm-specific budget extension.
5. Same fresh paired nominal/F0/timing/duration/compound evaluation tape;
   training seed, not episode, is the inferential unit.
6. Native raw-to-aggregate source closure, risk-set trigger validity,
   unconditional collision/timeout/constraint summaries, and pre-trigger
   collision reporting are mandatory.

## Future endpoints

The future evaluation report must include `J_nominal`, `J_F0`, `J_OOD_mean`,
`J_OOD_worst`, per-condition returns, seed dispersion, collision, timeout,
constraint violation, survival-to-onset, risk-set trigger success, and
pre-trigger collision. It must also report the T2 mechanism telemetry:
pre/early/mid/late task-support, legal-information continuity, path/source
behavior, role target progress, and terminal-window precursors.

The principal robustness comparison is **future final method versus UTR-SG**:
the two must have equal graph capacity and identical exposure. MAPPO and
matched SG answer distinct controls; HAPPO is the single external structural
reference. A future result may not attribute any difference to relation
semantics, adaptive sampling, privileged topology, or a different failure
distribution.

## Non-authorizations

This document does not authorize training, tape creation, seed selection,
implementation, a new loss, an encoder, a curriculum, held-out runs, or
canonical runs. A separate method-design and pre-training contract is required.
