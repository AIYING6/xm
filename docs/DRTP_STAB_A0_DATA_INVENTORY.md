# DRTP-STAB-A0 Data Inventory

**Scope:** read-only, zero-training, zero-rollout audit.  
**Historical status retained:** `DRTP_Q2_LIMITATION_ONLY`; development
`NO-GO`; held-out v2 `HELD_OUT_FAIL`.

## Inventory result

| Historical seed | Frozen class | Per-update `q` / weights | Difficulty / EMA trajectory | PPO trajectory | Evaluation milestones | Checkpoint milestones | A0 usability |
|---:|---|---|---|---|---|---|---|
| 1901 | strong development | not present in current workspace | not present | not present | final + selected summaries | documented | summary-only |
| 1902 | weak development | not present in current workspace | not present | not present | final + selected summaries | documented | summary-only |
| 2001 | strong held-out | not present in current workspace | not present | not present | final confirmation only | documented | summary-only |
| 2002 | weak held-out | snapshot values quoted in prior forensic only | snapshot values quoted in prior forensic only | aggregate statistics quoted in prior forensic only | final confirmation only | documented | partial, summary-only |
| 2003 | strong held-out | not present in current workspace | not present | not present | final confirmation only | documented | summary-only |

The current repository retains the DRTP sampler implementation, one-update
technical-verification logs, and the maintained historical reports. The two
cloud code packages retain implementation/provenance material, not the full
historical result directories needed to reconstruct five seed trajectories.

## What is available

- The frozen update rule and log schema are preserved in
  `algorithms/ri_gmappo/drtp_topology_sampler.py`.
- The historical forensic report retains seed2002 snapshots at approximately
  0.5M, 1M, 3M, and terminal summaries.
- Final paired performance, safety, and exposure values exist for development
  and held-out seeds.
- The historical forensic reports establish previously checked counterexamples
  and PPO aggregate comparisons.

## What is missing

The following critical time series are unavailable in the current workspace:

- all historical per-update weight rows for seeds 1901/1902/2001/2002/2003;
- all historical per-update EMA/difficulty rows;
- sampled per-window completed returns/counts;
- training-time timeout/task-progress trajectories;
- aligned milestone evaluation for the held-out final contract.

Consequently, M1--M6 weight descriptors, weight/difficulty cross-correlations,
ranking-flip counts, and exact temporal precedence cannot be reconstructed
without fabricating data. No retrieval, evaluator rerun, rollout, or new tape
was attempted.

Machine-readable availability is recorded in
`artifacts/drtp_stab_a0/seed_weight_metrics.csv`.

## Backup recovery addendum — controlling inventory

After the initial workspace-only inventory, a read-only search recovered
`D:\Code\backup\drtp_strict_10m_results.tar.gz`
(`08bae982a858c2bab6ecd21cc0f59e10f881bb134d14bab6d26cb6545293ca45`) and
`D:\Code\backup\drtp_heldout_v2_results.tar.gz`
(`fcfd308fe84bb5214c6adc7cad98a562d7e1df86497bebde6e8b57f78acc7949`).
These archives contain all five DRTP sampler and PPO training logs. The
earlier “missing per-update history” statement is superseded.

All five seeds now have 1,220 `weight_update` rows containing q, EMAs,
difficulties and window counts, plus full PPO training logs. Held-out
evaluation still has final-only F0/OOD/safety endpoints; its final behavioral
failure cannot be dated to a precise training update.
