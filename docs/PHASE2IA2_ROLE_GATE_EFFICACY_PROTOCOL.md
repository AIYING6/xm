# Phase 2I-A2 Role-Gate efficacy closure protocol

**Status:** frozen before development training  
**Scope:** `DEVELOPMENT_ONLY`; this is not canonical training, canonical evaluation, or manuscript evidence.

## Question and decision boundary

The historical Full encoder already uses relation-conditioned, receiver/sender role-pair payload gates.  Phase 2I-A established that those gates are mathematically active, but did not establish whether they add value after optimization.  This protocol answers only whether the corrected gate should remain in the prospective final architecture.

The comparison is fixed before any development outcome is inspected.  It must not be expanded to shared-gate variants, alternate endpoints, canonical seeds, or canonical test scenarios.

## Fixed arms

| Arm | Encoder and residual | Gate |
|---|---|---|
| `full_gate` | Multi-relation EA-RG-MAPPO-S; union/global residual weight 1.0 | Relation-conditioned role-pair payload gate; configured probability prior `p=0.4`, initialized with `logit(p)` |
| `no_role_gate` | Identical to `full_gate` | No gate parameters; payload multiplier exactly `g=1` |

All remaining model dimensions, optimizer, rollout, reward, observation, communication, failure timing, checkpoint rule, and scenario settings are identical between arms.  This experiment cannot alter any formal protocol.

## Development-only budget and identifiers

- Train seeds: `101`, `202`, `303`; no seed in `0–4` is permitted.
- Budget per arm/seed: **200,000 environment steps** (`4 environments × 64 rollout steps × 782 updates = 200,192`, the first whole-update budget at 20% of the frozen 1M development budget).
- No resume, no initialization checkpoint, no early stopping, and no seed exclusion.
- Training uses the existing frozen Gate-1 scenario configuration.  The development validation suite is the four frozen failure-timing scenarios from `configs/paper/main_gate1.yaml`.
- Validation episode identities are deterministically derived from `210000 + 10000 * seed + 1000 * scenario_index + episode_index`; these are development-only identifiers, not canonical test IDs.
- No canonical test evaluation, primary survival calculation, checkpoint promotion, or headline result is allowed.

## Required records

Each update records the following from the same PPO minibatches used for optimization:

1. L2 norm of the gate-gradient (`|grad(theta_g)L|`), pre-optimizer-step gate displacement from initialization, and gate mean/std/min/max.
2. Gate summaries by relation and ordered receiver/sender role pair.
3. Relation-wise summaries of attention `alpha`, gate `g`, and effective payload weight `alpha × g`, using only legal active edges.
4. Existing optimization-stability fields (loss, KL, entropy, clipping, gradient norm, explained variance).

At the fixed final update, both arms are evaluated only on the development validation suite.  The report may describe strict risk-set size, recovery probability and timing, and training stability as development diagnostics; it cannot make a confirmatory statistical or manuscript claim.

## Predeclared retention rule

Retain the corrected relation-conditioned gate only if all conditions hold:

1. finite, non-zero gate gradients and material parameter displacement occur in each development seed;
2. gate values are not predominantly saturated and show relation/role-pair differentiation;
3. effective payload weights are not explained solely by an inverse attention response in the recorded diagnostic; and
4. across the three unexcluded development seeds, `full_gate` is not worse than `no_role_gate` on the fixed development-validation recovery diagnostics while remaining stable.

If these conditions are not met, remove Role-Gate from the prospective final method, repeat parameter matching for the simpler Full encoder, and record the result as an architecture simplification.  Mixed or inconclusive results keep architecture freeze at NO-GO; they do not authorize selecting favorable endpoints or rerunning selected seeds.

## Procedural-deviation closure

The legacy seed-0 smoke output remains a documented Phase 2I-A deviation.  It did not inform this protocol.  Closure requires an independent review and a new engineering-only smoke using development seed `909`, with reward, success, recovery, and all episode-performance fields suppressed from console and artifact output.

## Authority boundary

This document authorizes only the listed development runs after implementation tests pass.  It does not authorize `CANONICAL_V2_TRAINING_READY`, Phase 3A, canonical runs, or any change to endpoint, tau, seed set, failure protocol, or checkpoint selection.
