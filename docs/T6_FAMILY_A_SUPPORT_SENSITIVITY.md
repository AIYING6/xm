# T6 Family A — Support Sensitivity Magnitude

## Measurement

For every recorded state and role, the frozen checkpoint was evaluated with actor-legal support features intact and with their fixed local-missing mask. Sensitivity is total-variation distance between those action distributions. This is an offline forward probe, not an environment intervention or policy update. GOOD–WEAK comparison was standardized within role, F0/timing/duration family, phase, progress, local topology label, support state, expected-action-norm bin, and target-visibility strata.

## Result

| Scope | Matched cells | GOOD minus WEAK sensitivity |
|---|---:|---:|
| All failure families | 121 | +0.0765 |
| F0 | 32 | +0.0768 |
| Timing | 42 | +0.0737 |
| Duration | 47 | +0.0788 |

Per seed: 2201 `0.0938`, 2202 `0.1222`, 2203 `0.0261`, 2204 `0.1620`, and 2205 `0.0671`. Both GOOD seeds are above both WEAK seeds. The frozen criterion was a positive matched gap above `0.01` in every condition; therefore **Family A PASS**.

The five-seed rank association with each `J_F0`, `J_OOD_mean`, and `J_OOD_worst` is Spearman `+0.80`; association with timeout is `-0.20`. These are descriptive only and were not used to tune a method.

## Interpretation boundary

Better existing policies change their action distribution more when already legal support information is masked, even after the fixed controls. This identifies **calibrated actor-legal support sensitivity** as a development target. It does not show that uniformly maximizing sensitivity, masking information during training, or adding a new loss would help.
