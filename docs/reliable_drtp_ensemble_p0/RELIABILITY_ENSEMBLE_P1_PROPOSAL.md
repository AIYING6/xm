# Reliable-DRTP ensemble P1 proposal

**Status:** RELIABILITY_ENSEMBLE_P1_PREPARED_NOT_AUTHORIZED.

This proposal follows the P0 source-interface audit. It authorizes nothing:
no training, checkpoint loading, environment rollout, evaluation, member
selection, or modification of Mainline A is included.

## First candidate: execution-only E-DRTP

The first experiment should test a fixed, uniform three-member
execution-only ensemble (E-DRTP), not distillation and not an
ensemble-plus-distillation hybrid. This isolates the only new operation:
at every decision state, pool the three fixed categorical action
probabilities and take the deterministic argmax of the pooled
distribution. The critics are not used at execution.

Distillation is explicitly deferred. It would add a training-loss weight and
teacher-data construction choice, so it cannot diagnose whether any benefit
comes from the ensemble itself.

## Candidate P1 design, pending a separate authorization

| Item | Frozen candidate |
| --- | --- |
| Methods | E-UTR and E-DRTP; single UTR and single Original DRTP are contextual references only |
| Ensemble size | K = 3 |
| Weights | Uniform, exactly 1/3 per member |
| Aggregation | Arithmetic mean of member action probabilities; deterministic pooled argmax |
| Training budget per member | 499,968 environment steps (1,953 updates) |
| Cohort A candidate member seeds | bundles A1: 4601–4603; A2: 4604–4606; A3: 4607–4609 |
| Cohort B candidate member seeds | bundles B1: 4611–4613; B2: 4614–4616; B3: 4617–4619 |
| Training trajectories | 2 methods × 2 cohorts × 3 bundles × 3 members = 36 |
| Candidate development tape | 100 new same-base episode IDs 650000–650099, evaluated separately under nominal, F0_44_80, T28_28_80, D120_44_120, and C28_120 |
| Selection | Fixed final checkpoint of every member; no best-checkpoint promotion; no result-driven member deletion/replacement |
| Continuation | No automatic continuation beyond 0.5M |

The candidate seed intervals were absent from the source/config/document scan
performed for this proposal. A full provenance audit, including archived
registries and cloud-result manifests, remains a mandatory preflight before
any execution.

## Mandatory no-leakage boundary

The new development tape is for post-training P1 evaluation only. It must not
enter policy updates, sampler updates, member selection, ensemble weighting,
checkpoint selection, or any later distillation target. Formal, independent,
and held-out/unseen tapes remain completely unavailable to the training and
ensemble-construction code.

## P1 interpretation boundary

P1 is a directional pilot, not a claim that Reliable-DRTP is established.
The independent unit is an ensemble bundle (three trained members), not an
episode or a member. Cohorts A and B must be reported separately.

A possible directional GO to independent replication would require, in both
cohorts:

1. E-DRTP has positive mean paired robust advantage over E-UTR;
2. no E-DRTP bundle is catastrophic relative to its paired E-UTR bundle;
3. E-DRTP does not create a worse lower tail than the corresponding
   single-policy DRTP member distribution;
4. nominal, collision, timeout, and constraint endpoints show no material
   degradation; and
5. the ensemble upper tail is reported alongside the mean and lower tail,
   rather than hidden by averaging.

Failure of either cohort is P1 no-go. The two cohorts may not be pooled. A
P1 directional go would authorize only a new double-cohort replication
contract, not a 1M/3M continuation and not distillation.

## Required P1 preflight additions

Before execution, the implementation must prove:

- default-off equivalence: one-member aggregation reproduces the current
  deterministic actor action exactly;
- probability-simplex validity for pooled outputs;
- identical observation/graph/role tensors reach all members;
- member order does not change pooled actions;
- evaluation-only tape identifiers are rejected by all training-side inputs;
- E-UTR and E-DRTP have identical member budgets and inference conventions;
- checkpoint, member list, source commit, tape hash, and aggregation rule are
  recorded in every bundle manifest.

## Explicit stop boundary

No code path from this proposal may select a member according to any formal,
independent, held-out, or final-return result. There is no authorization for
distillation, weighted ensembles, a K sweep, or any paper change.
