# TATG-MAPPO P1 topology-transition information-gap diagnostic

**Verdict:** `TATG_P1_INFORMATION_GAP_PRESENT`.

P1 uses no policy, reward, return, evaluation tape, checkpoint or PPO update. Its labels are derived only from two consecutive legal communication relation snapshots.

## Interpretation boundary

A pass establishes a narrow topology-transition information gap: the frozen current structural topology snapshot, including its current edge-age proxy, maps to more than one transition label, whereas a one-step legal topology history removes that ambiguity in both state cohorts. It does not establish improved control return, full-observation non-Markovness, or novelty of a generic recurrent graph network.

## Cohorts

- Cohort A: `{"history_mixed_code_count": 0, "loss_events": 10, "mixed_events": 0, "pass": true, "recovery_events": 10, "rows": 320, "snapshot_ambiguous_rows": 130, "snapshot_mixed_code_count": 1}`
- Cohort B: `{"history_mixed_code_count": 0, "loss_events": 10, "mixed_events": 0, "pass": true, "recovery_events": 10, "rows": 320, "snapshot_ambiguous_rows": 240, "snapshot_mixed_code_count": 2}`

A pass authorizes only a separate exact-formula, fairness and serialization audit. It does not authorize TATG implementation, PPO training or cloud execution.
