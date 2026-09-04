# RACG-PPO P0 evidence synthesis

## Decision target

The project needs one deployable policy whose training retains the high-return potential exposed by Original DRTP without reproducing its cross-cohort instability. The next candidate must explain two completed failures at once:

1. EGTR showed that damping adaptive sampling can improve Original DRTP, but it did not repeat a reliable advantage over fixed UTR in both fresh cohorts.
2. TGTR showed that ordinary PPO can improve the average surrogate while harming individual topology groups in 4/5 source states, but a hard held-stream non-harm certificate rejected 20/20 actor epochs and reduced the method to actor freezing.

The new design therefore cannot adapt the collection distribution and cannot demand exact per-group non-harm from one noisy update.

## Literature basis and boundary

| Work | Useful principle | What RACG-PPO does not claim |
| --- | --- | --- |
| Schulman et al., TRPO, ICML 2015 | Keep policy motion close enough to an ordinary performance-oriented direction. | A PPO clip or local surrogate is not a cross-seed monotonicity guarantee. |
| Schulman et al., PPO, 2017 | Reuse on-policy data through a clipped surrogate and retain the existing implementation baseline. | Clipping alone does not create a strict trust region. |
| Wang et al., Truly PPO, UAI 2020 | PPO clipping can fail to enforce a true policy trust region. | A global KL threshold does not identify harmful topology-group updates. |
| Liu et al., CAGrad, NeurIPS 2021 | Anchor conflict avoidance to the average objective rather than optimize an arbitrary Pareto point. | Supervised multi-task results do not prove UAV-RL reliability. |
| Fernando et al., MoCo, ICLR 2023 | Stochastic multi-objective gradient manipulation is biased; gradient tracking is a principled response. | The proposed candidate is not a direct copy of MoCo and has no convergence claim yet. |
| Chen et al., MoDo analysis, 2023 | Dynamic conflict-avoidant weights trade off optimization, generalization and stability; independent double sampling targets gradient-product bias. | Two rollout streams are not independent training seeds. |
| Liu et al., STIMULUS, UAI 2025 | Recursive multi-gradient estimation can reduce stochastic sample complexity. | The project has not validated a recursive estimator under PPO policy drift. |
| Huang and Chen, MoRe preprint, 2026 | When a stochastic conflict-avoidance subproblem is irregular, switch toward fixed scalarization. | This recent preprint is method inspiration, not validation of RACG-PPO. |
| Xu et al., GDR-RL, AISTATS 2023 | Group robustness should balance worst-group and average performance instead of blindly optimizing the empirical worst group. | Episode/task-group robustness is not the same as cross-training-seed reliability. |

Primary sources:

- https://proceedings.mlr.press/v37/schulman15.html
- https://arxiv.org/abs/1707.06347
- https://proceedings.mlr.press/v115/wang20b.html
- https://proceedings.neurips.cc/paper/2021/hash/9d27fdf2477ffbff837d73ef7ae23db9-Abstract.html
- https://openreview.net/forum?id=dLAYGdKTi2
- https://arxiv.org/abs/2305.20057
- https://proceedings.mlr.press/v286/liu25d.html
- https://arxiv.org/abs/2607.15412
- https://proceedings.mlr.press/v206/xu23d.html

## New mechanistic hypothesis

The useful signal is not “a group was negative once.” It is whether a topology-group gradient direction is reproducible across fixed, independent training streams. Group correction should scale continuously with that reproducibility. When reproducibility is absent, the method must revert to ordinary PPO rather than reject the update.

This hypothesis is narrower and more falsifiable than claiming a universal failure precursor. It predicts:

- ordinary PPO remains the exact update when cross-fitted group gradients disagree;
- repeatable group conflicts receive a bounded correction;
- the correction cannot cancel the ordinary direction;
- collection exposure remains fixed, so no seed-dependent sampler feedback is introduced;
- if cross-stream agreement is usually near zero, the candidate has no useful actuation and must stop before fresh-seed training.

## Why this is not another EGTR/TGTR patch

RACG-PPO changes neither sampling probabilities nor the reward. It replaces TGTR's binary certificate with uncertainty-dependent interpolation around ordinary PPO. It is a new optimization mechanism, but P0 treats it only as a design hypothesis. No performance claim is made.
