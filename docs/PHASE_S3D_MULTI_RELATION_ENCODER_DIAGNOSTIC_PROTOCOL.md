# Phase S3-D — Multi-Relation Encoder Root-Cause Diagnosis

## Status

This is a bounded, read-only diagnosis following the S3-R2 NO-GO. It does not
authorize training, environment changes, evaluation-tape changes, checkpoint
promotion, seed changes, or hyperparameter search.

## Question

Why did the current multi-relation candidates underperform the
parameter-matched Single-Graph candidate on the frozen S3 tape?

The diagnosis compares existing final checkpoints only:

| Candidate | Source | Seeds |
|---|---|---|
| `full` | S3 three-method smoke, relation-conditioned Role-Gate | 1501, 1502, 1503 |
| `simple_full_no_role_gate` | S3-R2, multi-relation without Role-Gate | 1501, 1502, 1503 |
| `matched_single_graph` | S3 three-method smoke, parameter-matched Single-Graph | 1501, 1502, 1503 |

MAPPO is retained in the evidence inventory and training-log comparison, but
has no relation encoder and is not treated as a multi-relation mechanism
control in the forward probe.

## Frozen input and unit of analysis

- Evaluation tape: episode IDs `340000–340099`.
- Conditions: the existing nominal and relay-failure conditions.
- Policy: deterministic, fixed final checkpoint only.
- Environment and failure semantics: unchanged S2 contract.
- No canonical seeds, test results, or headline results are used.
- The independent training unit remains the training seed. Episode/timestep
  rows are diagnostic observations nested within a seed, not independent
  replicates for inferential claims.

## Measurements

For each checkpoint, seed, condition, episode, timestep, and relation channel:

1. **Adjacency sparsity**: off-diagonal active-edge count and empty-graph flag
   for Perception, Communication, Task-Support, and the union graph.
2. **Branch representation scale**: mean node-wise L2 norm of each relation
   branch and the union branch after the encoder layer.
3. **Union dominance**: union-branch norm divided by the mean relation-branch
   norm, plus the corresponding post-fusion representation norm.
4. **Attention behavior**: legal-support entropy, maximum legal attention, and
   attention support size for each branch.
5. **Training telemetry availability**: final and trajectory values of loss,
  policy loss, value loss, entropy, approximate KL, clip fraction, and the
  logged aggregate gradient norm. Separate historical actor/critic gradient
  norms are reported as unavailable unless present in source artifacts.

The forward probe records every tenth timestep and the frozen failure-boundary
steps `43`, `44`, and `45`. This bounded resolution is sufficient for branch
sparsity, scale, and attention-degeneration diagnosis while keeping the
read-only artifact reproducible on the local workstation. It is not a new
evaluation protocol and is not used to compute a headline endpoint.

The probe is instrumentation only. It does not call backward, optimizer.step,
or any training/evaluation-selection code.

A reset-state supplemental probe may be used to verify initial relation scales
and masks without rolling out a policy. Reset-state evidence alone cannot
support the bug decision; if no dynamic forward evidence is available, the
conservative outcome is `NO ACTIONABLE ROOT CAUSE — DROP CURRENT FULL`.

## Conservative interpretation rule

The result can have only one of two final decisions:

- `BUG / DESIGN DEGENERACY FOUND`: a reproducible structural or implementation
  pathology is present across the relevant development seeds and is directly
  connected to the failed candidate (for example, a consistently empty branch,
  severe branch-scale domination, or attention collapse), with the missing
  evidence and scope stated explicitly.
- `NO ACTIONABLE ROOT CAUSE — DROP CURRENT FULL`: no reproducible actionable
  pathology is established by the available forward probe and logs, or the
  necessary historical telemetry is absent. This decision drops the current
  Full candidate; it does not claim that every possible relation-aware design
  is impossible.

Descriptive differences are not promoted to a bug without a reproducible
mechanism. No third “inconclusive, train longer” outcome is permitted.

## Outputs

The executor writes only new diagnostic artifacts under
`results/development/phase_s3d_encoder_diagnosis/` and a report at
`docs/PHASE_S3D_MULTI_RELATION_ENCODER_DIAGNOSIS_REPORT.md`.
