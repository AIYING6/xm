# TC-SAM-D0 PPO/SAM Interaction Audit

## Preserved PPO semantics

Both SAM passes use the same stored rollout tensors: observations, legal graph features, relation adjacency, role identifiers, actions, old log-probabilities, advantages, returns, intent labels, and exact minibatch indices. The PPO importance ratio is recomputed under the relevant current/perturbed actor, but its denominator remains the frozen old-policy log-probability. The clipped surrogate, entropy term, intent loss, chain loss, and their coefficients are unchanged.

No extra environment sample is requested. GAE, return construction, value targets, normalization, rollout length, PPO epochs, and minibatching are unchanged. The critic is evaluated and updated once at base parameters, so its value target and fitting rule are ordinary PPO.

## Gradient and clipping order

`raw actor first gradient -> SAM perturbation -> second actor gradient -> exact restore -> ordinary critic backward -> existing final global gradient clip -> one Adam step`.

The first gradient is intentionally not clipped before constructing `epsilon`; clipping it would silently redefine the frozen SAM geometry. The final pre-existing global clip remains the only clipping operation. Mixed precision/distributed-specific logic is absent from the current PPO path; any future introduction requires a separate technical amendment, not a training-time change.

## Risk register

| Risk | Prevention in D0 | Future diagnostic / stop condition |
|---|---|---|
| PPO clipping and perturbation interact destructively | Same stored PPO batch; fixed small standard rho; no first-pass clipping | Track KL, clip fraction, policy loss; stop future route on persistent safety/finite-value failure under its frozen contract |
| Radius too large | One fixed `rho=0.05`, no adaptive feedback | Track perturbation/second-gradient norms and entropy; no mid-run rho change |
| Critic destabilization | Actor-only SAM | Track value loss/explained variance; critic scope cannot change mid-run |
| Final clipping erases SAM effect | SAM geometry is formed before final clip | Log first, perturbation, second, and final norms |
| Entropy collapse or excessive KL | Entropy coefficient and PPO clipping unchanged | Future frozen diagnostics: entropy, approximate KL, clip fraction |

These are prospective diagnostics, not permission for a mid-run redesign.
