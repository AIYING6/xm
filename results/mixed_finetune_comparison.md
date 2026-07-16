# Mixed Target Fine-Tuning Comparison

## Setting

- Environment: `UAVPursuitEnv`
- Target policy: `mixed`
- Target speed: `0.75`
- Evaluation: deterministic policy, 100 independent episodes unless otherwise noted
- Starting checkpoints:
  - MAPPO: `results/mappo_curriculum_slow_150/actor_critic_latest.pt`
  - Hybrid GAT-MAPPO: `results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt`

## Main Results

| Model | Checkpoint | Success | Collision | Timeout | Avg steps | Avg mean distance |
|---|---:|---:|---:|---:|---:|---:|
| MAPPO | pre fine-tune | 0.87 | 0.12 | 0.01 | 51.99 | 2.93 |
| Hybrid GAT-MAPPO | pre fine-tune | 0.82 | 0.14 | 0.05 | 54.94 | 3.37 |
| MAPPO | direct FT, lr=5e-4, latest | 0.76 | 0.24 | 0.00 | 65.07 | 2.97 |
| Hybrid GAT-MAPPO | direct FT, lr=5e-4, latest | 0.70 | 0.21 | 0.09 | 69.53 | 4.53 |
| MAPPO | conservative FT, lr=1e-4, best | 0.86 | 0.10 | 0.04 | 56.17 | 3.37 |
| Hybrid GAT-MAPPO | conservative FT, lr=1e-4, best | 0.83 | 0.11 | 0.06 | 54.06 | 3.29 |

## Interpretation

1. Direct mixed-target fine-tuning with `lr=5e-4` damages both policies. It should not be used as the default training recipe.
2. Conservative fine-tuning with `lr=1e-4` is safer, but still does not produce a clear gain over the slow-curriculum checkpoints.
3. Current hybrid GAT-MAPPO learns the task, but it does not yet outperform MAPPO. A plain graph attention layer is not strong enough to serve as the main paper contribution.
4. The next publishable direction should add task-specific information that MAPPO lacks:
   - target intent prediction,
   - relative edge features,
   - communication-limited graph masks,
   - role-aware coordination.

## Code Changes Made

- `algorithms/mappo/simple_mappo.py`
  - flushes CSV logs during training,
  - saves `actor_critic_best.pt` based on evaluation success, collision, timeout, and steps.
- `algorithms/gat_mappo/simple_gat_mappo.py`
  - same logging and best-checkpoint behavior.

## Next Experiment

Implement RI-GMAPPO v1:

1. Add a target-intent label in the environment:
   - `straight`, `escape_nearest`, `turn_left`, `turn_right`, `random/unknown`.
2. Add an auxiliary intent prediction head to the graph model.
3. Feed predicted intent embedding into the policy branch.
4. Compare:
   - MAPPO,
   - hybrid GAT-MAPPO,
   - RI-GMAPPO without intent loss,
   - RI-GMAPPO with intent loss.

The desired result is not just higher success rate, but better robustness under mixed target behavior and fewer collisions.
