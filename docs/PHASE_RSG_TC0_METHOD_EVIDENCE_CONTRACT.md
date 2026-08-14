# Phase RSG-TC-0 — Method and Evidence Contract

## Status

Frozen pre-training contract for the only new candidate on branch
`codex/relation-aware-single-graph-v1`. This phase permits implementation,
static checks, parameter counting, and a one-update integration smoke only. It
does not authorize the `3 methods × 3 seeds × 200k` development experiment.

The old Multi-Relation Full remains closed and is not a parent checkpoint or a
claim source for RSG-TC.

## Candidate

`RSG-TC` is a shared two-layer Single-Graph attention encoder with a local
topology-conditioned attention-score correction. It has no relation branches,
Role-Gate, union residual, consistency loss, or auxiliary robustness loss.

For receiver `i` and sender `j`, the frozen edge context is:

\[
z_{ij}=[r^P_{ij},r^C_{ij},r^T_{ij},
\tilde d_{ij},s_{ij},c_{ij},u_{ij},\widetilde{age}_{ij},conf_{ij}].
\]

The relation vector is multi-hot; it is never reduced with `argmax`. The six
local edge-feature fields are, in the 3D environment's frozen `edge_feat`
schema:

| Field | Source index | Meaning |
|---|---:|---|
| `distance_norm` | 3 | normalized receiver-sender distance |
| `sensing_valid` | 11 | local perception validity |
| `communication_valid` | 12 | local communication validity |
| `task_support_valid` | 13 | local task-support validity |
| `message_age_norm` | 15 | local message age |
| `confidence` | 16 | local confidence |

The correction is:

\[
b_{ij}=MLP(z_{ij}),\qquad
\alpha_{ij}=softmax(a(Wh_i,Wh_j)+b_{ij}).
\]

`b` is an attention-score bias. It is not a sender-message payload. The final
linear layer of the correction MLP is initialized exactly to zero, so the
initial RSG-TC forward pass has zero relation/topology correction.

## Information boundary

Allowed inputs are the receiver-local graph tensors already exposed by the
frozen environment: `relation_adj` and the listed `edge_feat` fields. The
following are explicitly forbidden:

- shortest path or full-graph connectivity;
- explicit `0-1-2` / `0-2` path labels;
- failure labels or simulator node-failure truth;
- ground-truth route, future link, future state, or target truth;
- centralized-critic-only information in the actor;
- any new paired nominal/failure information during training.

## Parameter match

The frozen development lineup uses:

| Method | Encoder hidden size | Parameters |
|---|---:|---:|
| Matched Single-Graph | 115 | 116,728 |
| RSG-TC | 114 | 117,424 |

The absolute difference is 696 parameters, or 0.596% relative to RSG-TC.

## RSG-1 development contract

This contract is frozen before any RSG-1 result:

- methods: MAPPO, matched Single-Graph, RSG-TC;
- seeds: `1501/1502/1503` only;
- budget: 200,192 environment steps per method and seed;
- final checkpoint only; no resume, early stopping, promotion, or seed removal;
- paired tape: episode IDs `340000–340099`, nominal and relay-failure;
- no canonical seeds, test results, or headline result use;
- no consistency or robustness auxiliary loss.

### Retention gates

RSG-TC may proceed beyond development smoke only if all rules below are
assessed on the pre-registered paired tape:

1. Mean nominal score ratio `mean(J_N_RSG_TC) / mean(J_N_SG) >= 0.90`.
2. Mean failure score `mean(J_F_RSG_TC) >= 0.90 * mean(J_F_SG)`.
3. Mean degradation is lower: `mean(ΔJ_RSG_TC) < mean(ΔJ_SG)`.
4. At least two of three development seeds satisfy
   `ΔJ_RSG_TC < ΔJ_SG`, and the pooled mean has the same direction.
5. Collision, timeout, and constraint-violation rates are not more than 0.05
   absolute above matched SG.
6. Mechanism telemetry shows non-zero, relation/state-stratified bias use; a
   model with effectively zero or indistinguishable `b_ij` cannot claim the
   relation mechanism even if its reward is higher.

Any failed mandatory gate is `RSG-1 NO-GO`; it authorizes no fourth network.

