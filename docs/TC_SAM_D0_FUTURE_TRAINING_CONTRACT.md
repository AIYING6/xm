# TC-SAM-D0 Future Training Contract

This document freezes the conditions of any later request; it **does not authorize training**.

## Comparator fairness

The future comparison is paired `UTR-SG-MAPPO` versus `TC-SAM-UTR` on the same five development seeds, 1,000,192 environment steps, topology exposure, environment, reward, evaluator, actor/critic/SG architecture, runtime persistence, final-checkpoint rule, and fixed evaluation tape. Both retain 116,728 parameters and the same environment-sample budget. TC-SAM's extra optimizer computation must be reported alongside its zero inference overhead.

## Frozen TC-SAM settings

- actor-only standard Euclidean SAM;
- `sam_enabled=True`, `sam_rho=0.05`, `sam_epsilon=1e-12`;
- existing UTR actor-gradient mode and fixed 50% nominal / six-group uniform failure sampler;
- same-batch two-pass actor update, unperturbed critic;
- raw first gradient, second gradient, then existing final global clip;
- one base Adam step.

Forbidden after authorization: rho/LR/clip/entropy/optimizer changes, critic SAM, adaptive SAM, topology-conditioned rho, DRTP-style return feedback, architecture changes, seed exclusions, checkpoint promotion, or selective budget extension.

## Future mandatory diagnostics

At update/milestone granularity where already available, log policy loss, value loss, entropy, approximate KL, clip fraction, standard/final gradient norm, SAM first/perturbation/second norms, explained variance, and training-return summaries. At only the frozen evaluation points report nominal, F0, topology OOD, worst-case OOD, collision, timeout, constraint, and exposure metrics.

## Conservative paper positioning

TC-SAM-UTR is a controlled integration of mature sharpness-aware policy optimization into fixed topology-randomized graph MARL for relay-node failure robustness. The novelty is the problem-aligned integration and its planned seed/OOD/safety validation, not the invention of SAM.

The basic optimizer is mature and acknowledged. Flatness is a generalization-motivated hypothesis, not an established causal explanation; future results must justify any benefit against the added training compute and zero inference gain.
