# Phase R1–R2 Recovery Feasibility Report

**Protocol:** `PHASE-R1-R2-RC-V1` with Amendment A1  
**Status:** `R2-INFEASIBLE`  
**Training:** not started  
**Canonical seeds/checkpoints:** not used

## Executive result

The A1 transparent replay established that a legal post-fault Scout→Attacker
alternative path can occur, but the complete pre-registered R2 adequacy gate
did not pass. The task is therefore not ready for MARL training.

This is materially different from the original IA9 finding: the original task
lacked a relay dependency, whereas the R0–R2 task now has a reachable recovery
path in some eligible episodes. The remaining issue is stability and
repeatability of the frozen transparent controller protocol.

## Cell results

| Controller | Seed | Eligible | Loss | Recovery | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| structural_oracle | 1201 | 55 | 11 | 11 | FAIL: loss rate |
| structural_oracle | 1202 | 54 | 5 | 5 | FAIL: loss rate |
| structural_oracle | 1203 | 60 | 9 | 9 | FAIL: loss rate |
| legal_observation | 1201 | 2 | 2 | 2 | FAIL: eligibility |
| legal_observation | 1202 | 3 | 3 | 3 | FAIL: eligibility |
| legal_observation | 1203 | 1 | 1 | 1 | FAIL: eligibility |

The frozen thresholds required at least 10 eligible episodes per cell, at
least 80% loss among eligible episodes, and at least 50% recovery among lost
episodes. Recovery among the episodes that did lose information was 100% in
all six cells, but the first two conditions failed.

## Interpretation

The geometry and implementation now support the intended causal pattern in
individual episodes:

```text
Scout-Relay-Attacker information path -> relay fault -> information loss
                                      -> post-fault Scout-Attacker path -> recovery
```

However, the transparent legal-observation controller rarely establishes the
primary chain, and the structural controller often retains a legal attacker
information path during the relay fault. These are task/controller adequacy
limitations, not algorithm results.

## Decisions

- R0 task redesign: **PARTIAL PASS** — explicit dependency and legal
  alternative path are implemented and observable.
- R1 geometry feasibility: **PASS** — initial direct Scout–Attacker link is
  absent and the closing-time margin is positive.
- R2 transparent feasibility: **NO-GO / INFEASIBLE** under the frozen A1
  controller and cell thresholds.
- MARL training: **NO-GO**.
- Phase 3A: **NO-GO**.
- Role-Gate: **UNRESOLVED**.

## Minimal next step

Do not start training. The only justified next action is a separately frozen
R2 controller/task adequacy amendment that addresses the two observed issues:

1. make the pre-failure formation controller maintain the Scout–Relay–Attacker
   chain without using hidden target truth in the legal arm; and
2. ensure that, once that chain is established, the relay-1 fault is the
   primary cause of attacker-information loss rather than an incidental
   dropout or geometry change.

Any such amendment must be committed before re-execution and must preserve the
same endpoint, provenance requirements, and no-training gate. If a defensible
amendment cannot be written without changing the scientific task, the project
should stop the recovery claim and use the evidence as a bounded task-design
finding.
