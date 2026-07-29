# Role-Graph Gate Diagnostics Update

Last updated: 2026-07-28

## Motivation

Chain auxiliary learning did not improve short-horizon policy learning. The next
question is whether the original EA-RG-MAPPO mechanism is actually being used:

- perception / communication / task-support relation attention;
- role-pair gate differentiation.

## Added Diagnostic Tool

Added:

```text
scripts/diagnose_role_graph_usage.py
```

The script evaluates a checkpoint and writes:

- `episode_relation_attention.csv`;
- `role_pair_gate.csv`;
- `role_graph_diagnostics.md`.

It reports:

- relation-level attention mass;
- task-support active rate;
- role-pair gate mean/std/min/max;
- gate deviation from the neutral value `0.5`.

## Diagnostic Findings

Smoke diagnostic on a 100-update checkpoint showed role-pair gates were almost
unchanged:

- mean absolute gate deviation from 0.5: `0.000098`;
- max absolute gate deviation from 0.5: `0.001106`.

Diagnostics on dev-1M EA-RG-MAPPO validation-selected checkpoints under
`dropout030_delay2_relay_failure` show the same pattern:

| Run | Success Mean | Task-Support Attention | Communication Attention | Perception Attention | Mean Gate Delta | Max Gate Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| seed0 update1700 | 0.8000 | 0.0925 | 0.7500 | 0.1974 | 0.000087 | 0.001331 |
| seed1 update2200 | 0.4000 | 0.0707 | 0.7500 | 0.1397 | 0.000146 | 0.002733 |
| seed2 update2400 | 0.6000 | 0.0789 | 0.7500 | 0.1274 | 0.000229 | 0.003581 |

Average over the three diagnostics:

- task-support attention mass: `0.0807`;
- communication attention mass: `0.7500`;
- perception attention mass: `0.1548`;
- task-support active rate: `0.4903`;
- mean gate deviation from 0.5: `0.000154`;
- max gate deviation from 0.5: `0.002548`.

Interpretation:

The multi-relation structure is active, but the role-pair gate is effectively
neutral. This weakens the paper claim that role-pair-conditioned message passing
is doing meaningful work.

## Implemented Candidate Fix

Added optional role-compatible gate initialization:

```text
--role-gate-prior-strength
```

Default is `0.0`, so existing experiments are unchanged.

New config:

```text
configs/paper/ea_rg_mappo_gate_prior.yaml
```

Current candidate:

```text
role_gate_prior_strength = 0.4
```

This initializes compatible role pairs with gate logits near `0.4`
(`sigmoid(0.4) ~= 0.5987`) while leaving incompatible pairs neutral.

Verification:

- training help exposes `--role-gate-prior-strength`;
- config audit passed: 13 configs;
- 1-update gate-prior smoke training passed;
- role-graph diagnostic confirms max gate deviation near `0.0987`;
- Gate 1 information-boundary tests passed: `24 passed`.

## Decision

Do not launch 1M with the current gate-prior candidate.

The 100-update gate-prior development run has been completed and is summarized
in:

```text
docs/gate_prior_dev100_training_summary.md
```

Result:

| Method | Mean Final Success | Mean Best Online Success |
| --- | ---: | ---: |
| Original EA-RG-MAPPO | 0.3333 | 0.4000 |
| EA-RG-MAPPO + gate prior 0.4 | 0.0000 | 0.1333 |

The follow-up fixed validation sweep with 30 matched episodes per checkpoint
was less extreme but reached the same decision:

| Method | Mean Selected Success | Mean Best-by-Success |
| --- | ---: | ---: |
| Original EA-RG-MAPPO | 0.0778 | 0.0778 |
| EA-RG-MAPPO + gate prior 0.4 | 0.0889 | 0.1000 |

Interpretation:

The prior successfully makes the role gate non-neutral in diagnostics, but the
`0.4` setting does not yield a meaningful policy-learning gain. It is not a safe
candidate for longer formal training.

Next step: return to the original EA-RG-MAPPO mainline and harden the validation
and training protocol before introducing further model changes.
