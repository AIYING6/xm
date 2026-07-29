# Chain Auxiliary Development Comparison Protocol

Last updated: 2026-07-28

## Purpose

This protocol checks whether explicit kill-chain auxiliary learning improves the
main method before launching another expensive 1M/2M formal training batch.

The comparison is:

- EA-RG-MAPPO;
- EA-RG-MAPPO + Chain Auxiliary.

Both methods must use the same environment, seeds, budget, and validation rule.

## Training Scenario

Use a fixed hard communication condition and randomized relay-failure timing:

- env: `3d_intercept`;
- target policy: `straight`;
- strict target sensing: enabled;
- actor target information bottleneck: enabled;
- communication dropout: `0.30`;
- message delay: `2`;
- failed blue agent: `1`;
- node failure start: randomly sampled from `[25, 70]`;
- node failure duration: `80`.

This is a frozen training distribution, not another cherry-picked single
scenario.

## Stage A: 100-Update Development Check

Run seeds 0/1/2 for both methods. This is not paper evidence. It only checks:

- training does not collapse;
- `chain_aux_loss` decreases or remains finite;
- `chain_aux_acc` is meaningfully above chance;
- validation-selected recovery does not get worse.

If the auxiliary version is clearly worse at this stage, do not launch 1M.

## Stage B: 1M Development Run

Launch 1M only if Stage A is neutral or positive.

Use identical seeds and budget for both methods. After training, run validation
checkpoint selection on the frozen scenario suite:

- `dropout030_delay2_relay_failure`;
- `dropout030_delay2_relay_failure_early`;
- `dropout030_delay2_relay_failure_delayed`;
- `dropout030_delay2_relay_failure_late`.

## Decision Rule

The auxiliary version is worth keeping only if it improves at least two of:

- mean recovery rate;
- worst-seed recovery rate;
- recovery time;
- cross-scenario stability;
- EA-vs-Single-Graph margin.

If it does not improve these, keep the original EA-RG-MAPPO and move to a
conservative paper claim.

