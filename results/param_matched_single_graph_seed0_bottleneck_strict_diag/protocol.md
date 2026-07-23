# Formal Strict-Sensing 3DOF Protocol

Generated: 2026-07-22T03:14:58

Purpose:

```text
Formalize the strict-sensing relay-failure main experiment.
Training saves snapshots every save interval.
Validation split selects checkpoints.
Test split evaluates only selected validation checkpoints.
```

## Configuration

```text
seeds = [0]
graph_encoders = ['single']
updates = 2
save_interval = 1
validation_episodes = 5
test_episodes = 5
validation_base_seed = 362000
test_base_seed = 363000
max_selection_collision_rate = None
scenarios = ['dropout030_relay_failure']
strict_target_sensing = True
agent_target_info_bottleneck = True
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
lr = 5e-05
entropy_coef = 0.001
communication_range_random = [0.65, 1.0]
communication_dropout_random = [0.0, 0.2]
message_delay_random = [0, 2]
radar_dropout_random = [0.0, 0.15]
node_failure_random_prob = 0.75
node_failure_start_random = [30, 60]
node_failure_duration_random = [60, 100]
safety_proximity_distance = 0.0
safety_proximity_penalty_weight = 0.0
```

## Paper Boundary

- Validation rows are for checkpoint selection and training-budget diagnosis only.
- If configured, validation checkpoints above `max_selection_collision_rate` are rejected before final testing.
- Test rows are used only after checkpoint selection is frozen.
- The paper claim should prioritize relay failure; scout failure remains supporting unless separated.
- This protocol does not add 4v2, missile, JSBSim, or self-play complexity.
- The default uses the currently available source seeds 0--2. For the final main result, extend to `--seeds 0 1 2 3 4` after preparing seed-3/4 source checkpoints.
