# OOD and held-out contract

| Partition | admissible structures | purpose | allowed use |
|---|---|---|---|
| training support | frozen Tier-R classes and timing/duration combinations | learner exposure | training only |
| development | disjoint members of same support family | implementation/method choice | development only |
| held-out | same family, unseen specific structural masks | standard generalization | final only |
| structural OOD | unseen edge compounds, node+edge compositions, redundancy tier and/or larger scale | structural transfer | final only |

All membership lists, evaluation seeds, scenario geometry and timing/duration combinations must be hashed before learner training. Held-out/OOD scores never choose a method, threshold, curriculum probability or checkpoint.
