# SR-DRTP P0 shadow-branch specification

## Purpose

The P0 shadow runner demonstrates a strict update-boundary state copy. It
supports `exact_replay_only`, not accept/rollback selection and not a future
intervention.

## Required copied state

- actor and critic parameters;
- optimizer state;
- global update and best-key metadata;
- Python, NumPy, CPU Torch and CUDA Torch RNG states;
- per-environment runtime state, current observations and episode counters;
- DRTP selection, q, EMA, active return window and adaptation count;
- decomposed action/minibatch/environment RNG state when enabled;
- read-only telemetry state.

## Matched execution rules

1. A branch starts only from a saved update-boundary runtime checkpoint.
2. The P0 runner rejects policy guards, KLR thresholds, intervention utility,
   counterfactual critic, and non-Original DRTP sampler modes.
3. It uses `diagnostic_rng_branch_mode=exact_replay`; future RNG is not
   replaced in P0.
4. It writes to a fresh output directory and cannot mutate the official source
   checkpoint or its log.
5. It runs no formal or held-out evaluation tape.

The P0 acceptance test is strict state equality after one uninterrupted update
versus one update after restore. It is a feasibility proof only, not an
estimate of intervention benefit.
