# UTR-SG Residual Gap Diagnosis

**Status:** completed — zero-training diagnosis
**Evidence source:** Phase-D 2M UTR final checkpoints and the 6,000 UTR rows within the 18,000-record development evaluation archive
**Conclusion:** a real residual *performance/stability* gap exists, but no real, isolated, candidate-specific *algorithmic mechanism* has been identified from the allowed evidence. This is insufficient authorization for a new method.

## 1. Frozen problem and interpretation boundary

S1-B established the bounded problem mechanism:

```text
Relay-node failure → relay-edge removal → legal path/source reconfiguration → mission-score degradation.
```

The system does **not** support an information-blackout claim: direct Scout→Attacker communication may remain legal, and cache information can become fresher after reconfiguration. This diagnosis therefore asks whether the current fixed-exposure UTR-SG policy has a measured topology-robustness deficiency that a new, nontrivial algorithm can specifically address.

## 2. UTR 2M descriptive results

Pooled over five development training seeds, with training seed—not episode—as the inferential unit:

| Metric | UTR-SG 2M pooled value |
|---|---:|
| `J_nominal` | 103.801 |
| `J_F0` | 93.106 |
| `J_OOD_mean` | 93.443 |
| `J_OOD_worst` | 83.252 |
| collision | 0.0609 |
| timeout | 0.8282 |
| constraint violation | 0.0000 |
| all-episode exposure | 0.9965 |
| trigger success in alive-at-onset risk set | 1.0000 |

Per-seed OOD-worst values are highly dispersed:

| Seed | `J_nominal` | `J_F0` | `J_OOD_mean` | `J_OOD_worst` |
|---:|---:|---:|---:|---:|
| 2002 | 126.642 | 117.460 | 121.421 | 115.397 |
| 2101 | 120.800 | 105.884 | 108.950 | 96.791 |
| 2102 | 60.342 | 59.697 | 51.323 | 36.046 |
| 2103 | 124.889 | 118.919 | 122.132 | 116.450 |
| 2104 | 86.329 | 63.568 | 63.391 | 51.575 |

This is a meaningful **training-seed competence dispersion**. It does not, by itself, identify why a particular representation or optimizer must be changed.

## 3. Condition and safety patterns

The most difficult pooled conditions are compound onset-28/duration-120 (`J=85.994`) and duration-44/duration-120 (`J=89.779`), while the ordinary nominal condition is 103.801. The long/compound conditions also have high timeout fractions (0.844–0.860). Short duration-44/40 episodes are not uniformly easiest in task support or legal-information usage, so a simple “longer failure requires one missing feature” story is not supported.

No constraint violation occurs. Collisions are present but modest relative to the large low-seed score gaps. Timeout is the dominant observable poor-outcome mode, especially UTR seed2102 (0.9791) and seed2104 (0.8500). Pre-trigger collisions are retained safety outcomes, not evaluator defects: only UTR seed2103 has them in the Phase-D summary (19 of 1,100 scheduled failure episodes; risk-set trigger success remains 1.0).

## 4. Topology and decision telemetry

Across failure rows, descriptive Pearson associations with return are:

| Telemetry | Association with episode return | Correct interpretation |
|---|---:|---|
| task-support fraction | +0.736 | Higher legal task-support availability co-occurs with better outcomes; causal direction is not identified. |
| path-switch count | +0.443 | Better episodes often complete more legal reconfiguration activity; this is not proof that the encoder cannot represent a switch. |
| legal-information fraction | +0.339 | Information availability is not the claimed lost quantity and may be compensated by direct paths. |
| timeout | −0.157 | Timeout contributes to lower score, but is not a unique topology cause. |
| collision | −0.200 | Collision contributes to lower score, but cannot explain the seed dispersion alone. |
| mean cache age | −0.122 | Weak descriptive association. |
| direct-path fraction | −0.039 | No useful simple direct-path deficiency signal. |

These episode-level associations are confounded by training seed and failure condition. They may not be interpreted as causal mediation or as proof of a missing actor input.

## 5. Representation and legality audit

The present SG actor already consumes an ordinary local observation branch plus graph features. In `envs/uav_intercept_3d_env.py`, legal graph edges include relative geometry/velocity, legal sensing, communication, task-support, attack, message/cache age, and confidence; relation adjacencies cover perception, communication, and task support. The actor does not receive `share_obs`, global paths, future state, or a failure label.

Therefore the following candidate premises fail immediately on the current evidence:

- **“The actor lacks a legal topology/reliability variable.”** Existing edge features already include the available local relation, communication, age, and confidence state.
- **“The actor cannot observe path reconfiguration.”** The legal graph changes with sensing/communication/task-support relations; S1-B showed the source/path switch in the evaluator.
- **“The problem is an information-loss problem.”** S1-B specifically rejected that causal claim.

What remains plausible but unproven is that the *use* of the legal information is seed-sensitive. Evidence available here cannot localize this to aggregation, temporal aliasing, critic coupling, policy optimization, or task geometry.

## 6. Historical stability evidence

The program’s stability warning is empirical, not speculative:

- DRTP had a held-out failure and was classified `C — NO_ACTIONABLE_CAUSE / INTRINSIC_SEED_SENSITIVITY`.
- TCR/2101 collapsed between 1M and 2M (`J_F0`: 105.851→51.758; OOD-worst: 88.789→52.621) despite finite diagnostics, complete runtime restoration, and no unique projection/PPO/topology signature. TCR is permanently closed.
- The same seed’s UTR and SPC controls improved, which rejects a simple evaluator, common-PPO, or deterministic environment failure explanation.
- F0 specialization is learnable in the Phase-FL maturity study, so the data do not support a universal claim that F0 itself is unlearnable under SG.

The residual issue is thus: **the fixed-distribution shared policy has seed-dependent competence and timeout-heavy weak cells.** It is not yet a demonstrated topology-specific representational defect.

## 7. Required gap test

The convergence program required a real problem that is measurable, directly topology-robustness related, and demonstrably not adequately handled by current SG/UTR. The audit yields:

| Required element | Result | Evidence boundary |
|---|---|---|
| Measurable residual performance gap | PASS | OOD-worst ranges 36.046–116.450 across UTR development seeds. |
| Relation to topology-robustness task | PASS | Difficulty occurs under frozen timing/duration/compound topology perturbations. |
| Isolated SG structural insufficiency | **FAIL** | Existing legal SG features cover the proposed local relation/topology states; aggregates do not isolate a missing computation. |
| Candidate-specific causal target | **FAIL** | No current log/checkpoint result distinguishes temporal aliasing, aggregation defect, optimization sensitivity, or task-quality variation. |
| Safe basis for a new algorithm | **FAIL** | Training a mechanism now would return to the prohibited “invent then train” loop. |

## 8. Decision

There is no defensible residual gap from which to derive a high-quality final algorithm candidate under the zero-training constraints. Future work may retain the measured seed dispersion, timeout profile, and topology/path telemetry as **system-robustness evidence** under R1. It may not infer that a new encoder, predictor, gate, auxiliary loss, recurrence module, or adaptive objective is justified.
