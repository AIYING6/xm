# PP-DRTP P4 independent validation contract

**Status:** `P4_AUTHORIZED`
**Scope:** Mainline-B development only. Mainline-A sources, evidence and claims are immutable.

P3 remains `PP_PILOT_NO_GO`. Its result is not reclassified or pooled into the
P4 gate. P4 is a new independent validation of the unchanged PP-DRTP candidate.

## Frozen execution

| Item | Frozen value |
| --- | --- |
| Arms | UTR / Original DRTP / unchanged PP-DRTP |
| Seeds | 3501--3505, paired, provenance-clean before execution |
| Budget | 1,953 updates = 499,968 training env steps per trajectory |
| Trajectories | 15 from-scratch runs |
| PP probe | unchanged 4 common base IDs x 7 groups per post-warm-up boundary |
| Evaluation | independent tape 570000--570099, five fixed conditions |
| Checkpoint | common final 500k only; 250k is diagnostic only |
| Concurrency | exactly 15 training processes; exactly 15 evaluation workers |

No actor, critic, PPO, network, reward, environment, DRTP formula, probe count,
probe schedule or RNG semantics may change.

## Independent-unit and gate definition

The independent unit is the training seed (`n=5`). Evaluation episodes are
paired technical repetitions and must not be reported as independent `n`.
Define `G_m,s = J_pert_mean(m,s) - J_pert_mean(UTR,s)` and retain the frozen
measurement margin `epsilon_J = 7.874919837916801`.

`P4_EARLY_GO` requires all of the following:

1. Mean PP-DRTP values for `J_nominal`, `J_F0`, `J_pert_mean` and
   `J_pert_worst` are each no more than `epsilon_J` below Original DRTP.
2. The worst PP paired gain improves on the worst Original gain by more than
   `epsilon_J`; PP has zero catastrophic seeds and does not increase the count.
3. Range and sample SD of paired gains both decrease. MAD and IQR are reported
   descriptively and are not primary gates because P3 showed that three-seed
   MAD can move opposite to a large range/SD improvement.
4. At least four of five PP paired gains are non-negative.
5. At least two Original upper-tail seeds (`G_original > epsilon_J`) exist and
   every such seed retains `J_pert_mean` within `epsilon_J` under PP.
6. Pooled failure collision and timeout deltas versus paired UTR are at most
   0.05; every seed-condition delta is at most 0.10; constraint violation is 0.
7. All run/tape/checkpoint/probe integrity checks pass. Every PP seed must have
   exact 4 x 7 paired records at every probe boundary and must leave uniform at
   least once. Probe interactions are reported separately.

If items 1--4, 6 and 7 pass but fewer than two Original upper-tail seeds exist,
the only decision is `P4_INCONCLUSIVE_UPPER_TAIL`; it is not a GO. Any other
failure is `P4_NO_GO`.

No decision automatically authorizes continuation, parameter tuning, seed
replacement, rerun, 1M/3M training or a new PP variant. The approximately 83%
P3 probe-interaction overhead remains a declared limitation; a resource-matched
control is mandatory before a final paper-facing efficiency claim.

## Seed provenance

Before freezing this contract, exact path and text searches were performed for
`seed3501`--`seed3505`, `--seed 3501`--`--seed 3505`, and JSON seed/training-seed
fields across tracked sources and non-result manifests. No scientific run,
checkpoint, evaluation, debug result or abandoned result using these seeds was
found. Incidental numeric coordinate/value matches were excluded because they
were not seed fields.
