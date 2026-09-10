# P8F–P8G ACFID runner and evaluator audit

## Decision

`ACFID_RUNNER_DRYRUN_PASS` and `ACFID_FIXED_ENDPOINT_EVALUATOR_PASS`.

The result authorizes freezing a short learning-pilot contract. It does not
authorize the complete 1M-per-method experiment and is not performance
evidence.

## P8F matched clipped-PPO runner

- Training support contains nominal, all six single faults, and six frozen
  training pairs (13 sets total).
- The 44 held-out pairs, triples, and quadruples are absent from rollout data.
- Direct, additive, and ACFID policies consume the same rollout tape
  (`a37b3b0eac4d4e99d93536ea6f90961ee1a5cb898d5ecc290d00f71b67fa9410`).
- Actor parameter counts are 15,005, 15,157, and 15,119; the maximum gap is
  1.013%.
- All losses and gradients are finite and all actors update.
- No pair-identity embedding or oracle counterfactual value enters policy
  training.

The first P8F execution stopped because its audit searched its own source check
and because the realized-noise tensor had the wrong shape. That stopped output
is retained as an implementation audit, not a scientific result. The corrected
execution uses one realized two-branch transition per rollout.

## P8G fixed-endpoint evaluator

- The frozen test tape has 132 cases: three contexts for each of 44 held-out
  fault sets.
- All methods use the same context seeds, fault sets, and noise seeds.
- Evaluation is deterministic and leaves parameters byte-for-byte unchanged.
- Selected-action value and oracle action value share the same noise bank;
  action regret is therefore paired and nonnegative by construction.
- Held-out data are reporting-only and cannot select a checkpoint.

Untrained-policy success, timeout, and regret values emitted by this audit are
interface smoke diagnostics only. They must not appear as method results.

## Remaining gate

P8H must preregister a deliberately short, inexpensive learning pilot. Its job
is to establish optimization learnability and early method separation without
spending the final budget. Stop rules, seeds, endpoint, and decision thresholds
must be frozen before execution.
