# TC-SAM-D0 Formalization

## Frozen identity and scope

**TC-SAM-UTR** is the existing fixed-exposure UTR-SG-MAPPO update with a training-only, standard Euclidean Sharpness-Aware Minimization (SAM) actor update. It is not a new SAM variant, graph encoder, or inference-time module.

The frozen model remains the matched Single-Graph actor/critic with **116,728 trainable parameters**. The environment, reward, relay-failure semantics, actor information boundary, PPO hyperparameters, 50% nominal exposure, and conditional-uniform six-group failure exposure remain unchanged.

## Exact update

For the existing stratified UTR PPO minibatch `B`, let the actor objective be `L_A(theta_A; B) = L_clip - c_H H + c_I L_intent + c_C L_chain`. All terms, coefficients, old log-probabilities, actions, returns, advantages, and minibatch indices are the pre-existing PPO quantities. The critic keeps the ordinary unperturbed PPO objective `L_V(theta_C; B)`.

With frozen `rho = 0.05` and `delta = 1e-12`, TC-SAM performs:

1. `g = grad_{theta_A} L_A(theta_A; B)` without pre-SAM clipping.
2. `epsilon = rho * g / (||g||_2 + delta)`.
3. Temporarily set `theta_A^+ = theta_A + epsilon`.
4. Recompute the same actor objective using the **identical** `B`, then take `g_SAM = grad_{theta_A^+} L_A(theta_A^+; B)`.
5. Restore `theta_A` exactly, backpropagate the ordinary critic loss at `theta_C`, assign `g_SAM` to actor parameters, apply the pre-existing final global gradient clip, then make one Adam step.

There is no optimizer step, moment update, gradient accumulation, sampler adaptation, or environment interaction between steps 1 and 5. `rho=0` is an explicit technical identity control for the ordinary UTR actor update.

## Parameter groups receiving SAM

SAM covers every trainable tensor below `agent.actor`: the Single-Graph actor encoder, actor input/observation encoders, role and intent embeddings, policy/action head, and the existing intent/chain auxiliary heads. The critic and its value head receive the unchanged PPO value-loss update only.

This actor-only decision follows the frozen M0 choice of standard rather than adaptive SAM and its conservative RL positioning: policy robustness is the target, while perturbing the value-fitting branch would add an uncontrolled critic-stability variable. It does not change the model or any execution path.

## Why `rho=0.05`

`rho=0.05` is prospectively fixed from the mature standard-SAM reference configuration adopted in the M0 dossier. It was selected before any TC-SAM MARL result, with no radius sweep, adaptive radius, topology-dependent radius, return feedback, or seed-specific exception. The frozen value is a design choice, not an empirical claim of optimality.

## Claim boundary

The paper may later test whether fixed legal topology exposure plus sharpness-aware actor optimization improves reliability under relay-induced topology changes. It must not claim a new SAM theory, certified flatness, guaranteed seed stability, or topology-robustness guarantee.
