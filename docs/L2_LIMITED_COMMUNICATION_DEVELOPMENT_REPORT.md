# L2 limited-communication development report

## Scope

L2 adds exactly one factor to the frozen L1 learnability configuration:
communication range scale `0.5`. Packet loss, message delay, relay failure,
and any new method were not introduced. The run remains development-only.

## Results

| policy | geometry entry | neutralized by 180 | mean RMTN180 |
|---|---:|---:|---:|
| L2 seed 8501 | 32/32 | 20/32 | 100.69 |
| L2 seed 8502 | 29/32 | 28/32 | 68.72 |
| random | 9/32 | 0/32 | 180.00 |
| scripted | 32/32 | 32/32 | 53.22 |
| oracle | 32/32 | 32/32 | 52.72 |

No collision or constraint-failure inflation was observed.

## Interpretation

With the role-specialized actor baseline and non-attacker commit mask held
fixed, halving communication range retained a non-zero, cross-seed mission
learning signal. Relative to the L1 role-specific development results, the
limited-range condition is a meaningful but not catastrophic degradation. It
supports a staged benchmark progression; it does not establish robustness to
packet loss, delay, or relay failure, and it is not formal paper evidence.

## Decision

`L2_LIMITED_COMMUNICATION_LEARNING_SIGNAL_RETAINED`.

No automatic L3, N3, new method, or formal training follows from this report.
Any next stage must be separately authorized and add only one further
communication factor.
