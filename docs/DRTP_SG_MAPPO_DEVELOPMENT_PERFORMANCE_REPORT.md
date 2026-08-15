# DRTP-SG-MAPPO Development Performance Report

## Decision

**Development retention: NO-GO. Held-out confirmation (`2001/2002/2003`): NOT
AUTHORIZED.**

The development result contains a strong pooled DRTP signal at 3M, but it does
not meet the pre-registered stopping and retention contract:

1. DRTP's pooled `J_OOD_worst` improved by 36.97% from approximately 2.5M to
   3M, with non-negative improvement in both development seeds. The frozen 3M
   cap therefore yields `training maturity unresolved at <=3M`.
2. The final 3M development retention rows for F0, OOD mean, and timeout safety
   fail. Pooled improvements cannot override a failed seed-consistency or
   condition-level safety rule.

No held-out tape, held-out seed, canonical seed, new algorithm, or additional
training has been started as a consequence of this report.

## Provenance and completeness

| item | verified value |
|---|---|
| input archive | `drtp_sg_development_results.tar.gz` |
| archive SHA256 | `2025d3d1b49718e727eb97c87982501eb15b1a7d3c94a33a586082f6da4be1c1` |
| method implementation commit | `8267887` |
| development controller commit | `a26b3167c13fb139c61d1839d39c5db147ae45a4` |
| completed run manifests | 12 (UTR/DRTP x seeds 1901/1902 x budgets 1M/2M/3M) |
| checkpoint hash verification | PASS for all 12 final checkpoints |
| evaluation rows | 9,600 raw rows and 96 seed-condition summary rows at each budget |
| development tape | `420000–420099`; 100 base IDs x 12 paired conditions |
| held-out tape `430000–430099` | not generated or used |
| canonical seeds `0–4` | not used |

The final 3M checkpoint SHA256 values are:

| arm | seed 1901 | seed 1902 |
|---|---|---|
| UTR-SG | `d1f97ed242176b145a0ebadebfc62e4c852c08d703b1f24f8913d1c89e5709ae` | `dd2b105f0163d1ff33ecc7d28a498f50211b63e74ca08d567bebfe165aa5c657` |
| DRTP-SG | `d09b9243a5d78818603f3b32b31e62da0c4f58a01459694a1bd2e3b9c5812e3a` | `d0b3131e94b88703ec3e9cadc3c46d7eb152133cce55164c8e33321a88f71109` |

Every trajectory was a separate from-scratch run at its common budget: 1M
(`1,000,192` steps), 2M (`2,000,128`), and 3M (`3,000,064`). Milestones were
curve-only and were not selected as method-result checkpoints.

## Pre-registered maturity results

The primary maturity metric was pooled `J_OOD_worst`.

| boundary | arm triggering common extension | pooled change | two-seed direction | decision |
|---|---|---:|---|---|
| 750k -> 1M | UTR-SG | +11.61% | both non-negative | run all arms fresh to 2M |
| 1.5M -> 2M | UTR-SG | +38.52% | both non-negative | run all arms fresh to 3M |
| 2.5M -> 3M | DRTP-SG | +36.97% | both non-negative | maximum reached; maturity unresolved |

At the last boundary, UTR-SG changed by +3.85% but failed the two-seed direction
rule. DRTP-SG was the sole trigger: seed 1901 increased from 125.92 to 180.65
(+43.47%) and seed 1902 from 125.58 to 163.83 (+30.46%). This is evidence that
the DRTP final-budget estimate is still sensitive to training budget; it is not
evidence that a 3M checkpoint may be replaced by a better intermediate point.

The fixed training logs retain the required curve points: 500k/750k/1M for the
1M trajectories, 1.5M/2M for the 2M trajectories, and 2.5M/3M for the 3M
trajectories. These raw curves are provenance artifacts only; their noisy
per-update rewards were not used for method selection.

## Final 3M performance: descriptive development evidence

| metric | UTR pooled | DRTP pooled | DRTP / UTR |
|---|---:|---:|---:|
| `J_nominal` | 147.157 | 171.007 | 1.162 |
| `J_F0` | 127.929 | 183.880 | 1.437 |
| `J_OOD_mean` | 120.607 | 183.464 | 1.521 |
| `J_OOD_worst` | 103.149 | 172.241 | 1.670 |
| `R_OOD_mean` | 0.960 | 0.998 | 1.040 |
| `R_OOD_worst` | 0.816 | 0.937 | 1.148 |
| failure collision rate | 0.0136 | 0.0014 | — |
| failure timeout rate | 0.8086 | 0.5600 | — |
| failure constraint violation | 0.0000 | 0.0000 | — |
| failure exposure | 1.0000 | 1.0000 | — |

This is a positive pooled signal, especially for OOD worst-case performance. It
is nevertheless descriptive development evidence only: the independent units
for a method comparison are the two training seeds, not the 100 deterministic
evaluation episodes within each seed. No p value, confidence interval, or paper
superiority claim is justified from these two development seeds.

## Seed consistency and failed gate rows

| final 3M metric | seed 1901: UTR -> DRTP | seed 1902: UTR -> DRTP | contract outcome |
|---|---:|---:|---|
| `J_nominal` | 89.226 -> 130.020 | 205.087 -> 211.995 | PASS |
| `J_F0` | 59.997 -> 193.586 | 195.862 -> 174.175 | FAIL: seed 1902 ratio 0.889 < 0.90 |
| `J_OOD_mean` | 59.602 -> 191.100 | 181.613 -> 175.828 | FAIL: seed 1902 direction negative |
| `J_OOD_worst` | 50.017 -> 180.648 | 156.281 -> 163.833 | PASS |

The collision row passes and constraints remain exactly zero. The timeout safety
row fails despite DRTP's lower pooled timeout rate: at seed 1902 under
`compound_60_120`, DRTP minus UTR timeout was `+0.19`, exceeding the frozen
per-seed-condition ceiling of `+0.10`. This row cannot be replaced by a pooled
average.

## Interpretation boundary and next state

The evidence supports neither a mature performance estimate nor development
authorization for held-out confirmation. The correct current state is:

```text
3M development complete
training maturity unresolved at <=3M
development retention NO-GO
held-out confirmation NO-GO
```

The result does support one bounded observation for future protocol design:
under the same seven-group training universe and nominal anchor, DRTP showed a
large pooled 3M OOD signal, but it was not sufficiently seed-consistent across
all frozen retention and safety rows. Any 4M–6M extension, if later considered,
must be separately pre-registered with a common fresh budget for all four arms;
it must not reuse an intermediate checkpoint or selectively extend DRTP.
