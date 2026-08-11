# M0 actor-information legality and interface specification v1

**Status:** `M0_STAGE_AWARE_ACQUISITION_METHOD_DESIGN_FROZEN__NO_IMPLEMENTATION__NO_TRAINING`

## Scope

This specification defines the legal actor boundary for the candidate stage-aware acquisition policy. It is stricter than a tensor-shape contract: each representation needs a permitted source and expiry rule. It introduces no new raw actor information relative to the corrected-contract L4 baseline.

## Canonical actor inputs

At time \(t\), recipient \(i\) receives the same current actor vector \(o_{i,t}\) already supplied to the corrected-contract baseline. It may contain self physical state, role encoding, current legal local sensing, delivered/cache-valid packet snapshots, and their availability/age/confidence/provenance fields. The candidate consumes this vector without appending global state, target truth, centralized observation, or evaluator labels.

The actor may also use its own previously executed action. This is local action history, not teammate action history or a simulator-state read.

| Information | Candidate actor use | Source and expiry rule |
| --- | --- | --- |
| Self physical state and role | Permitted. | Current local actor observation. |
| Target-relative state | Permitted only when fields arise from local sensing or delivered/cache-valid packet. | Existing corrected-contract construction. |
| Availability, age, confidence, provenance | Permitted. | Existing delivered/cache-valid metadata. |
| Own previous hybrid action | Permitted. | Recipient's own executed action at \(t-1\); reset on episode start. |
| Global target truth and `last_detected_target` | Forbidden. | Must not enter features, memory updates, masks, or action heads. |
| Pending or dropped payload | Forbidden. | Must not enter memory or outputs. |
| Expired packet/cache payload | Forbidden. | Must be absent from current target features and reset target-memory content. |
| `share_obs`, critic state, evaluator geometry, `chain_closed`, reward | Forbidden. | Training-only or evaluator-only quantities. |

## Causal internal-state contract

The candidate may maintain two recipient-private recurrent states.

1. **Target state** \(m^T_{i,t}\) updates only from current legal target-bearing fields and their metadata. Let \(v_{i,t}=1\) exactly when current local sensing or a delivered/cache-valid target packet is present. When \(v_{i,t}=0\), both the target-state output and stored target state reset to zero. The actor cannot retain expired or missing target payload in a hidden state.

2. **Self-history state** \(m^S_{i,t}\) updates only from self state, role, and own prior action. It cannot read any target feature, packet payload, availability, age, confidence, teammate state, or critic quantity.

The progress representation may consume the current legal vector, \(m^T_{i,t}\), and \(m^S_{i,t}\). States are separate for every recipient and vectorized environment instance, reset on termination, and may not be pooled across agents or passed through a graph/union residual path.

## Frozen candidate action interface

The task retains the existing hybrid action interface:

- normalized continuous `turn_command` and `climb_command` in \([-1,1]\), decoded only by the common fixed deterministic 3DOF controller;
- Bernoulli `engage_commit` for the attacker; non-attacker commit remains masked as in the role-specific L4 baseline.

The candidate adds no action, message, or control privilege. The bounded continuous distribution must preserve the existing log-probability semantics; an implementation may not sample an unbounded Gaussian and silently clip it before environment execution.

## Semantic policy interface

```text
current legal actor vector o_i,t -> legal target encoder -> mT_i,t
                                      (reset when v_i,t = 0)
self state + own action at t-1 -> self-history encoder -> mS_i,t

[o_i,t, mT_i,t, mS_i,t] -> unsupervised progress latent z_i,t
current actor backbone h_i,t -> condition(h_i,t, z_i,t)
                               -> role-specific hybrid action heads
```

`z_i,t` has no environment-provided stage target and must not be interpreted as a verified semantic phase until a later analysis validates it. Conditioning may modulate the actor backbone but may not alter relation masks, packet delivery, cache validity, reward, mission termination, or critic input.

## Comparator interface parity

`B0` receives exactly \(o_{i,t}\). `B1` receives the same \(o_{i,t}\), own-action history, and legal recurrent-state interfaces as Full, but bypasses progress-conditioned modulation. `B1` must be parameter-matched to Full within a predeclared tolerance before any pilot result is inspected. All methods retain role-specific action heads and the same commit mask.

## Mandatory M1 deterministic tests

Before a pilot, implementation must prove without training that:

- changing global target state or `last_detected_target` while \(v=0\) leaves target state, progress latent, action distribution, and deterministic action unchanged;
- changing expired, pending, or dropped packet content leaves those quantities unchanged;
- transition from \(v=1\) to \(v=0\) zeros target state before the next actor action, rather than merely lowering confidence;
- fresh local sensing and delivered/cache-valid packets can affect target state and actor output through their legal paths;
- one recipient's recurrent state cannot affect another recipient's action;
- critic-only information cannot affect actor states or outputs;
- action masking, PPO old/new log probabilities, ratio, and gradients stay finite and consistent for continuous and commit heads.

## Frozen claim boundary

The candidate can claim only to use a causal representation of legal evidence after successful implementation tests. It cannot claim belief-state reconstruction, accurate target estimation during missing evidence, communication recovery, failure recovery, or physical-interception superiority unless separately demonstrated.
