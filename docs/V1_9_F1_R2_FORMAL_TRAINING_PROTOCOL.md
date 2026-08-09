# v1.9 F1-R2 Formal Training Protocol

**Status: `D2_R2_PROTOCOL_FROZEN__F1_FORMAL_TRAINING_AUTHORIZED__F2_NOT_AUTHORIZED`.**

## Scope and prohibitions

F1 creates the formal trained-model population only.  It is not an evaluation,
does not open the F2 confirmatory population, and does not permit a comparison
claim, architecture change, seed replacement, or tuning from validation curves.
Training-time validation exists solely to operate the frozen checkpoint selector.

The frozen methods are `pcrf_r2`, `single_r2`, and `matched_nongraph_r2`.
Each receives exactly the formal seed set `0,1,2,3,4,5,6,7`, yielding 24 runs.
The D2 seeds `9501,9502` remain permanently non-evidentiary.

## Frozen common run configuration

Every run uses 300 updates, 8 environments, 128 rollout steps, PPO epochs 4,
role/intent width 8, strict target sensing, recipient-specific P/C source
semantics, communication dropout 0.30, message delay 2, radar dropout 0.10,
relay 1 failure at step 40 for 80 steps, and `K=4`.  The method/width pairs are
`pcrf_r2/128`, `single_r2/147`, and `matched_nongraph_r2/152`.

Validation occurs at updates `1,10,20,...,300` using the same independent
development episode IDs `410000`--`410015` for every method and training seed.
Each point persists an immutable actor-critic snapshot, metadata, SHA256,
episode-level event records, and summary.  F1 logs RMTE80/RMTE220 plus the
frozen physical-engagement-readiness RMPE80/RMPE220 secondary fields.  RMPE is
evaluator-only and does not enter actor observations, rewards, or selection.

## Frozen selector

For each method × training seed, select exactly one snapshot using the
lexicographic order:

1. lower RMTE80;
2. higher establishment probability at 80;
3. lower terminal-failure incidence at 80;
4. lower RMTE220;
5. earlier update on an exact tie.

The selector reads only immutable training-time validation files and verifies
method, seed, update, source commit, SHA256, and event-record schema.  RMPE,
F2 data, and post-training evaluation never enter selection.

## Completion gate

F1 passes only if all 24 runs have contiguous updates 1--300, empty stderr,
finite PPO quantities, all 31 immutable validation points, correct R2 encoder
provenance, a valid CUDA/source attestation, and a frozen selection manifest
with 24 SHA256-verified checkpoints.  The passing state is
`F1_R2_FORMAL_TRAINING_COMPLETE__CHECKPOINTS_FROZEN__READY_FOR_F2_AUTHORIZATION`.

F2 remains prohibited until separately authorized.
