# Phase RSG-1 Development Smoke Report

> Frozen nine-cell development smoke; descriptive development evidence only.

## Final decision

**REMOVE RSG-TC / RSG-1 NO-GO**

The result does not authorize canonical training or a headline claim. The fixed protocol, tape, seeds, and checkpoint rule were not changed.

## Evidence integrity

- 3 methods × 3 seeds = 9 completed cells.
- 200,192 environment steps per cell; 782 updates per cell.
- Fixed final checkpoint only; no resume, early stopping, promotion, or seed exclusion.
- Shared paired evaluation tape: episode IDs 340000–340099.
- Archive SHA256: `B5612CEA1A5B8D611CEFB1F813B942E3B536F78F689CDC6EFA3C6441CD52FE92`.

## Descriptive primary metrics

| Method | Mean nominal J | Mean failure J | Mean ΔJ |
|---|---:|---:|---:|
| matched Single-Graph | 35.9243 | 28.2205 | 7.7038 |
| RSG-TC | 12.5320 | 4.6966 | 7.8354 |

RSG-TC nominal competence is substantially below matched Single-Graph, and its mean failure score is also lower. Its mean degradation is not lower than matched Single-Graph.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| G1 nominal competence | FAIL | ratio 0.3488, threshold ≥ 0.90 |
| G2 failure score | FAIL | ratio 0.1664, threshold ≥ 0.90 |
| G3 mean degradation | FAIL | RSG-TC 7.8354 vs SG 7.7038 |
| G4 seed direction | FAIL | 2/3 better; pooled direction FAIL |
| G5 safety | PASS | collision/timeout/constraint margins checked at 0.05 |
| G6 bias telemetry | PASS | pooled std 0.609979; seed rule checked |

## Interpretation

RSG-TC does not pass the pre-registered development retention rules. Two seeds have a smaller ΔJ than matched Single-Graph, but the pooled direction fails and the nominal/failure competence gates fail. The apparent lower degradation is therefore not sufficient evidence of robustness; it is confounded by weak and unstable nominal competence.

The relation-bias telemetry is reported as mechanism diagnostics only. It cannot rescue the failed competence gates or justify a formal RSG-TC claim.

## Next action

- Stop RSG-TC architecture screening under this frozen contract.
- Do not start canonical RSG-TC training, confirmatory seeds, or Phase 3A on the basis of this result.
- Retain MAPPO and matched Single-Graph as controls/evidence; decide separately whether the simpler matched Single-Graph line is publishable as an application/robustness study.
- Do not alter the environment, failure semantics, tape, or seeds to improve this outcome.

Raw evidence remains under the archival result directory; `RSG1_GATE_AUDIT.json` contains the machine-readable audit.
