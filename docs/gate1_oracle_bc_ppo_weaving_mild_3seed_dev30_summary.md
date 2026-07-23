# Gate 1 Oracle-Assisted Nominal `weaving_mild` Three-Seed Development Summary

Last updated: 2026-07-22

## Purpose

This development run tests whether the oracle-assisted route can make the nominal maneuvering-target scenario usable before adding strict sensing or relay failure.

The previous curriculum-only route reached only `27.3%` aggregate success on `weaving_mild`, with seed 1 stuck at `0.0%`. The new route uses:

- offset geometric-oracle behavior cloning;
- attacker-weighted BC loss;
- short PPO fine-tuning;
- matched 30-episode testing per seed.

This is still development evidence. It is not yet a formal manuscript table because fair baselines and validation/test protocol still need to be completed.

## Protocol

For each seed:

1. Resume from the mature straight-target `multi_relation` source checkpoint.
2. Run offset geometric-oracle BC:
   - demo episodes: `30`
   - epochs: `12`
   - balanced loss: off
   - attacker action weight: `4.0`
3. Run nominal `weaving_mild` PPO:
   - updates: `30`
   - rollout envs: `8`
   - rollout steps: `128`
   - learning rate: `1e-5`
   - entropy coefficient: `0.01`
4. Evaluate the best checkpoint on:
   - episodes: `30`
   - base seed: `409000`

No strict sensing, target-information bottleneck, relay failure, or node failure is used in this Stage 1 scenario-depth diagnostic.

## Results

| Seed | Success | Attack-window formed | Collision | Timeout | Tracking | Connectivity |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.767 | 0.800 | 0.000 | 0.233 | 0.462 | 0.771 |
| 1 | 0.400 | 0.400 | 0.000 | 0.600 | 0.426 | 0.478 |
| 2 | 0.700 | 0.733 | 0.000 | 0.300 | 0.499 | 0.984 |
| mean | 0.622 | 0.644 | 0.000 | 0.378 | 0.462 | 0.744 |

Reachability artifacts:

- `results/gate1_oracle_bc_ppo_weaving_mild_seed0_cont30/reachability_eval30/summary.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_cont30/reachability_eval30/summary.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed2_cont30/reachability_eval30/summary.csv`

Combined artifacts:

- `results/gate1_oracle_bc_ppo_weaving_mild_3seed_dev30_summary/combined_summary.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_3seed_dev30_summary/aggregate.json`

## Comparison With Previous Route

Previous `weaving_tiny -> weaving_mild` curriculum-only diagnostic:

- seed 0: `58.0%`
- seed 1: `0.0%`
- seed 2: `24.0%`
- aggregate: `27.3%`

Oracle-assisted route:

- seed 0: `76.7%`
- seed 1: `40.0%`
- seed 2: `70.0%`
- aggregate: `62.2%`

The most important change is seed 1: the policy is no longer locked at zero.

## Interpretation

The nominal maneuvering-target Stage 1 gate is now development-pass:

- success is in the intended discriminative range, not saturated and not near zero;
- all seeds are nonzero;
- collision remains zero;
- attack-window formation tracks success, so the improvement is aligned with the intended task mechanism.

However, the result cannot yet be used as a final paper claim because the training assistance is now stronger. Any formal use must keep baselines fair:

- `single` and/or `no_graph` must receive the same oracle-BC and PPO budget;
- checkpoint selection must be explicit;
- final test episodes must remain disjoint from any validation decision;
- rules/oracle assistance must be described as training support, not the core innovation.

## Decision

Do not add strict sensing or relay failure to `weaving_mild` yet.

Next step: run a fairness control under the same oracle-assisted route, starting with a `single` graph seed-1 diagnostic. If `single` also jumps to high success, then the maneuvering-target improvement is mostly from the oracle training aid. If `multi_relation` remains stronger under equal oracle assistance, the scenario-depth result can support the paper mechanism more credibly.
