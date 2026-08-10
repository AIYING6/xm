# L1 shared-actor plus commit-mask control

## Purpose

This development-only control separates the two changes in the preceding
role-specific-head result. It retains the shared actor and masks
`engage_commit` for Scout/Relay. All other L1 conditions remain unchanged.
It is not L2, N3, formal training, or paper evidence.

## Results

| policy | geometry entry | neutralized by 180 | mean RMTN180 |
|---|---:|---:|---:|
| shared + mask, seed 8401 | 16/32 | 8/32 | 147.88 |
| shared + mask, seed 8402 | 16/32 | 8/32 | 147.88 |
| random | 14/32 | 2/32 | 172.28 |
| scripted | 32/32 | 32/32 | 53.34 |
| oracle | 32/32 | 32/32 | 52.69 |

No collision or constraint-failure inflation was observed.

## Attribution

Masking the invalid non-attacker commit action partially restores learning:
both seeds exceed random and leave the all-horizon-saturated regime. However,
the effect is substantially smaller than the role-specific-head plus mask
condition (31/32 and 18/32 neutralizations; RMTN180 56.16 and 108.72).

Therefore the evidence supports a combined interpretation: invalid role action
semantics contribute to the shared-actor failure, while insufficient
role-specialized policy outputs remain an additional optimization bottleneck.
The result does not justify the broader claim that fully shared parameters are
the sole cause; the tested intervention changes the output-head sharing and
the commit mask, not the entire actor trunk.

## Decision

`L1_SHARED_MASK_CONTROL_ESTABLISHES_LEARNING_SIGNAL`.

This closes the attribution control requested before any L2/N3 decision. No
new method or formal experiment is authorized by this report.
