# P2-R corrected-learner requalification contract

## Status

`P2_R_PREFLIGHT_ONLY`. This contract freezes a prospective baseline
requalification after P2.5 identified two learner-interface defects and P2.6
validated their minimal correction. It does **not** authorize a training run.

## Purpose

P2-R will answer only whether the corrected learner makes the frozen
redundant-topology main scale learnable under matched Plain and UTR collection.
It is not a comparison against historical P2 scores: those trajectories used a
defective learner and remain retained forensic evidence.

## Frozen prospective design

| Item | Frozen value |
| --- | --- |
| Learner | `RoleSharedSGMPPO` from P2.6 |
| Environment | P1 main scale, unchanged |
| Arms | Plain SG-MAPPO; UTR SG-MAPPO |
| Training seeds | `65011, 65012, 65013, 65014, 65015` matched across arms |
| Budget | 1,000,192 environment steps / 3,907 updates per trajectory |
| Trajectories | 10 total |
| Milestones | 250k, 500k, 750k, 1M |
| Evaluation | frozen development tape only; training never reads it |
| Continuation | none; P3 is not authorized |

Plain uses the frozen nominal training condition. UTR uses the frozen uniform
distribution across nominal and six failure conditions. Apart from collection
condition, all PPO, critic, reward, environment, graph and checkpoint
semantics must be matched.

## Learner correction boundary

P2-R uses three independent policy bodies, shared only inside role: Scout
shared by S1/S2, Relay shared by R1/R2, and Terminal shared by T1/T2. Relay is
a deterministic one-action PASS interface and contributes no categorical
log-probability, entropy, or actor gradient. The centralized critic,
environment, reward and PPO hyperparameters are unchanged from P2.

## Seed registry

Historical P2 seeds `6201–6203` are permanently excluded. The prospective
requalification range is `65011–65015`; the reserved independent replication
and confirmatory ranges are `65021–65025` and `65031–65035`, respectively.
No range may be replaced, reordered, or used for a performance rerun.

## Gate precommitment

The training-level P2-R gate is not activated by this preflight. Before any
cloud execution, its exact score/safety thresholds, evaluation tape hash,
package hash and no-continuation rule must be included in the execution
package. Results must report every seed and arm; episode rows are technical
replicates, not independent training seeds.

## Explicit prohibitions

- No P2-R formal training, evaluation, or checkpoint selection in this stage.
- No modification to the environment, reward, deadline, topology or critic.
- No adjustment of role bodies, PPO hyperparameters or relay semantics.
- No reuse of 6201–6203 and no performance-driven seed replacement.
- No automatic P3, algorithm comparison or paper claim.
