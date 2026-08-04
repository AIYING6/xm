# v1.5 Checkpoint-Selector Adjudication (frozen)

**Freeze date:** 2026-08-04
**Status:** Frozen before any v1.5 formal validation run and before any v1.5
model selection. Hash recorded externally in
`V1_5_CHECKPOINT_SELECTOR_ADJUDICATION.md.sha256`.
**Development-diagnostic seed `888000` must NOT be used for v1.5 selection.**

## 1. Motivation

The v1.4 selector averaged `post_failure_chain_recovered_mean` over **all**
episodes, counting episodes that finished before the failure as recovered=0.
This systematically penalises fast methods. v1.5 therefore selects on
**conditional** recovery given actual failure exposure, while reporting the
unconditional success/time metrics jointly.

## 2. Frozen rule

### Validation split (new, never run)

```text
scenarios : dropout030_delay2_relay_failure_early
            dropout030_delay2_relay_failure
            dropout030_delay2_relay_failure_delayed
            dropout030_delay2_relay_failure_late   (all four, kept)
base_seed : a new fixed validation seed NEVER used before (not 120000, not 888000),
            sealed in the v1.5 command manifest before running
episodes  : 50 per (method, seed, scenario)
```

### Definitions

```text
failure_exposed        : episode reaches the scenario failure step
                         (final_step >= node_failure_start_step)
recovered_count        : exposed episodes with post_failure_chain_recovered == 1
exposed_count          : number of failure_exposed episodes (pooled over the 4
                         scenarios)
recovery_given_exposure: recovered_count / exposed_count
```

### Eligibility (all must hold)

```text
collision_rate == 0
checkpoint file exists
checkpoint SHA256 matches the sealed training manifest
all 4 scenarios evaluated completely
failure_exposed_count > 0          (checkpoint must actually experience failure)
```

If `exposed_count < 10`, the checkpoint may still be selected but its
recovery rate is flagged "estimate unstable"; `k/n` with tiny n must not be
treated as a reliable advantage.

### Ranking (maximise / minimise as marked)

```text
(
  recovery_given_exposure_wilson_lower_95 ↑,   # Wilson 95% lower bound of k/n
  unconditional_success_rate ↑,
  time_to_recovery_given_exposure ↓,
  time_to_success ↓,
  checkpoint_update ↑
)
```

- Wilson lower bound: `(p + z²/2n - z*sqrt(p(1-p)/n + z²/4n²)) / (1 + z²/n)`,
  `z=1.96`. It automatically penalises checkpoints with few exposed episodes.
- No unexposed episode is counted as a recovery failure.

### Grouping & eligible updates

```text
grouping : each (method, train_seed) selected independently
eligible : 100, 200, 300, 400, 500, 600, 700, 800, 900, 977
```

## 3. Full / baselines / ablations use the SAME selector

- v1.4 locked results are untouched (15/15 frozen, not re-selected).
- For v1.5 comparisons, **Full EA-RG must be re-selected** on the new
  validation split with this selector, from its existing 100..977 checkpoints.
- `no_graph`, `param_matched_single`, and HAPPO, if included in the v1.5 main
  comparison, use the same selector and the same new split.
- Ablations (w/o Gate Prior, w/o Task-Support, w/o Role-Pair Gate) use the
  same selector, same split, same eligible updates, same seeds.
- This requires re-evaluating existing checkpoints, not retraining (unless an
  ablation's config requires it).

## 4. Prohibitions

```text
- The development-diagnostic seed 888000 (and the v1.4 seed 120000) must not
  be used for v1.5 selection.
- No re-weighting of the tuple after seeing results.
- No manual checkpoint substitution.
- No use of held-out test results in selection.
- This document must not change without a new freeze + hash.
```

## 5. Audit requirements

```text
- policy/schema audit of the selection CSV
- 15/15 (or 9/12 + full) method-seed uniqueness
- eligible-update check
- checkpoint path existence + SHA match
- exposed_count and recovery counts recorded per row
- 'estimate unstable' flags where exposed_count < 10
- evaluation commit/tag recorded
```
