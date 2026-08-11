# L4 message-delay development report

## Calibration and scope

L4 preserves the L3 configuration: communication-range scale `0.5`, packet
dropout `0.3`, role-specific actor heads, non-attacker commit mask, continuous
guidance, aligned reward, and the N0/N1 mission contract. A
method-independent communication calibration evaluated 2, 4, 8, and 16 delay
steps across eight fixed seeds. The frozen choice was 8 steps: it increased
message age while retaining common cache-valid evidence.

## Results

| policy | geometry entry | neutralized by 180 | mean RMTN180 |
|---|---:|---:|---:|
| L4 seed 8901 | 11/32 | 8/32 | 147.63 |
| L4 seed 8902 | 11/32 | 8/32 | 147.63 |
| random | 13/32 | 0/32 | 180.00 |
| scripted | 32/32 | 32/32 | 53.84 |
| oracle | 32/32 | 32/32 | 53.19 |

No collision or constraint-failure inflation was observed.

## Interpretation boundary

The additional delay produces a harder but still non-zero learning setting in
this two-seed development screen. This does not estimate a causal L3-to-L4
mean performance drop because adjacent stages use different training seeds.
The ladder is used to locate loss of baseline learnability, not to claim
cross-stage effect sizes. Relay failure and any new method remain untested.

## Decision

`L4_DELAY_LEARNING_SIGNAL_RETAINED`.

Further complexity requires an explicit next-stage authorization. If the next
factor is relay failure, it must be calibrated independently and be the only
new environmental change.
