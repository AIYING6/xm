# Phase S2 Final Freeze Report

## A. Frozen scientific question

When Relay failure causes relation-specific communication-topology and
path-composition changes, can multi-relation communication–task graph modeling
reduce mission-performance degradation under decentralized information
constraints?

## B. Closed claims

Strict recovery, Relay-mediated information loss, Relay necessity, and
Role-Gate as a core contribution are closed/non-core. Role-Gate is
non-blocking and unresolved.

## C. Environment and failure contract

- base: `configs/paper/s2_environment_frozen.yaml`
- nominal: `configs/paper/s2_nominal_condition.yaml`
- failure: `configs/paper/s2_failure_condition.yaml`
- exact environment/failure hashes: `results/s2_freeze/environment_contract_manifest.json`
- failure: Relay 1, step 44, 80 steps; Relay incident edges removed; direct
  `Scout→Attacker` remains governed by physical communication rules.

## D. Metric hierarchy

Primary: `Delta_J = J_nominal - J_failure`, aggregated over all planned pairs.
Mechanism analyses condition on exposed episodes and report exposure rate.
Key secondary metrics are success degradation, task-chain availability,
path composition/switching, and coordination burden. Information availability,
age, staleness, connectivity, and safety are diagnostics. Strict recovery,
KM, and RMST are exploratory only.

## E. Claim boundary

Allowed: Relay-node failures induce reproducible relation-specific topology and
path-composition changes associated with mission-performance degradation; S3/S4
may test whether Full reduces that degradation.

Prohibited: information-loss mediation, unique Relay necessity, restoring lost
information, strict recovery headline, and unsupported Role-Gate claims.

## F. Methods and fairness

The initial S3 lineup is MAPPO, parameter-matched Single-Graph, and
Multi-Relation Full. All use the same frozen environment, reward, budget,
paired validation tape, and legal decentralized actor boundary. Full has
117,302 parameters; matched Single-Graph has 116,728 (0.4893% mismatch);
MAPPO has 35,771.

## G. Validation results

- environment smoke: PASS;
- communication/failure and information-boundary regression: PASS (36 tests
  in the executed combined suite; the existing information-boundary report
  records its prior 44-test fixed-input suite separately);
- explicit graph-legality verifier: PASS;
- logging ON/OFF invariance: PASS, max difference 0.0;
- S1-B topology/path mechanism: PASS;
- provenance/config/tape contracts: present and hashed.

## H. S3 draft contract

`configs/paper/s3_development_smoke.yaml` is prepared but not launched:
development seeds `1501/1502/1503`, equal 200,000 environment steps per
method, final checkpoint only, no early stopping, no checkpoint promotion,
paired nominal/failure validation, no canonical test, and no headline claims.

## I. Gate matrix

| Gate | Result |
|---|---|
| E Environment | PASS |
| F Failure semantics | PASS |
| M Metrics | PASS |
| C Claim boundary | PASS |
| I Information legality | PASS |
| P Parameter fairness | PASS |
| T Telemetry/invariance | PASS |
| R Provenance/reproducibility | PASS |

## J. Final decision

**S2-FROZEN / S3 DEVELOPMENT SMOKE AUTHORIZED**

This authorization is for the separately specified S3 development smoke only.
No MARL training was started during S2. Phase 3A canonical training remains
**NO-GO** unless separately authorized.
