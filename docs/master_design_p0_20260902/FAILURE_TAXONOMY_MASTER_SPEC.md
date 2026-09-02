# Failure taxonomy master specification

Primary labels are topology structures; timing and duration are orthogonal factors.

| Structural class | Tier candidate | Definition | Main use |
|---|---|---|---|
| noncritical directed edge loss | R | one path edge removed; legal alternate route remains | main training/evaluation |
| relay ingress/egress partial loss | R/C | selected relay links removed | main / stress |
| single relay-node loss | R/C | all incident task-support links disabled | recovery stress |
| scout or terminal partial capability/link loss | R/C | role-specific support degradation | held-out family member |
| multi-edge redundancy loss | C | two non-cut edges jointly removed | critical stress |
| local-subnetwork degradation | C | correlated mask/dropout within one branch | structural OOD candidate |
| edge+node compound | C/I | composition classified by reachability | OOD / lower bound |
| cut-set / complete impossible topology | I | no legal source-to-terminal task path | impossibility reference only |

Each class later crosses `structure × onset {early,middle,late} × duration {short,medium,long}`. No timing/duration label may be reported as a new topology class.
