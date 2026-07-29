# Gate-Prior Dev100 Training Summary

Last updated: 2026-07-28

## Purpose

This run tested whether a stronger role-compatible initialization for the
role-pair gate can make the EA-RG-MAPPO role-pair message mechanism more active
without hurting early policy learning.

Candidate:

```text
configs/paper/ea_rg_mappo_gate_prior.yaml
role_gate_prior_strength = 0.4
```

Scenario:

```text
3d_intercept
strict target sensing
agent target information bottleneck
communication dropout = 0.30
message delay = 2 steps
failed blue agent = 1
failure start random range = [25, 70]
failure duration = 80 steps
100 PPO updates
seeds = 0, 1, 2
```

## Result

Online evaluation uses only 5 episodes per update, so the numbers are noisy.
However, the short-run signal is clearly negative.

| Method | Mean Final Success | Mean Best Online Success | Seed-Level Final Success |
| --- | ---: | ---: | --- |
| Original EA-RG-MAPPO | 0.3333 | 0.4000 | 0.0 / 0.0 / 1.0 |
| EA-RG-MAPPO + gate prior 0.4 | 0.0000 | 0.1333 | 0.0 / 0.0 / 0.0 |

Gate-prior best online checkpoints:

| Seed | Best Update | Best Success |
| ---: | ---: | ---: |
| 0 | 1 | 0.0 |
| 1 | 40 | 0.4 |
| 2 | 1 | 0.0 |

## Fixed Validation Sweep

After the online-log check, both original EA-RG-MAPPO and gate-prior EA were
re-evaluated on fixed matched validation episodes:

```text
split = validation
scenario = dropout030_delay2_relay_failure
episodes = 30 per checkpoint
seeds = 0, 1, 2
checkpoints = updates 20 / 40 / 60 / 80 / 100
base_seed = 20000
```

Outputs:

```text
results/paper_config_runs/gate_prior_dev100_validation/original_ea/
results/paper_config_runs/gate_prior_dev100_validation/gate_prior_04/
```

Selected-checkpoint results:

| Method | Mean Selected Success | Mean Selected Recovery | Selected Updates |
| --- | ---: | ---: | --- |
| Original EA-RG-MAPPO | 0.0778 | 0.0778 | 100 / 100 / 100 |
| EA-RG-MAPPO + gate prior 0.4 | 0.0889 | 0.0889 | 60 / 40 / 100 |

Best-by-success results:

| Method | Mean Best Success | Mean Best Recovery |
| --- | ---: | ---: |
| Original EA-RG-MAPPO | 0.0778 | 0.0778 |
| EA-RG-MAPPO + gate prior 0.4 | 0.1000 | 0.1000 |

This fixed validation result is slightly less negative than the online log, but
it is still not a meaningful improvement. Both variants remain weak under the
current 100-update stress protocol.

## Interpretation

The `0.4` role-gate prior is not a safe improvement. It preserves the intended
mechanistic idea, but it does not produce a robust short-run performance gain.
The fixed validation sweep shows that the larger issue is not simply the gate
initialization: the current 100-update stress setting is itself too unstable and
too weakly learned to justify promoting any gate-prior variant.

This is different from a diagnostic success. The diagnostic confirmed that the
gate can be moved away from the neutral value, but training shows that forcing
that movement does not automatically improve task performance.

## Decision

Do not promote `role_gate_prior_strength = 0.4` to 1M or formal training.

Keep the original EA-RG-MAPPO as the current main method. The gate-prior result
should be recorded as development evidence that naive hand-biased gate
initialization is not sufficient, and that the next bottleneck is training
stability/checkpoint validation rather than another architectural addition.

## Next Step

Stop adding new algorithm modules until the current protocol is stable.

Priority order:

1. run fixed validation checkpoint sweeps for the original EA and main
   baselines under the stress scenario;
2. inspect whether poor results are caused by checkpoint selection, short
   training, reward scale, or unstable PPO updates;
3. only then decide whether to tune training hyperparameters or use a lighter
   role-gate prior such as `0.1` or `0.2`.
