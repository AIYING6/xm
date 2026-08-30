# B5 observational cohort contract (preparation only)

**Status:** `PREP_ONLY_NOT_AUTHORIZED`. This contract does not authorize training.

## Frozen design

- Arms: `utr_sg, drtp_sg`.
- Provisional seeds: `3601, 3602, 3603, 3604, 3605`; provisionally clean by repository filename and source-text audit; archive-content audit required before freeze.
- Ceiling: `1000192` environment steps; milestones `250112, 499968, 750080, 1000192`.
- Same paired seeds, environment, reward, PPO, actor/critic, failure semantics, sampler parameters and frozen evaluation tape.
- No early stopping, best-checkpoint promotion, seed replacement, performance rerun or algorithm change.
- The 0.5M milestone is descriptive only. Existing R1 failures first appeared between 0.75M and 1M, so 0.5M cannot falsify the candidate mechanism.

## Mechanism GO

All conditions are required:

- signal precedes endpoint degradation;
- same-direction pattern in at least two of five adverse DRTP seeds;
- matched UTR lacks an equally strong pattern;
- at least two middle-layer indicators support the credit-assignment layer;
- optimization-to-behavior/task-support-to-outcome chain is continuous;
- conclusion is robust to preregistered neighboring thresholds;

**NO-GO:** If the complete signature is absent by 1M, close B-line algorithm development; do not invent another patch.
