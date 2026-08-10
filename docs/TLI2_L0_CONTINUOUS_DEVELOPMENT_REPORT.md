# TLI2 L0 continuous-action development report

Status: `TLI2_CONTINUOUS_ACTION_ESTABLISHES_L0_LEARNING_SIGNAL`

This is a non-evidentiary learnability diagnostic. It is not a formal F1/F2
result and does not authorize L1 or N3.

## Frozen comparison

Relative to TLI1, the only intended change was the actor action interface:
continuous bounded `turn_command` and `climb_command` in `[-1, 1]`, plus the
unchanged Bernoulli `engage_commit` head. Seeds were 8101 and 8102, with the
same 60-update budget, observation, reward alignment, dynamics, controller,
timescale, horizon (180), and evaluation seeds (32 episodes).

The continuous policy uses a tanh-squashed Gaussian with the exact Jacobian
log-probability correction and a Bernoulli commit head. The evaluator maps
legacy scripted/oracle guidance commands into the same continuous interface;
the trained policies emit the hybrid action directly.

## Development outcome summary

| mode | geometry entry | neutralized by 180 | mean RMTN180 |
|---|---:|---:|---:|
| random | 9/32 (28.1%) | 0/32 | 180.00 |
| scripted | 32/32 (100%) | 32/32 | 54.19 |
| oracle | 32/32 (100%) | 32/32 | 52.97 |
| continuous seed 8101 | 9/32 (28.1%) | 4/32 (12.5%) | 163.84 |
| continuous seed 8102 | 12/32 (37.5%) | 10/32 (31.25%) | 140.06 |

Both development seeds satisfy the pre-registered minimum signal criteria:
non-zero geometry entry, non-zero neutralization above random, and RMTN180
below the horizon. The learned policies remain far below the scripted/oracle
ceiling, so this is not a ceiling or evaluator artifact.

## Interpretation and boundary

The result supports the narrow statement that the continuous hybrid action
interface establishes a reproducible L0 learning signal under the aligned
reward. It does **not** establish superiority, multi-agent learnability,
communication robustness, or any mission-level paper claim. No L1, N3, formal
training, OOD, or confirmatory evaluation is authorized by this report.

The four earlier attempts that stopped during integration were preserved in
separate result directories; they were implementation failures (action shape,
log-prob broadcasting, update reshaping, and evaluator action conversion), not
performance observations. The final run reused the completed training
snapshots from the training-only attempt for evaluator debugging and did not
alter the frozen training experiment.
