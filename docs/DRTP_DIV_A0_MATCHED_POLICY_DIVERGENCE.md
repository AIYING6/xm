# DRTP-DIV-A0 — Matched-State Policy Divergence

## Method

For each paired seed, the recorded UTR 500k runtime observation/graph state is
used as a common actor-legal bank. Archived UTR and DRTP models at each 0.5M
milestone are evaluated only by forward pass on this bank. Metrics are action
total variation, Jensen–Shannon divergence, entropy difference, and greedy
action disagreement. Each bank contains 4 environment states × 3 agents.

## Result

DRTP and UTR policies diverge substantially for **all** historical seed
classes; weak seeds do not show an earlier or larger unique divergence.

| milestone | weak mean TV / JS | strong mean TV / JS |
|---|---:|---:|
| 0.5M | 0.458 / 0.159 | 0.535 / 0.221 |
| 1M | 0.658 / 0.308 | 0.612 / 0.292 |
| 2M | 0.599 / 0.270 | 0.610 / 0.320 |
| 3M | 0.690 / 0.351 | 0.732 / 0.433 |
| 10M | 0.701 / 0.376 | 0.737 / 0.435 |

At 0.5M, the weak average is lower than the strong average. At 3M and 10M it
remains lower. Thus policy mapping difference from UTR is a general consequence
of DRTP training, not a discriminative precursor of weak outcomes.

## H2 assessment

**H2 — matched-state policy divergence first: not supported.** The bank is
sparse and does not establish behavior, but it is sufficient to rule out the
proposed pattern of a common early excess DRTP–UTR policy divergence confined to
weak seeds.

