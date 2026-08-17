# DRTP-SG-MAPPO Held-out Confirmation v2 Audit Report

**Verdict: `HELD_OUT_FAIL`.** This report audits the uploaded held-out result
archive and records the v2 decision without changing the historical v1
development `NO-GO` conclusion.

## Scope and provenance

- Archive: `drtp_heldout_v2_results.tar.gz`
- Archive SHA256:
  `fcfd308fe84bb5214c6adc7cad98a562d7e1df86497bebde6e8b57f78acc7949`
- Training seeds: 2001, 2002, and 2003 only; no canonical seeds were used.
- Arms: UTR-SG-MAPPO and DRTP-SG-MAPPO.
- Training budget: 39,063 updates = 10,000,128 environment steps per arm/seed.
- Evaluation tape: 430000--430099; SHA256
  `6522353d962918e06fd40d54571436eee3800fbf0eb88e2453db53b45aecb99e`.
- Evaluation design: 12 fixed nominal/F0/OOD conditions x 100 episodes x 6
  final checkpoints = 7,200 raw episode records.
- Primary inference unit: training seed (`n=3`), not individual episode.

## Integrity audit

All six run manifests report `completed`. Each run was from scratch, used the
common 10M final checkpoint only, and reports a strict continuous trajectory,
no runtime resume, no warm restart, no early stopping, no checkpoint promotion,
and runtime-state persistence from update zero. The archived SHA256 of every
final model checkpoint and final runtime-state checkpoint matches its manifest.

The evaluation manifest is complete, binds the 430000--430099 held-out tape,
contains 7,200 raw rows, and explicitly records that the development tape and
canonical seeds were not used.

## Final-10M results

| Arm | Seed | J nominal | J F0 | J OOD mean | J OOD worst | Failure exposure | Collision | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UTR-SG | 2001 | 99.223 | 102.603 | 91.713 | 77.737 | 1.000 | 0.0527 | 0.9345 |
| DRTP-SG | 2001 | 248.282 | 206.868 | 198.913 | 170.363 | 0.9636 | 0.0564 | 0.4782 |
| UTR-SG | 2002 | 187.061 | 186.921 | 176.961 | 150.697 | 1.000 | 0.0000 | 0.5145 |
| DRTP-SG | 2002 | 170.807 | 72.970 | 88.835 | 53.597 | 1.000 | 0.0036 | 0.9064 |
| UTR-SG | 2003 | 194.740 | 197.038 | 196.390 | 186.628 | 1.000 | 0.0145 | 0.8864 |
| DRTP-SG | 2003 | 245.390 | 226.842 | 222.695 | 210.316 | 0.9782 | 0.0309 | 0.7955 |

Pooled means are 160.341/162.187/155.021/138.354 for UTR-SG and
221.493/168.893/170.147/144.758 for DRTP-SG, in the order nominal/F0/OOD
mean/OOD worst. Thus, pooled DRTP-over-UTR ratios are 1.381, 1.041, 1.098, and
1.046, respectively.

## Why the confirmation failed

The result is not a v1 self-reference-ratio failure: both `R_OOD_mean` and
`R_OOD_worst` were reported only as descriptive diagnostics under v2. The v2
hard-gate result is instead driven by independent-seed inconsistency and the
pre-registered absolute/safety gates:

- `nominal_retention`: PASS.
- `F0_retention`: FAIL.
- `OOD_mean`: PASS.
- `OOD_worst`: FAIL.
- `constraints`: PASS.
- `collision_safety`: PASS.
- `timeout_safety`: FAIL.
- `all_planned_pairs_reported`: PASS.

Seed 2002 is a true adverse realization under the frozen protocol, not an
evaluation omission: DRTP-SG is lower than UTR-SG by 88.126 in OOD mean and by
97.100 in OOD worst, with F0 falling from 186.921 to 72.970. Its failure
exposure is 1.0, so the reversal cannot be attributed to unexposed failures.
It also has a substantially higher timeout rate (0.9064 versus 0.5145).

Seeds 2001 and 2003 favor DRTP-SG in OOD outcomes, but the central claim needs
stable performance across independent training seeds. With `n=3`, the pooled
advantage is insufficient to override the pre-registered F0, OOD-worst, and
safety failures.

## Interpretation boundary and required stop

The data support only a descriptive statement that DRTP-SG had favorable
pooled means in this held-out set. They do **not** support the confirmatory
claim that DRTP-SG reliably improves F0 or worst-case OOD robustness over the
capacity- and topology-group-matched UTR-SG baseline.

Accordingly, canonical seeds, formal five-seed training, ablations, and
follow-on OOD studies remain unstarted. No failed seed may be excluded, no
checkpoint may be promoted, and no method or threshold may be revised from
these data. Any future project decision must be a separately authorized
post-failure analysis or a new scientific route, rather than a continuation of
this DRTP confirmation.
