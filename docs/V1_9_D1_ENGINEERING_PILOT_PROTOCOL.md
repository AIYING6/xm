# v1.9 D1 Engineering Feasibility Pilot Protocol

**Status: prepared, not launched.** D1 is an engineering gate, not formal
evidence. Its output may not be used in a paper, to choose a final architecture,
or to inspect a confirmatory population.

## Purpose

Verify on a CUDA instance that PCRF has no runtime/shape/provenance failure,
that its conflict gate remains numerically active, and that training-time
snapshot/event artifacts can be persisted under a realistic rollout load.

## Fixed D1 matrix

| Method | encoder | hidden width | engineering seeds |
|---|---|---:|---|
| PCRF | `pcrf` | 128 | 9101, 9102 |
| parameter-matched wider single graph | `single` | 168 | 9101, 9102 |

The width pairing was fixed by D0 actor-parameter audit: 196,856 PCRF actor
parameters versus 195,837 single-graph actor parameters (0.52% gap).

## Common non-formal settings

- 8 environments; 128 rollout steps; 20 updates; PPO epochs 4;
- strict recipient-specific sensing/bottleneck; communication dropout 0.3;
  message delay 2; radar dropout 0.1;
- relay 1; failure onset 40; failure duration 80; `K=4`; min-success step 80;
- validation at updates 1, 10, 20; four fixed episodes per seed;
- immutable snapshots and episode event/censor records enabled;
- fresh engineering validation base seeds `2910100 + 100*(seed-9100)`;
- CUDA is required. CPU is not a substitute for this throughput/memory gate.

The shortened update count and four validation episodes are intentional. They
are not a reduced formal matrix and cannot estimate method superiority.

## D1 pass criteria

1. CUDA runtime manifest is written before training.
2. All four runs finish 20 updates without NaN, crash, or shape failure.
3. Each run has exactly snapshots and immutable event records at updates 1, 10,
   and 20, with re-verifiable hashes/provenance.
4. R5 actor-boundary suite passes on the same source commit.
5. PCRF diagnostics are finite; its gate is non-uniform on a fixed conflict
   batch and has nonzero gradient in the D0 test.
6. The artifact gate reports no missing/modified file.

## Stopping rules

Stop on an actor-boundary deviation, unavailable CUDA, NaN, missing snapshot,
event-record/hash mismatch, or a PCRF gate that is numerically non-finite.
Do not alter hidden width, reward, optimizer, or training length after seeing
pilot reward or validation values. Any repair requires a new D1 protocol
revision and author decision.

## Explicitly excluded

- no formal method comparison;
- no checkpoint selection claim;
- no confirmatory/held-out or OOD episode;
- no MAPPO/HAPPO, ablation, or Role-Pair experiment;
- no architecture selection from pilot performance.
