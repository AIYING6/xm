# INNOVATION_IDENTIFIABILITY_AUDIT_V1_8

**Scope:** R6.5 read-only/low-cost structural audit. No formal training,
held-out evaluation, OOD run, architecture change, or paper rewrite was done.

## Relation separability

The method-independent rollout audit used 240 environment steps per condition
(three fixed seeds; deterministic action sequences) in nominal, Early/Nominal
anchor, and relay-delay-loss conditions. Relation tensors were compared before
any encoder. Results are rates over complete receiver relation matrices.

| condition | P/C identical | C/TS identical | P/TS identical | P/C Jaccard | C/TS Jaccard | P/TS Jaccard | P/C disagreement | C/TS disagreement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| nominal | 0.000 | 0.000 | 0.000 | 0.500 | 0.600 | 0.200 | 0.0417 | 0.0417 |
| Early+Nominal anchor | 0.158 | 0.158 | 0.158 | 0.663 | 0.663 | 0.327 | 0.0351 | 0.0351 |
| relay + delay + loss | 0.029 | 0.033 | 0.025 | 0.603 | 0.609 | 0.223 | 0.0413 | 0.0406 |

The union is therefore not identical to any one relation. The three masks are
structurally distinguishable, but task-support is a strict subset in this
rollout family: there were no task-support edges without communication, while
40% of communication edges lacked task-support (`task/communication=0.60`).
Mean edge counts per time step (over all receiver matrices) were
`P/C/TS = 3.00/5.00/3.00` nominal, `3.32/5.00/3.32` Early+Nominal, and
`2.93/4.88/2.93` under relay+delay+loss.
This is meaningful one-sided separation, not independent task-support
activation. Delay/loss/failure did not materially increase aggregate
disagreement in this short fixed rollout, so a dedicated conflict suite remains
necessary; it must not be inferred from the nominal audit.

## Union residual

Using fixed random batches and the R6 EA pilot checkpoint, the first-layer
union path contributed 34.5% of summed output norm and 41.4% of grouped gradient
norm; random initialization gave 33.4% and 36.3%. Relation-channel norms were
similar to the union norm, and attention entropy was finite (relation mean
0.843, union 1.267 for the pilot checkpoint). The union path is substantial but
not dominant or demonstrably masking the relation channels in this audit.

## Gate Prior and Role-Pair

Gate Prior should be evaluated as structured initialization/optimization, not as
an online fault-adaptation mechanism. The preregistered mechanism endpoints
are training-return AUC, establishment-rate AUC, time-to-threshold, seed
variance, and convergence stability.

Role-Pair gates had near-zero variation in the two-update pilot checkpoint
(gate standard deviation `1.14e-4`, range `1.12e-3`; representation delta after
zeroing the gate `2.94e-4`). This is insufficient evidence for headline
innovation. Retain Role-Pair as an auxiliary design and do not add a special
experiment solely to rescue the claim.

## Answers and decision

1. The relations are distinguishable, but Task-Support is not independently
   activated on both sides of communication; identifiability is moderate, not
   strong.
2. Task-Support has sufficient nonzero separation to audit, but not enough
   independent activation to support a standalone headline claim.
3. Union residual is material, not long-run dominant in the fixed audit; it is a
   monitored structural risk rather than a demonstrated failure.
4. Gate Prior uses optimization/learning-curve endpoints listed above.
5. Role-Pair is not presently justified as a headline innovation.
6. The most diagnostic conditions are the pre-registered relation conflicts in
   [RELATION_CONFLICT_DIAGNOSTIC_PROTOCOL_V1_8.md](RELATION_CONFLICT_DIAGNOSTIC_PROTOCOL_V1_8.md).
7. No architecture modification is recommended before formal training.
8. No performance-based modification was made; any future structural change
   requires a new audit and author authorization.
9. Protocol status remains `READY_FOR_FORMAL_V1_8_TRAINING`, but execution is
   paused pending explicit author authorization.

Audit scripts:

- [audit_relation_separability_v1_8.py](../scripts/audit_relation_separability_v1_8.py)
- [audit_union_residual_and_gate_v1_8.py](../scripts/audit_union_residual_and_gate_v1_8.py)
