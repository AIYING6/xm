# Nominal Source Budget Diagnostic Seed 0

This diagnostic tested whether the fair staged source protocol can learn the base 3DOF interception task before topology curriculum and strict-sensing fine-tuning.

Configuration:

```text
seed = 0
methods = single, multi_relation
BC source = results/intercept_3d_fair_staged_source_dev_seed0/stage1_bc/<method>/seed0/actor_critic_best.pt
nominal PPO updates = 20
num_envs = 2
rollout_steps = 16
eval_episodes = 5
```

Result:

| Method | Final update | Eval success | Timeout | Eval avg steps |
|---|---:|---:|---:|---:|
| single | 20 | 0.0% | 100.0% | 260.0 |
| multi_relation | 20 | 0.0% | 100.0% | 260.0 |

Interpretation:

The current fair staged development budget is still below the threshold for learning the base nominal interception task. Strict-sensing relay-failure results should not be interpreted until the source policy has nonzero nominal success.

Next decision:

Use a stronger known-learnable source budget before strict-sensing experiments:

```text
BC episodes >= 200
BC epochs >= 80
nominal PPO updates ~= 60
```

Alternatively, reuse the existing successful `single` and `multi_relation` source checkpoints and prepare only the missing comparable `no_graph` source checkpoint before rerunning strict-sensing fair baselines.
