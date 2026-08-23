# DRTP REL-A0 — Multi-Tape Reliability Audit Report

- Protocol: `DRTP-REL-A0-AGGREGATION-V1`
- Training started: **NO**
- Raw records: **25,000/25,000**
- Technical coverage: **PASS**
- Raw episode artifact: `artifacts/drtp_reliability_a0/full_evaluation/raw_episode_metrics.csv`

## Paired UTR/DRTP absolute performance

The following are pooled descriptive means across tapes and episodes; training seed remains the independent unit.

| condition | UTR J | DRTP J | DRTP−UTR mean | median | wins/5 | worst |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 166.1763 | 216.1181 | 49.9419 | 56.8126 | 3/5 | -21.1736 |
| f0 | 132.9569 | 174.8640 | 41.9070 | 80.2254 | 4/5 | -113.1039 |
| timing | 133.4924 | 170.0339 | 36.5415 | 65.8405 | 4/5 | -116.9032 |
| duration | 152.9341 | 197.1101 | 44.1759 | 46.9180 | 4/5 | -76.5188 |
| compound | 114.7606 | 175.8057 | 61.0451 | 87.3675 | 4/5 | -36.4877 |

## Main finding

DRTP has positive pooled and median paired return differences and wins four of
five training seeds on every failure condition. The fifth seed (2002) is a
large and consistent reversal across F0, timing, duration, and compound
conditions. The evidence therefore supports the descriptive label
**high-average-return, seed-sensitive DRTP**, not seed-stable or universally
superior DRTP.

## Seed-level table

| method | seed | J_nominal | J_f0 | J_timing | J_duration | J_compound |
|---|---:|---:|---:|---:|---:|---:|
| utr_sg | 1901 | 157.9053 | 126.5315 | 143.4511 | 174.5434 | 104.3814 |
| utr_sg | 1902 | 199.6795 | 60.0328 | 59.2906 | 116.3889 | 67.6506 |
| utr_sg | 2001 | 96.9015 | 100.2573 | 92.0724 | 91.7105 | 76.2912 |
| utr_sg | 2002 | 185.2694 | 185.3607 | 184.2611 | 186.1594 | 146.4229 |
| utr_sg | 2003 | 191.1256 | 192.6024 | 188.3867 | 195.8686 | 179.0568 |
| drtp_sg | 1901 | 229.5351 | 206.7569 | 209.2916 | 221.4613 | 208.5295 |
| drtp_sg | 1902 | 187.5368 | 162.6678 | 151.7326 | 182.0218 | 155.0182 |
| drtp_sg | 2001 | 251.4849 | 210.5539 | 196.0865 | 235.3192 | 199.8732 |
| drtp_sg | 2002 | 164.0958 | 72.2567 | 67.3579 | 109.6406 | 109.9352 |
| drtp_sg | 2003 | 247.9382 | 222.0846 | 225.7011 | 237.1075 | 205.6726 |

## Interpretation boundary

This audit reports cross-tape reliability and paired effects. It does not rewrite historical NO-GO/TECHNICAL_INVALID conclusions, does not establish universal DRTP superiority, and does not authorize new training. Weak or reversed seeds remain included.

## Stop rule

REL-A0 ends after this report. Any subsequent training or algorithm decision requires separate authorization.
