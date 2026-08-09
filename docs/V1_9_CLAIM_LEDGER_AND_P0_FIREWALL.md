# v1.9 Claim Ledger and P0 Firewall

## Rule

No headline claim may enter the paper merely because a training curve or a
single endpoint looks favorable. Every claim needs pre-specified positive
evidence, a falsifying condition, and a provenance-preserving audit. A failed
condition withdraws that claim; it does not trigger post-hoc metric or method
redesign.

| Candidate claim | Required evidence | Kill condition | Current status |
| --- | --- | --- | --- |
| Recipient-specific execution is information-fair | actor-boundary counterfactual tests | unavailable/global truth changes actor output | PASS (14/14); re-audit before F1 |
| P and C are distinct legal sources | source intervention and identifiability audit | sources cannot be independently varied or a common bypass exists | PASS (D0-R2 12/12); re-audit before F1 |
| PCRF representation adds architectural value | untouched F2: PCRF-R2 vs matched single-R2 | no practical primary-comparator advantage | not tested |
| Conflict deviation is a mechanism | frozen `Full vs Delta=0` and controlled conflict diagnostic | removing delta has no effect under its intervention | not tested |
| Generalization has a bounded benefit | fully reported frozen graded OOD protocol | pre-specified target distribution shift fails | not tested |

## Mandatory firewalls

1. Before new training, audit reality, actor legality, independent intervention,
   comparator input/capacity/budget parity, endpoint, censoring, selection, and
   seed contracts.
2. Before F1, perform an independent red-team P0 audit from a clean commit. Its
   purpose is to falsify claims, not to prepare a favorable narrative.
3. Before F2, freeze training code, selected-checkpoint procedure, statistics,
   primary endpoint, and confirmatory population. F2 remains untouched until
   then.
4. Before results writing, perform a Paper P0 Audit: trace every displayed value
   to episode records; check code-to-claim correspondence, fair baselines,
   statistic populations, execution legality, literature novelty, and complete
   reporting of negative results.
5. Claim freeze: only claims with a passing ledger row may appear as headline
   contributions. Method/background writing may start earlier, but result claims,
   abstract conclusions, and discussion are frozen only after this audit.

This firewall reduces the probability that a claim-critical problem is first
found after full training or paper drafting. It does not promise that no new
problem can exist.
