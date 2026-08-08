# CONFIRMATORY_EVALUATION_PROTOCOL_V1_8

**Status: PRE-FLIGHT REVISION REQUIRED pending failure-duration decision.**

## Population and generation

Training seeds are `{0, 1, 2}`. Validation uses seeds
`10000 + 100*training_seed + episode_index` and is isolated from confirmation.
The confirmatory population uses a new deterministic anchor with episode seeds
`70000 + episode_index`, independent of every training and validation seed.
The anchor and all episode indices are frozen before training and are not
selected from pilot or training results.

The fixed confirmatory population contains 300 episodes **per method × trained-
seed checkpoint**. Early/Nominal are not distinct scientific populations: the
prior index split used identical scenario parameters and differed only by seed.
The v1.8 confirmatory estimand is therefore the single 300-episode population.
For transparent descriptive reporting only, episodes 0–149 may be labelled
`anchor_half_A` and 150–299 `anchor_half_B`; these labels have no scientific
scenario meaning and cannot be selected after results are seen.

The same 300 episode seeds are applied to each trained-seed checkpoint for
matched evaluation. No episode is removed because it is difficult or because
its outcome is unfavorable.

## Failure and endpoint

Relay failure onset is the configured fixed start step (agent 1, step 80) and
failure duration is fixed at 4 steps. Primary endpoint is time from this onset
to the first task-chain establishment that remains true for `K=4` consecutive
steps. This is not labelled true recovery. Episodes with no stable
establishment are right-censored at 260 steps or the first terminal event.

Report RMST from failure onset at `tau=80` and `tau=220`; tau values and the
censoring rule cannot change after results are observed. The primary
architecture comparator is corrected EA-RG Full versus corrected wider
single-graph. Matched-information non-graph is secondary; MAPPO/HAPPO are
conditional system-level comparators under the expanded no-graph invariance
audit.

## Analysis lock

Checkpoint selection uses only the frozen validation population and the
censoring-aware rule in [FAIR_ACTOR_PROTOCOL_V1_8.md](FAIR_ACTOR_PROTOCOL_V1_8.md). Confirmatory episodes
are never used for early stopping, hyperparameter selection, or checkpoint
selection. Use hierarchical bootstrap: resample the three independent training
seeds, then episodes within seed, 10,000 replicates, percentile 95% confidence
intervals. Report the single confirmatory population; any anchor-half display
is descriptive only and cannot become a separate scientific population.

The following are locked: episode count, seed formulas, failure protocol,
population split, censoring, primary comparator, endpoint, `K=4`, and tau values.
Any change requires a new v1.8.x protocol version and invalidates confirmatory
claims from the changed analysis.
