# Phase FL — Training-Maturity Upper-Bound Report

## Final conclusion

The 1M-step maturity experiment establishes that the frozen F0 failure condition **is learnable by the existing matched Single-Graph backbone when trained for a sufficiently long fixed budget**. The earlier 300k FL result therefore should not be interpreted as proof that failure is unlearnable.

At the 1M final checkpoint:

- F0 expert pooled `J_failure = 63.9176`;
- nominal expert pooled `J_failure = 23.6345`;
- pooled failure-score gain `G_F = +40.2831` (`+170.44%` relative to the nominal expert);
- F0 expert pooled `J_nominal = 59.7746` versus nominal expert `65.0348` (`-8.09%`).

The F0 expert improves failure behavior in both seeds, but the nominal effect is heterogeneous: it decreases nominal performance for seed 1801 and increases it for seed 1802. This experiment therefore confirms failure learnability at long budget, but does not by itself establish a stable nominal–failure interference law or authorize a new algorithm.

## Protocol integrity

- Archive: `phase_fl_maturity_results.tar.gz`
- Archive SHA256: `31A4CA6BA8C3FD6B38CCB1A53BF5447609B4287DE3736AB203387F354C7E95A6`
- Arms: `fl_nominal_expert`, `fl_f0_expert`
- Seeds: `1801,1802`
- Completed runs: `4/4`
- Budget: `4 × 64 × 3907 = 1,000,192` env steps per run
- Architecture: matched Single-Graph, `116,728` parameters
- Evaluation: final 1M checkpoint on FL tape `370000–370049`
- Tape hash: `1a56599c869e031e2df90ada85942c3298e221b23caa450c005285e739ab0625`
- Milestones: saved for curve analysis only; no checkpoint selection
- Canonical seeds, new algorithms, new losses, and new curricula: not used

All manifests report final completion, `3907` updates, no resume, no early stopping, and no checkpoint promotion.

## Per-seed final evaluation

| Arm | Seed | J_nominal | J_failure | Delta_J | Collision failure | Timeout failure | Constraint failure | Exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Nominal expert | 1801 | 107.9009 | 35.6247 | 72.2762 | 0.00 | 1.00 | 0.00 | 1.00 |
| Nominal expert | 1802 | 22.1687 | 11.6443 | 10.5244 | 0.00 | 0.94 | 0.00 | 1.00 |
| F0 expert | 1801 | 80.3808 | 63.6048 | 16.7759 | 0.00 | 1.00 | 0.00 | 1.00 |
| F0 expert | 1802 | 39.1684 | 64.2305 | -25.0621 | 0.02 | 0.98 | 0.00 | 1.00 |

## Pooled final evaluation

| Arm | J_nominal | J_failure | Delta_J | Collision failure | Timeout failure | Constraint failure |
|---|---:|---:|---:|---:|---:|---:|
| Nominal expert | 65.0348 | 23.6345 | 41.4003 | 0.00 | 0.97 | 0.00 |
| F0 expert | 59.7746 | 63.9176 | -4.1431 | 0.01 | 0.99 | 0.00 |

The negative pooled `Delta_J` for the F0 expert means its final policy performed better under the F0 evaluation condition than under the nominal evaluation condition. This is a diagnostic specialization pattern, not a claim that failure is preferable as a task condition.

## Training maturity curve

Values below are pooled across the two seeds at the fixed milestones. Milestones are not selected checkpoints.

| Arm | Milestone | Actual steps | Train reward | Loss | Approx. KL | Clip fraction | Explained variance |
|---|---|---:|---:|---:|---:|---:|---:|
| Nominal expert | 300k | 300,032 | 0.0760 | 0.1250 | 0.0008 | 0.0042 | 0.9012 |
| Nominal expert | 500k | 499,968 | 0.0550 | 0.2973 | 0.0009 | 0.0046 | 0.8083 |
| Nominal expert | 750k | 750,080 | 0.1054 | 0.0818 | 0.0016 | 0.0104 | 0.9802 |
| Nominal expert | 1M | 1,000,192 | 0.1395 | 0.2887 | 0.0008 | 0.0024 | 0.9679 |
| F0 expert | 300k | 300,032 | 0.0149 | 0.0312 | 0.0006 | 0.0020 | 0.9720 |
| F0 expert | 500k | 499,968 | 0.0664 | 0.3982 | 0.0005 | 0.0003 | 0.7898 |
| F0 expert | 750k | 750,080 | 0.1169 | 0.6124 | 0.0005 | 0.0005 | 0.8227 |
| F0 expert | 1M | 1,000,192 | 0.1522 | 0.4597 | 0.0004 | 0.0000 | 0.8913 |

The F0 expert's failure competence emerges only at the longer budget: its final failure score is approximately `16.36` at the earlier 300k FL experiment but `63.92` after the fixed 1M maturity budget. This is the central maturity finding.

## Final topology/path telemetry

| Metric during failure | Nominal expert | F0 expert |
|---|---:|---:|
| Episode length | 260.00 | 259.74 |
| Path switches | 1.30 | 5.58 |
| Direct-path fraction | 0.0038 | 0.3588 |
| Relay-path fraction | 0.0000 | 0.0000 |
| Task-support fraction | 0.0000 | 0.1803 |
| Legal-information fraction | 0.0038 | 0.4701 |
| Mean cache age | 44.3167 | 18.4914 |
| Traveled distance | 142,826.90 | 162,473.90 |
| Control effort | 1,180.86 | 996.49 |

The F0 expert uses more direct-path and task-support availability, with lower cache age, while also switching paths more often. These are consistent with a policy specialized to the F0 topology, but they do not identify which future algorithm should be used.

## Decision boundary

```text
Failure learnability at long budget: ESTABLISHED
300k failure-only training: insufficient for this backbone/condition
Stable shared-policy interference: NOT ESTABLISHED by this experiment
New algorithm design: STOP
New training: STOP
TP-2: NO-GO
```

The project should not launch another diagnostic or invent a new loss from this result. The only defensible conclusion is that training maturity materially changes failure competence, and any future shared-policy experiment would require a separately authorized protocol.
