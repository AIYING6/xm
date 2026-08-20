# T5 — Final Method Design Review

## Candidate reviewed

The sole candidate was a **topology-equivariant role-specific support-response coupling** regularizer. It leaves the 116,728-parameter SG encoder, actor inputs, critic, PPO, reward, environment, and fixed UTR exposure unchanged. A training-only finite-difference response to an actor-legal support substitution would have been compared across matched topology contexts; no failure truth, route, global topology, future state, or `share_obs` would enter the actor.

Its hypothetical objective would have been ordinary PPO plus one bounded response-contrast term. It is not an encoder module, gate, memory, relation branch, predictor, adaptive sampler, gradient surgery, or return-driven controller.

## Failure-mode and fairness review

| Risk | Mechanism | Observable signature | Preventive design considered | Residual assessment |
|---|---|---|---|---|
| Generic-conditioning novelty collapse | finite-difference response is viewed as a gate/FiLM | no advantage over ordinary conditioning control | action-response rather than latent modulation | **High** after prior-art review |
| Wrong response law | good policy lacks the desired consistency | good≤weak pre→early cosine | offline falsification before implementation | **Observed: reject** |
| Perturbation artifact | masked support tuple is out of distribution | mask-only signal | use within-stratum recorded-value permutation | partly controlled in T4, but not enough |
| Topology overconstraint | legitimate reconfiguration is penalized | reduced failure adaptation | align response contrasts, not actions | design-wise limited, empirically unsupported |
| Compute/memory burden | paired response forwards | 2–4× actor-forward activation use | parameter-neutral control and reporting | acceptable only if a valid mechanism survived |
| Role shortcut | static roles replace evidence | role-only effects | require role-specificity audit | not established |

## Parameter and comparator consequences if it had survived

The candidate would add no inference parameters: SG and the candidate would remain 116,728 parameters. It would increase training-only actor-forward/activation cost because each response contrast needs original and perturbed forwards. The frozen comparator contract would remain MAPPO, matched SG, UTR-SG, the candidate, and HAPPO; an ordinary conditioning control plus no-coupling and no-support-loss ablations would be required before any claim.

These are counterfactual design notes, not an implementation or training authorization.

## Result-free paper test

**Hypothetical title:** *Topology-Equivariant Support-Response Regularization for Robust Heterogeneous Multi-UAV Coordination*.

**Hypothetical contribution:** maintain a role-specific response to actor-legal support changes while permitting topology-specific base actions after Relay-node failure.

This paper would only be compelling with large, stable gains because the basic ingredients are close to policy invariance and input-response regularization. Since its key response-consistency premise fails offline, a moderate gain would not carry a coherent independent contribution. It therefore does not meet either Strong-Q2 or Solid-Q2 readiness.
