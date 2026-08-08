# OOD_GRADED_PROTOCOL_V1_8

**Status: redesigned and frozen for future authorization; no OOD evaluation was
run in R6.5.**

## Severity grid

Each axis has three fixed levels, defined before seeing formal results:

| axis | mild | medium | strong |
|---|---|---|---|
| geometry | target range scale 1.10 | 1.25 | 1.45 |
| communication | dropout 0.10, delay 1 | dropout 0.25, delay 2 | dropout 0.40, delay 4 |
| maneuver | heading amplitude 1.10× nominal | 1.30× | 1.60× |

The joint set is limited and pre-specified: geometry-medium +
communication-medium, communication-strong + maneuver-medium, and
geometry-strong + maneuver-strong. No additional joint combinations may be
selected because they favor one method.

## Evaluation lock

All 9 single-axis cells and all 3 joint cells are reported for every method,
with the same recipient-specific packet contract, episode seeds, failure
protocol, checkpoint selection, episode count, censoring, endpoint, `K=4`, and
`tau=80/220` as the confirmatory protocol. OOD is secondary and descriptive; it
does not replace the nominal Early/Nominal primary analysis.

The protocol is designed to avoid the prior maneuver/joint RMST80 saturation
problem by reporting full endpoint distributions, establishment rate, censoring
rate, and both RMST horizons. It may only be executed after a separate author
authorization.
