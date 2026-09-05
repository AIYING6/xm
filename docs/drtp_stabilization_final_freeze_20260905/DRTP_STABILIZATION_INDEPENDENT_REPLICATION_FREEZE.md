# DRTP independent replication freeze

**Cohort:** `B`
**Method:** Global-Anchored EGTR-SG-MAPPO, `alpha = 0.75`.

This is a pre-result independent replication of the already frozen final
method, not a new development iteration. It uses the disjoint training seeds
`78021--78025` and a separate evaluation tape with identifiers
`781000--781099`. The four arms, PPO, environment, reward, 10M endpoint and
reporting rules are unchanged from Cohort A.

Cohort A and Cohort B must be reported separately. Pooled `n=10` confirmation
is forbidden, and no Cohort A outcome may select a Cohort B seed, tape,
checkpoint or algorithm revision.
