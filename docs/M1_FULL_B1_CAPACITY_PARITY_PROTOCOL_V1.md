# M1 Full--B1 capacity and information-parity protocol v1

**Status:** `M1_PARTIAL__METHOD_NOVELTY_REDESIGN_REQUIRED__NO_IMPLEMENTATION__NO_TRAINING`

## Purpose

This protocol pre-registers the only fair architecture comparison for the M0 candidate. It prevents a future result from being attributed to progress-conditioned control when it could instead arise from more legal history, more parameters, a different action interface, or a different optimisation budget.

It is a design contract only. No candidate actor has been implemented or trained under this protocol.

## Methods and fixed common boundary

| Method | Permitted actor information | Intended role |
| --- | --- | --- |
| `B0` | Current corrected-contract actor vector only. | System baseline. |
| `B1` | The exact same current vector, legal target-memory interface, target-free self-history interface, and own-action history as Full. | Primary matched architecture comparator. |
| Full | Exactly the `B1` inputs and histories, plus the internal progress representation and its modulation of control. | Candidate mechanism. |

All three retain the same role-specific action heads, attacker-only `engage_commit`, continuous guidance interface, fixed controller, reward, horizon, communication configuration, centralized critic boundary, PPO hyperparameters, training budget, validation rule, and evaluation episode generator.

No method may receive target truth, `last_detected_target`, pending/dropped/expired payload, evaluator geometry, `chain_closed`, teammate hidden state, or critic-only state in an actor path.

## Exact Full--B1 comparison rule

Full may contain (i) a legal target-memory encoder, (ii) a target-free self-history encoder, (iii) a progress-latent encoder, and (iv) progress-conditioned modulation before the role-specific action heads.

`B1` must contain the same two recurrent encoders, consume the same per-step legal fields and own-action history, and feed their outputs directly into a non-conditioned actor backbone. It must not receive a progress latent, multiplicative modulation, phase label, geometry label, or any extra raw feature.

To match capacity, `B1` uses a direct-fusion backbone width selected *before any pilot result* so that total trainable actor parameters satisfy

\[
  \left|P_{B1}-P_{Full}\right| / P_{Full} \le 0.5\%.
\]

The parameter count includes recurrent encoders, direct-fusion/backbone layers, role-specific heads, and continuous/commit distribution heads. It excludes the shared critic only because that critic is identical and held fixed across the comparison. The exact layer widths, parameter counts, and source hash must be written to an immutable pre-pilot capacity manifest.

`B1` is deliberately allowed a capacity-matched direct MLP, not inactive or frozen dummy parameters. Thus it is a strong capacity control without silently reintroducing the progress-conditioning mechanism.

## Required static evidence before any pilot

The implementation gate must produce, for Full and `B1`:

1. an identical raw-source hash for every actor field at every recipient/time pair;
2. the same history length, reset rule, availability gate, and expiry reset rule;
3. an actor-only parameter manifest proving the 0.5% tolerance;
4. action-distribution shape and role-mask equivalence;
5. a gradient smoke test for every trainable component;
6. a counterfactual proving unavailable/expired target changes do not alter either method's target-memory output or action;
7. a source-commit/config/provenance manifest.

Failure of any item is a comparator invalidation, not a reason to tune a method.

## Ablation interpretation

`Full - stage conditioning` is defined to be `B1`; it keeps legal recurrent history but removes the progress-conditioned modulation. `Full - temporal target memory` uses current legal evidence only while preserving target-free self history and conditioning capacity. Neither ablation may change raw inputs, reward, task physics, or action semantics.

## Frozen claim limit

Even if a future Full--`B1` result is favourable, it can support only the incremental value of the specified conditioning mechanism over a matched legal-history policy. It cannot establish novelty of recurrent MARL, generic memory, generic task stages, or generic hierarchical control.
