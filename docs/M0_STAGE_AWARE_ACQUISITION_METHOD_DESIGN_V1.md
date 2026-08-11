# M0 stage-aware acquisition method design v1

**Status:** `METHOD_DESIGN_AUTHORIZED__ATTACK_RANGE_ACQUISITION_PROBLEM__NO_TRAINING_YET`

## Decision boundary

This document freezes a *candidate* method hypothesis. It is not a claim of novelty, effectiveness, or publication readiness, and it authorizes neither code implementation nor training. The L4 checkpoints are diagnostic-only development evidence.

The candidate method is deliberately unnamed at M0. It is described only as a **stage-aware acquisition policy** so that a name cannot substitute for evidence.

## Problem identified before method design

Under the corrected recipient-specific contract, range scale 0.5, packet dropout 0.3, and message delay 8, two frozen L4 checkpoints were replayed on the same 32 episodes. In each checkpoint, 12 of 24 non-neutralized episodes (50.0%) had legal target evidence but never acquired attack range. The remaining failure labels were 37.5% no legal geometry and 12.5% no four-step hold. The predeclared cross-checkpoint criterion therefore identifies attack-range acquisition as the dominant mission-stage failure.

This supports the bounded problem statement: with only legal, potentially intermittent target evidence, the current role-specific MAPPO baseline often fails to convert evidence into approach behavior that enters the physical attack range.

It does **not** establish that delay, dropout, range, a Relay role, or any specific neural module is the causal source of the failure.

## Scientific hypothesis

> A causal representation of currently legal target evidence and its recent task progress can improve attack-range acquisition after evidence becomes available, relative to comparators with the same legal raw inputs and action interface.

This is falsified if the candidate does not improve the prespecified evidence-conditioned acquisition endpoints versus the history-matched comparator, even if it changes final reward or neutralization incidentally.

## Frozen task and control boundary

The following stay unchanged from the corrected-contract L4 development task:

- 3DOF dynamics, `NEUTRALIZED` as the sole mission-success terminal outcome, four-step hold, failure precedence, and the 180-step horizon;
- communication range scale 0.5, dropout 0.3, and delay 8;
- recipient-specific actor contract, packet provenance, cache age/confidence, and expiry semantics;
- the TLI1 aligned physical reward, continuous turn/climb guidance action, attacker-only Bernoulli `engage_commit`, and fixed low-level controller;
- role-specific policy output heads and the non-attacker commit mask.

The candidate may not add a reward term, success proxy, learned communication channel, graph message passing, evaluator geometry feature, or privileged critic feature to the actor.

## Candidate mechanism: minimal causal stage-aware actor

1. **Legal temporal target representation.** A target-evidence encoder reads only the current actor vector's already legal target-bearing fields, availability, age, confidence, and provenance. Its causal target-memory state summarizes consecutive valid target evidence and resets whenever neither local sensing nor delivered/cache-valid target evidence is available. An expired, pending, dropped, or unavailable packet therefore cannot persist through this module as latent target content.

2. **Unsupervised progress representation.** A low-dimensional latent is inferred from the current legal actor vector, the target representation, and a target-free causal summary of self state and own previously executed action. It receives no environment phase label, `chain_closed`, or attack-geometry label. It is an internal policy state, not an annotation.

3. **Stage-conditioned control.** The progress latent modulates the existing actor backbone before role-specific hybrid-action heads produce bounded turn/climb commands and attacker commit probability. It changes neither the reward nor a communication path.

The proposal is intentionally not a graph, attention, hierarchical-RL, auxiliary-loss, or learned-communication method. If this minimal design fails, those additions are not automatically authorized.

## Prespecified mechanism endpoints

For attacker \(a\), let \(t_E\) be the first time its actual actor input has legal target evidence and \(t_R\) be the first time the evaluator's physical attacker-target distance is no greater than `attack_range_max`. The range predicate is never exposed to the actor. For horizon \(H=180\), report:

- evidence-conditioned acquisition incidence \(P(t_R \le H \mid t_E < H)\);
- evidence-to-range restricted mean latency \(E[\min(t_R-t_E, H-t_E)\mid t_E < H]\), with no acquisition contributing the remaining horizon;
- `NO_ATTACK_RANGE_ACQUISITION` among non-neutralized episodes;
- separate mission endpoints: neutralization incidence, RMTN180, and terminal-outcome decomposition.

A mission improvement without acquisition improvement does not support this hypothesis. An acquisition improvement without mission improvement supports only the local mechanism, not mission superiority.

## Comparator and ablation hierarchy

All future comparators use the identical legal current actor vector, hybrid action semantics, role-specific heads, reward, horizon, and communication task.

| Role | Definition | Purpose |
| --- | --- | --- |
| `B0` static role-specific MAPPO | Corrected-contract L4 baseline; no actor history or progress conditioning. | Transparent system baseline. |
| `B1` history-matched MAPPO | Same legal temporal target/self-history inputs and comparable parameter budget as Full, but direct fusion without progress-conditioned modulation. | Primary architecture comparator. |
| Full candidate | Legal temporal target representation plus progress-conditioned control. | Tests the hypothesis. |
| `Full - temporal target representation` | Current legal target evidence only; retain target-free self history and conditioning capacity. | Isolates temporal target representation. |
| `Full - stage conditioning` | Equivalent to `B1`. | Isolates control conditioning. |

The primary future claim is Full versus `B1`, not versus old EA-RG or another checkpoint with a different information set.

## Required M1 implementation gate

Before any development training, M1 must establish:

1. a field-level source map for every candidate input and memory update;
2. counterfactual tests that global target truth, `last_detected_target`, and pending/dropped/expired payloads cannot change actor output;
3. target-memory reset when current legal target availability becomes false;
4. permitted fresh sensing and cache-valid delivery paths still affect actor output;
5. no actor access to `share_obs`, critic state, evaluator range/geometry, or future observations;
6. action/log-probability, role-mask, gradient, and parameter-budget tests;
7. a focused literature/novelty check on recurrent MAPPO, task-progress conditioning, and legal-history representations.

Only an M1 pass may request a small development pilot. The pilot may not change this task, reward, or comparator hierarchy in response to its outcome.

## Claim ledger

| Candidate claim | Required future evidence | Kill condition |
| --- | --- | --- |
| Actor uses only legal history. | M1 source and counterfactual tests. | Any unavailable, expired, or global target change affects actor output. |
| Progress representation targets acquisition. | Full improves evidence-conditioned acquisition versus `B1`. | No acquisition benefit versus `B1`. |
| Conditioning contributes beyond capacity. | Full versus `B1`. | Direct history fusion performs equivalently. |
| Method improves mission completion. | Untouched formal neutralization/RMTN180 evidence without adverse terminal-outcome tradeoff. | No mission benefit or unsafe tradeoff. |

## M0 conclusion

`M0_STAGE_AWARE_ACQUISITION_METHOD_DESIGN_FROZEN__M1_IMPLEMENTATION_NOT_YET_AUTHORIZED`
