# EDR-D1 Five-Seed One-Shot Development Training Contract

**Status:** `FROZEN BEFORE FIRST EDR MARL RUN`  
**Training protocol:** `EDR-D1-FIVE-SEED-DEVELOPMENT-TRAINING-V1`  
**Technical gate:** `TECHNICAL_PASS`

## Runs and endpoint

Exactly five EDR-SG-MAPPO runs are authorized, all from scratch and strictly
continuous: `2201`, `2202`, `2203`, `2204`, `2205`.

Each run uses `4 × 64 × 3907 = 1,000,192` environment steps.  Final checkpoint
only is eligible for development comparison.  There is no resume, checkpoint
promotion, early stopping, seed exclusion, extension, canonical seed, or
held-out seed.

## Frozen equality with T1 UTR

The clean UTR reference is
`results/development/t1_telemetry_native_reference_1m_run1`.  EDR shares its
environment, reward, critic, PPO settings, legal actor inputs, fixed 50%
nominal plus conditionally uniform six-group failure exposure, rollout,
normalization, optimizer, horizon, runtime persistence and evaluation protocol.
The only difference is `graph_encoder: single → edr`.

- SG/EDR parameters: `116,728` exactly.
- actor gradient mode: `utr` (ordinary PPO update; no projection).
- DRTP/TCR/SPC state: absent.
- runtime state: saved every 500 updates from update zero.
- frozen normalized training-config hash: `6532d194d2ad0c8e188409de0c9cda2265c4fad14a740c45de0306c62fead3f4`.

## Evaluation

The existing development-only T1 tape is reused without alteration:
namespace `920000–920099`, hash
`3de6e4fabf07bb76fe7c9271b3f3e70a5910262581ac14b3de162533ef83e6c3`.
It covers nominal, F0, timing, duration and compound perturbations.  All
episode outcomes remain in unconditional aggregates; trigger validity is
reported on the alive-at-onset risk set.

Final reports will include seed-level and pooled nominal, F0, OOD mean/worst,
collision, timeout, constraint, exposure/risk-set diagnostics, parameter/FLOPs
accounting and EDR-minus-UTR paired seed differences.  The training seed is the
independent unit.

## Stop boundary

This one-shot development experiment must end in exactly one of
`A — EDR_DEV_PASS`, `B — EDR_DEV_MIXED`, or `C — EDR_DEV_FAIL`.  It authorizes
neither a redesign nor automatic held-out/canonical work.

