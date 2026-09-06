# DRTP final paper evidence tables (frozen skeleton)

Terminology: **robustness benefit** means higher frozen-endpoint perturbed return under the stated condition set; **reliability** means the observed seed-level lower-tail, spread and safety profile. Neither term means universal seed-stable superiority.

## Table A — Cohort A (completed)

| Method | Perturbed mean | Worst seed | Sample SD | Primary inference unit |
|---|---:|---:|---:|---|
| UTR | 177.02 | 79.75 | 64.53 | training seed |
| Original DRTP | 216.66 | 191.49 | 23.48 | training seed |
| EGTR | 226.13 | 203.92 | 15.86 | training seed |
| GA-EGTR alpha=.75 | 210.82 | 128.64 | 46.73 | training seed |

## Table B — Cohort B (completed)

| Method | Perturbed mean | Worst seed | Sample SD | Primary inference unit |
|---|---:|---:|---:|---|
| UTR | 187.18 | 164.98 | 21.66 | training seed |
| Original DRTP | 210.34 | 172.03 | 30.54 | training seed |
| EGTR | 144.00 | 29.13 | 76.84 | training seed |
| GA-EGTR alpha=.75 | 181.23 | 110.07 | 40.62 | training seed |

## Table C — Frozen held-out structural OOD (do not populate until the cloud evaluation is complete)

| Condition | UTR | Original DRTP | Paired direction | Timeout | Collision |
|---|---:|---:|---:|---:|---:|
| structural_scout_node |  |  |  |  |  |
| structural_symmetric_longest_edge |  |  |  |  |  |
| structural_directed_longest_edge |  |  |  |  |  |
| structural_scout_node_plus_edge |  |  |  |  |  |

## Table D — External comparator (blank until separately executed)

| Method | Budget | Matched cohort | Perturbed return | Lower-tail | Timeout / collision |
|---|---:|---|---:|---:|---:|
| UTR |  |  |  |  |  |
| Original DRTP |  |  |  |  |  |
| PLR-style replay |  |  |  |  |  |

## Table E — 6-UAV cross-scale (blank until separately executed)

| Method | Scale | Budget | Robust return | Lower-tail | Safety |
|---|---|---:|---:|---:|---:|
| UTR | 2S/2R/2T |  |  |  |  |
| Original DRTP | 2S/2R/2T |  |  |  |  |
