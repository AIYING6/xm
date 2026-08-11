# L3 packet-loss development report

## Calibration

A method-independent calibration used eight fixed environment seeds and
random actions. With the L2 communication-range scale fixed at `0.5`,
candidate dropout probabilities were 0.1, 0.3, 0.5, and 0.7. The pre-registered
choice was `0.3`, selected as an intermediate degradation level rather than by
learning performance.

## Results

| policy | geometry entry | neutralized by 180 | mean RMTN180 |
|---|---:|---:|---:|
| L3 seed 8701 | 14/32 | 10/32 | 140.69 |
| L3 seed 8702 | 29/32 | 29/32 | 64.19 |
| random | 13/32 | 2/32 | 172.22 |
| scripted | 32/32 | 32/32 | 52.75 |
| oracle | 32/32 | 32/32 | 52.25 |

No collision or constraint-failure inflation was observed.

## Interpretation

Packet loss caused a substantial seed-dependent degradation relative to the
L2 range-only condition, but both development seeds retained non-zero mission
learning signals and exceeded random neutralization. Thus packet delivery
loss is a meaningful stressor, not yet a confirmed learnability breakpoint.
Delay and relay failure were not introduced.

## Decision

`L3_PACKET_LOSS_LEARNING_SIGNAL_RETAINED`.

This is development evidence only. No automatic delay stage, relay-failure
stage, new method, or formal training follows without a separate decision.
