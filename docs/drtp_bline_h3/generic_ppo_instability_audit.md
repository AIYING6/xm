# Generic PPO/MARL instability audit

`generic PPO sensitivity` remains a permissible null explanation but is not established.

The historical formal and independent cohorts have similar mean PPO KL for DRTP
(0.001366 vs 0.001354) and for UTR (0.001409 vs 0.001389). UTR late training
reward is also similar or higher in the independent cohort (0.264135 vs 0.270590),
whereas DRTP late training reward declines (0.276372 to 0.242910) and the paired
evaluation direction reverses across both evaluation tapes. These facts do not
prove DRTP specificity, because the historical cohorts have no synchronized
behavior telemetry; however, they do not support a simple “all methods have the
same magnitude of PPO instability” account either.

Generic PPO sensitivity cannot be selected as H3: it has no DRTP-specific temporal
signature, no single sampler-level repair, and would require a broader seed study
rather than the promised minimum-cost mechanism falsification.
