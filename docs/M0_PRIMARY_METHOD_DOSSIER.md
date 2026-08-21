# M0 Primary Method Dossier — TC-SAM-UTR

## Identity

**Name:** Topology-Conditioned Sharpness-Aware UTR-SG-MAPPO (TC-SAM-UTR).

**Mature principle:** SAM-style local parameter-neighbourhood optimisation.

**Adaptation target:** the existing fixed 50% nominal plus six-group uniform topology-failure UTR PPO objective, not a new actor encoder or topology sampler.

## Future method definition (frozen only upon separate contract)

For the existing PPO loss `L_PPO(theta; B)` evaluated over the frozen UTR batch `B`, define

`epsilon = rho * grad_theta L_PPO / (||grad_theta L_PPO||_2 + delta)`

and optimise the loss gradient at `theta + epsilon`, while applying the final optimiser update to restored parameters `theta`. The future contract must specify whether actor and critic use the same independently computed SAM mechanism; it may not change this choice after observing performance.

The method contains no topology-dependent trainable parameter, no new actor observation, and no execution-time operation beyond the unchanged SG-MAPPO actor.

## Why it fits relay failure

The deployment difficulty is not a hidden failure label but policy generalisation across legal topology/path reconfiguration conditions. UTR fixes the condition distribution. TC-SAM-UTR asks whether the *same* legal training distribution produces a policy whose local parameter neighbourhood has a more stable PPO objective, reducing the tendency for a stochastic training seed to settle on a fragile topology-specific solution.

## Expected future ablation

`UTR-SG-MAPPO` versus `TC-SAM-UTR`, with identical 116,728 parameters, PPO, fixed sampler, seed set, runtime persistence, final training budget, tape, and final-checkpoint rule. A zero-radius TC-SAM configuration must reproduce the UTR update as a technical identity control.

## Development protocol required later

One implementation → technical audit → five paired development seeds → a single frozen endpoint → one evaluation → one decision. The protocol must include nominal, F0, timing/duration/compound OOD, timeout/collision/constraint, exposure validity, seed dispersion, and exact continuation checks. It must set a common compute budget acknowledging the approximately 2× update cost.

## Prohibited modifications

- no new encoder, memory, gate, support-sensitivity head, role module, or inference ensemble;
- no DRTP-like adaptive weights, return-conditioned sampling, learned adversary, gradient surgery, or curriculum;
- no reward/environment/failure-semantics/actor-boundary changes;
- no checkpoint promotion, seed deletion, or adaptation after observing development outcomes.

## Claim boundary

TC-SAM-UTR is a mature optimisation adaptation for a fixed relay-failure topology robustness problem. It is **not** a new flatness theory, certified graph robustness method, information-recovery method, or guarantee of robustness.
