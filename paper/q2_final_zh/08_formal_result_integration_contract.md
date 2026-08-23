# 08 Formal Result Integration Contract

## Purpose

This contract binds the in-progress prospective UTR/DRTP five-seed experiment to the Chinese manuscript. It permits result insertion only after the cloud launcher completes training, final-checkpoint evaluation, aggregation, and packaging successfully.

## Required authoritative inputs

The downloaded result archive must contain all of the following under one common output root:

- `formal_tape_manifest.json`;
- ten completed `runs/{utr_sg,drtp_sg}/seed230{1..5}/run_manifest.json` files;
- ten final model and runtime-state checkpoints with SHA256;
- `evaluations/final_10m/evaluation_manifest.json` with 12,000 raw records;
- `evaluations/final_10m/per_seed_condition_summary.csv`;
- `evaluations/final_10m/paired_seed_results.csv`;
- `evaluations/final_10m/DRTP_UTR_Q2_FORMAL_DECISION.json`;
- `DRTP_UTR_Q2_FORMAL_FIVE_SEED_CONFIRMATION_REPORT.md`;
- archive SHA256.

No intermediate checkpoint, partial seed set, manually recomputed cell, or cloud-screen excerpt may be substituted for these inputs.

## Integrity gate before manuscript insertion

All checks below must pass:

1. ten of ten run manifests have `status=completed`;
2. every run has 39,063 updates and 10,000,128 environment steps;
3. methods and seeds are exactly UTR/DRTP × 2301–2305;
4. all final checkpoint and runtime-state hashes are present;
5. tape IDs are exactly 490000–490099 and the tape hash matches evaluation and decision files;
6. raw evaluation count is 12,000;
7. all onset-surviving failure episodes trigger correctly;
8. no seed exclusion, checkpoint promotion, canonical seed, warm restart, or unauthorized continuation occurred;
9. the machine verdict is one of the four frozen verdicts;
10. historical development NO-GO and held-out FAIL remain preserved.

Any failed integrity row stops manuscript result insertion and is reported as a technical gap rather than a performance result.

## Manuscript mappings

| Manuscript location | Machine source | Required content |
|---|---|---|
| Abstract | decision JSON and paired summary | verdict-bounded primary result, 3/5 direction, catastrophe and safety boundary |
| Section 6.2 | pooled cells | absolute UTR/DRTP values before deltas |
| Section 6.3 | paired seed results | all five seed deltas, dispersion, win count and catastrophe |
| Section 6.4 | per-condition summary | ten OOD conditions and worst condition |
| Section 6.5 | raw/condition summaries | collision, timeout, constraint, pre-trigger collision and risk-set validity |
| Section 6.6 | sampler logs and telemetry | q/EMA/difficulty/group counts and bounded mechanism description |
| Discussion/Conclusion | frozen verdict | only the wording authorized below |

## Verdict-specific writing boundary

### `FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE`

DRTP may remain the primary method. The manuscript may state that the prospective five-seed experiment supports positive mean and median robustness effects under the frozen conditions, provided the exact win counts, safety result, and any catastrophic seed are stated adjacent to the claim. It may not use “stable”, “consistently superior”, or “universally robust”.

### `FORMAL_CONFIRMATION_LIMITATION_ONLY`

The paper may report DRTP as a high-upside but unconfirmed adaptive-weighting study. Prospective superiority must not be claimed; UTR remains the reliable reference and DRTP is presented through a limitation/reliability analysis.

### `FORMAL_CONFIRMATION_FAIL_DEMOTE_DRTP`

DRTP is removed from the primary-method claim. The manuscript is reframed around relay-failure topology robustness, the matched UTR reference, and the negative result that adaptive weighting did not prospectively reproduce. No replacement algorithm is introduced.

### `FORMAL_CONFIRMATION_TECHNICAL_INVALID`

No formal performance conclusion is inserted. The manuscript remains a working draft until a separately authorized technical resolution exists.

## Prohibited post-result edits

- changing the paper metric hierarchy after seeing results;
- replacing the final checkpoint with a milestone;
- omitting a weak seed or condition;
- combining historical and formal seeds into one homogeneous inference sample;
- adding a new favorable threshold;
- rewriting historical FAIL/NO-GO decisions;
- starting a new algorithm, seed rescue, or extra training from this writing stage.

