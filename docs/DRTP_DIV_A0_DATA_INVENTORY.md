# DRTP-DIV-A0 — Data Inventory

## Scope and integrity

This is a zero-training, zero-rollout forensic audit. It reads only the two
author-provided DRTP archives. No environment was constructed, no simulator
method was called, no new evaluation tape was created, and no historical result
was overwritten.

| Source contract | paired seeds | archived assets used | status |
|---|---:|---|---|
| Strict 10M development | 1901 (strong), 1902 (weak) | PPO logs, sampler logs, 0.5M–10M runtime states | usable |
| Held-out v2 | 2001 (strong), 2002 (weak), 2003 (strong) | PPO logs, sampler logs, 0.5M–10M runtime states | usable |

The five historical classifications are descriptive and contract-specific;
they are not pooled as if they were a single confirmatory experiment.

## Evidence capability

| Question | Evidence | Capability |
|---|---|---|
| PPO optimization timeline | complete `train_log.csv` | estimable |
| Matched-state actor mapping | twenty archived runtime states per method × seed | estimable, sparse bank (4 environments × 3 actors at each bank) |
| Adaptive-weight history | sampler logs | estimable |
| Step-level coordination sequence | not present | not estimable |
| Milestone external performance | not present; only final-condition evaluation summaries | not estimable |

Runtime snapshots contain model/optimizer/RNG/environment state plus `obs` and
`graph_obs`. For every paired seed, the UTR 500k snapshot supplies the common
actor-legal state bank. Both archived UTR and DRTP actor states are forwarded on
that same bank at each milestone. This is an offline model interrogation, not
an environment interaction.

Machine-readable outputs are in `artifacts/drtp_div_a0/`. Figure exports are
available in SVG, PDF, PNG, and 600-dpi TIFF formats.

