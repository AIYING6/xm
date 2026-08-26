# DRTP S1-R P3 — G/B Reference Training Contract

## Status

This contract is frozen for the separately authorized P3 reference stage. It
does not authorize P4 intervention training, new seeds, held-out runs, or
canonical seeds.

Historical S1-R v1/v2 conclusions and the P2 technical-license report remain
unchanged.

## Authorized runs

| Run | Reference | Training seed | RNG tuple | Budget |
|---|---|---:|---|---:|
| `R0_G_REF` | G reference | 2001 | frozen `G` tuple | 1,000,192 env steps |
| `R1_B_REF` | B reference | 2002 | frozen `B` tuple | 1,000,192 env steps |

The selected identities and all six stream values are read from
`artifacts/drtp_s1r_protocol_v2/frozen_contract.json` and
`artifacts/drtp_s1r_protocol_v2/rng_tuples.json`; they are not re-derived or
manually replaced by the runner.

## Frozen training conditions

- SG single-graph backbone, 116,728 parameters.
- Existing PPO, reward, S2 environment, failure semantics, and actor
  information boundary unchanged.
- Existing DRTP seven-group sampler and configuration unchanged.
- Four parallel environments and 64-step rollouts.
- 3,907 updates, exactly 1,000,192 environment steps per run.
- Strict from-scratch execution; no resume, warm restart, early stopping,
  checkpoint promotion, extension, seed exclusion, or canonical seed.
- Runtime-state persistence is enabled from update 0.
- Milestones are diagnostic only and cannot replace the final checkpoint.

## Required milestone artifacts

At updates 976, 1,953, 2,930, and 3,907, corresponding to 250,048,
500,096, 750,144, and 1,000,192 environment steps, each run must retain:

- model, optimizer/training-state, and complete runtime-state checkpoints;
- checkpoint SHA256 records;
- training/PPO telemetry and DRTP sampler telemetry;
- milestone trajectory/precursor telemetry and legal probe-bank readback;
- manifest fields proving the run identity, seed, tuple, budget, and
  from-scratch status.

## Evaluation and gates

Only after both runs pass technical completeness may the final checkpoints be
evaluated on the imported REL-A0 tapes T0–T4. The full result contains 5,000
raw episode records: two references × five tapes × five conditions × 100
episodes.

The frozen P3 gates are:

- **R1:** all four failure-return mean gaps `G_REF - B_REF` are positive.
- **R2:** at least three of four return metrics favor G on at least four of
  five tapes.
- **R3:** timeout quality favors G in the pooled mean and on at least three of
  five tapes.
- **M2 precursor:** the 500,096-step TP50 subset is confirmatory only. At
  least two of the three frozen precursor metrics must separate G and B under
  the existing eligibility rule.

The only allowed P3 outcomes are:

`P3_REFERENCE_QUALIFIED`, `F_REFERENCE_NOT_REPRODUCED`,
`F_PRECURSOR_REFERENCE_NOT_SEPARATED`, and `P3_TECHNICAL_INVALID`.

P4 is not started automatically under any outcome.
