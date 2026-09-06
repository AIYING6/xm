# DRTP stabilization: double-cohort method selection

Both downloaded archives passed SHA256 validation and each contains 14,000 raw
endpoint episodes plus a read-only reaggregation report. Cohorts remain
separate inferential units.

| Method | A mean / worst seed | B mean / worst seed |
|---|---:|---:|
| UTR | 177.02 / 79.75 | 187.18 / 164.98 |
| Original DRTP | 216.66 / 191.49 | 210.34 / 172.03 |
| EGTR | 226.13 / 203.92 | 144.00 / 29.13 |
| Global-Anchored EGTR | 210.82 / 128.64 | 181.23 / 110.07 |

**Selection:** Original DRTP is the principal method. Against UTR, its mean
perturbed-return difference is `+39.64` in A and `+23.15` in B, with `3/5` and
`4/5` positive paired seeds, respectively. Its observed worst seed exceeds
UTR in both cohorts and timeout is lower in both cohorts.

EGTR is not selected because its A-leading outcome reverses sharply in B.
Global-Anchored EGTR is not selected because it does not retain a consistent
advantage over UTR or Original DRTP. These outcomes are retained as frozen
comparisons, not hidden or retrospectively altered.

The resulting paper claim is bounded: under two completed frozen 10M cohorts
and their separate fixed endpoint tapes, Original DRTP repeatedly improves
perturbed return over UTR with favorable observed lower-tail and timeout
behavior. This does not claim universal seed-stable superiority, nor erase
earlier historical cohort-sensitivity evidence.

No further stabilization module is authorized. The next work is held-out/OOD,
matched external comparators, scale-transfer/6-UAV validation, and manuscript
evidence integration.
