# v1.5 Validation Split Freeze

**Freeze date:** 2026-08-04
**Supersedes / completes:** `V1_5_CHECKPOINT_SELECTOR_ADJUDICATION.md`
(which left the exact base seed open; this document fixes it).

## Frozen split

```text
validation_base_seed = 641939
episodes             = 50
scenarios            = dropout030_delay2_relay_failure_early
                       dropout030_delay2_relay_failure
                       dropout030_delay2_relay_failure_delayed
                       dropout030_delay2_relay_failure_late
```

## Deterministic seed derivation (auditable)

```text
selector SHA256 (v1.5.0) = 868C4DF3B1C837F5BE7D1073D7E2424B4C9BD95850352850743355EB2D9232E6
first 8 hex             = 868C4DF3
int("868C4DF3", 16)     = 2257341939
2257341939 mod 800000   = 541939
validation_base_seed    = 100000 + 541939 = 641939
```

The seed is derived purely from the frozen selector hash before any v1.5
evaluation, so it cannot be accused of being chosen after seeing results.

## Constraints

- `641939` must be used as the v1.5 validation base seed for **all** methods
  (Full, baselines, ablations).
- The development-diagnostic seeds `120000` (v1.4) and `888000` (supplemental
  diagnostic) are **excluded** from v1.5 selection.
- This split is frozen before any v1.5 validation run.

## Document hash

SHA256 recorded externally in `V1_5_VALIDATION_SPLIT_FREEZE.md.sha256`.
