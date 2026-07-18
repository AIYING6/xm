# Five-Seed Formal Dropout-Relay Bottleneck Summary

Last updated: 2026-07-18

## Protocol

- Scenario: `dropout030_relay_failure`
- Target policy: `straight`
- Actor sensing: `--strict-target-sensing`
- Information bottleneck: `--agent-target-info-bottleneck`
- Validation: 50 matched episodes per method/seed/checkpoint
- Test: 100 matched episodes per selected method/seed
- Training seeds: 0, 1, 2, 3, 4
- Candidate checkpoints per method/seed: updates 10, 20, 30, 40, 50, 60
- Checkpoint selection: validation score with `--max-selection-collision-rate 0.0`
- Test split: disjoint from validation and not used for model selection

Outputs:

- `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/validation_checkpoint_summary.csv`
- `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/validation_selected_checkpoints.csv`
- `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/test_checkpoint_summary.csv`
- `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/test_episode_metrics.csv`

## Validation Integrity

- Validation candidate rows: 90
- Selected checkpoints: 15
- Test checkpoint rows: 15
- Test episode rows: 1500
- No selected checkpoint had validation collision rate above the configured zero-collision threshold.

## Test Checkpoint-Level Result

| Method | Recovery / success | Timeout | Collision | Notes |
|---|---:|---:|---:|---|
| `no_graph` | 34.2% | 64.0% | 1.8% | Large seed variance; weak seeds are retained rather than selectively repaired. |
| `single` | 51.8% | 47.4% | 0.8% | One seed nearly saturates, but several seeds fail under the bottleneck. |
| `multi_relation` | 96.2% | 3.8% | 0.0% | Strong across all five seeds. |

## Seed-Aware Bootstrap

Hierarchical bootstrap resamples training seeds first, then matched episodes within each selected seed.

`multi_relation` vs `single`:

- Task success / post-failure recovery: `96.2%` vs `51.8%`
- Delta: `+44.4 pp`
- 95% CI: `[+16.2, +74.4] pp`
- Timeout delta: `-43.6 pp`, 95% CI `[-73.0, -15.6] pp`
- Restricted mean recovery steps: `23.45` vs `108.44`, delta `-85.00`, 95% CI `[-153.87, -22.93]`

`multi_relation` vs `no_graph`:

- Task success / post-failure recovery: `96.2%` vs `34.2%`
- Delta: `+62.0 pp`
- 95% CI: `[+27.8, +95.2] pp`
- Timeout delta: `-60.2 pp`, 95% CI `[-93.0, -27.2] pp`
- Restricted mean recovery steps: `23.45` vs `143.69`, delta `-120.24`, 95% CI `[-190.78, -50.61]`

## Interpretation

This is the first paper-facing five-seed result after the Gate 1 communication-feasibility fixes. It supports the main 3v1 mechanism claim:

> Under strict intermittent sensing, communication dropout, relay failure, and an actor-side target-information bottleneck, the multi-relation role graph improves post-failure kill-chain recovery probability and reduces timeout relative to both a single union graph and a no-graph actor.

The result is suitable as a core 3v1 mechanism table. For a Q1 target, it should not be treated as sufficient by itself. The next work should raise paper quality through mechanism explanation, stronger ablations, and one controlled scenario-depth extension rather than by immediately adding 5v2, JSBSim, or self-play.

## Current Limitations

- The target is still a straight high-value target.
- The protocol is 3v1, not 4v2/5v2.
- `no_graph` has weak source-policy caveats and fewer actor parameters than graph baselines.
- The recovered-only recovery-step mean is not the right headline speed metric because failed episodes are censored; use restricted mean recovery time.
- This result establishes the communication-feasible mechanism foundation, not a complete Q1 evidence chain.

## Next Recommended Work

1. Generate recovery-process evidence: post-failure tracking, connectivity, and chain-closure curves over time, plus one matched representative case.
2. Add formal mechanism ablations under the same five-seed protocol: no task-support relation and no role-pair gate.
3. Add one controlled scenario-depth extension, preferably a mild maneuvering or task-support dependency curriculum, only after checking that success rates remain in a separable range.
4. Report parameter counts, inference time, communication load, and seed-level scatter for fair baseline credibility.
5. Keep 4v2/5v2 and JSBSim as later Q1 enhancement gates after the 3v1 mechanism evidence is fully defensible.
