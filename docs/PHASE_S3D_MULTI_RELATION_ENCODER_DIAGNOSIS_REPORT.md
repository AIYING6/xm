# Phase S3-D Multi-Relation Encoder Diagnosis Report

## Final decision

> **NO ACTIONABLE ROOT CAUSE — DROP CURRENT FULL**

This decision applies to the current `multi_relation` Full candidates tested in
S3 and S3-R2. It does not claim that every future relation-aware encoder is
invalid. It means that the available evidence does not justify one bounded
repair followed by another training round.

## Scope and provenance

The diagnosis used only existing final checkpoints and existing training logs.
No MARL training, backward pass, optimizer step, checkpoint promotion, seed
change, environment change, or evaluation-tape change was performed.

The fixed tape was `340000–340099`, with nominal and relay-failure conditions,
development seeds `1501/1502/1503`. The independent unit for comparison remains
the training seed; episode and timestep rows are nested diagnostic observations.

The read-only manifest and raw reset-state probe are recorded in:

- `results/development/phase_s3d_encoder_diagnosis/manifest.json`
- `results/development/phase_s3d_encoder_diagnosis/raw_forward_probe.csv`
- `results/development/phase_s3d_encoder_diagnosis/summary_by_seed_condition.csv`
- `results/development/phase_s3d_encoder_diagnosis/checkpoint_inventory.json`
- `results/development/phase_s3d_encoder_diagnosis/telemetry_inventory.json`

All nine checkpoint SHA256 values and nine train-log SHA256 values are in the
manifest/inventory artifacts. The manifest records
`training_started=false`, `backward_called=false`, and
`optimizer_step_called=false`.

The raw relation rows cover the two multi-relation candidates (`full` and
`simple_full_no_role_gate`) across 3 seeds, 2 conditions, and 100 tape episodes.
The Single-Graph checkpoint was loaded as the parameter-matched control but has
no relation-branch tensor to probe; its role in the diagnosis is the existing
performance/optimization control, not a fabricated multi-relation statistic.

## Findings

### 1. Relation adjacency sparsity

At the reset-state probe, across all three methods and all three seeds:

| Channel | Mean off-diagonal active edges | Empty-graph ratio |
|---|---:|---:|
| Perception | 1.0 | 0.0 |
| Communication | 4.0 | 0.0 |
| Task-Support | 2.0 | 0.0 |
| Union | 9.0 | 0.0 |

The relation branches are sparse by construction, but they are not empty.
Therefore “an empty relation branch is continuously fused into the actor” was
not established as the root cause.

### 2. Branch-scale and union residual

For the Role-Gate Full candidate, the reset-state mean union-to-mean-relation
norm ratio was approximately `1.85` in layer 1 and `1.80` in layer 2. This is a
descriptive union contribution, not evidence of a bug or a 10x domination
pathology.

For the S3-R2 no-Role-Gate candidate, the corresponding ratios were
approximately `0.85` and `1.00`. Thus the proposed union-dominance explanation
does not consistently explain both failing multi-relation candidates: removing
Role-Gate materially changed the ratio while nominal competence remained poor.

### 3. Attention behavior

Perception attention has normalized entropy around `0.20–0.25` and mean maximum
weight around `0.88–0.92`, but its mean support is only about `1.25` (one legal
edge plus the mandatory self-loop). This is expected sparse-support behavior,
not evidence of a global one-hot collapse.

Communication, Task-Support, and Union channels show broader support and
normalized entropy roughly in the `0.46–0.74` range at reset. No cross-seed
attention-degeneration signature was established.

### 4. Training optimization telemetry

The available final logs are finite and do not show a common PPO failure:

- Full final approximate KL: approximately `0.00025–0.00101`;
- No-Role-Gate Full final approximate KL: approximately `0.00036–0.00060`;
- Full final clip fraction: `0–0.0052`;
- No-Role-Gate Full final clip fraction: `0–0.0023`.

The logs contain only one aggregate `grad_norm`; historical actor-gradient and
critic-gradient norms are not present. A separate gradient diagnosis cannot be
reconstructed from a final checkpoint because gradients are not checkpoint
state. No claim about actor-versus-critic optimization causality is therefore
made.

### 5. Existing performance evidence remains negative

The S3-R2 fixed-tape result is unchanged:

| Candidate | Mean nominal score | Mean failure score | Mean degradation |
|---|---:|---:|---:|
| No-Role-Gate Full | 20.642 | 3.745 | 16.897 |
| Parameter-Matched Single-Graph | 35.922 | 28.224 | 7.698 |

The simplified Full nominal score is about `57.5%` of matched Single-Graph and
does not have a smaller mean degradation. This is not a pseudo-robustness
success.

## Why the result is not `BUG / DESIGN DEGENERACY FOUND`

The probe did not establish a single reproducible pathology that explains the
failed current Full family:

1. No relation channel is empty at reset.
2. Union dominance is present in the old Full but not in the no-Role-Gate Full,
   while both candidates fail the screening question.
3. Attention concentration is explained by sparse legal support and is not a
   cross-channel collapse.
4. Available PPO telemetry does not show a shared KL/clip/finite-value failure.
5. The decisive training-time quantities—separate actor/critic gradients,
   relation branch norms through training, and dynamic attention trajectories—
   were not archived.

Calling any of these a confirmed bug would exceed the evidence.

## Consequence

The current Full architecture is dropped from the paper's candidate lineup.
No repair-and-retrain round is authorized by this report. The project may still
continue with the validated task and the matched Single-Graph baseline, or a
separately designed simpler relation-type encoding in a future protocol. Such a
future design must be treated as a new candidate, not as a reproduction or
silent repair of the dropped Full model.

Phase 3A and formal canonical training remain **NO-GO**. No environment or
headline claim is changed by this diagnosis.
